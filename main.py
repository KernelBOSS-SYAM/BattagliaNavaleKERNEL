import pygame
import sys
import math
import Grid
import Nave
import AI

# ═══════════════════════════════════════════════════════════════════════
# RISOLUZIONE DINAMICA
#
# Tutta la logica di gioco e il rendering lavorano su una superficie
# interna fissa BASE_W × BASE_H (1400×900).
# Al termine di ogni frame, questa superficie viene scalata alla
# risoluzione reale dello schermo (fullscreen o finestra ridimensionata).
#
# Toggle fullscreen: [F11] o [ALT+INVIO]
# ═══════════════════════════════════════════════════════════════════════
pygame.init()
pygame.font.init()

BASE_W, BASE_H = 1400, 900   # coordinate interne fisse — NON cambiare

# ── Risoluzione display ───────────────────────────────────────────────
display_info = pygame.display.Info()
NATIVE_W     = display_info.current_w
NATIVE_H     = display_info.current_h

fullscreen   = False

def make_window(fs):
    """Crea o ricrea la finestra. Ritorna (screen, scale, offset_x, offset_y)."""
    if fs:
        surf = pygame.display.set_mode((NATIVE_W, NATIVE_H), pygame.FULLSCREEN)
        sw, sh = NATIVE_W, NATIVE_H
    else:
        # Finestra iniziale: 90% del desktop, con proporzione 14:9
        win_w = int(NATIVE_W * 0.9)
        win_h = int(win_w * BASE_H / BASE_W)
        if win_h > int(NATIVE_H * 0.9):
            win_h = int(NATIVE_H * 0.9)
            win_w = int(win_h * BASE_W / BASE_H)
        surf = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        sw, sh = win_w, win_h

    scale   = min(sw / BASE_W, sh / BASE_H)
    off_x   = (sw - int(BASE_W * scale)) // 2
    off_y   = (sh - int(BASE_H * scale)) // 2
    return surf, scale, off_x, off_y

screen, SCALE, OFF_X, OFF_Y = make_window(fullscreen)
pygame.display.set_caption("BATTAGLIA NAVALE // RADAR OPS")

# Superficie interna su cui si disegna tutto
canvas = pygame.Surface((BASE_W, BASE_H))

def present():
    """Scala canvas → screen e mostra."""
    scaled = pygame.transform.smoothscale(
        canvas, (int(BASE_W * SCALE), int(BASE_H * SCALE))
    )
    screen.fill((0, 0, 0))
    screen.blit(scaled, (OFF_X, OFF_Y))
    pygame.display.flip()

def screen_to_canvas(pos):
    """Converti coordinate mouse (schermo reale) → canvas interno."""
    mx = (pos[0] - OFF_X) / SCALE
    my = (pos[1] - OFF_Y) / SCALE
    return (mx, my)

def toggle_fullscreen():
    global screen, SCALE, OFF_X, OFF_Y, fullscreen
    fullscreen = not fullscreen
    screen, SCALE, OFF_X, OFF_Y = make_window(fullscreen)

# ── Fonts ─────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    for name in ["Courier New", "Courier", "FreeMono", "monospace"]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f: return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

font_title = load_font(36, bold=True)
font_big   = load_font(28, bold=True)
font_med   = load_font(20, bold=True)
font_small = load_font(15)
font_tiny  = load_font(13)

# ── Palette ───────────────────────────────────────────────────────────
C_GREEN      = (0,   255,  80)
C_GREEN_DIM  = (0,   140,  45)
C_GREEN_DARK = (0,    40,  15)
C_AMBER      = (255, 180,   0)
C_RED        = (220,  40,  40)
C_RED_BRIGHT = (255,  80,  80)
C_CYAN       = (0,   210, 220)
C_WHITE      = (220, 235, 220)
C_GREY       = (80,  100,  80)
C_PANEL_BG   = (4,    14,   8)
C_PANEL_EDGE = (0,   180,  50)
C_SCANLINE   = (0,   255,  80, 18)

# ── Costanti layout (coordinate canvas) ──────────────────────────────
CELL           = 40
COLS           = 13
ROWS           = 13
MY_OFFSET_X    = 90
MY_OFFSET_Y    = 155
ENEMY_OFFSET_X = 790
ENEMY_OFFSET_Y = 155
ANALYSIS_DELAY = 2500

# ── Sfondi (caricati una volta, scalati al canvas) ────────────────────
main_bg  = pygame.transform.scale(pygame.image.load('./img/main.png').convert(),  (700, BASE_H))
radar_bg = pygame.transform.scale(pygame.image.load('./img/radar.jpg').convert(), (700, BASE_H))

# ── Griglie ───────────────────────────────────────────────────────────
my_grid    = Grid.Grid(CELL, COLS, ROWS, C_GREEN_DIM)
enemy_grid = Grid.Grid(CELL, COLS, ROWS, C_GREEN_DIM)

# ── Navi ──────────────────────────────────────────────────────────────
SHIP_DEFS = [
    ("portaerei",          "./img/portaAerei.png",        5),
    ("corazzata",          "./img/corazzata.png",         4),
    ("incrociatore1",      "./img/incrociatore.png",      3),
    ("incrociatore2",      "./img/incrociatore.png",      3),
    ("cacciatorpediniere", "./img/cacciatorpediniere.png", 2),
]
DOCK_POSITIONS   = [(80,720),(180,720),(280,720),(380,720),(480,720)]
TOTAL_SHIP_CELLS = sum(s for _, _, s in SHIP_DEFS)

ships = []
for i, (nome, img_path, size) in enumerate(SHIP_DEFS):
    ship      = Nave.Nave(nome, img_path, size)
    base_img  = pygame.image.load(img_path).convert_alpha()
    ship.rect = base_img.get_rect(topleft=DOCK_POSITIONS[i])
    ships.append(ship)

# ── Stato posizionamento ──────────────────────────────────────────────
player_ship_cells = {}
player_occupied   = set()

# ── Colpi ─────────────────────────────────────────────────────────────
def player_shots_available():
    return TOTAL_SHIP_CELLS - sum(
        1 for c in player_occupied if my_grid.get_cell_state(c[0], c[1]) == "hit"
    )

def ai_shots_available():
    return TOTAL_SHIP_CELLS - sum(
        1 for c in ai.ship_cells if enemy_grid.get_cell_state(c[0], c[1]) == "hit"
    )

ai             = AI.AIOpponent()
player_targets = []

# ── Stato di gioco ────────────────────────────────────────────────────
STATE          = "placement"
winner         = ""
analysis_lines = []
analysis_timer = 0
status_msg     = "POSIZIONA LE NAVI  |  TRASCINA SULLA GRIGLIA  //  [R] RUOTA"
status_color   = C_GREEN

clock      = pygame.time.Clock()
scan_angle = 0.0

# ═══════════════════════════════════════════════════════════════════════
# PRIMITIVI UI  (disegnano su canvas)
# ═══════════════════════════════════════════════════════════════════════

def hud_panel(rect, title="", corner=8, alpha=210):
    x, y, w, h = rect
    c = corner
    panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    panel_surf.fill((*C_PANEL_BG, alpha))
    for px, py in [(0,0),(w-c,0),(0,h-c),(w-c,h-c)]:
        pygame.draw.rect(panel_surf, (0,0,0,0), (px, py, c, c))
    canvas.blit(panel_surf, (x, y))

    pts_outer = [(x+c,y),(x+w-c,y),(x+w,y+c),(x+w,y+h-c),
                 (x+w-c,y+h),(x+c,y+h),(x,y+h-c),(x,y+c)]
    pygame.draw.polygon(canvas, C_GREEN_DIM, pts_outer, 1)

    m = 3
    pts_inner = [(x+c+m,y+m),(x+w-c-m,y+m),(x+w-m,y+c+m),(x+w-m,y+h-c-m),
                 (x+w-c-m,y+h-m),(x+c+m,y+h-m),(x+m,y+h-c-m),(x+m,y+c+m)]
    pygame.draw.polygon(canvas, C_PANEL_EDGE, pts_inner, 1)

    tick = 10
    for ax, ay, dx, dy in [(x,y,1,0),(x,y,0,1),(x+w,y,-1,0),(x+w,y,0,1),
                            (x,y+h,1,0),(x,y+h,0,-1),(x+w,y+h,-1,0),(x+w,y+h,0,-1)]:
        pygame.draw.line(canvas, C_GREEN, (ax,ay), (ax+dx*tick, ay+dy*tick), 2)

    if title:
        tag = font_tiny.render(f"  {title}  ", True, C_PANEL_BG)
        tw, th = tag.get_width()+4, tag.get_height()+2
        pygame.draw.rect(canvas, C_PANEL_EDGE, (x+c+4, y-th//2, tw, th))
        canvas.blit(tag, (x+c+6, y-th//2+1))


def draw_scanlines(rect, spacing=4):
    x, y, w, h = rect
    ls = pygame.Surface((w, h), pygame.SRCALPHA)
    for ly in range(0, h, spacing):
        pygame.draw.line(ls, C_SCANLINE, (0, ly), (w, ly))
    canvas.blit(ls, (x, y))


def draw_shot_pips(x, y, total, selected):
    pip_w, pip_h, gap = 16, 8, 4
    for i in range(total):
        col = C_AMBER if i < selected else C_GREY
        rx  = x + i * (pip_w + gap)
        pygame.draw.rect(canvas, col, (rx, y, pip_w, pip_h))


# ═══════════════════════════════════════════════════════════════════════
# SEZIONI UI COMPOSTE
# ═══════════════════════════════════════════════════════════════════════

def draw_title_bar():
    bar_h = 44
    pygame.draw.rect(canvas, C_PANEL_BG, (0, 0, BASE_W, bar_h))
    pygame.draw.line(canvas, C_PANEL_EDGE, (0, bar_h),   (BASE_W, bar_h),   2)
    pygame.draw.line(canvas, C_GREEN_DIM,  (0, bar_h+2), (BASE_W, bar_h+2), 1)

    a_surf = font_big.render("⚓", True, C_GREEN)
    canvas.blit(a_surf, (20, 6))
    canvas.blit(a_surf, (BASE_W - 20 - a_surf.get_width(), 6))

    title_txt = font_title.render("BATTAGLIA NAVALE  //  RADAR OPERATIONS", True, C_GREEN)
    canvas.blit(title_txt, (BASE_W//2 - title_txt.get_width()//2, 6))

    # F11 hint (top-right)
    hint = font_tiny.render("[F11] FULLSCREEN", True, C_GREEN_DIM)
    canvas.blit(hint, (BASE_W - hint.get_width() - 10, bar_h + 4))

    for i in range(12):
        angle = math.radians(i * 30 + scan_angle * 4)
        tx    = int(BASE_W - 130 + math.cos(angle) * 10)
        ty    = int(bar_h // 2 + math.sin(angle) * 6)
        alpha = int(255 * (i / 12))
        pygame.draw.circle(canvas, (0, alpha, 0), (tx, ty), 2)


def draw_panel_headers():
    hud_panel((MY_OFFSET_X-10, 50, 560, 34), title="SISTEMA")
    t = font_med.render("·· SCHIERA LA TUA FLOTTA ··", True, C_GREEN)
    canvas.blit(t, (MY_OFFSET_X - 10 + 560//2 - t.get_width()//2, 56))

    hud_panel((ENEMY_OFFSET_X-10, 50, 560, 34), title="AI-SONAR v1.3")
    t2 = font_med.render("·· RADAR NEMICO ··", True, C_GREEN)
    canvas.blit(t2, (ENEMY_OFFSET_X - 10 + 560//2 - t2.get_width()//2, 56))


def draw_hud():
    shots    = player_shots_available()
    selected = len(player_targets)
    px, py, pw = MY_OFFSET_X - 10, 700, 560

    hud_panel((px, py, pw, 90), title="ARSENALE")
    draw_scanlines((px, py, pw, 90))

    label = font_small.render(
        f"COLPI: {shots:02d}   SELEZIONATI: {selected:02d}/{shots:02d}".upper(),
        True, C_GREEN
    )
    canvas.blit(label, (px+14, py+10))
    draw_shot_pips(px+14, py+34, shots, selected)

    if STATE == "player_selecting":
        if selected < shots:
            tip_txt = f"SELEZIONA ANCORA {shots-selected} BERSAGLI  //  [INVIO] FUOCO"
            tip_col = C_GREEN_DIM
        else:
            tip_txt = "[INVIO] APRI IL FUOCO  ·  CLIC DX PER DESELEZIONARE"
            tip_col = C_AMBER
        tip = font_tiny.render(tip_txt, True, tip_col)
        canvas.blit(tip, (px+14, py+66))


def draw_status_bar():
    bar_y = 855
    pygame.draw.rect(canvas, C_PANEL_BG, (0, bar_y, BASE_W, 45))
    pygame.draw.line(canvas, C_PANEL_EDGE, (0, bar_y),   (BASE_W, bar_y),   2)
    pygame.draw.line(canvas, C_GREEN_DIM,  (0, bar_y+2), (BASE_W, bar_y+2), 1)

    for i, bx in enumerate(range(8, 80, 10)):
        alpha = max(0, 255 - i * 30)
        pygame.draw.rect(canvas, (0, alpha, 0), (bx, bar_y+16, 6, 12))

    prefix = font_small.render("·· STATO: ", True, C_GREEN_DIM)
    canvas.blit(prefix, (90, bar_y+12))
    msg_surf = font_med.render(status_msg.upper(), True, status_color)
    canvas.blit(msg_surf, (90 + prefix.get_width(), bar_y+10))

    for i, bx in enumerate(range(BASE_W-8, BASE_W-80, -10)):
        alpha = max(0, 255 - i * 30)
        pygame.draw.rect(canvas, (0, alpha, 0), (bx-6, bar_y+16, 6, 12))


def draw_analysis_panel():
    px, py, pw, ph = 300, 160, 800, 560
    hud_panel((px, py, pw, ph), title="RAPPORTO DI COMBATTIMENTO", alpha=240)
    draw_scanlines((px, py, pw, ph), spacing=3)

    title = font_big.render("//  FASE DI ANALISI  //", True, C_GREEN)
    canvas.blit(title, (px + pw//2 - title.get_width()//2, py+18))
    pygame.draw.line(canvas, C_PANEL_EDGE, (px+20, py+54), (px+pw-20, py+54), 1)

    for i, line in enumerate(analysis_lines[:22]):
        if "COLPITO" in line or "AFFONDA" in line or "colpisce" in line:
            col, marker = C_RED_BRIGHT, "▶ "
        elif "Acqua" in line or "manca" in line:
            col, marker = C_CYAN, "· "
        elif "---" in line:
            col, marker = C_GREEN, ""
        else:
            col, marker = C_AMBER, "★ "
        txt = font_small.render(marker + line.strip(), True, col)
        canvas.blit(txt, (px+30, py+66 + i*21))

    pygame.draw.line(canvas, C_PANEL_EDGE, (px+20, py+ph-38), (px+pw-20, py+ph-38), 1)
    hint = font_tiny.render("[QUALSIASI TASTO]  PROSSIMO TURNO  ··", True, C_GREEN_DIM)
    canvas.blit(hint, (px + pw//2 - hint.get_width()//2, py+ph-26))


def draw_gameover():
    overlay = pygame.Surface((BASE_W, BASE_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    canvas.blit(overlay, (0, 0))

    pw, ph = 640, 260
    px     = BASE_W//2 - pw//2
    py     = BASE_H//2 - ph//2
    hud_panel((px, py, pw, ph), title="FINE PARTITA", alpha=250)
    draw_scanlines((px, py, pw, ph), spacing=3)

    if winner == "Player":
        msg, sub, color = "//  VITTORIA  //", "FLOTTA NEMICA DISTRUTTA", C_GREEN
    else:
        msg, sub, color = "//  SCONFITTA  //", "LA TUA FLOTTA È AFFONDATA", C_RED_BRIGHT

    m_surf = font_title.render(msg, True, color)
    canvas.blit(m_surf, (BASE_W//2 - m_surf.get_width()//2, py+60))
    s_surf = font_med.render(sub, True, C_WHITE)
    canvas.blit(s_surf, (BASE_W//2 - s_surf.get_width()//2, py+110))
    hint = font_small.render("CHIUDI LA FINESTRA PER USCIRE", True, C_GREEN_DIM)
    canvas.blit(hint, (BASE_W//2 - hint.get_width()//2, py+165))


def draw_placement_hint():
    t = font_tiny.render(
        "·· TRASCINA LE NAVI SULLA GRIGLIA  //  [R] RUOTA MENTRE TRASCINI ··",
        True, C_GREEN_DIM
    )
    canvas.blit(t, (MY_OFFSET_X, 836))


# ═══════════════════════════════════════════════════════════════════════
# LOGICA DI BATTAGLIA
# ═══════════════════════════════════════════════════════════════════════

def check_sunk(hits_set, all_ship_cells, ship_configs):
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

    sizes_left, sunk = [s for _, s in ship_configs], []
    for comp in components:
        if all(c in all_ship_cells for c in comp):
            sz = len(comp)
            if sz in sizes_left:
                sizes_left.remove(sz)
                sunk.append(sz)
    return sunk


def resolve_player_volley():
    global analysis_lines
    analysis_lines = ["--- Il tuo turno ---"]
    for col, row in player_targets:
        coord = f"{chr(65+col)}{row+1}"
        if ai.has_ship_at(col, row):
            enemy_grid.set_cell_state(col, row, "hit")
            analysis_lines.append(f"  {coord} → COLPITO!")
        else:
            enemy_grid.set_cell_state(col, row, "miss")
            analysis_lines.append(f"  {coord} → Acqua")
    all_hits = {(c,r) for c in range(COLS) for r in range(ROWS)
                if enemy_grid.get_cell_state(c, r) == "hit"}
    for sz in check_sunk(all_hits, ai.ship_cells, AI.AIOpponent.SHIP_CONFIGS):
        analysis_lines.append(f"  *** Nave affondata (dimensione {sz})! ***")
    return all_hits >= ai.ship_cells


def resolve_ai_volley(num_shots):
    analysis_lines.append("--- Turno IA ---")
    for _ in range(num_shots):
        ac, ar = ai.fire()
        coord  = f"{chr(65+ac)}{ar+1}"
        if (ac, ar) in player_ship_cells:
            my_grid.set_cell_state(ac, ar, "hit")
            hit_ship   = player_ship_cells[(ac, ar)]
            fully_sunk = all(my_grid.get_cell_state(c, r) == "hit"
                             for c, r in hit_ship.grid_cells)
            ai.report((ac, ar), "sunk" if fully_sunk else "hit")
            analysis_lines.append(
                f"  {coord} → IA AFFONDA la tua {hit_ship.nome}!" if fully_sunk
                else f"  {coord} → IA colpisce!"
            )
        else:
            my_grid.set_cell_state(ac, ar, "miss")
            ai.report((ac, ar), "miss")
            analysis_lines.append(f"  {coord} → IA manca")
    all_ai_hits = {(c,r) for c in range(COLS) for r in range(ROWS)
                   if my_grid.get_cell_state(c, r) == "hit"}
    return all_ai_hits >= player_occupied


# ═══════════════════════════════════════════════════════════════════════
# GAME LOOP
# ═══════════════════════════════════════════════════════════════════════
running = True
while running:
    now = pygame.time.get_ticks()
    clock.tick(60)
    scan_angle = (scan_angle + 0.5) % 360

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()

        # ── Toggle fullscreen ─────────────────────────────────────────
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11 or (
                event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT
            ):
                toggle_fullscreen()
                continue  # salta il resto del processing per questo evento

        # ── Resize finestra ───────────────────────────────────────────
        if event.type == pygame.VIDEORESIZE and not fullscreen:
            screen, SCALE, OFF_X, OFF_Y = make_window(fullscreen)

        # ── Converti coordinate mouse → canvas ───────────────────────
        # Inietta una copia dell'evento con posizione scalata
        if hasattr(event, 'pos'):
            cx, cy = screen_to_canvas(event.pos)
            # Ricrea evento con posizione canvas per tutti i controlli
            event = pygame.event.Event(event.type, {
                **{k: v for k, v in event.__dict__.items() if k != 'pos'},
                'pos': (cx, cy)
            })

        # ── POSIZIONAMENTO ────────────────────────────────────────────
        if STATE == "placement":
            was_dragging = {s for s in ships if s.dragging}
            for ship in ships:
                ship.handle_event(event)

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
                status_msg   = f"TURNO 1  //  SELEZIONA {player_shots_available()} BERSAGLI  [INVIO] FUOCO"
                status_color = C_GREEN

        # ── SELEZIONE BERSAGLI ────────────────────────────────────────
        elif STATE == "player_selecting":
            shots = player_shots_available()

            if event.type == pygame.MOUSEBUTTONDOWN:
                cell = enemy_grid.get_pos_OnClick(
                    event.pos[0], event.pos[1],
                    offset_x=ENEMY_OFFSET_X, offset_y=ENEMY_OFFSET_Y
                )
                if cell:
                    col, row        = cell
                    already_fired   = enemy_grid.get_cell_state(col, row) in ("hit", "miss")
                    already_pending = (col, row) in player_targets

                    if event.button == 1:
                        if already_fired:
                            status_msg, status_color = "CELLA GIA' COLPITA", C_AMBER
                        elif already_pending:
                            status_msg, status_color = "GIA' SELEZIONATA  //  CLIC DX PER RIMUOVERE", C_AMBER
                        elif len(player_targets) >= shots:
                            status_msg, status_color = f"MAX {shots} BERSAGLI  //  PREMI [INVIO]", C_AMBER
                        else:
                            player_targets.append((col, row))
                            status_msg   = f"BERSAGLI: {len(player_targets)}/{shots}  //  [INVIO] PER SPARARE"
                            status_color = C_GREEN
                    elif event.button == 3:
                        if already_pending:
                            player_targets.remove((col, row))
                            status_msg   = f"RIMOSSO  //  BERSAGLI: {len(player_targets)}/{shots}"
                            status_color = C_GREEN_DIM

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if not player_targets:
                    status_msg, status_color = "SELEZIONA ALMENO UN BERSAGLIO", C_AMBER
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

        # ── ANALISI ───────────────────────────────────────────────────
        elif STATE == "analysis":
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                analysis_timer = 1

    # Auto-avanzamento analisi
    if STATE == "analysis" and analysis_timer and now >= analysis_timer:
        analysis_timer = 0
        analysis_lines = []
        STATE          = "player_selecting"
        shots          = player_shots_available()
        status_msg     = f"IL TUO TURNO  //  SELEZIONA {shots} BERSAGLI"
        status_color   = C_GREEN

    # ─────────────────────────────────────────────────────────────────
    # RENDER SUL CANVAS (coordinate sempre BASE_W×BASE_H)
    # ─────────────────────────────────────────────────────────────────
    canvas.blit(main_bg,  (0,   0))
    canvas.blit(radar_bg, (700, 0))

    draw_title_bar()
    draw_panel_headers()

    my_grid.draw_grid(canvas,    offset_x=MY_OFFSET_X,    offset_y=MY_OFFSET_Y)
    enemy_grid.draw_grid(canvas, offset_x=ENEMY_OFFSET_X, offset_y=ENEMY_OFFSET_Y)

    if STATE == "player_selecting":
        enemy_grid.draw_pending(canvas, player_targets, ENEMY_OFFSET_X, ENEMY_OFFSET_Y)

    for ship in ships:
        if ship.placed:
            ship.draw_on_grid(canvas, CELL, MY_OFFSET_X, MY_OFFSET_Y)
        else:
            ship.draw_nave(canvas)

    if STATE in ("player_selecting", "analysis"):
        draw_hud()

    if STATE == "placement":
        draw_placement_hint()

    draw_status_bar()

    if STATE == "analysis":
        draw_analysis_panel()

    if STATE == "gameover":
        draw_gameover()

    # ── Scala canvas → schermo reale ─────────────────────────────────
    present()

pygame.quit()