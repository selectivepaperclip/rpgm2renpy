init python:
    class GameActors(SelectivelyPickle):
        def __init__(self):
            self.overrides = {}

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'overrides'):
                self.overrides = {}

        def data(self):
            return game_file_loader.json_file(rpgm_data_path("Actors.json"))

        def actor_name(self, index):
            actor = self.by_index(index)
            if actor:
                return actor.get_property('name')
            else:
                return ''

        def by_index(self, index):
            if index > len(self.data()) - 1:
                return None
            actor_data = self.data()[index]
            if not index in self.overrides:
                self.overrides[index] = {}
            return GameActor(actor_data, self.overrides[index])

    class GameActor(SelectivelyPickle):
        def __init__(self, actor_data, overrides):
            self.actor_data = actor_data
            self.overrides = overrides
            if 'level' not in overrides:
                overrides['level'] = actor_data['initialLevel']
            if 'classExp' not in overrides:
                overrides['classExp'] = {actor_data['classId']: 0}
            if 'hp' not in overrides or 'mp' not in overrides:
                self.recover_all()

        def populate_states(self):
            if not 'affected_states' in self.overrides:
                self.overrides['affected_states'] = Set()

        def populate_skills(self):
            if not 'learned_skills' in self.overrides:
                self.overrides['learned_skills'] = Set()

        def populate_param_plus(self):
            if not 'param_plus' in self.overrides:
                self.overrides['param_plus'] = [0,0,0,0,0,0,0,0]

        def populate_hp_mp(self):
            if 'hp' not in self.overrides:
                self.overrides['hp'] = self.param(0) # Max HP
            if 'mp' not in self.overrides:
                self.overrides['mp'] = self.param(1) # Max MP

        def set_property(self, property_name, property_value):
            self.overrides[property_name] = property_value

        def get_property(self, property_name):
            if property_name in self.overrides:
                return self.overrides[property_name]
            return self.actor_data[property_name]

        def add_state(self, state_to_change):
            self.populate_states()
            self.overrides['affected_states'].add(state_to_change)

        def remove_state(self, state_to_change):
            self.populate_states()
            affected_states = self.overrides['affected_states']
            if state_to_change in affected_states:
                affected_states.remove(state_to_change)

        def is_state_affected(self, state):
            self.populate_states()
            affected_states = self.overrides['affected_states']
            return state in affected_states

        def learn_skill(self, skill_id):
            self.populate_skills()
            self.overrides['learned_skills'].add(skill_id)

        def forget_skill(self, skill_id):
            self.populate_skills()
            learned_skills = self.overrides['learned_skills']
            if skill_id in learned_skills:
                learned_skills.remove(skill_id)

        def is_learned_skill(self, skill_id):
            self.populate_skills()
            learned_skills = self.overrides['learned_skills']
            return skill_id in learned_skills

        def has_weapon(self, weapon_id):
            # TODO: respond to weapon changes
            # TODO: respond to dual wield / alternate item slot setups. if merited.
            return self.actor_data['equips'][0] == weapon_id

        def has_armor(self, armor_id):
            # TODO: respond to armor changes
            for item_id in self.actor_data['equips'][1:]:
                if armor_id == item_id:
                    return True
            return False

        def add_exp(self, exp):
            new_level = self.overrides['level']
            self.overrides['classExp'][self.get_property('classId')] += exp
            while (new_level < self.get_property('maxLevel') and self.current_exp() >= self.exp_for_level(new_level + 1)):
                new_level = new_level + 1
            self.set_property('level', new_level)

        def add_level(self, level_delta):
            new_level = self.overrides['level'] + level_delta
            self.set_property('level', new_level)

        def change_hp(self, value):
            self.populate_hp_mp()
            self.overrides['hp'] += value

        def change_mp(self, value):
            self.populate_hp_mp()
            self.overrides['mp'] += value

        def recover_all(self):
            self.overrides['hp'] = self.param(0) # Max HP
            self.overrides['mp'] = self.param(1) # Max MP

        def param_base(self, param_id):
            class_data = self.current_class()
            return class_data['params'][param_id][self.overrides['level']]

        def param_plus(self, param_id):
            self.populate_param_plus()
            # TODO: equipment
            return self.overrides['param_plus'][param_id]

        def hp(self):
            self.populate_hp_mp()
            return self.get_property('hp')

        def mp(self):
            self.populate_hp_mp()
            return self.get_property('mp')

        def param(self, param_id):
            return self.param_base(param_id) + self.param_plus(param_id)

        def add_param(self, param_id, value):
            self.populate_param_plus()
            self.overrides['param_plus'][param_id] += value

        def current_class(self):
            return game_file_loader.json_file(rpgm_data_path("Classes.json"))[self.get_property('classId')]

        def current_exp(self):
            return self.overrides['classExp'][self.get_property('classId')]

        def exp_for_level(self, level):
            class_data = self.current_class()
            basis, extra, acc_a, acc_b = class_data['expParams']

            return int(basis * (level-1 ** 0.9 + acc_a / 250.0) * level * (level+1) / (6 + (level ** 2) / 50.0 / acc_b) + (level - 1) * extra)
