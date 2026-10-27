"""Regresje A3 (P1.1/P1.2): okno kamery wyliczane z levelLength,
drawLevel działa na końcu poziomu (bez cichego zamrożenia encji)."""

import pygame

from classes.Camera import Camera
from classes.Maths import Vec2D


class _FakeEntity:
    """Wystarcza pozycja jako float dla Camera.move."""

    def __init__(self, x):
        self.x = x

    def getPosIndexAsFloat(self):
        return Vec2D(self.x, 0.0)


def test_camera_follows_window_60():
    """Długość 60: zachowane historyczne okno (10..50)."""
    cam = Camera(pygame.Rect(0, 0, 32, 32), _FakeEntity(11.0), levelLength=60)
    cam.move()
    assert cam.pos.x == -1  # -11 + 10


def test_camera_follows_window_90():
    """Długość 90: kamera podąża za Mario za kafel 50 (regresja P1.2)."""
    cam = Camera(pygame.Rect(0, 0, 32, 32), _FakeEntity(70.0), levelLength=90)
    cam.move()
    assert cam.pos.x == -60  # stare hardkodowane okno tu by nie ruszyło


def test_camera_stops_scrolling_before_level_end():
    """Kamera przestaje podążać na kafelku levelLength-10 (okno ~20 kafelków)."""
    cam = Camera(pygame.Rect(0, 0, 32, 32), _FakeEntity(201.5), levelLength=212)
    cam.move()
    assert -192 < cam.pos.x < -191  # okno kończy się przy ~-(levelLength-20)


def test_camera_clamps_at_level_end():
    """pos.x przycinane do [-(levelLength-20), 0] — bezpiecznik."""
    cam = Camera(pygame.Rect(0, 0, 32, 32), _FakeEntity(250.0), levelLength=212)
    cam.pos.x = -195  # sztucznie poza zakresem okna
    cam.move()
    assert cam.pos.x == -192  # -(212 - 20)


def test_drawLevel_past_end_updates_entities(level, screen):
    """P1.1: dla camera.pos.x <= -40 drawLevel nie wyrzuca IndexError
    i nie przerywa przed updateEntities (stary kod cicho wracał)."""
    cam = Camera(pygame.Rect(0, 0, 32, 32), None, levelLength=60)
    cam.pos.x = -45
    calls = []
    original = level.updateEntities
    level.updateEntities = lambda c: (calls.append(c), original(c))[1]
    try:
        level.drawLevel(cam)
    finally:
        level.updateEntities = original
    assert calls == [cam]
