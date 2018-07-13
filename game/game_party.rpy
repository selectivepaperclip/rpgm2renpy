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