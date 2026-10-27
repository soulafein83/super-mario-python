"""Smoke test baseline — poziom 1-1 ładuje się i działa bez wyjątków.

Utworzony z /tmp/opencode/smoke_test.py (faza A, baseline przed fazą B).
"""

import pygame

from classes.Camera import Camera


def test_level_loads(level):
    assert level.levelLength == 60
    assert len(level.entityList) == 37


def test_grid_shape(level):
    assert len(level.level) == 15
    assert all(len(row) == 60 for row in level.level)


def test_frames_run(level, screen):
    """120 klatek symulacji + renderu bez wyjątków."""
    cam = Camera(pygame.Rect(0, 0, 32, 29), None)
    for _ in range(120):
        level.updateEntities(cam)
        level.drawLevel(cam)
    pygame.display.update()


def test_mario_full_loop(level, screen, dashboard, sound, base_dir):
    """Mario spada, rusza kamerę i nie ginie w 30 klatkach."""
    from entities.Mario import Mario

    mario = Mario(0, 0, level, screen, dashboard, sound, base_dir=base_dir)
    for _ in range(30):
        level.drawLevel(mario.camera)
        dashboard.update()
        mario.update()
    assert mario.alive
    assert mario.rect.y > 0


def test_camera_from_foreign_cwd(level, tmp_path, monkeypatch):
    """Kamera i render nie zależą od CWD (regresja A2)."""
    monkeypatch.chdir(tmp_path)
    cam = Camera(pygame.Rect(0, 0, 32, 29), None)
    for _ in range(10):
        level.updateEntities(cam)
        level.drawLevel(cam)
