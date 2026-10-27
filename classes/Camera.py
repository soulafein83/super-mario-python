from classes.Maths import Vec2D


class Camera:
    def __init__(self, pos, entity, levelLength=60):
        self.pos = Vec2D(pos.x, pos.y)
        self.entity = entity
        self.levelLength = levelLength
        self.x = self.pos.x * 32
        self.y = self.pos.y * 32

    def move(self):
        xPosFloat = self.entity.getPosIndexAsFloat().x
        # Okno podążania wyliczane z długości poziomu: Mario trzymany
        # na kafelku 10 ekranu, aż do 10 kafelków przed końcem.
        if 10 < xPosFloat < self.levelLength - 10:
            self.pos.x = -xPosFloat + 10
        self.pos.x = max(-(self.levelLength - 20), min(0, self.pos.x))
        self.x = self.pos.x * 32
        self.y = self.pos.y * 32
