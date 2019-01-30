init python:
    class GameActors(SelectivelyPickle):
        def __init__(self):
            self.overrides = {
            }

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'overrides'):
                self.overrides = {}

        def data(self):
            return game_file_loader.json_file(rpgm_data_path("Actors.json"))

        def set_property(self, index, property_name, property_value):
            self.populate_override(index)
            self.overrides[index][property_name] = property_value

        def add_state(self, index, state_to_change):
            self.populate_states(index)
            self.overrides[index]['affected_states'].add(state_to_change)

        def remove_state(self, index, state_to_change):
            self.populate_states(index)
            affected_states = self.overrides[index]['affected_states']
            if state_to_change in affected_states:
                affected_states.remove(state_to_change)

        def populate_override(self, index):
            if not self.overrides.has_key(index):
                self.overrides[index] = {}

        def populate_states(self, index):
            self.populate_override(index)
            overrides = self.overrides[index]
            if not hasattr(overrides, 'affected_states'):
                overrides['affected_states'] = Set()

        def add_exp(self, index, exp):
            actor_data = self.by_index(index)
            new_level = actor_data['level']
            actor_data['classExp'][actor_data['classId']] += exp
            new_exp = actor_data['classExp'][actor_data['classId']]
            while (new_level < actor_data['maxLevel'] and exp >= self.exp_for_level(index, new_level + 1)):
                new_level = new_level + 1
            self.set_property(index, 'level', new_level)

        def add_level(self, index, level_delta):
            actor_data = self.by_index(index)
            new_level = actor_data['level'] + level_delta
            self.set_property(index, 'level', new_level)

        def exp_for_level(self, index, level):
            actor_data = self.data()[index]
            class_data = game_file_loader.json_file(rpgm_data_path("Classes.json"))[actor_data['classId']]
            basis, extra, acc_a, acc_b = class_data['expParams']

            return int(basis * (level-1 ** 0.9 + acc_a / 250.0) * level * (level+1) / (6 + (level ** 2) / 50.0 / acc_b) + (level - 1) * extra)

        def by_index(self, index):
            if index > len(self.data()) - 1:
                return None
            actor_data = self.data()[index]
            overrides = self.overrides.get(index, {})
            if 'level' not in overrides:
                overrides['level'] = actor_data['initialLevel']
            if 'classExp' not in overrides:
                overrides['classExp'] = {actor_data['classId']: 0}
            actor_data.update(overrides)
            return actor_data
