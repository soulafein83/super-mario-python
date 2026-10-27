"""A5 (P1.4): konwencja (kolumna, wiersz) w JSON i bez offsetów w
konstruktorach. Pozycje spawne zmierzone na kodzie legacy przed zmianą
konwencji (plan.md, P1.4) — muszą być identyczne po ujednoliceniu.

Swiezny Level na module (nie wspólna fixtura sesji): testy kamery
uruchamiaja updateEntities i przemieszczaja moby o 1-2 px.
"""

import pytest

import pygame

from classes.Camera import Camera


@pytest.fixture(scope="module")
def fresh_level(screen, sound, dashboard, base_dir):
    from classes.Level import Level

    lv = Level(screen, sound, dashboard, base_dir)
    lv.loadLevel("Level1-1")
    return lv


def _spawns(level, name):
    return {(e.rect.x, e.rect.y) for e in level.entityList
            if e.__class__.__name__ == name}


def test_goomba_spawns(fresh_level):
    """JSON [kolumna, wiersz]: [15,11], [12,11], [8,9] (legacy [12,15] itd.)."""
    assert _spawns(fresh_level, "Goomba") == {(15 * 32, 11 * 32),
                                              (12 * 32, 11 * 32),
                                              (8 * 32, 9 * 32)}


def test_koopa_spawns(fresh_level):
    """JSON [kolumna, wiersz]: [24,12], [21,12], [32,12], [39,12]."""
    assert _spawns(fresh_level, "Koopa") == {(24 * 32, 12 * 32),
                                             (21 * 32, 12 * 32),
                                             (32 * 32, 12 * 32),
                                             (39 * 32, 12 * 32)}


def test_random_box_mushroom_spawn(screen, sound, dashboard, base_dir):
    """Skrzynka (4,3) -> grzyb w kolumnie 4, wierszu 1 (2 wiersze wyżej).

    Nowy Level (nie wspólna fixtura), bo wywołanie box.update() modyfikuje
    entityList, a test_smoke liczy encje.
    """
    from classes.Level import Level

    lv = Level(screen, sound, dashboard, base_dir)
    lv.loadLevel("Level1-1")
    box = next(e for e in lv.entityList
               if e.__class__.__name__ == "RandomBox"
               and (e.rect.x, e.rect.y) == (4 * 32, 3 * 32))
    box.triggered = True
    n_before = len(lv.entityList)
    box.update(Camera(pygame.Rect(0, 0, 32, 32), None, lv.levelLength))
    assert len(lv.entityList) == n_before + 1
    mushroom = lv.entityList[n_before]
    assert mushroom.__class__.__name__ == "RedMushroom"
    assert (mushroom.rect.x, mushroom.rect.y) == (4 * 32, 1 * 32)
