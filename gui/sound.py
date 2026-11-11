"""Sound effects synthesised with numpy, so the project needs no audio files."""

from __future__ import annotations

import numpy as np
import pygame

RATE = 44100


def _tone(duration: float, wave) -> pygame.mixer.Sound:
    """Turn wave(t) (values roughly in [-1, 1]) into a stereo pygame Sound."""
    t = np.linspace(0, duration, int(RATE * duration), False)
    samples = (wave(t) * 24000).astype(np.int16)
    return pygame.sndarray.make_sound(np.repeat(samples[:, None], 2, axis=1))


def _arpeggio(t: np.ndarray) -> np.ndarray:
    """C major chord with each note starting 70 ms after the previous one."""
    out = np.zeros_like(t)
    for i, freq in enumerate((523.25, 659.25, 783.99, 1046.50)):
        s = np.clip(t - i * 0.07, 0, None)
        out += np.where(t >= i * 0.07, np.sin(2 * np.pi * freq * s) * np.exp(-s * 7), 0) * 0.27
    return out


class SoundManager:
    def __init__(self) -> None:
        self.muted = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=RATE, size=-16, channels=2, buffer=512)
            self.sounds = {
                # a low thud whose pitch falls quickly
                "drop": (_tone(0.09, lambda t: np.sin(2 * np.pi * 220 * np.exp(-15 * t) * t) * np.exp(-45 * t)), 0.35),
                "hint": (_tone(0.16, lambda t: (0.6 * np.sin(2 * np.pi * 659.25 * t)
                                               + 0.4 * np.sin(2 * np.pi * 987.77 * t)) * np.exp(-18 * t) * 0.8), 0.30),
                "win": (_tone(0.45, _arpeggio), 0.40),
                "click": (_tone(0.03, lambda t: np.sin(2 * np.pi * 800 * t) * np.exp(-100 * t) * 0.6), 0.20),
            }
            for sound, volume in self.sounds.values():
                sound.set_volume(volume)
        except pygame.error:
            self.sounds = {}  # no audio device (e.g. headless): play silently

    def _play(self, name: str) -> None:
        if name in self.sounds and not self.muted:
            self.sounds[name][0].play()

    def play_drop(self) -> None:
        self._play("drop")

    def play_hint(self) -> None:
        self._play("hint")

    def play_win(self) -> None:
        self._play("win")

    def play_click(self) -> None:
        self._play("click")

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        return self.muted
