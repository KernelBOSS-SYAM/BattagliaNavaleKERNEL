"""
main_ai.py — Entry point con AI e interfaccia HUD militare.

File originali del gruppo (NON modificati):
    Grid.py, Nave.py, game_handler.py, main.py

Nuovi file aggiunti:
    AI.py       — AI Hunt & Target
    hud.py      — grafica militare HUD
    main_ai.py  — questo file (sostituisce main.py per la versione con AI)

Avvia con:  python main_ai.py
"""

import pygame
import sys
import math

import Grid
import Nave
import game_handler as gh
import AI as ai_module
import hud

# ═══════════════════════════════════════════════════════════════════════
# RISOLUZIONE DINAMICA — canvas interno 1400×900 scalato allo schermo
# ═══════════════════════════════════════════════════════════════════════
pygame.init()

BASE_W, BASE_H = 1400, 900

info     = pygame.display.Info()
NATIVE_W = info.current_w
NATIVE_H = info.current_h
fullscreen = False


def make_window(fs):
    if fs:
        surf = pygame.display.set_mode((NATIVE_W, NATIVE_H), pygame.FULLSCREEN)
        sw, sh = NATIVE_W, NATIVE_H
    else:
        ww = int(NATIVE_W * 0.9)
        wh = int(ww * BASE_H / BASE_W)
        if wh > int(NATIVE_H * 0.9):
            wh = int(NATIVE_H * 0.9)
            ww = int(wh * BASE_W / BASE_H)
        surf = pygame.display.set_mode((ww, wh), pygame.RESIZABLE)
        sw, sh = ww, wh
    scale = min(sw / BASE_W, sh / BASE_H)
    ox    = (sw - int(BASE_W * scale)) // 2
    oy    = (sh - int(BASE_H * scale)) // 2
    return surf, scale, ox, oy


def toggle_fs():
    global screen, SCALE, OX, OY, fullscreen
    fullscreen = not fullscreen
    screen, SCALE, OX, OY = make_window(fullscreen)


def to_canvas(pos):
    return ((pos[0] - OX) / SCALE, (pos[1] - OY) / SCALE)


screen, SCALE, OX, OY = make_window(fullscreen)
pygame.display.set_caption("BATTAGLIA NAVALE // RADAR OPS — AI Edition")
canvas = pygame.Surface((BASE_W, BASE_H))


def present():
    scaled = pygame.transform.smoothscale(canvas, (int(BASE_W * SCALE), int(BASE_H * SCALE)))
    screen.fill((0, 0, 0))
    screen.blit(scaled, (OX, OY))
    pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════
# COSTANTI LAYOUT
# ═══════════════════════════════════════════════════════════════════════
CELL        = 40
COLS        = 13
ROWS        = 13
MY_OFF_X    = 90
MY_OFF_Y    = 170
ENEMY_OFF_X = 790
ENEMY_OFF_Y = 170

ANALYSIS_DELAY = 2500   # ms

# ═══════════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════════

# Sfondi (invariati)
main_img, radar_img = gh.load_backgrounds()

# Griglie
my_grid    = Grid.Grid(CELL, COLS, ROWS, (59,  68, 255))
enemy_grid = Grid.Grid(CELL, COLS, ROWS, (0,  255,   0))

# Navi giocatore
ships = gh.create_ships()
# Grid.py chiama ship.dimensione ma Nave.py non lo definisce (usa ship.hp).
# Patch non-invasiva: aggiungiamo una property alla classe a runtime,
# così dimensione riflette sempre hp senza toccare Nave.py.
import Nave as _Nave
if not hasattr(_Nave.Nave, 'dimensione'):
    _Nave.Nave.dimensione = property(lambda self: self.hp)

# Bottone CONFERMA — stile HUD
BUTTON_RECT = (1100, 800, 200, 60)

# AI
ai = ai_module.AIOpponent()

# ═══════════════════════════════════════════════════════════════════════
# STATO DI GIOCO
# ═══════════════════════════════════════════════════════════════════════
game_state    = "PLACEMENT"
ships_placed  = 0
confirmed     = False

player_shots  = []          # bersagli selezionati questo turno
analysis_lines = []
analysis_timer = 0
winner        = None        # "player" | "ai"

status_msg   = "POSIZIONA LE NAVI  //  [E]/[R] RUOTA  //  CONFERMA QUANDO PRONTE"
status_color = hud.C_GREEN

scan_angle = 0.0
clock      = pygame.time.Clock()

# ═══════════════════════════════════════════════════════════════════════
# HELPER — colpi disponibili (usa game_handler originale)
# ═══════════════════════════════════════════════════════════════════════

def player_shots_total():
    return gh.calcola_colpi_disponibili(ships)

def ai_shots_total():
    """Colpi AI = celle nave ancora intatte nella grid_matrix AI (valore 0)."""
    return max(sum(
        1 for c in range(ai.GRID_COLS)
          for r in range(ai.GRID_ROWS)
          if ai.grid_matrix[c][r] == 0
    ), 0)

# ═══════════════════════════════════════════════════════════════════════
# LOGICA TURNI
# ═══════════════════════════════════════════════════════════════════════

def resolve_player_volley():
    """Applica tutti i colpi del giocatore sulla griglia AI."""
    global analysis_lines
    analysis_lines = ["--- Il tuo turno ---"]

    for col, row in player_shots:
        coord  = f"{chr(65+col)}{row+1}"
        result = ai.receive_shot(col, row)

        if result == "hit":
            analysis_lines.append(f"  {coord} → COLPITO!")
        elif result == "sunk":
            analysis_lines.append(f"  {coord} → COLPITO!")
            analysis_lines.append(f"  ★ NAVE AFFONDATA!")
        elif result == "miss":
            analysis_lines.append(f"  {coord} → Acqua")
        else:
            analysis_lines.append(f"  {coord} → già sparato")

    return ai.all_sunk()


def resolve_ai_volley():
    """AI spara sulla griglia del giocatore."""
    num_shots = ai_shots_total()
    analysis_lines.append("--- Turno IA ---")

    # Mappa celle giocatore: grid_matrix vale 0 dove c'è una nave
    # Costruiamo un set di celle occupate dalla griglia del giocatore
    player_cells = {
        (c, r)
        for c in range(COLS)
        for r in range(ROWS)
        if my_grid.grid_matrix[c][r] == 0
    }

    for _ in range(num_shots):
        ac, ar = ai.fire()
        coord  = f"{chr(65+ac)}{ar+1}"

        if (ac, ar) in player_cells:
            my_grid.grid_matrix[ac][ar] = 1   # colpito
            # Verifica se la nave è affondata (nessun 0 adiacente connesso)
            sunk = _check_player_ship_sunk(ac, ar)
            if sunk:
                ai.report((ac, ar), "sunk")
                analysis_lines.append(f"  {coord} → IA AFFONDA una tua nave!")
            else:
                ai.report((ac, ar), "hit")
                analysis_lines.append(f"  {coord} → IA colpisce!")
        else:
            my_grid.grid_matrix[ac][ar] = -2  # acqua sparata
            ai.report((ac, ar), "miss")
            analysis_lines.append(f"  {coord} → IA manca")

    # Controlla vittoria AI
    return all(
        my_grid.grid_matrix[c][r] != 0
        for c in range(COLS) for r in range(ROWS)
    )


def _check_player_ship_sunk(col, row):
    """BFS per verificare se la nave giocatore appena colpita è affondata."""
    visited = set()
    queue   = [(col, row)]
    while queue:
        c, r = queue.pop()
        if (c, r) in visited:
            continue
        visited.add((c, r))
        if my_grid.grid_matrix[c][r] == 0:
            return False
        for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
            nc, nr = c+dc, r+dr
            if (0 <= nc < COLS and 0 <= nr < ROWS
                    and (nc, nr) not in visited
                    and my_grid.grid_matrix[nc][nr] in (0, 1)):
                queue.append((nc, nr))
    return True

# ═══════════════════════════════════════════════════════════════════════
# GAME LOOP
# ═══════════════════════════════════════════════════════════════════════
MOUSE_EVS = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)

running = True
while running:
    now = pygame.time.get_ticks()
    clock.tick(60)
    scan_angle = (scan_angle + 0.5) % 360

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False
            sys.exit()

        # ── Resize ────────────────────────────────────────────────────
        if event.type == pygame.VIDEORESIZE and not fullscreen:
            screen, SCALE, OX, OY = make_window(fullscreen)
            continue

        # ── Fullscreen toggle ─────────────────────────────────────────
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11 or (
                event.key == pygame.K_RETURN and bool(event.mod & pygame.KMOD_ALT)
            ):
                toggle_fs()
                continue

        # ── Scala coordinate mouse → canvas ──────────────────────────
        if event.type in MOUSE_EVS:
            cx, cy = to_canvas(event.pos)
            event  = pygame.event.Event(event.type, {
                **{k: v for k, v in event.__dict__.items() if k != 'pos'},
                'pos': (int(cx), int(cy))
            })

        # ══════════════════════════════════════════════════════════════
        # PLACEMENT
        # ══════════════════════════════════════════════════════════════
        if game_state == "PLACEMENT":
            # Bottone CONFERMA
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                bx, by, bw, bh = BUTTON_RECT
                if ships_placed == 5 and pygame.Rect(BUTTON_RECT).collidepoint(event.pos):
                    confirmed     = True
                    game_state    = "PLAYER_TURN"
                    status_msg   = f"IL TUO TURNO  //  SELEZIONA {player_shots_total()} BERSAGLI"
                    status_color = hud.C_GREEN
                    continue

            # Drag & drop navi (delega a Nave.handle_event come nell'originale)
            if not confirmed:
                for ship in ships:
                    if not ship.placed:
                        dropped = ship.handle_event(event)
                        if dropped:
                            if my_grid.place_ship(ship, MY_OFF_X, MY_OFF_Y):
                                ships_placed += 1
                                status_msg   = f"NAVI PIAZZATE: {ships_placed}/5"
                                status_color = hud.C_GREEN
                            else:
                                status_msg   = "POSIZIONE NON VALIDA — RIPROVA"
                                status_color = hud.C_AMBER

        # ══════════════════════════════════════════════════════════════
        # PLAYER TURN — selezione bersagli
        # ══════════════════════════════════════════════════════════════
        elif game_state == "PLAYER_TURN":
            max_shots = player_shots_total()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = enemy_grid.get_pos_OnClick(
                    event.pos[0], event.pos[1], ENEMY_OFF_X, ENEMY_OFF_Y
                )
                if pos is not None:
                    col, row = pos
                    ai_val   = ai.grid_matrix[col][row]
                    already_fired   = ai_val in (1, -2)
                    already_pending = (col, row) in player_shots

                    if event.button == 1:
                        if already_fired:
                            status_msg, status_color = "CELLA GIA' SPARATA", hud.C_AMBER
                        elif already_pending:
                            status_msg, status_color = "GIA' SELEZIONATA  //  CLIC DX PER RIMUOVERE", hud.C_AMBER
                        elif len(player_shots) >= max_shots:
                            status_msg, status_color = f"MAX {max_shots} COLPI  //  PREMI [INVIO]", hud.C_AMBER
                        else:
                            player_shots.append((col, row))
                            status_msg   = f"BERSAGLI: {len(player_shots)}/{max_shots}  //  [INVIO] PER SPARARE"
                            status_color = hud.C_GREEN

                    elif event.button == 3:
                        if already_pending:
                            player_shots.remove((col, row))
                            status_msg   = f"RIMOSSO  //  BERSAGLI: {len(player_shots)}/{max_shots}"
                            status_color = hud.C_GREEN_DIM

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if not player_shots:
                    status_msg, status_color = "SELEZIONA ALMENO UN BERSAGLIO", hud.C_AMBER
                else:
                    player_won = resolve_player_volley()
                    player_shots.clear()
                    if player_won:
                        winner     = "player"
                        game_state = "GAMEOVER"
                    else:
                        ai_won = resolve_ai_volley()
                        if ai_won:
                            winner     = "ai"
                            game_state = "GAMEOVER"
                        else:
                            game_state     = "ANALYSIS"
                            analysis_timer = now + ANALYSIS_DELAY

        # ══════════════════════════════════════════════════════════════
        # ANALYSIS — skip su qualsiasi tasto/click
        # ══════════════════════════════════════════════════════════════
        elif game_state == "ANALYSIS":
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                analysis_timer = 1

    # ── Auto-avanzamento analisi ──────────────────────────────────────
    if game_state == "ANALYSIS" and analysis_timer and now >= analysis_timer:
        analysis_timer  = 0
        analysis_lines  = []
        game_state      = "PLAYER_TURN"
        shots           = player_shots_total()
        status_msg      = f"IL TUO TURNO  //  SELEZIONA {shots} BERSAGLI"
        status_color    = hud.C_GREEN

    # ═══════════════════════════════════════════════════════════════════
    # RENDER
    # ═══════════════════════════════════════════════════════════════════
    canvas.blit(main_img,  (0,   0))
    canvas.blit(radar_img, (700, 0))

    # Barra titolo
    hud.draw_title_bar(canvas, BASE_W, scan_angle)

    # Header pannelli
    hud.draw_panel_headers(canvas, MY_OFF_X, ENEMY_OFF_X)

    # Griglie
    my_grid.draw_grid(canvas,    offset_x=MY_OFF_X,    offset_y=MY_OFF_Y)
    enemy_grid.draw_grid(canvas, offset_x=ENEMY_OFF_X, offset_y=ENEMY_OFF_Y)

    # Marcatori hit/miss su entrambe le griglie
    hud.draw_markers(canvas, my_grid.grid_matrix,    MY_OFF_X,    MY_OFF_Y,    CELL)
    hud.draw_markers(canvas, ai.grid_matrix,          ENEMY_OFF_X, ENEMY_OFF_Y, CELL)

    # Bersagli selezionati (giallo)
    if game_state == "PLAYER_TURN":
        hud.draw_pending(canvas, player_shots, ENEMY_OFF_X, ENEMY_OFF_Y, CELL)

    # Navi giocatore
    gh.draw_ships(canvas, ships)

    # HUD colpi
    if game_state in ("PLAYER_TURN", "ANALYSIS"):
        hud.draw_hud_shots(canvas, game_state, player_shots_total(), len(player_shots), MY_OFF_X)

    # Hint posizionamento
    if game_state == "PLACEMENT":
        hud.draw_placement_hint(canvas, MY_OFF_X)
        if ships_placed == 5 and not confirmed:
            hud.draw_confirm_button(canvas, BUTTON_RECT)

    # Barra stato
    hud.draw_status_bar(canvas, BASE_W, status_msg, status_color)

    # Overlay analisi
    if game_state == "ANALYSIS":
        hud.draw_analysis_panel(canvas, BASE_W, BASE_H, analysis_lines)

    # Overlay game over
    if game_state == "GAMEOVER":
        hud.draw_gameover(canvas, BASE_W, BASE_H, winner)

    present()

pygame.quit()