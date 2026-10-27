class JumpTrait:
    def __init__(self, entity):
        self.verticalSpeed = -12
        self.jumpHeight = 120
        self.entity = entity
        self.initalHeight = 384
        self.deaccelerationHeight = self.jumpHeight - ((self.verticalSpeed*self.verticalSpeed)/(2*self.entity.gravity))
        self.releaseDamp = 0.4

    def jump(self, jumping):
        if jumping:
            if self.entity.onGround:
                self.entity.sound.play_sfx(self.entity.sound.jump)
                self.entity.vel.y = self.verticalSpeed
                self.entity.inAir = True
                self.initalHeight = self.entity.rect.y
                self.entity.inJump = True
                self.entity.obeyGravity = False  # always reach maximum height
        elif self.entity.vel.y < 0 and self.entity.inJump:
            # Zmienny skok (A7): puszczenie klawisza w fazie wznosu
            # przycina skok (prędkość pionowa x0.4 + natychmiastowa
            # grawitacja). Dotyczy tylko skoku gracza (inJump), nie
            # odbicia po stompie (bounceTrait nie ustawia inJump).
            self.entity.vel.y *= self.releaseDamp
            self.entity.inJump = False
            self.entity.obeyGravity = True

        if self.entity.inJump:
            if (self.initalHeight-self.entity.rect.y) >= self.deaccelerationHeight or self.entity.vel.y == 0:
                self.entity.inJump = False
                self.entity.obeyGravity = True

    def reset(self):
        self.entity.inAir = False
