"""Window size, board geometry, colours and fonts for the GUI."""

from __future__ import annotations

import os

import matplotlib
import pygame

WIN_W, WIN_H, FPS = 1280, 800, 60

BOARD_ROWS, BOARD_COLS = 6, 7
CELL_SIZE = 84
DISC_RADIUS = 34
BOARD_LEFT, BOARD_TOP = 36, 135  # top-left corner of the grid

# Disc colours are the same in both themes.
P1_DISC = (232, 86, 76)   # coral
P2_DISC = (244, 192, 62)  # gold

THEMES = {
    "dark": dict(
        BG=(26, 28, 35), SURFACE=(36, 39, 48), SURFACE_HI=(46, 50, 62), BORDER=(62, 67, 82),
        BOARD_BG=(36, 84, 168), BOARD_FRAME=(24, 58, 124), WIN_GLOW=(96, 214, 178),
        TEXT=(234, 236, 242), DIM_TEXT=(148, 154, 172),
        BTN_NORMAL=(46, 50, 62), BTN_HOVER=(64, 70, 88), SHADOW_ALPHA=70,
    ),
    "light": dict(
        BG=(248, 250, 252), SURFACE=(255, 255, 255), SURFACE_HI=(241, 245, 249), BORDER=(226, 232, 240),
        BOARD_BG=(44, 98, 188), BOARD_FRAME=(30, 70, 146), WIN_GLOW=(24, 150, 120),
        TEXT=(34, 37, 46), DIM_TEXT=(108, 112, 126),
        BTN_NORMAL=(241, 245, 249), BTN_HOVER=(226, 232, 240), SHADOW_ALPHA=40,
    ),
}
THEME_NAME = "dark"


def set_theme(name: str) -> None:
    """Swap the module-level colour constants to another palette.

    Other modules read colours as `T.BG` etc. at draw time, so the change shows
    up on the next frame."""
    global THEME_NAME
    globals().update(THEMES[name])
    THEME_NAME = name


def toggle_theme() -> None:
    set_theme("light" if THEME_NAME == "dark" else "dark")


set_theme("dark")

# Inter if it is installed, otherwise DejaVu, which ships with matplotlib.
_MPL_FONTS = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
_INTER = "/usr/share/fonts/opentype/inter"


def _font_file(inter: str, dejavu: str) -> str | None:
    for path in (os.path.join(_INTER, inter), os.path.join(_MPL_FONTS, dejavu)):
        if os.path.exists(path):
            return path
    return None  # pygame's default font


def load_fonts() -> dict[str, pygame.font.Font]:
    regular = _font_file("Inter-Regular.otf", "DejaVuSans.ttf")
    bold = _font_file("Inter-SemiBold.otf", "DejaVuSans-Bold.ttf")
    sizes = {"cap": (bold, 12), "sm": (regular, 14), "md": (regular, 16), "mdb": (bold, 16),
             "lg": (bold, 26), "xl": (bold, 46), "title": (bold, 60)}
    return {key: pygame.font.Font(path, size) for key, (path, size) in sizes.items()}
