"""All colors, sizes, and fonts in one place."""

from __future__ import annotations

import os
import sys

import pygame

# ── Window ───────────────────────────────────────────────────────────────────
WIN_W = 1280
WIN_H = 800
FPS   = 60

# ── Color palette — warm charcoal, classic board ────────────────────────────
BG          = (26,  28,  35)    # window background (also the board's holes)
SURFACE     = (36,  39,  48)    # cards and the coach panel
SURFACE_HI  = (46,  50,  62)    # raised / hovered surfaces
BORDER      = (62,  67,  82)    # hairlines and outlines
BOARD_BG    = (36,  84, 168)    # board slab
BOARD_FRAME = (24,  58, 124)    # slab edge and hole rim
EMPTY       = BG                # empty hole shows the window behind
P1_DISC     = (232,  86,  76)   # coral red (Player 1)
P2_DISC     = (244, 192,  62)   # warm gold (Player 2)
WIN_GLOW    = (96, 214, 178)    # soft teal highlight
TEXT        = (234, 236, 242)
DIM_TEXT    = (148, 154, 172)
PANEL_BG    = SURFACE
BTN_NORMAL  = (46,  50,  62)
BTN_HOVER   = (64,  70,  88)
BTN_TEXT    = TEXT
BANNER_BG   = (20,  22,  28, 225)  # semi-transparent overlay (RGBA)

# Kept for the starfield/nebula classes that still exist but are no longer drawn
NEBULA_A    = BG
NEBULA_B    = BG

# Player accent pairs (fill, glow)
P1_GLOW     = (244, 140, 130)
P2_GLOW     = (250, 215, 120)

# HvH mode third button color
HVH_COLOR   = ( 98, 196, 140)

# ── Theme switching ───────────────────────────────────────────────────────────
# Disc colours are identical in both themes; only surfaces, text and accents change.
_DARK = {
    "BG": (26, 28, 35), "SURFACE": (36, 39, 48), "SURFACE_HI": (46, 50, 62),
    "BORDER": (62, 67, 82), "BOARD_BG": (36, 84, 168), "BOARD_FRAME": (24, 58, 124),
    "WIN_GLOW": (96, 214, 178), "TEXT": (234, 236, 242), "DIM_TEXT": (148, 154, 172),
    "BTN_NORMAL": (46, 50, 62), "BTN_HOVER": (64, 70, 88),
    "BANNER_BG": (20, 22, 28, 225), "SHADOW_ALPHA": 70,
}
_LIGHT = {
    "BG": (243, 240, 234), "SURFACE": (253, 252, 249), "SURFACE_HI": (234, 230, 221),
    "BORDER": (212, 206, 195), "BOARD_BG": (44, 98, 188), "BOARD_FRAME": (30, 70, 146),
    "WIN_GLOW": (24, 150, 120), "TEXT": (34, 37, 46), "DIM_TEXT": (108, 112, 126),
    "BTN_NORMAL": (236, 232, 223), "BTN_HOVER": (223, 218, 207),
    "BANNER_BG": (243, 240, 234, 225), "SHADOW_ALPHA": 40,
}
THEMES = {"dark": _DARK, "light": _LIGHT}
THEME_NAME = "dark"
SHADOW_ALPHA = _DARK["SHADOW_ALPHA"]


def set_theme(name: str) -> None:
    """Switch every module-level colour to the ``"dark"`` or ``"light"`` palette."""
    global THEME_NAME, EMPTY, PANEL_BG, BTN_TEXT, NEBULA_A, NEBULA_B
    palette = THEMES[name]
    globals().update(palette)
    THEME_NAME = name
    EMPTY = BG            # type: ignore[name-defined]  # empty holes show the window
    PANEL_BG = SURFACE    # type: ignore[name-defined]
    BTN_TEXT = TEXT       # type: ignore[name-defined]
    NEBULA_A = NEBULA_B = BG  # type: ignore[name-defined]


# ── Board geometry ────────────────────────────────────────────────────────────
BOARD_COLS   = 7
BOARD_ROWS   = 6
CELL_SIZE    = 84          # px per cell
DISC_RADIUS  = 34
BOARD_LEFT   = 36          # left edge of the board area
BOARD_TOP    = 135         # top edge of the board area (room for top bar + hints)

# ── Fonts ─────────────────────────────────────────────────────────────────────
_MPLFONTS = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", ".venv", "lib",
    f"python{sys.version_info.major}.{sys.version_info.minor}",
    "site-packages", "matplotlib", "mpl-data", "fonts", "ttf",
))
_INTER = "/usr/share/fonts/opentype/inter"

# First existing file wins; DejaVu ships with matplotlib so it is the safe fallback.
_REGULAR_CANDIDATES = (
    os.path.join(_INTER, "Inter-Regular.otf"),
    os.path.join(_MPLFONTS, "DejaVuSans.ttf"),
)
_BOLD_CANDIDATES = (
    os.path.join(_INTER, "Inter-SemiBold.otf"),
    os.path.join(_INTER, "Inter-Bold.otf"),
    os.path.join(_MPLFONTS, "DejaVuSans-Bold.ttf"),
)


def _first_existing(paths: tuple[str, ...]) -> str | None:
    return next((p for p in paths if os.path.exists(p)), None)


FONT_REGULAR = _first_existing(_REGULAR_CANDIDATES)
FONT_BOLD    = _first_existing(_BOLD_CANDIDATES)


def load_fonts() -> dict[str, pygame.font.Font]:
    """Return a dict of pre-loaded font objects (type scale: tiny < sm < md < lg < xl)."""
    return {
        "tiny":  pygame.font.Font(FONT_REGULAR, 12),
        "cap":   pygame.font.Font(FONT_BOLD,    12),   # small caps-style section labels
        "sm":    pygame.font.Font(FONT_REGULAR, 14),
        "md":    pygame.font.Font(FONT_REGULAR, 16),
        "mdb":   pygame.font.Font(FONT_BOLD,    16),
        "lg":    pygame.font.Font(FONT_BOLD,    26),
        "xl":    pygame.font.Font(FONT_BOLD,    46),
        "title": pygame.font.Font(FONT_BOLD,    60),
    }
