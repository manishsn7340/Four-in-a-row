"""Reusable UI widgets for the Connect Four GUI."""

from __future__ import annotations

import pygame
import gui.theme as T
from gui.icons import (
    make_bulb_icon,
    make_chart_icon,
    make_demo_icon,
    make_export_icon,
    make_human_icon,
    make_puzzle_icon,
    make_robot_icon,
    make_sound_icon,
)

P1_COLOR = T.P1_DISC
P2_COLOR = T.P2_DISC


class Dropdown:
    """A clickable button that reveals a vertical list of selectable options."""

    ITEM_H = 34

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        options: list[str],
        initial: int = 0,
    ) -> None:
        self.rect     = pygame.Rect(rect)
        self.options  = options
        self.selected = initial
        self.open     = False

    @property
    def value(self) -> str:
        return self.options[self.selected]

    def set_value(self, option: str) -> None:
        """Select ``option`` programmatically (ignored if it is not in the list)."""
        if option in self.options:
            self.selected = self.options.index(option)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process a pygame event; return True if selection changed."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        pos = event.pos

        if self.rect.collidepoint(pos):
            self.open = not self.open
            return False

        if self.open:
            for i, opt_rect in enumerate(self._option_rects()):
                if opt_rect.collidepoint(pos):
                    changed       = i != self.selected
                    self.selected = i
                    self.open     = False
                    return changed
            # click outside — close
            self.open = False
        return False

    def draw(self, surf: pygame.Surface, fonts: dict) -> None:
        """Draw the closed field and, if open, the option list below it."""
        mouse = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse)
        pygame.draw.rect(surf, T.BTN_HOVER if (hover or self.open) else T.BTN_NORMAL,
                         self.rect, border_radius=10)
        pygame.draw.rect(surf, T.WIN_GLOW if self.open else T.BORDER, self.rect, width=1,
                         border_radius=10)
        label = fonts["md"].render(self.value, True, T.BTN_TEXT)
        surf.blit(label, label.get_rect(midleft=(self.rect.left + 14, self.rect.centery)))
        cx, cy = self.rect.right - 20, self.rect.centery
        pts = [(cx - 5, cy + 3), (cx + 5, cy + 3), (cx, cy - 3)] if self.open \
            else [(cx - 5, cy - 3), (cx + 5, cy - 3), (cx, cy + 3)]
        pygame.draw.polygon(surf, T.DIM_TEXT, pts)

        if self.open:
            rects = self._option_rects()
            menu = rects[0].unionall(rects).inflate(8, 8)
            pygame.draw.rect(surf, T.SURFACE, menu, border_radius=12)
            pygame.draw.rect(surf, T.BORDER, menu, width=1, border_radius=12)
            for i, opt_rect in enumerate(rects):
                if opt_rect.collidepoint(mouse):
                    pygame.draw.rect(surf, T.SURFACE_HI, opt_rect, border_radius=8)
                color = T.WIN_GLOW if i == self.selected else T.TEXT
                txt = fonts["md"].render(self.options[i], True, color)
                surf.blit(txt, txt.get_rect(midleft=(opt_rect.left + 14, opt_rect.centery)))

    def _option_rects(self) -> list[pygame.Rect]:
        """Compute the rect for each dropdown item (drawn below the button)."""
        return [
            pygame.Rect(self.rect.left, self.rect.bottom + i * self.ITEM_H,
                        self.rect.width, self.ITEM_H)
            for i in range(len(self.options))
        ]


class Slider:
    """Horizontal slider widget for speed/value selection."""

    def __init__(self, rect: tuple, min_val: float, max_val: float, initial: float, label: str = ""):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.dragging = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        return False

    def _set_from_x(self, x: int) -> None:
        rel = max(0.0, min(1.0, (x - self.rect.left) / self.rect.width))
        self.value = self.min_val + rel * (self.max_val - self.min_val)

    _update_val = _set_from_x

    def draw(self, surf: pygame.Surface, fonts: dict) -> None:
        pygame.draw.rect(surf, T.BG, self.rect, border_radius=4)
        pct = (self.value - self.min_val) / (self.max_val - self.min_val) if self.max_val > self.min_val else 0.0
        fill_w = int(pct * self.rect.width)
        if fill_w > 0:
            pygame.draw.rect(surf, T.WIN_GLOW, (self.rect.left, self.rect.top, fill_w, self.rect.height), border_radius=4)
        handle_x = self.rect.left + fill_w
        pygame.draw.circle(surf, T.TEXT, (handle_x, self.rect.centery), 7)
        pygame.draw.circle(surf, T.BORDER, (handle_x, self.rect.centery), 7, width=1)
        if self.label:
            val_txt = f"{self.label}: {self.value:.1f}s"
            txt = fonts["sm"].render(val_txt, True, T.DIM_TEXT)
            surf.blit(txt, (self.rect.left, self.rect.top - 16))


class Button:
    """Flat button with an optional procedural icon.

    ``variant`` is ``"default"``, ``"primary"`` (filled call-to-action) or
    ``"segment"`` (one of a mutually exclusive group; ``active`` marks the choice).
    """

    _ICONS = {
        "bulb": make_bulb_icon, "demo": make_demo_icon, "chart": make_chart_icon,
        "export": make_export_icon, "puzzle": make_puzzle_icon,
    }

    def __init__(
        self,
        rect: tuple,
        label: str = "",
        icon_type: str | None = None,
        accent: tuple | None = None,
        variant: str = "default",
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.icon_type = icon_type
        self.accent = accent
        self.variant = variant
        self.muted = False

    def draw(self, surf: pygame.Surface, fonts: dict, active: bool = False) -> None:
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        primary = self.variant == "primary"
        if primary:
            fill = tuple(min(255, c + 28) for c in T.WIN_GLOW) if hover else T.WIN_GLOW
            txt_col, edge = T.BG, fill
        elif active:
            fill, txt_col, edge = T.SURFACE_HI, T.TEXT, T.WIN_GLOW
        else:
            fill = T.BTN_HOVER if hover else T.BTN_NORMAL
            txt_col, edge = T.BTN_TEXT, T.BORDER

        pygame.draw.rect(surf, fill, self.rect, border_radius=10)
        pygame.draw.rect(surf, edge, self.rect, width=2 if active and not primary else 1,
                         border_radius=10)

        if self.icon_type == "sound":
            icon = make_sound_icon((235, 110, 100) if self.muted else txt_col, 20, muted=self.muted)
            surf.blit(icon, icon.get_rect(center=self.rect.center))
            return

        icon = None
        if self.icon_type in self._ICONS:
            icon = self._ICONS[self.icon_type](txt_col, 16)
        font = fonts["md"]
        if font.size(self.label)[0] + (24 if icon else 0) > self.rect.width - 12:
            font = fonts["sm"]
        lbl = font.render(self.label, True, txt_col)
        gap = 8 if icon else 0
        total = (icon.get_width() + gap if icon else 0) + lbl.get_width()
        x = self.rect.centerx - total // 2
        if icon:
            surf.blit(icon, (x, self.rect.centery - icon.get_height() // 2))
            x += icon.get_width() + gap
        surf.blit(lbl, (x, self.rect.centery - lbl.get_height() // 2))

    def clicked(self, event: pygame.event.Event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))
