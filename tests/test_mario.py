"""Regresja: powerup i sciezka obrazen (kurczenie) duzego Mario nie moga
wyrzucic NameError (legacy: `bigAnimation`/`smallAnimation` byly lokalnymi
zmiennymi __init__, niedostepne z powerup() i _onCollisionWithMob)."""

import pygame

from classes.EntityCollider import CollisionState


def test_powerup_makes_mario_big(level, screen, dashboard, sound, base_dir):
    from entities.Mario import Mario

    mario = Mario(0, 0, level, screen, dashboard, sound, base_dir=base_dir)
    mario.powerup(1)
    assert mario.powerUpState == 1
    assert mario.rect.size == (32, 64)
    assert mario.invincibilityFrames == 20


def test_big_mario_side_hit_shrinks(level, screen, dashboard, sound, base_dir):
    """Duzy Mario trafiajacy w moba z boku (isTop=False) kurczy sie zamiast
    grac - sciezka, w ktorej legacy kod rzucal NameError(smallAnimation)."""
    from types import SimpleNamespace

    from entities.Mario import Mario

    mario = Mario(0, 0, level, screen, dashboard, sound, base_dir=base_dir)
    mario.powerup(1)
    mario.invincibilityFrames = 0

    mob = SimpleNamespace(
        alive=True, active=True, bouncing=False,
        rect=pygame.Rect(64, 416 - 32, 32, 32),
        leftrightTrait=SimpleNamespace(direction=1, speed=1),
        timer=0,
    )
    mario._onCollisionWithMob(mob, CollisionState(True, False))

    assert mario.powerUpState == 0
    assert mario.rect.size == (32, 32)
    assert mario.invincibilityFrames == 60
    assert mob.alive  # mob przezywa kolizje boczna (to nie stomp)
