"""
main_ai.py — Versione con AI e HUD militare.

File del gruppo (NON modificati):
    Grid.py, Nave.py, game_handler.py, main.py

File aggiunti:
    AI.py, hud.py, main_ai.py

Avvia con: python main_ai.py
"""

import pygame
import sys
import Grid
import Nave
import game_handler as gh
import AI
import hud

# ── Patch compatibilità: Grid.py usa ship.dimensione, Nave.py usa ship.hp ──
import Nave as _Nave
if not hasattr(_Nave.Nave, 'dimensione'):
    _Nave.Nave.dimensione = property(lambda self: self.hp)

# ═══════════════════════════════════════════════════════════════════════
# SETUP — identico al main.py originale
# ═══════════════════════════════════════════════════════════════════════
pygame.init()

BASE_W, BASE_H = 1400, 900
info           = pygame.display.Info()
NATIVE_W       = info.current_w
NATIVE_H       = info.current_h
fullscreen     = False

def make_window(fs):
    if fs:
        surf    = pygame.display.set_mode((NATIVE_W, NATIVE_H), pygame.FULLSCREEN)
        sw, sh  = NATIVE_W, NATIVE_H
    else:
        ww = int(NATIVE_W * 0.9)
        wh = int(ww * BASE_H / BASE_W)
        if wh > int(NATIVE_H * 0.9):
            wh = int(NATIVE_H * 0.9)
            ww = int(wh * BASE_W / BASE_H)
        surf   = pygame.display.set_mode((ww, wh), pygame.RESIZABLE)
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
    return (int((pos[0] - OX) / SCALE), int((pos[1] - OY) / SCALE))

screen, SCALE, OX, OY = make_window(fullscreen)
pygame.display.set_caption("BATTAGLIA NAVALE — AI Edition")
canvas = pygame.Surface((BASE_W, BASE_H))

def present():
    scaled = pygame.transform.smoothscale(canvas, (int(BASE_W * SCALE), int(BASE_H * SCALE)))
    screen.fill((0, 0, 0))
    screen.blit(scaled, (OX, OY))
    pygame.display.flip()

# ── Stesse costanti del main.py originale ────────────────────────────
green          = (0, 255, 0)
blue           = (59, 68, 255)
cell_dimension = 40
Ncell          = 13

# Stessi offset del main.py originale
MY_OFF_X    = 90
MY_OFF_Y    = 170
ENEMY_OFF_X = 790
ENEMY_OFF_Y = 170

game_state   = "PLACEMENT"
ships_placed = 0
confirmed    = False

# ── Background (come nell'originale) ─────────────────────────────────
main_img, radar_img = gh.load_backgrounds()

# ── Griglie (come nell'originale) ────────────────────────────────────
my_grid    = Grid.Grid(40, 13, 13, (59, 68, 255))
enemy_grid = Grid.Grid(40, 13, 13, (0, 255, 0))

# ── Navi (come nell'originale) ───────────────────────────────────────
ships              = gh.create_ships()
portaerei          = ships[0]
corazzata          = ships[1]
incrociatore1      = ships[2]
incrociatore2      = ships[3]
cacciatorpediniere = ships[4]

# ── Bottone CONFERMA (come nell'originale) ────────────────────────────
button_rect  = pygame.Rect(1100, 800, 200, 60)
button_color = (0, 200, 0)
font         = pygame.font.SysFont(None, 40)

# ── AI ────────────────────────────────────────────────────────────────
ai = AI.AIOpponent()

# ── Stato aggiuntivo per i turni ─────────────────────────────────────
player_shots   = []   # celle selezionate questo turno
analysis_lines = []
analysis_timer = 0
winner         = None   # "player" | "ai"
ANALYSIS_DELAY = 2500   # ms

scan_angle   = 0.0
clock        = pygame.time.Clock()
MOUSE_EVS    = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)

# ═══════════════════════════════════════════════════════════════════════
# HELPER COLPI
# ═══════════════════════════════════════════════════════════════════════

def player_shots_total():
    """Usa calcola_colpi_disponibili di game_handler, invariato."""
    return gh.calcola_colpi_disponibili(ships)

def ai_shots_total():
    """Celle nave AI ancora intatte (valore 0 nella sua grid_matrix)."""
    return sum(
        1 for c in range(ai.GRID_COLS)
          for r in range(ai.GRID_ROWS)
          if ai.grid_matrix[c][r] == 0
    )

# ═══════════════════════════════════════════════════════════════════════
# LOGICA TURNI — usa grid_matrix esattamente come handle_evaluation()
# ═══════════════════════════════════════════════════════════════════════

def resolve_player_volley():
    """
    Applica i colpi del giocatore sulla griglia AI.
    Stessa logica di handle_evaluation() del gruppo, adattata per AI.
    """
    global analysis_lines
    analysis_lines = ["--- Il tuo turno ---"]

    for x, y in player_shots:
        coord = f"{chr(65+x)}{y+1}"
        cell  = ai.grid_matrix[x][y]

        if cell == 0:                        # nave colpita
            ai.grid_matrix[x][y] = 1
            analysis_lines.append(f"  {coord} → COLPITO!")
            if ai.all_sunk():
                analysis_lines.append("  ★ NAVE AFFONDATA!")
        elif cell == -1:                     # acqua
            ai.grid_matrix[x][y] = -2
            analysis_lines.append(f"  {coord} → Acqua")
        else:                                # già sparato
            analysis_lines.append(f"  {coord} → già sparato")

    return ai.all_sunk()


def resolve_ai_volley():
    """
    AI spara sulla griglia del giocatore.
    Modifica my_grid.grid_matrix direttamente, come handle_evaluation().
    """
    analysis_lines.append("--- Turno IA ---")

    for _ in range(ai_shots_total()):
        ac, ar = ai.fire()
        coord  = f"{chr(65+ac)}{ar+1}"
        cell   = my_grid.grid_matrix[ac][ar]

        if cell == 0:                        # nave giocatore colpita
            my_grid.grid_matrix[ac][ar] = 1
            # Cerca se la nave è affondata (nessun 0 connesso rimasto)
            sunk = not any(
                my_grid.grid_matrix[nc][nr] == 0
                for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]
                for nc, nr in [(ac+dc, ar+dr)]
                if 0 <= nc < 13 and 0 <= nr < 13
            )
            ai.report((ac, ar), "sunk" if sunk else "hit")
            if sunk:
                analysis_lines.append(f"  {coord} → IA AFFONDA una tua nave!")
            else:
                analysis_lines.append(f"  {coord} → IA colpisce!")
        elif cell == -1:                     # acqua
            my_grid.grid_matrix[ac][ar] = -2
            ai.report((ac, ar), "miss")
            analysis_lines.append(f"  {coord} → IA manca")
        # celle già colpite (-2 o 1): l'AI non ri-spara (fire() lo evita)

    # Vittoria AI: nessuna cella con valore 0 rimasta
    return all(
        my_grid.grid_matrix[c][r] != 0
        for c in range(13) for r in range(13)
    )

# ═══════════════════════════════════════════════════════════════════════
# GAME LOOP — struttura identica al main.py originale
# ═══════════════════════════════════════════════════════════════════════
running = True

while running:
    now = pygame.time.get_ticks()
    clock.tick(60)
    scan_angle = (scan_angle + 0.5) % 360

    # ── Disegno canvas (prima degli eventi, come nell'originale) ──────
    canvas.blit(main_img,  (0,   0))
    canvas.blit(radar_img, (700, 0))
    my_grid.draw_grid(canvas,    offset_x=MY_OFF_X,    offset_y=MY_OFF_Y)
    enemy_grid.draw_grid(canvas, offset_x=ENEMY_OFF_X, offset_y=ENEMY_OFF_Y)
    gh.draw_ships(canvas, ships)

    # Marcatori hit/miss (HUD)
    hud.draw_markers(canvas, my_grid.grid_matrix,  MY_OFF_X,    MY_OFF_Y,    cell_dimension)
    hud.draw_markers(canvas, ai.grid_matrix,        ENEMY_OFF_X, ENEMY_OFF_Y, cell_dimension)

    # Bersagli selezionati in giallo
    if game_state == "PLAYER_TURN":
        hud.draw_pending(canvas, player_shots, ENEMY_OFF_X, ENEMY_OFF_Y, cell_dimension)

    # Pulsante CONFERMA (come nell'originale, con stile HUD)
    if ships_placed == 5 and not confirmed:
        hud.draw_confirm_button(canvas, (button_rect.x, button_rect.y, button_rect.w, button_rect.h))

    # Overlay HUD sopra tutto
    hud.draw_title_bar(canvas, BASE_W, scan_angle)
    hud.draw_panel_headers(canvas, MY_OFF_X, ENEMY_OFF_X)
    if game_state in ("PLAYER_TURN", "ANALYSIS"):
        hud.draw_hud_shots(canvas, game_state, player_shots_total(), len(player_shots), MY_OFF_X)
    if game_state == "PLACEMENT":
        hud.draw_placement_hint(canvas, MY_OFF_X)

    if game_state == "PLACEMENT":
        if confirmed:
            sm, sc = "ATTENDI...", hud.C_GREEN_DIM
        elif ships_placed == 5:
            sm, sc = "TUTTE LE NAVI PRONTE  //  PREMI CONFERMA", hud.C_AMBER
        else:
            sm, sc = f"NAVI PIAZZATE: {ships_placed}/5  //  [E]/[R] RUOTA", hud.C_GREEN
    elif game_state == "PLAYER_TURN":
        shots = player_shots_total()
        sm, sc = f"SELEZIONA {shots} BERSAGLI  //  [INVIO] PER SPARARE  //  CLIC DX PER RIMUOVERE", hud.C_GREEN
    elif game_state == "ANALYSIS":
        sm, sc = "ANALISI IN CORSO...", hud.C_GREEN_DIM
    elif game_state == "GAMEOVER":
        sm, sc = "PARTITA TERMINATA", hud.C_GREEN
    else:
        sm, sc = "", hud.C_GREEN
    hud.draw_status_bar(canvas, BASE_W, sm, sc)

    if game_state == "ANALYSIS":
        hud.draw_analysis_panel(canvas, BASE_W, BASE_H, analysis_lines)
    if game_state == "GAMEOVER":
        hud.draw_gameover(canvas, BASE_W, BASE_H, winner)

    # ── Eventi ────────────────────────────────────────────────────────
    for event in pygame.event.get():
        present()   # flip ad ogni evento, come nell'originale

        if event.type == pygame.QUIT:
            running = False

        # Fullscreen / resize (non presente nell'originale, aggiunto)
        if event.type == pygame.VIDEORESIZE and not fullscreen:
            screen, SCALE, OX, OY = make_window(fullscreen)
            continue
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11 or (
                event.key == pygame.K_RETURN and bool(event.mod & pygame.KMOD_ALT)
            ):
                toggle_fs()
                continue

        # Scala coordinate mouse → canvas
        if event.type in MOUSE_EVS:
            cx, cy = to_canvas(event.pos)
            event  = pygame.event.Event(event.type, {
                **{k: v for k, v in event.__dict__.items() if k != 'pos'},
                'pos': (cx, cy)
            })

        # ── PLACEMENT (come nell'originale) ───────────────────────────
        if game_state == "PLACEMENT":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ships_placed == 5 and button_rect.collidepoint(event.pos):
                    confirmed  = True
                    game_state = "PLAYER_TURN"

            if not confirmed:
                for ship in ships:
                    if not ship.placed:
                        if ship.handle_event(event):
                            if my_grid.place_ship(ship, MY_OFF_X, MY_OFF_Y):
                                ships_placed += 1

        # ── PLAYER_TURN ───────────────────────────────────────────────
        elif game_state == "PLAYER_TURN":
            max_shots = player_shots_total()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = enemy_grid.get_pos_OnClick(
                    event.pos[0], event.pos[1], ENEMY_OFF_X, ENEMY_OFF_Y
                )
                if pos is not None:
                    x, y = pos
                    if event.button == 1:
                        already_fired   = ai.grid_matrix[x][y] in (1, -2)
                        already_pending = (x, y) in player_shots
                        if not already_fired and not already_pending and len(player_shots) < max_shots:
                            player_shots.append((x, y))
                    elif event.button == 3:
                        if (x, y) in player_shots:
                            player_shots.remove((x, y))

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if player_shots:
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

        # ── ANALYSIS ─────────────────────────────────────────────────
        elif game_state == "ANALYSIS":
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                analysis_timer = 1

    # Auto-avanzamento analisi (fuori dal loop eventi)
    if game_state == "ANALYSIS" and analysis_timer and now >= analysis_timer:
        analysis_timer = 0
        analysis_lines = []
        game_state     = "PLAYER_TURN"

pygame.quit()