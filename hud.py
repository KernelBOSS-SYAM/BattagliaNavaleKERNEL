"""
hud.py — Interfaccia grafica militare HUD per Battaglia Navale.

Usato da main_ai.py. Non dipende da nessun altro file del progetto.
Disegna su qualsiasi pygame.Surface passata come parametro.
"""

import pygame
import math

pygame.font.init()

# ── Font monospace (militare) ─────────────────────────────────────────
def _load_font(size, bold=False):
    for name in ["Courier New", "Courier", "FreeMono", "monospace"]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f: return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

font_title = _load_font(36, bold=True)
font_big   = _load_font(28, bold=True)
font_med   = _load_font(20, bold=True)
font_small = _load_font(15)
font_tiny  = _load_font(13)

# ── Palette ───────────────────────────────────────────────────────────
C_GREEN      = (0,   255,  80)
C_GREEN_DIM  = (0,   140,  45)
C_AMBER      = (255, 180,   0)
C_RED_BRIGHT = (255,  80,  80)
C_CYAN       = (0,   210, 220)
C_WHITE      = (220, 235, 220)
C_GREY       = (80,  100,  80)
C_PANEL_BG   = (4,    14,   8)
C_PANEL_EDGE = (0,   180,  50)
C_SCANLINE   = (0,   255,  80, 18)

# ─────────────────────────────────────────────────────────────────────
# PRIMITIVI
# ─────────────────────────────────────────────────────────────────────

def panel(surf, rect, title="", corner=8, alpha=210):
    """
    Pannello HUD: sfondo scuro semitrasparente, doppio bordo, angoli
    tagliati, tick decorativi e tab con titolo.
    """
    x, y, w, h = rect
    c = corner

    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    bg.fill((*C_PANEL_BG, alpha))
    for px, py in [(0,0),(w-c,0),(0,h-c),(w-c,h-c)]:
        pygame.draw.rect(bg, (0,0,0,0), (px, py, c, c))
    surf.blit(bg, (x, y))

    pts_out = [(x+c,y),(x+w-c,y),(x+w,y+c),(x+w,y+h-c),
               (x+w-c,y+h),(x+c,y+h),(x,y+h-c),(x,y+c)]
    pygame.draw.polygon(surf, C_GREEN_DIM, pts_out, 1)

    m = 3
    pts_in = [(x+c+m,y+m),(x+w-c-m,y+m),(x+w-m,y+c+m),(x+w-m,y+h-c-m),
              (x+w-c-m,y+h-m),(x+c+m,y+h-m),(x+m,y+h-c-m),(x+m,y+c+m)]
    pygame.draw.polygon(surf, C_PANEL_EDGE, pts_in, 1)

    tick = 10
    for ax, ay, dx, dy in [(x,y,1,0),(x,y,0,1),(x+w,y,-1,0),(x+w,y,0,1),
                            (x,y+h,1,0),(x,y+h,0,-1),(x+w,y+h,-1,0),(x+w,y+h,0,-1)]:
        pygame.draw.line(surf, C_GREEN, (ax,ay), (ax+dx*tick, ay+dy*tick), 2)

    if title:
        tag = font_tiny.render(f"  {title}  ", True, C_PANEL_BG)
        tw, th = tag.get_width()+4, tag.get_height()+2
        pygame.draw.rect(surf, C_PANEL_EDGE, (x+c+4, y-th//2, tw, th))
        surf.blit(tag, (x+c+6, y-th//2+1))


def scanlines(surf, rect, spacing=4):
    x, y, w, h = rect
    ls = pygame.Surface((w, h), pygame.SRCALPHA)
    for ly in range(0, h, spacing):
        pygame.draw.line(ls, C_SCANLINE, (0, ly), (w, ly))
    surf.blit(ls, (x, y))


def shot_pips(surf, x, y, total, selected):
    pip_w, pip_h, gap = 16, 8, 4
    for i in range(min(total, 50)):   # max 50 pip per non sforare
        col = C_AMBER if i < selected else C_GREY
        rx  = x + i * (pip_w + gap)
        pygame.draw.rect(surf, col, (rx, y, pip_w, pip_h))


def draw_markers(surf, grid_matrix, offset_x, offset_y, cell):
    """
    Disegna i marcatori colpito/mancato sulla griglia basandosi su
    grid_matrix (struttura del gruppo):
        1  → croce rossa (colpito)
       -2  → cerchio blu (mancato / acqua)
    """
    cols = len(grid_matrix)
    rows = len(grid_matrix[0]) if cols > 0 else 0
    pad  = 6

    for cx in range(cols):
        for ry in range(rows):
            val = grid_matrix[cx][ry]
            rx  = offset_x + cx * cell
            ry_ = offset_y + ry * cell

            if val == 1:   # colpito
                pygame.draw.rect(surf, (200, 40, 40), (rx, ry_, cell, cell))
                pygame.draw.line(surf, (255,255,255), (rx+pad, ry_+pad),       (rx+cell-pad, ry_+cell-pad), 3)
                pygame.draw.line(surf, (255,255,255), (rx+cell-pad, ry_+pad),  (rx+pad,      ry_+cell-pad), 3)

            elif val == -2:   # acqua sparata
                pygame.draw.rect(surf, (40, 80, 160), (rx, ry_, cell, cell))
                pygame.draw.circle(surf, (255,255,255), (rx+cell//2, ry_+cell//2), 6)


def draw_pending(surf, targets, offset_x, offset_y, cell):
    """Evidenzia in giallo le celle selezionate dal giocatore."""
    for col, row in targets:
        rx = offset_x + col * cell
        ry = offset_y + row * cell
        pygame.draw.rect(surf, (255, 220, 0),   (rx, ry, cell, cell))
        pygame.draw.rect(surf, (255, 255, 255), (rx, ry, cell, cell), 2)


# ─────────────────────────────────────────────────────────────────────
# SEZIONI COMPOSITE
# ─────────────────────────────────────────────────────────────────────

def draw_title_bar(surf, w, scan_angle):
    bar_h = 44
    pygame.draw.rect(surf, C_PANEL_BG, (0, 0, w, bar_h))
    pygame.draw.line(surf, C_PANEL_EDGE, (0, bar_h),   (w, bar_h),   2)
    pygame.draw.line(surf, C_GREEN_DIM,  (0, bar_h+2), (w, bar_h+2), 1)

    a = font_big.render("⚓", True, C_GREEN)
    surf.blit(a, (20, 6))
    surf.blit(a, (w - 20 - a.get_width(), 6))

    t = font_title.render("BATTAGLIA NAVALE  //  RADAR OPERATIONS", True, C_GREEN)
    surf.blit(t, (w//2 - t.get_width()//2, 6))

    hint = font_tiny.render("[F11] FULLSCREEN", True, C_GREEN_DIM)
    surf.blit(hint, (w - hint.get_width() - 10, bar_h + 4))

    for i in range(12):
        angle = math.radians(i * 30 + scan_angle * 4)
        tx    = int(w - 130 + math.cos(angle) * 10)
        ty    = int(bar_h // 2 + math.sin(angle) * 6)
        pygame.draw.circle(surf, (0, int(255 * i / 12), 0), (tx, ty), 2)


def draw_panel_headers(surf, my_off_x, enemy_off_x):
    panel(surf, (my_off_x-10, 50, 560, 34), title="SISTEMA")
    t = font_med.render("·· SCHIERA LA TUA FLOTTA ··", True, C_GREEN)
    surf.blit(t, (my_off_x - 10 + 560//2 - t.get_width()//2, 56))

    panel(surf, (enemy_off_x-10, 50, 560, 34), title="AI-SONAR v1.3")
    t2 = font_med.render("·· RADAR NEMICO ··", True, C_GREEN)
    surf.blit(t2, (enemy_off_x - 10 + 560//2 - t2.get_width()//2, 56))


def draw_hud_shots(surf, state, shots_total, shots_selected, my_off_x):
    px, py, pw = my_off_x - 10, 700, 560
    panel(surf, (px, py, pw, 90), title="ARSENALE")
    scanlines(surf, (px, py, pw, 90))

    label = font_small.render(
        f"COLPI: {shots_total:02d}   SELEZIONATI: {shots_selected:02d}/{shots_total:02d}",
        True, C_GREEN
    )
    surf.blit(label, (px+14, py+10))
    shot_pips(surf, px+14, py+34, shots_total, shots_selected)

    if state == "PLAYER_TURN":
        if shots_selected < shots_total:
            tip_txt = f"SELEZIONA {shots_total - shots_selected} BERSAGLI  //  [INVIO] FUOCO"
            tip_col = C_GREEN_DIM
        else:
            tip_txt = "[INVIO] APRI IL FUOCO  ·  CLIC DX PER DESELEZIONARE"
            tip_col = C_AMBER
        tip = font_tiny.render(tip_txt, True, tip_col)
        surf.blit(tip, (px+14, py+66))


def draw_status_bar(surf, w, status_msg, status_color):
    bar_y = 855
    pygame.draw.rect(surf, C_PANEL_BG, (0, bar_y, w, 45))
    pygame.draw.line(surf, C_PANEL_EDGE, (0, bar_y),   (w, bar_y),   2)
    pygame.draw.line(surf, C_GREEN_DIM,  (0, bar_y+2), (w, bar_y+2), 1)

    for i, bx in enumerate(range(8, 80, 10)):
        pygame.draw.rect(surf, (0, max(0, 255-i*30), 0), (bx, bar_y+16, 6, 12))

    prefix = font_small.render("·· STATO: ", True, C_GREEN_DIM)
    surf.blit(prefix, (90, bar_y+12))
    surf.blit(font_med.render(status_msg.upper(), True, status_color), (90+prefix.get_width(), bar_y+10))

    for i, bx in enumerate(range(w-8, w-80, -10)):
        pygame.draw.rect(surf, (0, max(0, 255-i*30), 0), (bx-6, bar_y+16, 6, 12))


def draw_analysis_panel(surf, w, h, analysis_lines):
    px, py, pw, ph = 300, 160, 800, 560
    panel(surf, (px, py, pw, ph), title="RAPPORTO DI COMBATTIMENTO", alpha=240)
    scanlines(surf, (px, py, pw, ph), spacing=3)

    t = font_big.render("//  FASE DI ANALISI  //", True, C_GREEN)
    surf.blit(t, (px + pw//2 - t.get_width()//2, py+18))
    pygame.draw.line(surf, C_PANEL_EDGE, (px+20, py+54), (px+pw-20, py+54), 1)

    for i, line in enumerate(analysis_lines[:22]):
        if "COLPITO" in line or "AFFONDA" in line or "colpisce" in line:
            col, marker = C_RED_BRIGHT, "▶ "
        elif "Acqua" in line or "manca" in line:
            col, marker = C_CYAN, "· "
        elif "---" in line:
            col, marker = C_GREEN, ""
        else:
            col, marker = C_AMBER, "★ "
        surf.blit(font_small.render(marker + line.strip(), True, col), (px+30, py+66+i*21))

    pygame.draw.line(surf, C_PANEL_EDGE, (px+20, py+ph-38), (px+pw-20, py+ph-38), 1)
    hint = font_tiny.render("[QUALSIASI TASTO]  PROSSIMO TURNO  ··", True, C_GREEN_DIM)
    surf.blit(hint, (px + pw//2 - hint.get_width()//2, py+ph-26))


def draw_confirm_button(surf, rect):
    """Bottone CONFERMA stile HUD."""
    x, y, w, h = rect
    panel(surf, rect, title="")
    t = font_med.render("[ CONFERMA FLOTTA ]", True, C_GREEN)
    surf.blit(t, (x + w//2 - t.get_width()//2, y + h//2 - t.get_height()//2))


def draw_placement_hint(surf, off_x):
    t = font_tiny.render(
        "·· TRASCINA LE NAVI  //  [E] o [R] RUOTA MENTRE TRASCINI ··",
        True, C_GREEN_DIM
    )
    surf.blit(t, (off_x, 836))


def draw_gameover(surf, w, h, winner):
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surf.blit(overlay, (0, 0))

    pw, ph = 640, 260
    px, py = w//2 - pw//2, h//2 - ph//2
    panel(surf, (px, py, pw, ph), title="FINE PARTITA", alpha=250)
    scanlines(surf, (px, py, pw, ph), spacing=3)

    if winner == "player":
        msg, sub, color = "//  VITTORIA  //", "FLOTTA NEMICA DISTRUTTA", C_GREEN
    else:
        msg, sub, color = "//  SCONFITTA  //", "LA TUA FLOTTA È AFFONDATA", C_RED_BRIGHT

    m = font_title.render(msg, True, color)
    surf.blit(m, (w//2 - m.get_width()//2, py+60))
    s = font_med.render(sub, True, C_WHITE)
    surf.blit(s, (w//2 - s.get_width()//2, py+110))
    hint = font_small.render("CHIUDI LA FINESTRA PER USCIRE", True, C_GREEN_DIM)
    surf.blit(hint, (w//2 - hint.get_width()//2, py+165))
