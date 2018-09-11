init python:
    class GameParty(SelectivelyPickle):
        MAX_GOLD = 99999999
        MAX_ITEMS = 99

        def __init__(self):
            self.members = [1]
            self.items = {}
            self.armors = {}
            self.weapons = {}
            self.gold = 0

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'gold'):
                self.gold = 0

        def migrate_missing_properties(self):
            if not hasattr(self, 'armors'):
                self.armors = {}
            if not hasattr(self, 'weapons'):
                self.weapons = {}
            if not hasattr(self, 'maic_quest_activity'):
                self.maic_quest_activity = {}

        def leader(self):
            if len(self.members) > 0:
                return self.members[0];

        def num_items(self, item):
            self.migrate_missing_properties()
            return self.storage_attribute_for_item(item).get(item['id'], 0)

        def item_choices(self, type):
            result = []
            for item_id in self.items:
                item = game_state.items.by_id(item_id)
                if item['itypeId'] == type:
                    result.append((item['name'], item['id']))
            return result

        def has_item(self, item):
            return self.num_items(item) > 0

        def gain_gold(self, amount):
            self.gold = max(0, min(self.gold + amount, GameParty.MAX_GOLD))

        def lose_gold(self, amount):
            self.gold = max(0, min(self.gold - amount, GameParty.MAX_GOLD))

        def gain_item(self, item, amount):
            storage_attribute = self.storage_attribute_for_item(item)

            existing_value = storage_attribute.get(item['id'], 0)
            storage_attribute[item['id']] = max(0, min(existing_value + amount, GameParty.MAX_ITEMS))
            if storage_attribute[item['id']] == 0:
                del storage_attribute[item['id']]

        def add_actor(self, actor_index):
            if actor_index not in self.members:
                self.members.append(actor_index)

        def remove_actor(self, actor_index):
            if actor_index in self.members:
                self.members.remove(actor_index)

        def has_actor(self, actor):
            return actor['id'] in self.members

        def storage_attribute_for_item(self, item):
            if 'wtypeId' in item:
                return self.weapons
            elif 'atypeId' in item:
                return self.armors
            else:
                return self.items

        def maic_quests_active(self):
            self.migrate_missing_properties()
            result = []
            for q in rpgm_game_data['maic_quests']:
                if q['id'] in self.maic_quest_activity and not self.maic_quest_activity[q['id']].get('completed', False):
                    q_copy = q.copy()
                    if 'objectives' in q_copy and len(q_copy['objectives']) > 0:
                        annotated_objectives = []
                        active_objectives = self.maic_quest_activity[q_copy['id']]['objectives']
                        for objective_index, objective_text in enumerate(q_copy['objectives']):
                            if objective_index in active_objectives:
                                annotated_objectives.append({
                                    'text': objective_text,
                                    'completed': 'completed' in active_objectives[objective_index]
                                })
                        q_copy['objectives'] = annotated_objectives

                    result.append(q_copy)
            return result

        def maic_quest_start(self, quest_id):
            self.migrate_missing_properties()
            self.maic_quest_activity[quest_id] = {}

        def maic_quest_complete(self, quest_id):
            self.migrate_missing_properties()
            if quest_id not in self.maic_quest_activity:
                self.maic_quest_activity[quest_id] = {}
            self.maic_quest_activity[quest_id]['completed'] = True

        def maic_quest_reveal_objective(self, quest_id, objective_index):
            self.migrate_missing_properties()
            if quest_id not in self.maic_quest_activity:
                self.maic_quest_activity[quest_id] = {}
            if 'objectives' not in self.maic_quest_activity[quest_id]:
                self.maic_quest_activity[quest_id]['objectives'] = {}
            self.maic_quest_activity[quest_id]['objectives'][objective_index] = {}

        def maic_quest_complete_objective(self, quest_id, objective_index):
            self.maic_quest_reveal_objective(quest_id, objective_index)
            objective_activity = self.maic_quest_activity[quest_id]['objectives']
            objective_activity[objective_index]['completed'] = True
            total_objectives = len(next(q for q in rpgm_game_data['maic_quests'] if q['id'] == quest_id)['objectives'])
            if len([v for v in objective_activity.values() if v.get('completed', None)]) == total_objectives:
                self.maic_quest_complete(quest_id)
