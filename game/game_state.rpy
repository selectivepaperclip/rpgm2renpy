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

        @classmethod
        def reverse_direction(cls, direction):
            if direction == GameDirection.UP:
                return GameDirection.DOWN
            elif direction == GameDirection.DOWN:
                return GameDirection.UP
            elif direction == GameDirection.LEFT:
                return GameDirection.RIGHT
            elif direction == GameDirection.RIGHT:
                return GameDirection.LEFT

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
            self.armors = GameArmors()
            self.weapons = GameWeapons()
            self.picture_since_last_pause = False
            self.shown_pictures = {}
            self.everything_reachable = False

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

        def migrate_shown_pictures(self):
            if not hasattr(self, 'shown_pictures'):
                self.shown_pictures = {}
                for tag in renpy.get_showing_tags():
                    picture_id = int(re.search("(\d+)$", tag).groups()[0])
                    displayable = renpy.display.core.displayable_by_tag('master', tag)
                    if len(displayable.children) == 1:
                      image_name = ' '.join(displayable.children[0].name)
                      game_state.show_picture(picture_id, {'image_name': rpgm_picture_name(image_name)})
                    renpy.hide(tag)
            elif not hasattr(self, 'migrated_image_prefixes'):
                for picture_args in self.shown_pictures.itervalues():
                    picture_args['image_name'] = rpgm_picture_name(picture_args['image_name'])
                self.migrated_image_prefixes = True

        def everything_is_reachable(self):
            if hasattr(self, 'everything_reachable'):
                return self.everything_reachable
            return False

        def show_picture(self, picture_id, args):
            self.migrate_shown_pictures()
            self.shown_pictures[picture_id] = args

        def hide_picture(self, picture_id):
            self.migrate_shown_pictures()
            if picture_id in self.shown_pictures:
                del game_state.shown_pictures[picture_id]

        def pictures(self):
            self.migrate_shown_pictures()
            return iter(sorted(self.shown_pictures.iteritems()))

        def system_data(self):
            if not hasattr(self, '_system_data'):
                with rpgm_file('www/data/System.json') as f:
                    self._system_data = json.load(f)

            return self._system_data

        def common_events_data(self):
            if not hasattr(self, '_common_events_data'):
                with rpgm_file('www/data/CommonEvents.json') as f:
                    self._common_events_data = json.load(f)

            return self._common_events_data

        def tilesets(self):
            if not hasattr(self, '_tilesets'):
                with rpgm_file('www/data/Tilesets.json') as f:
                    self._tilesets = json.load(f)

            return self._tilesets

        def plugins(self):
            return rpgm_plugins_loader.json()

        def replace_names(self, text):
            # Replace statements from actor numbers, e.g. \N[2] with their actor name
            text = re.sub(r'\\N\[(\d+)\]', lambda m: self.actors.by_index(int(m.group(1)))['name'], text, flags=re.IGNORECASE)
            # Replace statements from variable ids, e.g. \V[2] with their value
            text = re.sub(r'\\V\[(\d+)\]', lambda m: str(self.variables.value(int(m.group(1)))), text, flags=re.IGNORECASE)
            # Replace statements from literal strings, e.g. \n<Doug> with that string followed by a colon
            text = re.sub(r'\\n\<(.*?)\>', lambda m: ("%s: " % m.group(1)), text)
            # Remove statements with image replacements, e.g. \I[314]
            text = re.sub(r'\\I\[(\d+)\]', '', text, flags=re.IGNORECASE)
            # Remove font size increase statements, e.g. \{
            text = re.sub(r'\\{', '', text)
            # Remove fancy characters from GALV_VisualNovelChoices.js
            text = re.sub(r'\\C\[(\d+)\]', '', text, flags=re.IGNORECASE)
            return text

        def orange_hud_group_map(self):
            if hasattr(self, '_orange_hud_group_map'):
                return self._orange_hud_group_map

            plugins = self.plugins()
            group_data_list = [plugin_data for plugin_data in plugins if plugin_data['name'].startswith('OrangeHudGroup')]

            groups = {}
            for group_data in group_data_list:            
                groups[group_data['parameters']['GroupName']] = group_data
            main_group = next((plugin_data for plugin_data in plugins if plugin_data['name'] == 'OrangeHud'), None)
            if main_group:
                groups['main'] = main_group
            self._orange_hud_group_map = groups

            return self._orange_hud_group_map

        def orange_hud_groups(self):
            groups = []
            for group_name, group_data in self.orange_hud_group_map().iteritems():
                if group_name == 'main' and int(group_data['parameters']['HudX']) == 0:
                    continue
                group_switch_id = int(group_data['parameters']['SwitchId'])
                if group_switch_id < 1 or self.switches.value(group_switch_id) == True:
                    groups.append(group_data)
            return groups

        def orange_hud_pictures(self):
            plugins = self.plugins()
            pic_data_list = [plugin_data for plugin_data in plugins if plugin_data['name'].startswith('OrangeHudVariablePicture') or plugin_data['name'].startswith('OrangeHudFixedPicture')]

            group_map = self.orange_hud_group_map()
            pics = []
            for pic_data in pic_data_list:
                pic_params = pic_data['parameters']
                switch_id = int(pic_params['SwitchId'])
                group = group_map.get(pic_params['GroupName'], None)
                if group:
                    group_switch_id = int(group['parameters']['SwitchId'])
                    if group_switch_id > 0 and self.switches.value(group_switch_id) == False:
                        continue
                if switch_id < 1 or self.switches.value(switch_id) == True:
                    x = int(pic_params['X']) if len(pic_params['X']) > 0 else 0
                    y = int(pic_params['Y']) if len(pic_params['Y']) > 0 else 0
                    if group:
                        padding = int(group_map['main']['parameters']['WindowPadding'])
                        x += int(group['parameters']['HudX']) + padding
                        y += int(group['parameters']['HudY']) + padding

                    image = None
                    if 'Pattern' in pic_params:
                        image = pic_params['Pattern'].replace('%1', str(self.variables.value(int(pic_params['VariableId']))))
                    if 'FileName' in pic_params:
                        image = pic_params['FileName']

                    picture_name = rpgm_picture_name(image)
                    if not image in picture_image_sizes:
                        picture_image_sizes[image] = renpy.image_size(normal_images[picture_name])
                    image_size = picture_image_sizes[image]

                    pics.append({
                        'X': x,
                        'Y': y,
                        'image': picture_name,
                        'size': image_size
                    })

            return pics

        def orange_hud_lines(self):
            plugins = self.plugins()
            line_data_list = [plugin_data for plugin_data in plugins if plugin_data['name'].startswith('OrangeHudLine') or plugin_data['name'].startswith('OrangeHudGold')]

            group_map = self.orange_hud_group_map()
            lines = []
            for line_data in line_data_list:
                line_params = line_data['parameters']
                switch_id = int(line_params['SwitchId'])
                group = group_map.get(line_params['GroupName'], None)
                if group:
                    group_switch_id = int(group['parameters']['SwitchId'])
                    if group_switch_id > 0 and self.switches.value(group_switch_id) == False:
                        continue
                if switch_id < 1 or self.switches.value(switch_id) == True:
                    if line_data['name'] == 'OrangeHudGold':
                        replaced_text = line_params['Pattern'].replace('%1', str(self.party.gold))
                    else:
                        replaced_text = line_params['Pattern'].replace('%1', str(self.variables.value(int(line_params['VariableId']))))
                    # Remove color codes, e.g. \c[24] - for my_summer
                    replaced_text = re.sub(r'\\C\[(\d+)\]', '', replaced_text, flags=re.IGNORECASE)
                    x = int(line_params['X']) if len(line_params['X']) > 0 else 0
                    y = int(line_params['Y']) if len(line_params['Y']) > 0 else 0
                    if group:
                        padding = int(group_map['main']['parameters']['WindowPadding'])
                        x += int(group['parameters']['HudX']) + padding
                        y += int(group['parameters']['HudY']) + padding
                    lines.append({
                        'X': x,
                        'Y': y,
                        'text': replaced_text
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
                        activation_key = match.groups()[0]
                        result.append((activation_key.lower(), event_str))
                        if activation_key.upper() != activation_key.lower():
                            result.append((activation_key.upper(), event_str))
            return result

        def queue_common_and_parallel_events(self):
            if len(self.common_events_data()) > 0:
                self.common_events_index = 1
            self.queue_parallel_events()

        def queue_parallel_events(self):
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

        def migrate_missing_shop_data(self):
            if not hasattr(self, 'armors'):
                self.armors = GameArmors()
            if not hasattr(self, 'weapons'):
                self.weapons = GameWeapons()

        def show_shop_ui(self):
            self.migrate_missing_shop_data()

            shop_params = self.shop_params
            self.shop_params = None
            shop_items = []
            for item_params in shop_params['goods']:
                type, item_id, where_is_price, price_override = item_params[0:4]
                if type == 0:
                    item = self.items.by_id(item_id)
                    if item:
                        if where_is_price != 0:
                            item = item.copy()
                            item['price'] = price_override
                        shop_items.append(item)
                elif type == 1:
                    weapon = self.weapons.by_id(item_id)
                    if weapon:
                        if where_is_price != 0:
                            weapon = weapon.copy()
                            weapon['price'] = price_override
                        shop_items.append(weapon)
                elif type == 2:
                    armor = self.armors.by_id(item_id)
                    if armor:
                        if where_is_price != 0:
                            armor = armor.copy()
                            armor['price'] = price_override
                        shop_items.append(armor)
                else:
                    renpy.say(None, "Purchasing item type %s is not supported!" % type)
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
            if GameIdentifier().is_my_summer():
                # In the downstairs stealth scene, normally dad's view would sometimes shift to the right,
                # but this requires parsing his 'moveRoute' which the engine doesn't currently do, and running
                # it on some kind of a timer. Instead, let's just set him to always be looking right.
                if self.map.map_id == 2 and self.switches.value(312) == True and not self.switches.value(314) == True:
                    self.switches.set_value(314, True)

        def set_game_start_events(self):
            self.events = [e for e in [self.map.find_auto_trigger_event()] if e]
            if len(self.events) == 0:
                self.queue_parallel_events()

        def queue_common_event(self, event_id):
            common_event = self.common_events_data()[event_id]
            self.events.append(GameEvent(self, common_event, common_event))

        def do_next_thing(self, mapdest, keyed_common_event):
            self.migrate_player_x()
            self.skip_bad_events()
            if len(self.events) > 0:
                self.map.clear_reachability_grid_cache()

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
                        self.map.update_for_transfer()
                        self.player_x = this_event.new_x
                        self.player_y = this_event.new_y
                        self.queue_common_and_parallel_events()
                    self.events.pop()
                    if len(self.events) == 0 and self.common_events_index == None and self.parallel_events_index == None:
                        self.queue_common_and_parallel_events()
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
                # convert old-style mapdests that were x, y tuples to MapClickable objects
                if not hasattr(mapdest, 'x'):
                    mapdest =  MapClickable(
                        mapdest[0],
                        mapdest[1]
                    )

                if hasattr(mapdest, 'walk_destination') and mapdest.walk_destination:
                    new_x, new_y = mapdest.x, mapdest.y
                    self.player_direction = self.determine_direction(new_x, new_y)
                    self.player_x, self.player_y = new_x, new_y
                    return True

                map_event = self.map.find_event_for_location(mapdest.x, mapdest.y)
                if not map_event:
                    map_event = self.map.find_event_for_location(mapdest.x, mapdest.y, only_special = True)
                if (not self.map.clicky_event(map_event.event_data, map_event.page)) and (self.player_x != mapdest.x or self.player_y != mapdest.y):
                    if map_event.page['through'] == True and map_event.page['priorityType'] > 0:
                        new_x, new_y = mapdest.x, mapdest.y
                        self.player_direction = self.determine_direction(new_x, new_y)
                        self.player_x, self.player_y = new_x, new_y
                    else:
                        if hasattr(mapdest, 'reachable') and mapdest.reachable and not self.everything_is_reachable():
                            reachability_grid = self.map.reachability_grid_for_current_position()
                            adjacent_square, self.player_direction = self.map.last_square_before_dest(self.player_x, self.player_y, mapdest.x, mapdest.y)
                            self.player_x, self.player_y = adjacent_square
                        else:
                            first_open_square = self.map.first_open_adjacent_square(mapdest.x, mapdest.y)
                            if first_open_square:
                                self.player_direction = self.determine_direction(mapdest.x, mapdest.y)
                                self.player_x, self.player_y = first_open_square

                self.events.append(map_event)
                if debug_events:
                    renpy.say(None, "%d,%d" % (mapdest.x, mapdest.y))
                return True

            return False

        def show_map(self, in_interaction = False):
            game_state.picture_since_last_pause = False

            coordinates = []
            if not in_interaction:
                coordinates = self.map.map_options(self.player_x, self.player_y)
                if not game_state.everything_is_reachable():
                    self.map.assign_reachability(self.player_x, self.player_y, coordinates)
                if hide_unreachable_events:
                    coordinates = [map_clickable for map_clickable in coordinates if map_clickable.reachable]
                if not show_noop_events:
                    coordinates = [map_clickable for map_clickable in coordinates if not hasattr(map_clickable, 'has_commands') or map_clickable.has_commands]

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
            hud_groups = self.orange_hud_groups()

            if not in_interaction and draw_impassible_tiles:
                impassible_tiles=self.map.impassible_tiles()
            else:
                impassible_tiles = []

            viewport_xadjustment.set_value(x_initial)
            viewport_yadjustment.set_value(y_initial)

            switch_toggler_buttons = []

            common_event_queuers = []
            if GameIdentifier().is_milfs_villa() and not in_interaction:
                common_event_queuers.append({"text": 'Combine Items', "event_id": 1, "ypos": 140})
            if GameIdentifier().is_my_summer() and self.switches.value(1) == True:
                common_event_queuers.append({"text": 'Show Status', "event_id": 1, "ypos": 100})

            renpy.show_screen(
                "mapscreen",
                _layer="maplayer",
                mapfactor=mapfactor,
                coords=coordinates,
                player_position=(self.player_x, self.player_y),
                hud_pics=hud_pics,
                hud_lines=hud_lines,
                hud_groups=hud_groups,
                map_name=self.map.name(),
                sprites=self.map.sprites(),
                impassible_tiles=impassible_tiles,
                common_events_keymap=self.common_events_keymap(),
                background_image=background_image,
                width=width,
                height=height,
                viewport_xadjustment=viewport_xadjustment,
                viewport_yadjustment=viewport_yadjustment,
                x_offset=x_offset,
                y_offset=y_offset,
                in_interaction=in_interaction,
                switch_toggler_buttons=switch_toggler_buttons,
                common_event_queuers=common_event_queuers,
            )
