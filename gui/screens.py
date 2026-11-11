"""Full-screen pages: the start menu and the experiment-results viewer. Also the demo opening."""

from __future__ import annotations

import pathlib
import random

import pygame

import gui.theme as T
from game.board import Board
from gui.board_view import draw_disc
from gui.widgets import Button

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"
DEMO_MOVES = [3, 3, 2, 4, 3, 2, 4, 2, 1, 5]  # fixed opening used when no seed is given


def _quit() -> None:
    pygame.quit()
    raise SystemExit


def show_start_menu(screen: pygame.Surface, fonts: dict, clock: pygame.time.Clock) -> str:
    """Title screen with slowly falling discs. Returns "hva", "hvh", "avai" or "quit"."""
    rng = random.Random(7)

    def new_disc(y: float = -60.0) -> list:  # [x, y, speed, radius, color]
        return [rng.uniform(0, T.WIN_W), y, rng.uniform(40, 90), rng.randint(18, 36),
                T.P1_DISC if rng.random() < 0.5 else T.P2_DISC]

    discs = [new_disc(rng.uniform(-60, T.WIN_H)) for _ in range(16)]
    entries = [("hva", "Play vs computer"), ("hvh", "Two players"), ("avai", "Watch AI vs AI"),
               ("results", "Experiment results"), ("quit", "Quit")]
    buttons = {key: Button((T.WIN_W // 2 - 160, 300 + i * 66, 320, 52), label,
                           variant="primary" if i == 0 else "default")
               for i, (key, label) in enumerate(entries)}
    theme_btn = Button((T.WIN_W - 140, T.WIN_H - 56, 120, 38))
    keys = {pygame.K_1: "hva", pygame.K_2: "hvh", pygame.K_3: "avai", pygame.K_ESCAPE: "quit"}

    while True:
        dt = clock.tick(T.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key in keys:
                return keys[event.key]
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_l) or theme_btn.clicked(event):
                T.toggle_theme()
            for key, button in buttons.items():
                if button.clicked(event):
                    if key != "results":
                        return key
                    show_results_screen(screen, fonts, clock)

        screen.fill(T.BG)
        layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for i, d in enumerate(discs):
            d[1] += d[2] * dt
            if d[1] > T.WIN_H + 60:
                discs[i] = d = new_disc()
            draw_disc(layer, (int(d[0]), int(d[1])), d[4], d[3])
        layer.set_alpha(70 if T.THEME_NAME == "dark" else 110)
        screen.blit(layer, (0, 0))

        title = fonts["title"].render("Connect Four Lab", True, T.TEXT)
        screen.blit(title, title.get_rect(center=(T.WIN_W // 2, 150)))
        tag = fonts["md"].render("A strategy coach that shows how the AI thinks", True, T.DIM_TEXT)
        screen.blit(tag, tag.get_rect(center=(T.WIN_W // 2, 205)))
        for button in buttons.values():
            button.draw(screen, fonts)
        theme_btn.label = "Light mode" if T.THEME_NAME == "dark" else "Dark mode"
        theme_btn.draw(screen, fonts)
        hint = fonts["sm"].render("Keys: 1 · 2 · 3 to start  ·  L toggles theme  ·  Esc quits", True, T.DIM_TEXT)
        screen.blit(hint, hint.get_rect(center=(T.WIN_W // 2, T.WIN_H - 38)))
        pygame.display.flip()


def show_results_screen(screen: pygame.Surface, fonts: dict, clock: pygame.time.Clock) -> None:
    """Page through the PNG charts in results/ until the player goes back."""
    images = []
    for path in sorted(RESULTS_DIR.glob("*.png")):
        image = pygame.image.load(str(path)).convert()
        scale = min((T.WIN_W - 160) / image.get_width(), (T.WIN_H - 230) / image.get_height(), 1.0)
        size = (int(image.get_width() * scale), int(image.get_height() * scale))
        images.append((path.stem.replace("_", " ").capitalize(), pygame.transform.smoothscale(image, size)))
    back = Button((T.WIN_W - 130, 20, 100, 38), "Back")
    prev = Button((T.WIN_W // 2 - 170, T.WIN_H - 62, 90, 40), "Prev")
    nxt = Button((T.WIN_W // 2 + 80, T.WIN_H - 62, 90, 40), "Next")
    index = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _quit()
            key = event.key if event.type == pygame.KEYDOWN else None
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE) or back.clicked(event):
                return
            if images and (key == pygame.K_LEFT or prev.clicked(event) or getattr(event, "button", 0) == 4):
                index = (index - 1) % len(images)
            if images and (key == pygame.K_RIGHT or nxt.clicked(event) or getattr(event, "button", 0) == 5):
                index = (index + 1) % len(images)

        screen.fill(T.BG)
        screen.blit(fonts["lg"].render("Experiment results", True, T.TEXT), (40, 18))
        if images:
            caption, image = images[index]
            screen.blit(fonts["sm"].render(caption, True, T.DIM_TEXT), (40, 56))
            card = image.get_rect().inflate(32, 32)
            card.midtop = (T.WIN_W // 2, 84)
            pygame.draw.rect(screen, (255, 255, 255), card, border_radius=14)  # charts have white backgrounds
            pygame.draw.rect(screen, T.BORDER, card, width=1, border_radius=14)
            screen.blit(image, image.get_rect(center=card.center))
            prev.draw(screen, fonts)
            nxt.draw(screen, fonts)
            counter = fonts["md"].render(f"{index + 1} / {len(images)}", True, T.DIM_TEXT)
            screen.blit(counter, counter.get_rect(center=(T.WIN_W // 2, T.WIN_H - 42)))
        else:
            for i, line in enumerate(["No result images yet.", "",
                                      "Run  python -m experiments.run_all  to generate graphs,",
                                      "then reopen this screen."]):
                text = fonts["md"].render(line, True, T.DIM_TEXT)
                screen.blit(text, text.get_rect(centerx=T.WIN_W // 2, top=T.WIN_H // 2 - 60 + i * 32))
        back.draw(screen, fonts)
        pygame.display.flip()
        clock.tick(T.FPS)


def demo_board(seed: int | None = None) -> Board:
    """A mid-game position for the Demo button.

    Without a seed this is the fixed DEMO_MOVES opening. With a seed, 6-8 random
    centre-leaning moves are played from random.Random(seed), so each seed always
    gives the same opening. No move is allowed to end the game."""
    board = Board()
    if seed is None:
        for col in DEMO_MOVES:
            board.drop(col)
        return board
    rng = random.Random(seed)
    weight = {3: 4, 2: 3, 4: 3, 1: 2, 5: 2, 0: 1, 6: 1}
    for _ in range(rng.randint(6, 8)):
        options = board.legal_moves()
        rng.shuffle(options)
        options.sort(key=lambda c: rng.random() ** (1.0 / weight[c]), reverse=True)
        for col in options:
            board.drop(col)
            if not board.is_terminal():
                break
            board.undo()
    return board
