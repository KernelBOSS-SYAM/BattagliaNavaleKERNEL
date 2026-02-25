import pygame
import sys
import Grid
import Nave
import AI

# -----------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------
pygame.init()
pygame.font.init()

SCREEN_W, SCREEN_H = 1400, 900
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Battaglia Navale")

font_big   = pygame.font.SysFont("arial", 32, bold=True)
font_med   = pygame.font.SysFont("arial", 22)
font_small = pygame.font.SysFont("arial", 16)

# -----------------------------------------------------------------------
# Backgrounds
# -----------------------------------------------------------------------
main_bg  = pygame.image.load('./img/main.png').convert()
main_bg  = pygame.transform.scale(main_bg, (700, 900))
radar_bg = pygame.image.load('./img/radar.jpg').convert()
radar_bg = pygame.transform.scale(radar_bg, (700, 900))

# -----------------------------------------------------------------------
# Grid  (13x13 as per documentation)
# -----------------------------------------------------------------------
CELL           = 40
COLS           = 13
ROWS           = 13
MY_OFFSET_X    = 90
MY_OFFSET_Y    = 150
ENEMY_OFFSET_X = 790
ENEMY_OFFSET_Y = 150

my_grid    = Grid.Grid(CELL, COLS, ROWS, (59, 68, 255))
enemy_grid = Grid.Grid(CELL, COLS, ROWS, (0, 255, 0))

# -----------------------------------------------------------------------
# Player ships
# -----------------------------------------------------------------------
ships = [
    Nave.Nave("portaerei",          "./img/portaAerei.png",        5),
    Nave.Nave("corazzata",          "./img/corazzata.png",         4),
    Nave.Nave("incrociatore1",      "./img/incrociatore.png",      3),
    Nave.Nave("incrociatore2",      "./img/incrociatore.png",      3),
    Nave.Nave("cacciatorpediniere", "./img/cacciatorpediniere.png", 2),
]

TOTAL_SHIP_CELLS = sum(s.dimesione for s in ships)  # 17

DOCK_POSITIONS = [(80,720),(180,720),(280,720),(380,720),(480,720)]
for i, ship in enumerate(ships):
    img = pygame.image.load(ship.path_img).convert_alpha()
    ship.rect = img.get_rect(topleft=DOCK_POSITIONS[i])

# -----------------------------------------------------------------------
# State tracked in main.py — Grid.py and Nave.py untouched
# -----------------------------------------------------------------------

# Placement
player_ship_cells = {}          # (col, row) -> Nave
player_occupied   = set()
ship_placed       = {s: False for s in ships}
ship_grid_cells   = {s: []    for s in ships}
ship_rotation     = {s: 0     for s in ships}

# Boards: (col,row) -> "hit" | "miss" | "pending"
my_board    = {}   # AI shooting at player
enemy_board = {}   # Player shooting at AI

# -----------------------------------------------------------------------
# Shot system (core rule from documentation)
#
# shots_available = number of YOUR ship cells that are not yet hit
# Each turn the player selects exactly that many cells, then fires all at once.
# A hit-but-not-sunk cell costs 1 shot next turn (it's already removed from
# the available pool because it's now in my_board as "hit").
# A fully sunk ship contributes 0 shots (all its cells are hit).
# -----------------------------------------------------------------------

def player_shots_available():
    """Remaining un-hit player ship cells = shots for this turn."""
    hit_cells = {c for c, st in my_board.items() if st == "hit"}
    return TOTAL_SHIP_CELLS - len(hit_cells)

def ai_shots_available():
    """Same rule for the AI."""
    hit_cells = {c for c, st in enemy_board.items() if st == "hit"}
    return TOTAL_SHIP_CELLS - len(hit_cells)

# AI
ai             = AI.AIOpponent()
AI_TOTAL_CELLS = len(ai.ship_cells)

# Battle state
# "player_selecting" → player clicks cells to queue shots
# "analysis"         → show results of the volley, then AI fires
STATE        = "placement"
winner       = ""

# Player's queued targets for this turn (pending clicks)
player_targets = []   # list of (col,row) selected this turn

# Analysis panel: list of result strings shown after a volley
analysis_lines  = []
analysis_timer  = 0       # how long to show analysis before moving on
ANALYSIS_DELAY  = 2500    # ms

status_msg   = "Trascina le navi sulla tua griglia. Premi R per ruotare."
status_color = (255, 255, 255)

clock = pygame.time.Clock()

# -----------------------------------------------------------------------
# Helpers — placement
# -----------------------------------------------------------------------

def get_snap_cells(ship, col, row):
    size     = ship.dimesione
    rotation = ship_rotation[ship]
    cells    = [(col, row + i) if rotation == 0 else (col + i, row) for i in range(size)]
    for c, r in cells:
        if not (0 <= c < COLS and 0 <= r < ROWS):
            return None
        if (c, r) in player_occupied:
            return None
    return cells

def ship_pixel_rect(ship, cells):
    cols_ = [c for c, r in cells]
    rows_ = [r for c, r in cells]
    px = MY_OFFSET_X + min(cols_) * CELL
    py = MY_OFFSET_Y + min(rows_) * CELL
    w  = (max(cols_) - min(cols_) + 1) * CELL
    h  = (max(rows_) - min(rows_) + 1) * CELL
    return pygame.Rect(px, py, w, h)

def draw_ship_on_grid(ship, cells):
    rect = ship_pixel_rect(ship, cells)
    img  = pygame.image.load(ship.path_img).convert_alpha()
    if ship_rotation[ship] == 90:
        img = pygame.transform.rotate(img, 90)
    img = pygame.transform.scale(img, (rect.width, rect.height))
    screen.blit(img, rect.topleft)

# -----------------------------------------------------------------------
# Helpers — drawing markers
# -----------------------------------------------------------------------

def draw_board_markers(board, offset_x, offset_y):
    for (col, row), state in board.items():
        rx  = offset_x + col * CELL
        ry  = offset_y + row * CELL
        pad = 6
        if state == "hit":
            pygame.draw.rect(screen, (200, 40, 40), (rx, ry, CELL, CELL))
            pygame.draw.line(screen, (255,255,255), (rx+pad, ry+pad),      (rx+CELL-pad, ry+CELL-pad), 3)
            pygame.draw.line(screen, (255,255,255), (rx+CELL-pad, ry+pad), (rx+pad,      ry+CELL-pad), 3)
        elif state == "miss":
            pygame.draw.rect(screen, (40, 80, 160), (rx, ry, CELL, CELL))
            pygame.draw.circle(screen, (255,255,255), (rx + CELL//2, ry + CELL//2), 6)
        elif state == "pending":
            # Highlighted cells queued for firing this turn
            pygame.draw.rect(screen, (255, 220, 0), (rx, ry, CELL, CELL))
            pygame.draw.rect(screen, (255, 255,255), (rx, ry, CELL, CELL), 2)

def draw_pending_targets():
    """Highlight cells the player has selected this turn."""
    for col, row in player_targets:
        rx = ENEMY_OFFSET_X + col * CELL
        ry = ENEMY_OFFSET_Y + row * CELL
        pygame.draw.rect(screen, (255, 220, 0), (rx, ry, CELL, CELL))
        pygame.draw.rect(screen, (255, 255, 255), (rx, ry, CELL, CELL), 2)

# -----------------------------------------------------------------------
# Helpers — battle logic
# -----------------------------------------------------------------------

def check_sunk(hits_set, all_ship_cells_set, ship_configs):
    """
    Given a set of hit cells, check if any complete ship is newly sunk.
    Returns list of sunk ship sizes found.
    """
    visited, components = set(), []

    def bfs(start):
        q, comp = [start], set()
        while q:
            cell = q.pop()
            if cell in visited: continue
            visited.add(cell); comp.add(cell)
            c, r = cell
            for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
                nb = (c+dc, r+dr)
                if nb in hits_set and nb not in visited:
                    q.append(nb)
        return comp

    for cell in hits_set:
        if cell not in visited:
            components.append(bfs(cell))

    sizes_remaining = [s for _, s in ship_configs]
    sunk = []
    for comp in components:
        if all(c in all_ship_cells_set for c in comp):
            sz = len(comp)
            if sz in sizes_remaining:
                sizes_remaining.remove(sz)
                sunk.append(sz)
    return sunk

def resolve_player_volley():
    """
    Fire all player_targets at once. Build analysis lines. 
    Returns True if player wins.
    """
    global analysis_lines
    analysis_lines = []
    hits_this_turn = []
    misses_this_turn = []

    for col, row in player_targets:
        coord = f"{chr(65 + col)}{row + 1}"
        if ai.has_ship_at(col, row):
            enemy_board[(col, row)] = "hit"
            hits_this_turn.append((col, row))
            analysis_lines.append(f"  {coord} → COLPITO!")
        else:
            enemy_board[(col, row)] = "miss"
            misses_this_turn.append((col, row))
            analysis_lines.append(f"  {coord} → Acqua")

    # Check for sunk ships
    all_hits = {c for c, st in enemy_board.items() if st == "hit"}
    sunk_sizes = check_sunk(all_hits, ai.ship_cells, AI.AIOpponent.SHIP_CONFIGS)
    for sz in sunk_sizes:
        analysis_lines.append(f"  *** Nave affondata (dimensione {sz})! ***")

    # Win check
    if all_hits >= ai.ship_cells:
        return True
    return False

def resolve_ai_volley(num_shots):
    """
    AI fires num_shots at player. Build analysis lines.
    Returns True if AI wins.
    """
    global analysis_lines
    ai_lines = []
    ai_hits  = set()

    for _ in range(num_shots):
        ac, ar = ai.fire()
        coord  = f"{chr(65 + ac)}{ar + 1}"

        if (ac, ar) in player_ship_cells:
            my_board[(ac, ar)] = "hit"
            ai_hits.add((ac, ar))
            hit_ship   = player_ship_cells[(ac, ar)]
            fully_sunk = all(my_board.get(c) == "hit" for c in ship_grid_cells[hit_ship])
            ai.report((ac, ar), "sunk" if fully_sunk else "hit")
            if fully_sunk:
                ai_lines.append(f"  {coord} → IA AFFONDA la tua {hit_ship.nome}!")
            else:
                ai_lines.append(f"  {coord} → IA colpisce!")
        else:
            my_board[(ac, ar)] = "miss"
            ai.report((ac, ar), "miss")
            ai_lines.append(f"  {coord} → IA manca")

    # Append AI results to analysis
    analysis_lines.append("--- Turno IA ---")
    analysis_lines.extend(ai_lines)

    # Win check
    all_player_cells = {c for s in ships for c in ship_grid_cells[s]}
    all_ai_hits = {c for c, st in my_board.items() if st == "hit"}
    return all_ai_hits >= all_player_cells

# -----------------------------------------------------------------------
# Draw analysis panel
# -----------------------------------------------------------------------

def draw_analysis_panel():
    panel_x, panel_y = 350, 200
    panel_w, panel_h = 700, 500
    pygame.draw.rect(screen, (10, 10, 30), (panel_x, panel_y, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(screen, (80, 120, 200), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)

    title = font_big.render("FASE DI ANALISI", True, (255, 220, 50))
    screen.blit(title, (panel_x + panel_w//2 - title.get_width()//2, panel_y + 20))

    for i, line in enumerate(analysis_lines[:18]):
        color = (255, 100, 100) if "COLPITO" in line or "AFFONDA" in line or "IA colpisce" in line or "IA AFFONDA" in line else \
                (100, 200, 255) if "Acqua" in line or "manca" in line else \
                (255, 220, 50)
        txt = font_small.render(line, True, color)
        screen.blit(txt, (panel_x + 30, panel_y + 70 + i * 22))

    # Countdown hint
    hint = font_small.render("Prossimo turno in corso...", True, (160, 160, 160))
    screen.blit(hint, (panel_x + panel_w//2 - hint.get_width()//2, panel_y + panel_h - 35))

# -----------------------------------------------------------------------
# Draw HUD — shots counter
# -----------------------------------------------------------------------

def draw_hud():
    shots = player_shots_available()
    selected = len(player_targets)
    remaining_to_select = shots - selected

    # Shot counter bar
    bar_x, bar_y = 10, 110
    label = font_small.render(f"Colpi disponibili: {shots}  |  Selezionati: {selected}/{shots}", True, (255,255,255))
    screen.blit(label, (bar_x, bar_y))

    for i in range(shots):
        color = (255, 220, 0) if i < selected else (100, 100, 100)
        pygame.draw.rect(screen, color, (bar_x + i * 22, bar_y + 22, 18, 10), border_radius=3)

    if STATE == "player_selecting":
        if remaining_to_select > 0:
            tip = font_small.render(f"Seleziona ancora {remaining_to_select} celle, poi premi INVIO per sparare", True, (200,200,200))
        else:
            tip = font_small.render("Premi INVIO per sparare! (Clic destro per deselezionare)", True, (100,255,100))
        screen.blit(tip, (bar_x, bar_y + 38))

# -----------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------
running = True
while running:
    now = pygame.time.get_ticks()
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()

        # ==== PLACEMENT ====
        if STATE == "placement":
            was_dragging = {s for s in ships if s.dragging}

            for ship in ships:
                if not ship_placed[ship]:
                    ship.handle_event(event)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                for ship in was_dragging:
                    if not ship_placed[ship]:
                        ship_rotation[ship] = 90 if ship_rotation[ship] == 0 else 0

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                for ship in was_dragging:
                    if ship_placed[ship] or ship.rect is None:
                        continue
                    col   = round((ship.rect.x - MY_OFFSET_X) / CELL)
                    row   = round((ship.rect.y - MY_OFFSET_Y) / CELL)
                    cells = get_snap_cells(ship, col, row)
                    if cells:
                        ship_placed[ship]     = True
                        ship_grid_cells[ship] = cells
                        player_occupied.update(cells)
                        for c in cells:
                            player_ship_cells[c] = ship
                        ship.rect = ship_pixel_rect(ship, cells)

            if all(ship_placed[s] for s in ships):
                STATE        = "player_selecting"
                status_msg   = "Turno 1 — Seleziona i tuoi bersagli e premi INVIO"
                status_color = (100, 255, 100)

        # ==== PLAYER SELECTING TARGETS ====
        elif STATE == "player_selecting":
            shots = player_shots_available()

            if event.type == pygame.MOUSEBUTTONDOWN:
                cell = enemy_grid.get_pos_OnClick(
                    event.pos[0], event.pos[1],
                    offset_x=ENEMY_OFFSET_X, offset_y=ENEMY_OFFSET_Y
                )
                if cell:
                    col, row = cell
                    already_fired = (col, row) in enemy_board and enemy_board[(col, row)] in ("hit", "miss")
                    already_pending = (col, row) in player_targets

                    if event.button == 1:  # Left click: select target
                        if already_fired:
                            status_msg   = "Hai già sparato qui!"
                            status_color = (255, 200, 0)
                        elif already_pending:
                            status_msg   = "Già selezionata. Clic destro per rimuovere."
                            status_color = (255, 200, 0)
                        elif len(player_targets) >= shots:
                            status_msg   = f"Hai già selezionato {shots} bersagli. Premi INVIO!"
                            status_color = (255, 200, 0)
                        else:
                            player_targets.append((col, row))
                            status_msg   = f"Selezionati {len(player_targets)}/{shots}"
                            status_color = (255, 255, 255)

                    elif event.button == 3:  # Right click: deselect
                        if already_pending:
                            player_targets.remove((col, row))
                            status_msg   = f"Rimosso. Selezionati {len(player_targets)}/{shots}"
                            status_color = (200, 200, 200)

            # ENTER: fire the volley
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if len(player_targets) == 0:
                    status_msg   = "Seleziona almeno un bersaglio prima di sparare!"
                    status_color = (255, 200, 0)
                elif len(player_targets) < shots:
                    status_msg   = f"Seleziona ancora {shots - len(player_targets)} celle, oppure premi INVIO per sparare con meno colpi."
                    status_color = (255, 200, 0)
                    # Allow firing with fewer shots by pressing ENTER again
                    # (second press fires whatever was selected)
                else:
                    # Fire!
                    player_won = resolve_player_volley()
                    player_targets.clear()

                    if player_won:
                        STATE  = "gameover"
                        winner = "Player"
                    else:
                        # Now AI fires
                        ai_shots = ai_shots_available()
                        ai_won   = resolve_ai_volley(ai_shots)
                        STATE    = "analysis"
                        analysis_timer = now + ANALYSIS_DELAY

                        if ai_won:
                            STATE  = "gameover"
                            winner = "AI"

        # ==== ANALYSIS — auto-advance after delay ====
        elif STATE == "analysis":
            # Also allow clicking/enter to skip the delay
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                analysis_timer = 0

    # Auto-advance from analysis
    if STATE == "analysis" and analysis_timer and now >= analysis_timer:
        analysis_timer = 0
        analysis_lines = []
        STATE        = "player_selecting"
        shots        = player_shots_available()
        status_msg   = f"Il tuo turno! Seleziona {shots} bersagli"
        status_color = (100, 255, 100)

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------
    screen.blit(main_bg,  (0,   0))
    screen.blit(radar_bg, (700, 0))

    my_grid.draw_grid(screen,    offset_x=MY_OFFSET_X,    offset_y=MY_OFFSET_Y)
    enemy_grid.draw_grid(screen, offset_x=ENEMY_OFFSET_X, offset_y=ENEMY_OFFSET_Y)

    draw_board_markers(my_board,    MY_OFFSET_X,    MY_OFFSET_Y)
    draw_board_markers(enemy_board, ENEMY_OFFSET_X, ENEMY_OFFSET_Y)

    if STATE == "player_selecting":
        draw_pending_targets()

    # Ships
    for ship in ships:
        if ship_placed[ship]:
            draw_ship_on_grid(ship, ship_grid_cells[ship])
        else:
            img = pygame.image.load(ship.path_img).convert_alpha()
            if ship_rotation[ship] == 90:
                img = pygame.transform.rotate(img, 90)
            center = ship.rect.center
            ship.rect = img.get_rect(center=center)
            screen.blit(img, ship.rect.topleft)

    # HUD
    if STATE in ("player_selecting", "analysis"):
        draw_hud()

    # Status bar
    pygame.draw.rect(screen, (20, 20, 20), (0, 860, SCREEN_W, 40))
    screen.blit(font_med.render(status_msg, True, status_color), (20, 868))

    # Panel labels
    screen.blit(font_big.render("LA TUA FLOTTA", True, (59, 68, 255)), (MY_OFFSET_X,    MY_OFFSET_Y - 55))
    screen.blit(font_big.render("RADAR NEMICO",  True, (0, 200, 0)),   (ENEMY_OFFSET_X, ENEMY_OFFSET_Y - 55))

    if STATE == "placement":
        hint = font_small.render("Trascina le navi | R per ruotare", True, (180,180,180))
        screen.blit(hint, (20, 840))

    # Analysis overlay
    if STATE == "analysis":
        draw_analysis_panel()

    # Game over overlay
    if STATE == "gameover":
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        msg  = "HAI VINTO!" if winner == "Player" else "HA VINTO L'IA!"
        surf = font_big.render(msg, True, (255, 255, 100))
        screen.blit(surf, (SCREEN_W//2 - surf.get_width()//2, SCREEN_H//2 - 30))
        sub  = font_med.render("Chiudi la finestra per uscire.", True, (200, 200, 200))
        screen.blit(sub,  (SCREEN_W//2 - sub.get_width()//2,  SCREEN_H//2 + 30))

    pygame.display.flip()

pygame.quit()