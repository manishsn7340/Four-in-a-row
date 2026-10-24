"""gui/screens.py — Start menu, Results screen and Demo helpers.

show_start_menu:
  Title screen with falling discs.  Returns the chosen mode key.

show_results_screen:
  Pages through every PNG in results/ (buttons, ← / → keys or mouse wheel).
  Returns to the game on Esc / Enter / Back.

demo_board:
  Returns a pre-built mid-game board for the Demo button.
"""

from __future__ import annotations

import pathlib
import random

import pygame

from gui import theme as T
from gui.animation import draw_disc
from gui.widgets import Button

_RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"


# ── Start menu ─────────────────────────────────────────────────────────────────

class _FallingDiscs:
    """Slow decorative discs drifting down behind the start menu."""

    def __init__(self, n: int = 16, seed: int = 7) -> None:
        self._rng = random.Random(seed)
        self.discs = [self._spawn(random_y=True) for _ in range(n)]

    def _spawn(self, random_y: bool = False) -> list:
        r = self._rng
        y = r.uniform(-60, T.WIN_H) if random_y else -60.0
        color = T.P1_DISC if r.random() < 0.5 else T.P2_DISC
        return [r.uniform(0, T.WIN_W), y, r.uniform(40, 90), r.randint(18, 36), color]

    def update(self, dt: float) -> None:
        for i, d in enumerate(self.discs):
            d[1] += d[2] * dt
            if d[1] > T.WIN_H + 60:
                self.discs[i] = self._spawn()

    def draw(self, surf: pygame.Surface) -> None:
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for x, y, _, radius, color in self.discs:
            draw_disc(layer, (int(x), int(y)), color, radius)
        layer.set_alpha(70 if T.THEME_NAME == "dark" else 110)
        surf.blit(layer, (0, 0))


def show_start_menu(screen: pygame.Surface, fonts: dict, clock: pygame.time.Clock) -> str:
    """Show the title screen; return ``"hva"``, ``"hvh"``, ``"avai"`` or ``"quit"``."""
    sw, sh = screen.get_size()
    discs = _FallingDiscs()
    bw, bh, gap = 320, 52, 14
    x = (sw - bw) // 2
    y0 = 300
    entries = [("hva", "Play vs computer", "primary"), ("hvh", "Two players", "default"),
               ("avai", "Watch AI vs AI", "default"), ("results", "Experiment results", "default"),
               ("quit", "Quit", "default")]
    buttons = [(key, Button((x, y0 + i * (bh + gap), bw, bh), label=label, variant=variant))
               for i, (key, label, variant) in enumerate(entries)]
    theme_btn = Button((sw - 140, sh - 56, 120, 38), label="")

    while True:
        dt = clock.tick(T.FPS) / 1000.0
        discs.update(dt)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key == pygame.K_l:
                    T.set_theme("light" if T.THEME_NAME == "dark" else "dark")
                keymap = {pygame.K_1: "hva", pygame.K_2: "hvh", pygame.K_3: "avai"}
                if event.key in keymap:
                    return keymap[event.key]
            if theme_btn.clicked(event):
                T.set_theme("light" if T.THEME_NAME == "dark" else "dark")
            for key, btn in buttons:
                if btn.clicked(event):
                    if key == "results":
                        show_results_screen(screen, fonts, clock)
                    else:
                        return key

        screen.fill(T.BG)
        discs.draw(screen)
        title = fonts["title"].render("Connect Four Lab", True, T.TEXT)
        screen.blit(title, title.get_rect(center=(sw // 2, 150)))
        tag = fonts["md"].render("A strategy coach that shows how the AI thinks",
                                 True, T.DIM_TEXT)
        screen.blit(tag, tag.get_rect(center=(sw // 2, 205)))
        for _, btn in buttons:
            btn.draw(screen, fonts)
        theme_btn.label = "Light mode" if T.THEME_NAME == "dark" else "Dark mode"
        theme_btn.draw(screen, fonts)
        hint = fonts["sm"].render("Keys: 1 · 2 · 3 to start  ·  L toggles theme  ·  Esc quits",
                                  True, T.DIM_TEXT)
        screen.blit(hint, hint.get_rect(center=(sw // 2, sh - 38)))
        pygame.display.flip()


# ── Results screen ─────────────────────────────────────────────────────────────

def _load_result_images(screen_w: int, screen_h: int) -> list[tuple[str, pygame.Surface]]:
    """Load all PNGs from results/ as (caption, surface), scaled to fit the card."""
    images: list[tuple[str, pygame.Surface]] = []
    if not _RESULTS_DIR.exists():
        return images
    for path in sorted(_RESULTS_DIR.glob("*.png")):
        try:
            img = pygame.image.load(str(path)).convert()
            iw, ih = img.get_size()
            scale = min((screen_w - 160) / iw, (screen_h - 230) / ih, 1.0)
            img = pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))
            images.append((path.stem.replace("_", " ").capitalize(), img))
        except pygame.error:
            pass
    return images


def show_results_screen(screen: pygame.Surface, fonts: dict, clock: pygame.time.Clock) -> None:
    """Block until the user leaves the Results screen.  Call from the main loop."""
    sw, sh = screen.get_size()
    images = _load_result_images(sw, sh)
    idx = 0
    back_btn = Button((sw - 130, 20, 100, 38), label="Back")
    prev_btn = Button((sw // 2 - 170, sh - 62, 90, 40), label="Prev")
    next_btn = Button((sw // 2 + 80, sh - 62, 90, 40), label="Next")

    while True:
        step = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    return
                elif event.key == pygame.K_RIGHT:
                    step = 1
                elif event.key == pygame.K_LEFT:
                    step = -1
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4 or prev_btn.clicked(event):
                    step = -1
                elif event.button == 5 or next_btn.clicked(event):
                    step = 1
                elif back_btn.clicked(event):
                    return
        if images and step:
            idx = (idx + step) % len(images)

        screen.fill(T.BG)
        screen.blit(fonts["lg"].render("Experiment results", True, T.TEXT), (40, 18))

        if images:
            caption, img = images[idx]
            screen.blit(fonts["sm"].render(caption, True, T.DIM_TEXT), (40, 56))
            card = pygame.Rect(0, 0, img.get_width() + 32, img.get_height() + 32)
            card.midtop = (sw // 2, 84)
            pygame.draw.rect(screen, (255, 255, 255), card, border_radius=14)
            pygame.draw.rect(screen, T.BORDER, card, width=1, border_radius=14)
            screen.blit(img, (card.left + 16, card.top + 16))
            prev_btn.draw(screen, fonts)
            next_btn.draw(screen, fonts)
            counter = fonts["md"].render(f"{idx + 1} / {len(images)}", True, T.DIM_TEXT)
            screen.blit(counter, counter.get_rect(center=(sw // 2, sh - 42)))
        else:
            lines = ["No result images yet.", "",
                     "Run  python -m experiments.run_all  to generate graphs,",
                     "then reopen this screen."]
            y = sh // 2 - 60
            for line in lines:
                lbl = fonts["md"].render(line, True, T.DIM_TEXT)
                screen.blit(lbl, lbl.get_rect(centerx=sw // 2, top=y))
                y += 32

        back_btn.draw(screen, fonts)
        pygame.display.flip()
        clock.tick(T.FPS)


# ── Demo setup ─────────────────────────────────────────────────────────────────

# A carefully chosen mid-game sequence that looks interesting on a projector:
# P1 plays center bias; P2 plays spread; position is balanced and tactical.
_DEMO_MOVES = [3, 3, 2, 4, 3, 2, 4, 2, 1, 5]


def demo_board(seed: int | None = None):
    """Return a mid-game Board for the demo.

    With ``seed=None`` the fixed opening in ``_DEMO_MOVES`` is used.  With a seed,
    6-8 centre-biased random moves are played from ``random.Random(seed)``, so a
    given seed always reproduces the same opening.  No move ends the game.
    """
    from game.board import Board  # avoid circular at module level
    b = Board()
    if seed is None:
        for col in _DEMO_MOVES:
            if not b.is_terminal():
                b.drop(col)
        return b

    rng = random.Random(seed)
    weights = {3: 4, 2: 3, 4: 3, 1: 2, 5: 2, 0: 1, 6: 1}
    for _ in range(rng.randint(6, 8)):
        options = b.legal_moves()
        rng.shuffle(options)
        # Weighted order: try columns by a random draw biased towards the centre
        options.sort(key=lambda c: rng.random() ** (1.0 / weights.get(c, 1)), reverse=True)
        for col in options:
            b.drop(col)
            if b.is_terminal():
                b.undo()
                continue
            break
    return b
