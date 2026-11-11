"""Button, Dropdown and Slider widgets."""

from __future__ import annotations

import pygame

import gui.theme as T
from gui.icons import (make_bulb_icon, make_chart_icon, make_demo_icon,
                       make_puzzle_icon, make_sound_icon)

ICONS = {"bulb": make_bulb_icon, "demo": make_demo_icon, "chart": make_chart_icon,
         "puzzle": make_puzzle_icon}


def is_left_click(event: pygame.event.Event) -> bool:
    return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1


class Button:
    """`variant` is "default", "primary" (filled call to action) or "segment"
    (one of a group; pass active=True to draw() for the selected one)."""

    def __init__(self, rect: tuple, label: str = "", icon_type: str | None = None,
                 variant: str = "default") -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.icon_type = icon_type
        self.variant = variant
        self.muted = False  # only used by the sound button

    def clicked(self, event: pygame.event.Event) -> bool:
        return is_left_click(event) and self.rect.collidepoint(event.pos)

    def draw(self, surf: pygame.Surface, fonts: dict, active: bool = False) -> None:
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        if self.variant == "primary":
            fill = tuple(min(255, c + 28) for c in T.WIN_GLOW) if hover else T.WIN_GLOW
            text_color, edge, width = T.BG, fill, 1
        elif active:
            fill, text_color, edge, width = T.SURFACE_HI, T.TEXT, T.WIN_GLOW, 2
        else:
            fill, text_color, edge, width = (T.BTN_HOVER if hover else T.BTN_NORMAL), T.TEXT, T.BORDER, 1
        pygame.draw.rect(surf, fill, self.rect, border_radius=10)
        pygame.draw.rect(surf, edge, self.rect, width=width, border_radius=10)

        if self.icon_type == "sound":
            icon = make_sound_icon((235, 110, 100) if self.muted else text_color, 20, self.muted)
            surf.blit(icon, icon.get_rect(center=self.rect.center))
            return
        icon = ICONS[self.icon_type](text_color, 16) if self.icon_type else None
        icon_w = icon.get_width() + 8 if icon else 0
        font = fonts["md"] if fonts["md"].size(self.label)[0] + icon_w <= self.rect.width - 12 else fonts["sm"]
        label = font.render(self.label, True, text_color)
        x = self.rect.centerx - (icon_w + label.get_width()) // 2
        if icon:
            surf.blit(icon, icon.get_rect(midleft=(x, self.rect.centery)))
        surf.blit(label, label.get_rect(midleft=(x + icon_w, self.rect.centery)))


class Dropdown:
    ITEM_H = 34

    def __init__(self, rect: tuple, options: list[str], initial: int = 0) -> None:
        self.rect = pygame.Rect(rect)
        self.options = options
        self.selected = initial
        self.open = False

    @property
    def value(self) -> str:
        return self.options[self.selected]

    def _item_rects(self) -> list[pygame.Rect]:
        return [pygame.Rect(self.rect.left, self.rect.bottom + i * self.ITEM_H, self.rect.width, self.ITEM_H)
                for i in range(len(self.options))]

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Open/close on click; return True when a different option was picked."""
        if not is_left_click(event):
            return False
        if self.rect.collidepoint(event.pos):
            self.open = not self.open
            return False
        if self.open:
            self.open = False
            for i, rect in enumerate(self._item_rects()):
                if rect.collidepoint(event.pos):
                    changed, self.selected = i != self.selected, i
                    return changed
        return False

    def draw(self, surf: pygame.Surface, fonts: dict) -> None:
        mouse = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse) or self.open
        pygame.draw.rect(surf, T.BTN_HOVER if hover else T.BTN_NORMAL, self.rect, border_radius=10)
        pygame.draw.rect(surf, T.WIN_GLOW if self.open else T.BORDER, self.rect, width=1, border_radius=10)
        label = fonts["md"].render(self.value, True, T.TEXT)
        surf.blit(label, label.get_rect(midleft=(self.rect.left + 14, self.rect.centery)))
        cx, cy, d = self.rect.right - 20, self.rect.centery, -3 if self.open else 3
        pygame.draw.polygon(surf, T.DIM_TEXT, [(cx - 5, cy - d), (cx + 5, cy - d), (cx, cy + d)])

        if self.open:
            items = self._item_rects()
            menu = items[0].unionall(items).inflate(8, 8)
            pygame.draw.rect(surf, T.SURFACE, menu, border_radius=12)
            pygame.draw.rect(surf, T.BORDER, menu, width=1, border_radius=12)
            for i, rect in enumerate(items):
                if rect.collidepoint(mouse):
                    pygame.draw.rect(surf, T.SURFACE_HI, rect, border_radius=8)
                text = fonts["md"].render(self.options[i], True, T.WIN_GLOW if i == self.selected else T.TEXT)
                surf.blit(text, text.get_rect(midleft=(rect.left + 14, rect.centery)))


class Slider:
    def __init__(self, rect: tuple, min_val: float, max_val: float, initial: float, label: str = "") -> None:
        self.rect = pygame.Rect(rect)
        self.min_val, self.max_val = min_val, max_val
        self.value = initial
        self.label = label
        self.dragging = False

    def _set_from_x(self, x: int) -> None:
        frac = max(0.0, min(1.0, (x - self.rect.left) / self.rect.width))
        self.value = self.min_val + frac * (self.max_val - self.min_val)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True when the value changed."""
        if is_left_click(event) and self.rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if self.dragging and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            self._set_from_x(event.pos[0])
            return True
        return False

    def draw(self, surf: pygame.Surface, fonts: dict) -> None:
        frac = (self.value - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.left + int(frac * self.rect.width)
        pygame.draw.rect(surf, T.BG, self.rect, border_radius=4)
        pygame.draw.rect(surf, T.WIN_GLOW, (self.rect.left, self.rect.top, handle_x - self.rect.left,
                                            self.rect.height), border_radius=4)
        pygame.draw.circle(surf, T.TEXT, (handle_x, self.rect.centery), 7)
        pygame.draw.circle(surf, T.BORDER, (handle_x, self.rect.centery), 7, width=1)
        if self.label:
            text = fonts["sm"].render(f"{self.label}: {self.value:.1f}s", True, T.DIM_TEXT)
            surf.blit(text, (self.rect.left, self.rect.top - 16))
