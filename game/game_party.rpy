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
            return actor.get_property('id') in self.members

        def storage_attribute_for_item(self, item):
            if 'wtypeId' in item:
                return self.weapons
            elif 'atypeId' in item:
                return self.armors
            else:
                return self.items

        def maic_quest_manager(self):
            if not hasattr(self, 'maic_quest_manager_instance'):
                self.maic_quest_manager_instance = MaicQuestManager()
            return self.maic_quest_manager_instance

        def galv_quest_manager(self):
            if not hasattr(self, 'galv_quest_manager_instance'):
                self.galv_quest_manager_instance = GalvQuestManager()
            return self.galv_quest_manager_instance

        def print_items(self):
            for item_id, quantity in self.items.iteritems():
                item = game_state.items.by_id(item_id)
                print str(item_id) + ': ' + item['name'] + ' ' + str(quantity)
            
    class MaicQuestManager(SelectivelyPickle):
        def __init__(self):
            self.quest_activity = {}
    
        def quest_data(self):
            result = []
            for q in rpgm_game_data['maic_quests']:
                if q['id'] in self.quest_activity and not self.quest_activity[q['id']].get('completed', False):
                    q_copy = q.copy()
                    if 'objectives' in q_copy and len(q_copy['objectives']) > 0:
                        annotated_objectives = []
                        active_objectives = self.quest_activity[q_copy['id']]['objectives']
                        for objective_index, objective_text in enumerate(q_copy['objectives']):
                            if objective_index in active_objectives:
                                annotated_objectives.append({
                                    'text': objective_text,
                                    'completed': 'completed' in active_objectives[objective_index]
                                })
                        q_copy['objectives'] = annotated_objectives

                    result.append(q_copy)
            return result

        def start(self, quest_id):
            self.quest_activity[quest_id] = {}

        def complete(self, quest_id):
            if quest_id not in self.quest_activity:
                self.quest_activity[quest_id] = {}
            self.quest_activity[quest_id]['completed'] = True

        def reveal_objective(self, quest_id, objective_index):
            if quest_id not in self.quest_activity:
                self.quest_activity[quest_id] = {}
            if 'objectives' not in self.quest_activity[quest_id]:
                self.quest_activity[quest_id]['objectives'] = {}
            self.quest_activity[quest_id]['objectives'][objective_index] = {}

        def complete_objective(self, quest_id, objective_index):
            self.reveal_objective(quest_id, objective_index)
            objective_activity = self.quest_activity[quest_id]['objectives']
            objective_activity[objective_index]['completed'] = True
            total_objectives = len(next(q for q in rpgm_game_data['maic_quests'] if q['id'] == quest_id)['objectives'])
            if len([v for v in objective_activity.values() if v.get('completed', None)]) == total_objectives:
                self.complete(quest_id)
                
    class GalvQuestManager(SelectivelyPickle):
        def __init__(self):
            self.quest_activity = {}

        def presented_quests(self):
            result = []
            for quest_id in sorted(self.quest_activity.keys()):
                quest_data = game_file_loader.galv_quest_data()[quest_id]
                objective_data = quest_data['desc'][0].split(self.__sep())

                annotated_objectives = []
                for objective_index, objective_status in enumerate(self.quest_activity[quest_id]['objectives']):
                    if objective_status == -1:
                        continue

                    annotated_objectives.append({
                        'text': game_state.replace_names(objective_data[objective_index]),
                        'completed': objective_status == 1,
                        'failed': objective_status == 2
                    })

                presented_quest = {
                    'name': game_state.replace_names(quest_data['name']),
                    'status': self.quest_activity[quest_id]['status'],
                    'description': game_state.replace_names("\n".join(quest_data['desc'][2:])),
                    'objectives': annotated_objectives
                }
                if self.quest_activity[quest_id]['resolution']:
                    resolutions = quest_data['desc'][1].split(self.__sep())
                    resolution_text = re.sub('\|', "\n", resolutions[self.quest_activity[quest_id]['resolution']])
                    presented_quest['resolution'] = game_state.replace_names(resolution_text)
                result.append(presented_quest)

            return sorted(result, key=lambda q: q['status'])

        def popup(self, quest_id, status, objective_id = None):
            plugin = game_file_loader.plugin_data_exact('Galv_QuestLog')
            parts = []
            if status == -1: # Hidden Objective
                return

            txt_key = None
            if objective_id:
                if status == 0:
                    txt_key = 'Pop New Objective'
                elif status == 1:
                    txt_key = 'Pop Complete Objective'
                elif status == 2:
                    txt_key = 'Pop Fail Objective'
            else:
                if status == 0:
                    txt_key = 'Pop New Quest'
                elif status == 1:
                    txt_key = 'Pop Complete Quest'
                elif status == 2:
                    txt_key = 'Pop Fail Quest'

            if txt_key:
                parts.append(plugin['parameters'][txt_key])

                quest_data = game_file_loader.galv_quest_data()[quest_id]
                if objective_id:
                    objective_data = quest_data['desc'][0].split(self.__sep())
                    parts.append(game_state.replace_names(objective_data[objective_id]))
                else:
                    parts.append(quest_data['name'])

                renpy.notify(' '.join(parts))

        def activate(self, quest_id, hide_popup = None):
            self.__create_quest(quest_id)
            if not hide_popup:
                self.popup(quest_id, 0)

        def complete(self, quest_id, hide_popup = None):
            self.__create_quest(quest_id)
            self.quest_activity[quest_id]['status'] = 1
            if not hide_popup:
                self.popup(quest_id, 1)

        def fail(self, quest_id, hide_popup = None):
            self.__create_quest(quest_id)
            self.quest_activity[quest_id]['status'] = 2
            if not hide_popup:
                self.popup(quest_id, 2)

        def objective(self, quest_id, objective_index, status, hide_popup = None):
            self.__create_quest(quest_id)
            status_id = {
                '0': 0,
                '1': 1,
                '2': 2,
                '-1': -1,
                'hide': -1,
                'active': 0,
                'activate': 0,
                'completed': 1,
                'complete': 1,
                'failed': 2,
                'fail': 2,
            }[status]

            self.quest_activity[quest_id]['objectives'][objective_index] = status_id
            if not hide_popup:
                self.popup(quest_id, status_id, objective_index)

        def resolution(self, quest_id, resolution):
            self.__create_quest(quest_id)
            self.quest_activity[quest_id]['resolution'] = resolution

        def cat_status(self, category_id, status):
            pass

        def __sep(self):
            plugin = game_file_loader.plugin_data_exact('Galv_QuestLog')
            return plugin['parameters']['Separator Character']

        def __create_quest(self, quest_id):
            if quest_id not in self.quest_activity and quest_id in game_file_loader.galv_quest_data():
                quest_data = game_file_loader.galv_quest_data()[quest_id]
                objective_data = quest_data['desc'][0].split(self.__sep())
                if objective_data == ['']:
                    objective_data = []
                self.quest_activity[quest_id] = {
                    'id': quest_id,
                    'cat': 0,
                    'objectives': [None for i in xrange(len(objective_data))], # indexes can be 0,1,2 to store the status of objectives. 0 (or undefined/null) is not yet complete, 1 is completed, 2 is failed
                    'resolution': -1, # the selected resolution to display under the quest description in the quest log. -1 for none.
                    'status': 0 # 0 is not yet completed, 1 is completed, 2 is failed
                }
