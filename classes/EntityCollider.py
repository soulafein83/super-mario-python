class EntityCollider:
    def __init__(self, entity):
        self.entity = entity

    def check(self, target):
        if self.entity.rect.colliderect(target.rect):
            return self.determineSide(target.rect, self.entity.rect)
        return CollisionState(False, False)

    def determineSide(self, rect1, rect2):
        # rect1: cel kolizji, rect2: encja-właściciel kolidera.
        # Encja jest "na wierzchu" celu, gdy jej górna krawędź jest nad
        # górną krawędzią celu, a dolna krawędź weszła w cel płytko
        # (mniej niż wysokość celu) — czyli spadła z góry, a nie
        # uderzyła w bok albo od dołu (stomp vs. kolizja boczna).
        penetration = rect2.bottom - rect1.top
        if rect2.top < rect1.top and 0 < penetration < rect1.height:
            return CollisionState(True, True)
        return CollisionState(True, False)


class CollisionState:
    def __init__(self, _isColliding, _isTop):
        self.isColliding = _isColliding
        self.isTop = _isTop
