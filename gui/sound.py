"""gui/sound.py — Procedural audio synthesis for Connect Four.

Generates soft, pleasant sound effects dynamically using numpy and pygame.mixer.
No external audio files or dependencies required.
Safely handles environments without audio devices.
"""

from __future__ import annotations

import numpy as np
import pygame


class SoundManager:
    """Manages procedural sound effects with mute toggle and safe fallbacks."""

    def __init__(self) -> None:
        self.enabled = False
        self.muted = False
        self._snd_drop: pygame.mixer.Sound | None = None
        self._snd_hint: pygame.mixer.Sound | None = None
        self._snd_win: pygame.mixer.Sound | None = None
        self._snd_click: pygame.mixer.Sound | None = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._generate_sounds()
            self.enabled = True
        except Exception:
            # Headless or missing audio device — fail silently without crashing
            self.enabled = False

    def _generate_sounds(self) -> None:
        sr = 44100

        # 1. Soft disc drop: warm thud with exponential decay
        t_drop = np.linspace(0, 0.09, int(sr * 0.09), False)
        decay_drop = np.exp(-t_drop * 45)
        freq_drop = 220.0 * np.exp(-t_drop * 15)
        wave_drop = np.sin(2 * np.pi * freq_drop * t_drop) * decay_drop * 24000
        stereo_drop = np.repeat(wave_drop.astype(np.int16)[:, None], 2, axis=1)
        self._snd_drop = pygame.sndarray.make_sound(stereo_drop)
        self._snd_drop.set_volume(0.35)

        # 2. Hint chime: two crystalline bell harmonic frequencies
        dur_hint = 0.16
        t_hint = np.linspace(0, dur_hint, int(sr * dur_hint), False)
        decay_hint = np.exp(-t_hint * 18)
        wave_hint = (
            np.sin(2 * np.pi * 659.25 * t_hint) * 0.6  # E5
            + np.sin(2 * np.pi * 987.77 * t_hint) * 0.4  # B5
        ) * decay_hint * 20000
        stereo_hint = np.repeat(wave_hint.astype(np.int16)[:, None], 2, axis=1)
        self._snd_hint = pygame.sndarray.make_sound(stereo_hint)
        self._snd_hint.set_volume(0.30)

        # 3. Win chime: uplifting major chord arpeggio (C5 -> E5 -> G5 -> C6)
        dur_win = 0.45
        t_win = np.linspace(0, dur_win, int(sr * dur_win), False)
        notes = [523.25, 659.25, 783.99, 1046.50]
        chord = np.zeros_like(t_win)
        for i, f in enumerate(notes):
            t_offset = max(0.0, i * 0.07)
            mask = t_win >= t_offset
            sub_t = t_win[mask] - t_offset
            env = np.exp(-sub_t * 7)
            chord[mask] += np.sin(2 * np.pi * f * sub_t) * env * 0.25
        wave_win = chord * 26000
        stereo_win = np.repeat(wave_win.astype(np.int16)[:, None], 2, axis=1)
        self._snd_win = pygame.sndarray.make_sound(stereo_win)
        self._snd_win.set_volume(0.40)

        # 4. Soft UI click
        t_clk = np.linspace(0, 0.03, int(sr * 0.03), False)
        decay_clk = np.exp(-t_clk * 100)
        wave_clk = np.sin(2 * np.pi * 800 * t_clk) * decay_clk * 14000
        stereo_clk = np.repeat(wave_clk.astype(np.int16)[:, None], 2, axis=1)
        self._snd_click = pygame.sndarray.make_sound(stereo_clk)
        self._snd_click.set_volume(0.20)

    def play_drop(self) -> None:
        if self.enabled and not self.muted and self._snd_drop:
            try:
                self._snd_drop.play()
            except Exception:
                pass

    def play_hint(self) -> None:
        if self.enabled and not self.muted and self._snd_hint:
            try:
                self._snd_hint.play()
            except Exception:
                pass

    def play_win(self) -> None:
        if self.enabled and not self.muted and self._snd_win:
            try:
                self._snd_win.play()
            except Exception:
                pass

    def play_click(self) -> None:
        if self.enabled and not self.muted and self._snd_click:
            try:
                self._snd_click.play()
            except Exception:
                pass

    def toggle_mute(self) -> bool:
        """Toggle mute state and return the new muted status."""
        self.muted = not self.muted
        return self.muted
