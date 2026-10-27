from pathlib import Path
from pygame import mixer


BASE_DIR = Path(__file__).resolve().parent.parent / "sfx"


class Sound:
    def __init__(self):
        self.music_channel = mixer.Channel(0)
        self.music_channel.set_volume(0.2)
        self.sfx_channel = mixer.Channel(1)
        self.sfx_channel.set_volume(0.2)
        self.allowSFX = True

        self.soundtrack = mixer.Sound(str(BASE_DIR / "main_theme.ogg"))
        self.coin = mixer.Sound(str(BASE_DIR / "coin.ogg"))
        self.bump = mixer.Sound(str(BASE_DIR / "bump.ogg"))
        self.stomp = mixer.Sound(str(BASE_DIR / "stomp.ogg"))
        self.jump = mixer.Sound(str(BASE_DIR / "small_jump.ogg"))
        self.death = mixer.Sound(str(BASE_DIR / "death.wav"))
        self.kick = mixer.Sound(str(BASE_DIR / "kick.ogg"))
        self.brick_bump = mixer.Sound(str(BASE_DIR / "brick-bump.ogg"))
        self.powerup = mixer.Sound(str(BASE_DIR / "powerup.ogg"))
        self.powerup_appear = mixer.Sound(str(BASE_DIR / "powerup_appears.ogg"))
        self.pipe = mixer.Sound(str(BASE_DIR / "pipe.ogg"))

    def play_sfx(self, sfx):
        if self.allowSFX:
            self.sfx_channel.play(sfx)

    def play_music(self, music):
        self.music_channel.play(music)
