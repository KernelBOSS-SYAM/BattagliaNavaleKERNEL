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
pygame.display.set_caption("Sea Battle")

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
# Grid config  (must match what your friends set in Grid.Grid)
# -----------------------------------------------------------------------
CELL           = 40
COLS           = 13
ROWS           = 13
MY_OFFSET_X    = 90
MY_OFFSET_Y    = 170
ENEMY_OFFSET_X = 790
ENEMY_OFFSET_Y = 170

my_grid    = Grid.Grid(CELL, COLS, ROWS, (59, 68, 255))
enemy_grid = Grid.Grid(CELL, COLS, ROWS, (0, 255, 0))

# -----------------------------------------------------------------------
# Player ships  (same as original main.py)
# -----------------------------------------------------------------------
ships = [
    Nave.Nave("portaerei",          "./img/portaAerei.png",        5),
    Nave.Nave("corazzata",          "./img/corazzata.png",         4),
    Nave.Nave("incrociatore1",      "./img/incrociatore.png",      3),
    Nave.Nave("incrociatore2",      "./img/incrociatore.png",      3),
    Nave.Nave("cacciatorpediniere", "./img/cacciatorpediniere.png", 2),
]

# Park ships at the bottom of the left panel for dragging
DOCK_POSITIONS = [(60,700),(180,700),(300,700),(400,700),(500,700)]
for i, ship in enumerate(ships):
    img = pygame.image.load(ship.path_img).convert_alpha()
    ship.rect = img.get_rect(topleft=DOCK_POSITIONS[i])

# -----------------------------------------------------------------------
# State tracked entirely in main.py — no changes to Grid or Nave needed
# -----------------------------------------------------------------------

# --- Placement tracking ---
player_ship_cells   = {}   # (col, row) -> Nave object
player_occupied     = set()
ship_placed         = {ship: False for ship in ships}
ship_grid_cells     = {ship: [] for ship in ships}
ship_rotation       = {ship: 0 for ship in ships}

# --- Hit/miss boards ---
# (col, row) -> "hit" | "miss"
my_board    = {}   # AI shooting at player
enemy_board = {}   # Player shooting at AI

# --- AI ---
ai             = AI.AIOpponent()
AI_TOTAL_CELLS = len(ai.ship_cells)
player_hits_on_ai  = set()
player_total_cells = sum(size for _, size in AI.AIOpponent.SHIP_CONFIGS)
player_hits_by_ai  = set()

# --- Game state machine ---
STATE        = "placement"
winner       = ""
status_msg   = "Drag ships onto your grid. Press R to rotate while dragging."
status_color = (255, 255, 255)
ai_fire_time = 0

clock = pygame.time.Clock()

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def get_snap_cells(ship, col, row):
    size     = ship.dimesione
    rotation = ship_rotation[ship]
    cells    = [(col + i, row) if rotation == 0 else (col, row + i) for i in range(size)]
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
    img  = pygame.transform.rotate(img, ship_rotation[ship])
    img  = pygame.transform.scale(img, (rect.width, rect.height))
    screen.blit(img, rect.topleft)


def draw_board_markers(board, offset_x, offset_y):
    for (col, row), state in board.items():
        rx  = offset_x + col * CELL
        ry  = offset_y + row * CELL
        pad = 6
        if state == "hit":
            pygame.draw.rect(screen, (200, 40, 40), (rx, ry, CELL, CELL))
            pygame.draw.line(screen, (255,255,255), (rx+pad, ry+pad), (rx+CELL-pad, ry+CELL-pad), 3)
            pygame.draw.line(screen, (255,255,255), (rx+CELL-pad, ry+pad), (rx+pad, ry+CELL-pad), 3)
        elif state == "miss":
            pygame.draw.rect(screen, (60, 120, 200), (rx, ry, CELL, CELL))
            pygame.draw.circle(screen, (255,255,255), (rx + CELL//2, ry + CELL//2), 6)


def check_ai_ship_sunk():
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
                if nb in player_hits_on_ai and nb not in visited:
                    q.append(nb)
        return comp

    for cell in player_hits_on_ai:
        if cell not in visited:
            components.append(bfs(cell))

    sizes_left = [s for _, s in AI.AIOpponent.SHIP_CONFIGS]
    for comp in components:
        if all(c in ai.ship_cells for c in comp):
            sz = len(comp)
            if sz in sizes_left:
                sizes_left.remove(sz)
                return True, sz
    return False, 0


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

        # ---- PLACEMENT ----
        if STATE == "placement":
            for ship in ships:
                if not ship_placed[ship]:
                    ship.handle_event(event)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                for ship in ships:
                    if ship.dragging:
                        ship_rotation[ship] = 90 if ship_rotation[ship] == 0 else 0

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                for ship in ships:
                    if not ship_placed[ship] and not ship.dragging:
                        if ship.rect is None:
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
                STATE        = "battle"
                status_msg   = "All ships placed! Click the enemy grid to fire."
                status_color = (100, 255, 100)

        # ---- BATTLE — player fires ----
        elif STATE == "battle":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cell = enemy_grid.get_pos_OnClick(
                    event.pos[0], event.pos[1],
                    offset_x=ENEMY_OFFSET_X, offset_y=ENEMY_OFFSET_Y
                )
                if cell:
                    col, row = cell
                    if (col, row) in enemy_board:
                        status_msg   = "Already fired here — pick another cell!"
                        status_color = (255, 200, 0)
                    elif ai.has_ship_at(col, row):
                        enemy_board[(col, row)] = "hit"
                        player_hits_on_ai.add((col, row))
                        sunk, sz = check_ai_ship_sunk()
                        status_msg   = f"You sunk an enemy ship! (size {sz})" if sunk else "HIT!"
                        status_color = (255, 80, 80) if sunk else (255, 160, 50)
                        if len(player_hits_on_ai) >= AI_TOTAL_CELLS:
                            STATE  = "gameover"
                            winner = "Player"
                    else:
                        enemy_board[(col, row)] = "miss"
                        status_msg   = "Miss. AI is thinking..."
                        status_color = (150, 200, 255)
                        ai_fire_time = now + 800

    # ---- AI fires ----
    if STATE == "battle" and ai_fire_time and now >= ai_fire_time:
        ai_fire_time = 0
        ac, ar = ai.fire()

        if (ac, ar) in player_ship_cells:
            my_board[(ac, ar)] = "hit"
            player_hits_by_ai.add((ac, ar))
            hit_ship   = player_ship_cells[(ac, ar)]
            fully_sunk = all(my_board.get(c) == "hit" for c in ship_grid_cells[hit_ship])
            ai.report((ac, ar), "sunk" if fully_sunk else "hit")
            status_msg   = (f"AI sunk your {hit_ship.nome}!" if fully_sunk
                            else f"AI hit your ship at {chr(65+ac)}{ar+1}!")
            status_color = (255, 60, 60)
            if len(player_hits_by_ai) >= player_total_cells:
                STATE  = "gameover"
                winner = "AI"
        else:
            my_board[(ac, ar)] = "miss"
            ai.report((ac, ar), "miss")
            status_msg   = f"AI missed at {chr(65+ac)}{ar+1}. Your turn!"
            status_color = (150, 200, 255)

    # -------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------
    screen.blit(main_bg,  (0,   0))
    screen.blit(radar_bg, (700, 0))

    # Original draw_grid — completely unchanged
    my_grid.draw_grid(screen,    offset_x=MY_OFFSET_X,    offset_y=MY_OFFSET_Y)
    enemy_grid.draw_grid(screen, offset_x=ENEMY_OFFSET_X, offset_y=ENEMY_OFFSET_Y)

    # Markers drawn on top by main.py — no Grid changes needed
    draw_board_markers(my_board,    MY_OFFSET_X,    MY_OFFSET_Y)
    draw_board_markers(enemy_board, ENEMY_OFFSET_X, ENEMY_OFFSET_Y)

    # Ships
    for ship in ships:
        if ship_placed[ship]:
            draw_ship_on_grid(ship, ship_grid_cells[ship])
        else:
            ship.draw_nave(screen, pos_x=ship.rect.x, pos_y=ship.rect.y)

    # Status bar
    pygame.draw.rect(screen, (20, 20, 20), (0, 850, SCREEN_W, 50))
    screen.blit(font_med.render(status_msg, True, status_color), (20, 862))

    # Labels
    screen.blit(font_big.render("YOUR FLEET",  True, (59, 68, 255)), (MY_OFFSET_X,    MY_OFFSET_Y - 60))
    screen.blit(font_big.render("ENEMY RADAR", True, (0, 200, 0)),   (ENEMY_OFFSET_X, ENEMY_OFFSET_Y - 60))

    if STATE == "placement":
        hint = font_small.render("Drag ships to your grid  |  Press R to rotate while dragging", True, (180,180,180))
        screen.blit(hint, (20, 830))

    if STATE == "gameover":
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        msg  = "YOU WIN! 🎉" if winner == "Player" else "AI WINS! 💀"
        surf = font_big.render(msg, True, (255, 255, 100))
        screen.blit(surf, (SCREEN_W//2 - surf.get_width()//2, SCREEN_H//2 - 30))
        sub  = font_med.render("Close the window to exit.", True, (200, 200, 200))
        screen.blit(sub,  (SCREEN_W//2 - sub.get_width()//2,  SCREEN_H//2 + 30))

    pygame.display.flip()

pygame.quit()