import pygame
import sys
import Grid
import Nave
import AI

# -----------------------------------------------------------------------
# Pygame init
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
# Constants
# -----------------------------------------------------------------------
CELL           = 40
COLS           = 13
ROWS           = 13
MY_OFFSET_X    = 90
MY_OFFSET_Y    = 150
ENEMY_OFFSET_X = 790
ENEMY_OFFSET_Y = 150
ANALYSIS_DELAY = 2500   # ms

# -----------------------------------------------------------------------
# Backgrounds
# -----------------------------------------------------------------------
main_bg  = pygame.image.load('./img/main.png').convert()
main_bg  = pygame.transform.scale(main_bg, (700, 900))
radar_bg = pygame.image.load('./img/radar.jpg').convert()
radar_bg = pygame.transform.scale(radar_bg, (700, 900))

# -----------------------------------------------------------------------
# Grids
# -----------------------------------------------------------------------
my_grid    = Grid.Grid(CELL, COLS, ROWS, (59, 68, 255))
enemy_grid = Grid.Grid(CELL, COLS, ROWS, (0, 255, 0))

# -----------------------------------------------------------------------
# Player ships
# -----------------------------------------------------------------------
SHIP_DEFS = [
    ("portaerei",          "./img/portaAerei.png",        5),
    ("corazzata",          "./img/corazzata.png",         4),
    ("incrociatore1",      "./img/incrociatore.png",      3),
    ("incrociatore2",      "./img/incrociatore.png",      3),
    ("cacciatorpediniere", "./img/cacciatorpediniere.png", 2),
]
DOCK_POSITIONS   = [(80,720),(180,720),(280,720),(380,720),(480,720)]
TOTAL_SHIP_CELLS = sum(size for _, _, size in SHIP_DEFS)  # 17

ships = []
for i, (nome, img_path, size) in enumerate(SHIP_DEFS):
    ship      = Nave.Nave(nome, img_path, size)
    base_img  = pygame.image.load(img_path).convert_alpha()
    ship.rect = base_img.get_rect(topleft=DOCK_POSITIONS[i])
    ships.append(ship)

# -----------------------------------------------------------------------
# Placement state
# -----------------------------------------------------------------------
player_ship_cells = {}          # (col, row) -> Nave
player_occupied   = set()       # all cells taken by placed player ships

# -----------------------------------------------------------------------
# Battle state
# -----------------------------------------------------------------------
# shots_available = un-hit player ship cells (starts at 17, shrinks when hit)
def player_shots_available():
    return TOTAL_SHIP_CELLS - sum(
        1 for c in player_occupied if my_grid.get_cell_state(c[0], c[1]) == "hit"
    )

def ai_shots_available():
    return TOTAL_SHIP_CELLS - sum(
        1 for c in ai.ship_cells if enemy_grid.get_cell_state(c[0], c[1]) == "hit"
    )

ai             = AI.AIOpponent()
player_targets = []   # cells queued for firing this turn

# -----------------------------------------------------------------------
# Game state machine
# -----------------------------------------------------------------------
# States: "placement" | "player_selecting" | "analysis" | "gameover"
STATE          = "placement"
winner         = ""
analysis_lines = []
analysis_timer = 0
status_msg     = "Trascina le navi sulla tua griglia. Premi R per ruotare."
status_color   = (255, 255, 255)

clock = pygame.time.Clock()

# -----------------------------------------------------------------------
# Battle helpers
# -----------------------------------------------------------------------

def check_sunk(hits_set, all_ship_cells, ship_configs):
    """Return list of newly sunk ship sizes by finding fully-hit connected groups."""
    visited, components = set(), []

    def bfs(start):
        q, comp = [start], set()
        while q:
            cell = q.pop()
            if cell in visited:
                continue
            visited.add(cell)
            comp.add(cell)
            c, r = cell
            for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
                nb = (c+dc, r+dr)
                if nb in hits_set and nb not in visited:
                    q.append(nb)
        return comp

    for cell in hits_set:
        if cell not in visited:
            components.append(bfs(cell))

    sizes_left, sunk = [s for _, s in ship_configs], []
    for comp in components:
        if all(c in all_ship_cells for c in comp):
            sz = len(comp)
            if sz in sizes_left:
                sizes_left.remove(sz)
                sunk.append(sz)
    return sunk


def resolve_player_volley():
    """Fire all queued player targets. Returns True if player wins."""
    global analysis_lines
    analysis_lines = ["--- Il tuo turno ---"]

    for col, row in player_targets:
        coord = f"{chr(65 + col)}{row + 1}"
        if ai.has_ship_at(col, row):
            enemy_grid.set_cell_state(col, row, "hit")
            analysis_lines.append(f"  {coord} → COLPITO!")
        else:
            enemy_grid.set_cell_state(col, row, "miss")
            analysis_lines.append(f"  {coord} → Acqua")

    all_hits = {(c, r) for c in range(COLS) for r in range(ROWS)
                if enemy_grid.get_cell_state(c, r) == "hit"}
    for sz in check_sunk(all_hits, ai.ship_cells, AI.AIOpponent.SHIP_CONFIGS):
        analysis_lines.append(f"  *** Nave affondata (dimensione {sz})! ***")

    return all_hits >= ai.ship_cells


def resolve_ai_volley(num_shots):
    """Fire AI shots. Returns True if AI wins."""
    analysis_lines.append("--- Turno IA ---")

    for _ in range(num_shots):
        ac, ar = ai.fire()
        coord  = f"{chr(65 + ac)}{ar + 1}"

        if (ac, ar) in player_ship_cells:
            my_grid.set_cell_state(ac, ar, "hit")
            hit_ship   = player_ship_cells[(ac, ar)]
            fully_sunk = all(
                my_grid.get_cell_state(c, r) == "hit"
                for c, r in hit_ship.grid_cells
            )
            ai.report((ac, ar), "sunk" if fully_sunk else "hit")
            if fully_sunk:
                analysis_lines.append(f"  {coord} → IA AFFONDA la tua {hit_ship.nome}!")
            else:
                analysis_lines.append(f"  {coord} → IA colpisce!")
        else:
            my_grid.set_cell_state(ac, ar, "miss")
            ai.report((ac, ar), "miss")
            analysis_lines.append(f"  {coord} → IA manca")

    all_ai_hits = {(c, r) for c in range(COLS) for r in range(ROWS)
                   if my_grid.get_cell_state(c, r) == "hit"}
    return all_ai_hits >= player_occupied

# -----------------------------------------------------------------------
# Drawing helpers
# -----------------------------------------------------------------------

def draw_hud():
    shots    = player_shots_available()
    selected = len(player_targets)
    bar_x, bar_y = 10, 110

    screen.blit(
        font_small.render(f"Colpi disponibili: {shots}  |  Selezionati: {selected}/{shots}", True, (255,255,255)),
        (bar_x, bar_y)
    )
    for i in range(shots):
        color = (255, 220, 0) if i < selected else (100, 100, 100)
        pygame.draw.rect(screen, color, (bar_x + i * 22, bar_y + 22, 18, 10), border_radius=3)

    if STATE == "player_selecting":
        if selected < shots:
            tip = font_small.render(f"Seleziona ancora {shots - selected} celle, poi premi INVIO", True, (200,200,200))
        else:
            tip = font_small.render("Premi INVIO per sparare!  (Clic destro per deselezionare)", True, (100,255,100))
        screen.blit(tip, (bar_x, bar_y + 38))


def draw_analysis_panel():
    px, py, pw, ph = 350, 200, 700, 500
    pygame.draw.rect(screen, (10, 10, 30),    (px, py, pw, ph), border_radius=12)
    pygame.draw.rect(screen, (80, 120, 200),  (px, py, pw, ph), 2, border_radius=12)

    title = font_big.render("FASE DI ANALISI", True, (255, 220, 50))
    screen.blit(title, (px + pw//2 - title.get_width()//2, py + 20))

    for i, line in enumerate(analysis_lines[:20]):
        if "COLPITO" in line or "AFFONDA" in line or "IA colpisce" in line:
            color = (255, 100, 100)
        elif "Acqua" in line or "manca" in line:
            color = (100, 200, 255)
        else:
            color = (255, 220, 50)
        screen.blit(font_small.render(line, True, color), (px + 30, py + 70 + i * 22))

    hint = font_small.render("Premi un tasto per continuare...", True, (160, 160, 160))
    screen.blit(hint, (px + pw//2 - hint.get_width()//2, py + ph - 35))


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
            # Capture who is dragging BEFORE handle_event clears the flag
            was_dragging = {s for s in ships if s.dragging}

            for ship in ships:
                ship.handle_event(event)   # Nave.handle_event now manages rotation too

            # On mouse release: snap the ship that was just dropped
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                for ship in was_dragging:
                    if ship.placed or ship.rect is None:
                        continue
                    col   = round((ship.rect.x - MY_OFFSET_X) / CELL)
                    row   = round((ship.rect.y - MY_OFFSET_Y) / CELL)
                    cells = ship.get_snap_cells(col, row, COLS, ROWS, player_occupied)
                    if cells:
                        ship.snap(cells, CELL, MY_OFFSET_X, MY_OFFSET_Y)
                        player_occupied.update(cells)
                        for c in cells:
                            player_ship_cells[c] = ship

            if all(s.placed for s in ships):
                STATE        = "player_selecting"
                status_msg   = f"Turno 1 — Seleziona {player_shots_available()} bersagli e premi INVIO"
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
                    col, row       = cell
                    already_fired   = enemy_grid.get_cell_state(col, row) in ("hit", "miss")
                    already_pending = (col, row) in player_targets

                    if event.button == 1:
                        if already_fired:
                            status_msg, status_color = "Hai già sparato qui!", (255, 200, 0)
                        elif already_pending:
                            status_msg, status_color = "Già selezionata. Clic destro per rimuovere.", (255, 200, 0)
                        elif len(player_targets) >= shots:
                            status_msg, status_color = f"Hai già selezionato {shots} bersagli. Premi INVIO!", (255, 200, 0)
                        else:
                            player_targets.append((col, row))
                            status_msg, status_color = f"Selezionati {len(player_targets)}/{shots}", (255, 255, 255)

                    elif event.button == 3:
                        if already_pending:
                            player_targets.remove((col, row))
                            status_msg, status_color = f"Rimosso. Selezionati {len(player_targets)}/{shots}", (200, 200, 200)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if not player_targets:
                    status_msg, status_color = "Seleziona almeno un bersaglio!", (255, 200, 0)
                else:
                    player_won = resolve_player_volley()
                    player_targets.clear()
                    if player_won:
                        STATE, winner = "gameover", "Player"
                    else:
                        ai_won = resolve_ai_volley(ai_shots_available())
                        STATE  = "gameover" if ai_won else "analysis"
                        winner = "AI" if ai_won else ""
                        analysis_timer = now + ANALYSIS_DELAY

        # ==== ANALYSIS ====
        elif STATE == "analysis":
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                analysis_timer = 1   # force immediate advance

    # Auto-advance from analysis after delay
    if STATE == "analysis" and analysis_timer and now >= analysis_timer:
        analysis_timer = 0
        analysis_lines = []
        STATE          = "player_selecting"
        shots          = player_shots_available()
        status_msg     = f"Il tuo turno! Seleziona {shots} bersagli"
        status_color   = (100, 255, 100)

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------
    screen.blit(main_bg,  (0,   0))
    screen.blit(radar_bg, (700, 0))

    # Grids (now draw their own markers internally)
    my_grid.draw_grid(screen,    offset_x=MY_OFFSET_X,    offset_y=MY_OFFSET_Y)
    enemy_grid.draw_grid(screen, offset_x=ENEMY_OFFSET_X, offset_y=ENEMY_OFFSET_Y)

    # Pending targets highlight (Grid method)
    if STATE == "player_selecting":
        enemy_grid.draw_pending(screen, player_targets, ENEMY_OFFSET_X, ENEMY_OFFSET_Y)

    # Ships (Nave methods)
    for ship in ships:
        if ship.placed:
            ship.draw_on_grid(screen, CELL, MY_OFFSET_X, MY_OFFSET_Y)
        else:
            ship.draw_nave(screen)

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
        hint = font_small.render("Trascina le navi sulla griglia  |  R per ruotare", True, (180, 180, 180))
        screen.blit(hint, (20, 840))

    if STATE == "analysis":
        draw_analysis_panel()

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