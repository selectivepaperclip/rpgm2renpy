init python:
    class GameEnemy(SelectivelyPickle):
        def __init__(self, member, enemy):
            self.x = member['x']
            self.y = member['y']
            self.battlerName = enemy['battlerName']
            self.mhp = enemy['params'][0]
            self.hp = self.mhp
            self.states = Set()

        def add_state(self, state_id):
            self.states.add(state_id)

        def is_state_affected(self, state_id):
            return state_id in self.states