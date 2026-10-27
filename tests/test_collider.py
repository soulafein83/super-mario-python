"""Regresja A4 (P1.3): determineSide po krawędziach i głębokości
pionowego przeniknięcia, bez dzielenia współrzędnych."""

import pygame

from classes.EntityCollider import EntityCollider


class _DummyEntity:
    def __init__(self, rect):
        self.rect = rect


def _state(entity_rect, target_rect):
    s = EntityCollider(
        _DummyEntity(entity_rect)
    ).determineSide(target_rect, entity_rect)
    return (s.isColliding, s.isTop)


TARGET = pygame.Rect(0, 0, 32, 32)


def test_no_overlap_is_not_collision():
    collider = EntityCollider(_DummyEntity(pygame.Rect(40, 0, 32, 32)))
    s = collider.check(_DummyEntity(TARGET))
    assert (s.isColliding, s.isTop) == (False, False)


def test_stomp_shallow_from_above():
    """Mały Mario: dolna krawędź weszła w cel o 4 px -> stomp."""
    assert _state(pygame.Rect(0, -28, 32, 32), TARGET) == (True, True)


def test_big_mario_stomp_shallow():
    """Duży Mario (64 px) spadający na cel -> stomp."""
    assert _state(pygame.Rect(0, -60, 32, 64), TARGET) == (True, True)


def test_side_midheight():
    """Kolizja w połowie wysokości celu -> bok, nie stomp."""
    assert _state(pygame.Rect(0, 8, 32, 32), TARGET) == (True, False)


def test_same_ground_same_height_is_side():
    """Dwie encje 32 px na tej samej linii podłogi -> uderzenie w bok."""
    assert _state(pygame.Rect(0, 0, 32, 32), TARGET) == (True, False)


def test_big_mario_same_ground_is_side():
    """Duży Mario wchodzący w mob z boku (dno na dnie celu) -> nie stomp."""
    assert _state(pygame.Rect(0, -32, 32, 64), TARGET) == (True, False)


def test_head_bump_from_below():
    """Encja pod celem, uderzenie głową od dołu -> nie stomp."""
    assert _state(pygame.Rect(0, 28, 32, 32), TARGET) == (True, False)
