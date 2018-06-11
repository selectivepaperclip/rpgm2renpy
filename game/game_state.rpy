init python:
    class GameState(SelectivelyPickle):
        def __init__(self):
            self.common_events_index = None
            self.parallel_events_index = None
            self.events = []
            self.starting_map_id = self.system_data()['startMapId']
            self.map_registry = GameMapRegistry(self)
            self.map = self.map_registry.get_map(self.starting_map_id, self.system_data()['startX'], self.system_data()['startY'])
            self.switches = GameSwitches(self.system_data()['switches'])
            self.self_switches = GameSelfSwitches()
            self.variables = GameVariables(self.system_data()['variables'])
            self.party = GameParty()
            self.actors = GameActors()
            self.items = GameItems()
            self.branch = {}

        def __setstate__(self, d):
            self.__dict__.update(d)
            if not hasattr(self, 'events'):
                self.events = [event for event in [self.event] if event]

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

        def do_next_thing(self, mapdest, keyed_common_event):
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
                        self.map = self.map_registry.get_map(this_event.new_map_id, this_event.new_x, this_event.new_y)
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

            if mapdest:
                self.events.append(self.map.find_event_for_location(mapdest[0], mapdest[1]))
                if debug_events:
                    renpy.say(None, "%d,%d" % mapdest)
                return True

            coordinates = self.map.map_options()

            x_offset = 0
            y_offset = 0
            mapfactor = 1
            width = None
            height = None

            background_image = None
            width = float(self.map.data()['width'])
            height = float(self.map.data()['height'])

            if self.map.is_clicky():
                mapfactor = 0.46
            else:
                background_image = self.map.background_image()

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
                player_position=(self.map.x, self.map.y),
                hud_pics=hud_pics,
                hud_lines=hud_lines,
                map_name=self.map.name(),
                sprites=self.map.sprites(),
                impassible_tiles=impassible_tiles,
                common_events_keymap=self.common_events_keymap(),
                background_image=background_image,
                width=width,
                height=height,
                x_offset=x_offset,
                y_offset=y_offset
            )
