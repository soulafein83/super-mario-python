"""Wspólne fixtury testów — headless (bez okna, bez dźwięku)."""

import os
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


@pytest.fixture(scope="session")
def base_dir():
    return str(BASE_DIR)


@pytest.fixture(scope="session")
def screen(base_dir):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    import pygame

    pygame.init()
    s = pygame.display.set_mode((640, 480))
    yield s
    pygame.quit()


@pytest.fixture(scope="session")
def dashboard(screen, base_dir):
    from classes.Dashboard import Dashboard

    return Dashboard(str(Path(base_dir) / "img" / "font.png"), 8, screen)


@pytest.fixture(scope="session")
def sound():
    from classes.Sound import Sound

    return Sound()


@pytest.fixture(scope="session")
def level(screen, sound, dashboard, base_dir):
    from classes.Level import Level

    lv = Level(screen, sound, dashboard, base_dir)
    lv.loadLevel("Level1-1")
    return lv
