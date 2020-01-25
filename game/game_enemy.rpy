init python:
    class GameEnemy(SelectivelyPickle):
        def __init__(self, member, enemy):
            self.x = member['x']
            self.y = member['y']
            self.battlerName = enemy['battlerName']
            self.mhp = enemy['params'][0]
            self.hp = self.mhp