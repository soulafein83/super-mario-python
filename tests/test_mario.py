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


def test_input_read_before_physics(level, screen, dashboard, sound, base_dir):
    """P1.5: checkForInput wywolany przed moveMario w ramach jednej klatki
    (legacy: wejcie odczytywane na koncu -> opoznienie sterowania o klatke)."""
    from entities.Mario import Mario

    mario = Mario(0, 0, level, screen, dashboard, sound, base_dir=base_dir)
    order = []
    orig_input = mario.input.checkForInput
    orig_move = mario.moveMario
    mario.input.checkForInput = lambda: (order.append("input"), orig_input())[1]
    mario.moveMario = lambda: (order.append("move"), orig_move())[1]
    try:
        mario.update()
    finally:
        mario.input.checkForInput = orig_input
        mario.moveMario = orig_move
    assert order.index("input") < order.index("move")


def test_two_coins_collected_same_frame(screen, sound, dashboard, base_dir):
    """P1.6: dwie monety na tym samym polu - obie zbierane w jednej klatce
    (legacy: iteracja po zywej liscie + remove pomijala druga monete)."""
    from classes.Level import Level
    from entities.Coin import Coin
    from entities.Mario import Mario

    lv = Level(screen, sound, dashboard, base_dir)
    lv.loadLevel("Level1-1")
    mario = Mario(0, 0, lv, screen, dashboard, sound, base_dir=base_dir)
    c1 = Coin(screen, lv.sprites.spriteCollection, 0, 0)
    c2 = Coin(screen, lv.sprites.spriteCollection, 0, 0)
    lv.entityList += [c1, c2]
    coins_before = dashboard.coins
    mario.update()
    assert c1 not in lv.entityList
    assert c2 not in lv.entityList
    assert dashboard.coins - coins_before == 2


def _jump_apex(screen, sound, dashboard, base_dir, release_after=None):
    """Szczyt skoku (najmniejsze rect.y) przy sterowaniu samym traitem."""
    from classes.Level import Level
    from entities.Mario import Mario

    lv = Level(screen, sound, dashboard, base_dir)
    lv.loadLevel("Level1-1")
    m = Mario(0, 0, lv, screen, dashboard, sound, base_dir=base_dir)
    m.rect = pygame.Rect(0, 384, 32, 32)  # stoi na podlodze (kol. 0)
    m.onGround = True
    m.traits["jumpTrait"].jump(True)
    top = m.rect.y
    for i in range(150):
        # jak w grze: co klatke stan klawisza przez jump() (wyjscie z
        # fazy inJump jest oceniane wewnatrz)
        holding = release_after is None or i < release_after
        m.traits["jumpTrait"].jump(holding)
        m.moveMario()
        m.applyGravity()
        top = min(top, m.rect.y)
        if m.onGround and i > 2:  # wyladowal z powrotem
            break
    return top


def test_variable_jump_height(screen, sound, dashboard, base_dir):
    """A7: puszczenie klawisza w fazie wznosu przycina skok (szczyt nizej)."""
    full = _jump_apex(screen, sound, dashboard, base_dir)
    short = _jump_apex(screen, sound, dashboard, base_dir, release_after=2)
    assert short > full + 32  # skok przyciuty przynajmniej o kafelek wyzej
