init python:
    class GameDirection(object):
        UP = 8
        DOWN = 2
        LEFT = 4
        RIGHT = 6
        UP_LEFT = 7
        UP_RIGHT = 9
        DOWN_LEFT = 1
        DOWN_RIGHT = 3

    class GameState(SelectivelyPickle):
        def __init__(self):
            self.common_events_index = None
            self.parallel_events_index = None
            self.events = []
            self.starting_map_id = self.system_data()['startMapId']
            self.map_registry = GameMapRegistry(self)
            self.map = self.map_registry.get_map(self.starting_map_id)
            self.player_x = self.system_data()['startX']
            self.player_y = self.system_data()['startY']
            self.player_direction = GameDirection.DOWN
            self.switches = GameSwitches(self.system_data()['switches'])
            self.self_switches = GameSelfSwitches()
            self.variables = GameVariables(self.system_data()['variables'])
            self.party = GameParty()
            self.actors = GameActors()
            self.items = GameItems()
            self.picture_since_last_pause = False
            self.branch = {}

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'events'):
                self.events = [event for event in [self.event] if event]

        def migrate_player_x(self):
            # for game saves created before player_x moved from map to state
            if not hasattr(self, 'player_x'):
                if hasattr(self.map, 'x'):
                    self.player_x = self.map.x
            if not hasattr(self, 'player_y'):
                if hasattr(self.map, 'y'):
                    self.player_y = self.map.y

        def system_data(self):
            if not hasattr(self, '_system_data'):
                with renpy.file('unpacked/www/data/System.json') as f:
                    self._system_data = json.load(f)

            return self._system_data

        def common_events_data(self):
            if not hasattr(self, '_common_events_data'):
                with renpy.file('unpacked/www/data/CommonEvents.json') as f:
                    self._common_events_data = json.load(f)

            return self._common_events_data

        def tilesets(self):
            if not hasattr(self, '_tilesets'):
                with renpy.file('unpacked/www/data/Tilesets.json') as f:
                    self._tilesets = json.load(f)

            return self._tilesets

        def plugins(self):
            if not hasattr(self, '_plugins'):
                with renpy.file('unpacked/www/js/plugins.js') as f:
                    # the plugins.js file starts with "var $plugins = ["
                    # delete everything before the first [
                    content = f.read()
                    self._plugins = json.loads(content[content.find('['):].rstrip().rstrip(';'))

            return self._plugins

        def orange_hud_pictures(self):
            plugins = self.plugins()
            pic_data_list = [plugin_data for plugin_data in plugins if plugin_data['name'].startswith('OrangeHudVariablePicture')]

            pics = []
            for pic_data in pic_data_list:
                if self.switches.value(int(pic_data['parameters']['SwitchId']) == True):
                    pics.append({
                        'X': int(pic_data['parameters']['X']),
                        'Y': int(pic_data['parameters']['Y']),
                        'image': pic_data['parameters']['Pattern'].replace('%1', str(self.variables.value(int(pic_data['parameters']['VariableId']))))
                    })

            fixed_pic_data_list = [plugin_data for plugin_data in plugins if plugin_data['name'].startswith('OrangeHudFixedPicture')]
            for pic_data in fixed_pic_data_list:
                if self.switches.value(int(pic_data['parameters']['SwitchId']) == True):
                    pics.append({
                        'X': int(pic_data['parameters']['X']),
                        'Y': int(pic_data['parameters']['Y']),
                        'image': pic_data['parameters']['FileName']
                    })

            return pics

        def orange_hud_lines(self):
            plugins = self.plugins()
            line_data_list = [plugin_data for plugin_data in plugins if plugin_data['name'].startswith('OrangeHudLine')]

            lines = []
            for line_data in line_data_list:
                if self.switches.value(int(line_data['parameters']['SwitchId']) == True):
                    lines.append({
                        'X': int(line_data['parameters']['X']),
                        'Y': int(line_data['parameters']['Y']),
                        'text': line_data['parameters']['Pattern'].replace('%1', str(self.variables.value(int(line_data['parameters']['VariableId']))))
                    })
            return lines

        def common_events_keymap(self):
            plugins = self.plugins()
            yepp_common_events = next((plugin_data for plugin_data in plugins if plugin_data['name'] == 'YEP_ButtonCommonEvents'), None)
            if not yepp_common_events:
                return []

            result = []
            for key_desc, event_str in yepp_common_events['parameters'].iteritems():
                if event_str != "" and event_str != "0":
                    match = re.match("Key (\w)", key_desc)
                    if match:
                        result.append((match.groups()[0].lower(), event_str))
            return result

        def queue_common_and_parallel_events(self):
            if len(self.common_events_data()) > 0:
                self.common_events_index = 1
            if len(self.map.data()['events']) > 0:
                self.parallel_events_index = 1

        def show_inventory(self):
            interesting_items = []
            for item_id in self.party.items.keys():
                item = self.items.by_id(item_id)
                if item['effects'] and len(item['effects']) > 0:
                    common_event_effects = [effect for effect in item['effects'] if effect['code'] == 44]
                    if len(common_event_effects) > 0:
                        if len(common_event_effects) > 1:
                            renpy.say(None, "Items with more than one common event effect not supported!")
                        interesting_items.append(item)

            if len(interesting_items) == 0:
                return True

            result = renpy.display_menu([(item['name'], item) for item in interesting_items])
            common_event_effects = [effect for effect in result['effects'] if effect['code'] == 44]
            effect = common_event_effects[0]
            common_event = self.common_events_data()[int(effect['dataId'])]
            self.events.append(GameEvent(self, common_event, common_event))
            return True

        def show_shop_ui(self):
            shop_params = self.shop_params
            self.shop_params = None
            shop_items = []
            for item_params in shop_params['goods']:
                type, item_id, where_is_price, price_override = item_params[0:4]
                if type != 0:
                    renpy.say(None, "Purchasing item type %s is not supported!")
                item = self.items.by_id(item_id)
                if item:
                    if where_is_price != 0:
                        item = item.copy()
                        item['price'] = price_override
                    shop_items.append(item)
            renpy.call_screen(
                "shopscreen",
                shop_items = shop_items,
                purchase_only = shop_params['purchase_only']
            )

        def show_synthesis_ui(self):
            recipes = []
            for item_id in self.party.items:
                item = self.items.by_id(item_id)
                recipe_match = re.match('<Item Recipe: (\d+)>', item['note'])
                if recipe_match:
                    recipe_item_id = int(recipe_match.groups()[0])
                    if recipe_item_id not in recipes:
                        recipes.append(recipe_item_id)

            synthesizables = []
            for item_id in recipes:
                item = self.items.by_id(item_id)
                items_and_counts = self.synthesis_ingredients(item)
                if items_and_counts:
                    has_all = True
                    for (item_name, count) in items_and_counts:
                        ingredient_item = self.items.by_name(item_name)
                        renpy.say(None, ("has %s of %s" % (self.party.num_items(ingredient_item), ingredient_item['name'])))
                        if self.party.num_items(ingredient_item) < count:
                            has_all = False
                    if has_all:
                        synthesizables.append(item)

            renpy.call_screen(
                "synthesisscreen",
                synthesizables = synthesizables
            )

        def synthesis_ingredients(self, item):
            items_and_count = []
            ingredient_pattern = re.compile('<Synthesis Ingredients>[\r\n](.*?)[\r\n]</Synthesis Ingredients\>', re.DOTALL)
            ingredients = re.findall(ingredient_pattern, item['note'])[0]
            if ingredients:
                for ingredient in ingredients.split("\n"):
                    item_name, count_str = ingredient.split(": ")
                    items_and_count.append((item_name, int(count_str)))
                return items_and_count
            return None

        def synthesize_item(self, item):
            for (item_name, count) in self.synthesis_ingredients(item):
                ingredient_item = self.items.by_name(item_name)
                self.party.gain_item(ingredient_item, -1)
            self.party.gain_item(item, 1)

        def determine_direction(self, new_x, new_y):
            if new_y > self.player_y:
                return GameDirection.DOWN
            else:
                return GameDirection.UP

        def skip_bad_events(self):
            if GameIdentifier().is_milfs_villa():
                if self.map.map_id == 64 and not self.self_switches.value((64, 1, "B")):
                    self.self_switches.set_value((64, 1, "A"), True)
                    self.self_switches.set_value((64, 1, "B"), True)
                if self.map.map_id == 27 and self.switches.value(129) == True and not self.self_switches.value((27, 14, "B")):
                    self.self_switches.set_value((27, 14, "A"), True)
                    self.self_switches.set_value((27, 14, "B"), True)

        def do_next_thing(self, mapdest, keyed_common_event):
            self.migrate_player_x()
            self.skip_bad_events()
            if len(self.events) > 0:
                this_event = self.events[-1]
                new_event = this_event.do_next_thing()
                if new_event:
                    self.events.append(new_event)
                    return True
                if hasattr(self, 'shop_params') and self.shop_params:
                    self.show_shop_ui()
                    return True
                if this_event.done():
                    if this_event.new_map_id:
                        self.map = self.map_registry.get_map(this_event.new_map_id)
                        self.player_x = this_event.new_x
                        self.player_y = this_event.new_y
                        self.queue_common_and_parallel_events()
                    if self.common_events_index == None and self.parallel_events_index == None:
                        self.queue_common_and_parallel_events()
                    self.events.pop()
                return True

            if self.common_events_index != None and self.common_events_index < len(self.common_events_data()):
                for event in xrange(self.common_events_index, len(self.common_events_data())):
                    common_event = self.common_events_data()[self.common_events_index]
                    self.common_events_index += 1
                    if common_event['trigger'] > 0 and self.switches.value(common_event['switchId']) == True:
                        self.events.append(GameEvent(self, common_event, common_event))
                        return True
            self.common_events_index = None

            if self.parallel_events_index != None and self.parallel_events_index < len(self.map.data()['events']):
                for event in xrange(self.parallel_events_index, len(self.map.data()['events'])):
                    possible_parallel_event = self.map.parallel_event_at_index(self.parallel_events_index)
                    self.parallel_events_index += 1
                    if possible_parallel_event:
                        self.events.append(possible_parallel_event)
                        return True
            self.parallel_events_index = None

            self.events = [e for e in [self.map.find_auto_trigger_event()] if e]
            if len(self.events) > 0:
                return True

            if keyed_common_event:
                common_event = self.common_events_data()[int(keyed_common_event)]
                self.events.append(GameEvent(self, common_event, common_event))
                return True

            if show_synthesis:
                common_event = self.common_events_data()[1]
                self.events.append(GameEvent(self, common_event, common_event))
                return True

            if mapdest:
                map_event = self.map.find_event_for_location(mapdest[0], mapdest[1])
                if not map_event:
                    map_event = self.map.find_event_for_location(mapdest[0], mapdest[1], only_special = True)
                if not self.map.clicky_event(map_event.event_data, map_event.page):
                    if map_event.page['through'] == True and map_event.page['priorityType'] > 0:
                        new_x = map_event.event_data['x']
                        new_y = map_event.event_data['y']
                        self.player_direction = self.determine_direction(new_x, new_y)
                        self.player_x = new_x
                        self.player_y = new_y
                    else:
                        first_open_square = self.map.first_open_adjacent_square(map_event.event_data['x'], map_event.event_data['y'])
                        if first_open_square:
                            self.player_direction = self.determine_direction(map_event.event_data['x'], map_event.event_data['y'])
                            self.player_x, self.player_y = first_open_square

                self.events.append(map_event)
                if debug_events:
                    renpy.say(None, "%d,%d" % mapdest)
                return True

            game_state.picture_since_last_pause = False

            coordinates = self.map.map_options(self.player_x, self.player_y)

            x_offset = 0
            y_offset = 0
            x_initial = 0
            y_initial = 0
            mapfactor = 1

            background_image = self.map.background_image()
            width = background_image.width
            height = background_image.height

            if self.map.is_clicky(self.player_x, self.player_y):
                # assume we want to show about 40 tiles wide, 22 tiles high
                # player x, y should be centered in the visible map
                # if they are greater than (19, 12)

                mapfactor = 0.65

                #print ("px: %s, py: %s, w: %s, h: %s" % (self.player_x, self.player_y, width, height))

                if self.player_x > 19:
                    x_initial = int((self.player_x - 19) * GameMap.TILE_WIDTH * mapfactor)
                if self.player_y > 12:
                    y_initial = int((self.player_y - 12) * GameMap.TILE_HEIGHT * mapfactor)
                background_image = None
            else:
                map_width = background_image.width + 50
                map_height = background_image.height + 50

                width_ratio = config.screen_width / float(map_width)
                height_ratio = config.screen_height / float(map_height)

                if width_ratio >= 1:
                    x_offset = (config.screen_width - map_width) // 2
                    if height_ratio >= 1:
                        # Image smaller than screen, show in native size
                        mapfactor = 1
                    else:
                        # Image too tall, shrink to fit
                        mapfactor = float(config.screen_height) / map_height
                else:
                    if height_ratio >= 1:
                        # Image too wide, shrink to fit
                        mapfactor = float(config.screen_width) / map_width
                    else:
                        # Image overflowing in both dimensions
                        if width_ratio > height_ratio:
                            # Overflowing more on height
                            mapfactor = float(config.screen_height) / map_height
                        else:
                            # Overflowing more on width
                            mapfactor = float(config.screen_width) / map_width

            hud_pics = self.orange_hud_pictures()
            hud_lines = self.orange_hud_lines()

            if draw_impassible_tiles:
                impassible_tiles=self.map.impassible_tiles()
            else:
                impassible_tiles = []

            renpy.call_screen(
                "mapscreen",
                mapfactor=mapfactor,
                coords=coordinates,
                player_position=(self.player_x, self.player_y),
                hud_pics=hud_pics,
                hud_lines=hud_lines,
                map_name=self.map.name(),
                sprites=self.map.sprites(),
                impassible_tiles=impassible_tiles,
                common_events_keymap=self.common_events_keymap(),
                background_image=background_image,
                width=width,
                height=height,
                x_initial=x_initial,
                y_initial=y_initial,
                x_offset=x_offset,
                y_offset=y_offset,
                show_synthesis_button=GameIdentifier().is_milfs_villa()
            )
