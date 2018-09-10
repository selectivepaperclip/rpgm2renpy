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
        def delta_for_direction(cls, direction):
            if direction == GameDirection.UP:
                return (0, -1)
            elif direction == GameDirection.DOWN:
                return (0, 1)
            elif direction == GameDirection.LEFT:
                return (-1, 0)
            elif direction == GameDirection.RIGHT:
                return (1, 0)

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
            self.parallel_events = []
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
            self.timer = GameTimer()
            self.shown_pictures = {}
            self.queued_pictures = []
            self.everything_reachable = False

        def ensure_initialized_attributes(self):
            if not hasattr(self, 'events'):
                self.events = [event for event in [self.event] if event]
            if not hasattr(self, 'timer'):
                self.timer = GameTimer()
            if not hasattr(self, 'parallel_events'):
                self.parallel_events = []

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
                        child_size = displayable.child_size
                        game_state.show_picture(picture_id, {
                            'image_name': rpgm_picture_name(image_name),
                            'size': (int(child_size[0]), int(child_size[1])),
                        })
                    renpy.hide(tag)
            elif not hasattr(self, 'migrated_image_prefixes'):
                for picture_args in self.shown_pictures.itervalues():
                    picture_args['image_name'] = rpgm_picture_name(picture_args['image_name'])
                self.migrated_image_prefixes = True
            if not hasattr(self, 'queued_pictures'):
                self.queued_pictures = []

        def everything_is_reachable(self):
            if hasattr(self, 'everything_reachable'):
                return self.everything_reachable
            return False

        def occluded(self):
            return GameIdentifier().is_incest_adventure() and self.queued_picture(2) and self.queued_picture(2)['image_name'] == rpgm_picture_name('LOADINGANIMATIONS')

        def print_picture(self, picture):
            if isinstance(picture, RpgmAnimation):
                for frame in picture.images:
                    self.print_picture(frame)
            elif isinstance(picture, renpy.display.transform.Transform):
                self.print_picture(picture.children[0])
            elif isinstance(picture, renpy.display.image.ImageReference):
                print picture.visit()[0].filename
            else:
                print picture

        def print_pictures(self):
            for picture_id, picture_data in game_state.shown_pictures.iteritems():
                print "PICTURE %s:" % picture_id
                self.print_picture(picture_data['image_name'])

        def show_picture(self, picture_id, args):
            self.migrate_shown_pictures()
            args['faded_out'] = (hasattr(self, 'faded_out') and self.faded_out) or game_state.occluded()
            self.queued_pictures.append((picture_id, args))

        def move_picture(self, picture_id, args, wait, duration):
            self.migrate_shown_pictures()
            queued_picture = self.queued_picture(picture_id)
            if not queued_picture and picture_id in self.shown_pictures:
                shown_picture = self.shown_pictures[picture_id]
                reconstructed_picture_args = {
                    'image_name': shown_picture['image_name'],
                    'opacity': shown_picture['opacity']
                }
                if wait:
                    reconstructed_picture_args['wait'] = duration
                if 'final_x' in shown_picture:
                    reconstructed_picture_args.update({
                        'x': shown_picture['final_x'],
                        'y': shown_picture['final_y'],
                        'size': shown_picture['final_size']
                    })
                elif 'x' in shown_picture:
                    reconstructed_picture_args.update({
                        'x': shown_picture['x'],
                        'y': shown_picture['y'],
                        'size': shown_picture['size']
                    })
                self.queued_pictures.append((picture_id, reconstructed_picture_args))
            elif queued_picture and wait:
                queued_picture['wait'] = duration
            self.queued_pictures.append((picture_id, args))

        def hide_picture(self, picture_id):
            self.migrate_shown_pictures()
            if picture_id in self.shown_pictures:
                del self.shown_pictures[picture_id]
            self.queued_pictures = [(queued_picture_id, args) for (queued_picture_id, args) in self.queued_pictures if queued_picture_id != picture_id]

        def queued_picture(self, desired_picture_id):
            self.migrate_shown_pictures()
            for picture_id, picture_args in reversed(self.queued_pictures):
                if picture_id == desired_picture_id:
                    return picture_args

        def queued_or_shown_picture(self, desired_picture_id):
            queued_picture = self.queued_picture(desired_picture_id)
            if queued_picture:
                return queued_picture
            if desired_picture_id in self.shown_pictures:
                return self.shown_pictures[desired_picture_id]

        def queued_or_shown_picture(self, desired_picture_id):
            self.migrate_shown_pictures()
            for picture_id, picture_args in reversed(self.queued_pictures):
                if picture_id == desired_picture_id:
                    return picture_args
            if desired_picture_id in self.shown_pictures:
                return self.shown_pictures[desired_picture_id]

        def wait(self, frames):
            self.migrate_shown_pictures()
            if len(self.queued_pictures) > 0:
                last_picture_id, last_picture_args = self.queued_pictures[-1]
                if 'wait' in last_picture_args:
                    last_picture_args['wait'] += frames
                else:
                    last_picture_args['wait'] = frames

        def flush_queued_pictures(self):
            self.migrate_shown_pictures()
            if len(self.queued_pictures) == 0:
                return

            frame_data = {}
            for picture_id, picture_args in self.queued_pictures:
                if picture_id in frame_data:
                    existing_frame = frame_data[picture_id][-1]
                    if 'wait' in existing_frame and existing_frame['wait'] > 0 and not picture_args.get('faded_out', False):
                        frame_data[picture_id].append(picture_args)
                    else:
                        frame_data[picture_id][-1] = picture_args
                else:
                    frame_data[picture_id] = [picture_args]

            for picture_id, picture_frames in frame_data.iteritems():
                last_frame = picture_frames[-1]
                picture_args = {
                    "final_x": last_frame.get('x', 0),
                    "final_y": last_frame.get('y', 0),
                    "final_size": last_frame.get('size', None),
                    "opacity": picture_frames[-1].get('opacity', 255),
                    "size": None
                }
                if len(picture_frames) == 1:
                    picture_args['image_name'] = RpgmAnimationBuilder.image_for_picture(picture_frames[0])
                else:
                    should_loop = 'loop' in last_frame and last_frame['loop']
                    picture_transitions = RpgmAnimationBuilder(picture_frames).build(loop = should_loop)
                    picture_args['image_name'] = RpgmAnimation(*picture_transitions, anim_timebase = True)
                self.shown_pictures[picture_id] = picture_args

            self.queued_pictures = []

        def pictures(self):
            self.migrate_shown_pictures()

            if GameIdentifier().is_ics1():
                # ICS1 keeps showing pictures on top of each other, making the game slower and slower what with the compositing
                # we need to hide all but the topmost one
                if len(self.shown_pictures) > 0:
                    last_scene_image = None
                    for k, v in reversed(sorted(self.shown_pictures.iteritems())):
                        if hasattr(v['image_name'], 'children') and len(v['image_name'].children) > 0 and v['image_name'].children[0].name[0].startswith('rpgmpicture-scene'):
                            last_scene_image = k
                            break

                    tmp_shown_pictures = {}
                    for k, v in reversed(sorted(self.shown_pictures.iteritems())):
                        if hasattr(v['image_name'], 'children') and len(v['image_name'].children) > 0 and v['image_name'].children[0].name[0].startswith('rpgmpicture-scene') and last_scene_image != k:
                            continue
                        tmp_shown_pictures[k] = v

                    return iter(sorted(tmp_shown_pictures.iteritems()))
                else:
                    return []
            else:
                return iter(sorted(self.shown_pictures.iteritems()))

        def system_data(self):
            if not hasattr(self, '_system_data'):
                with rpgm_data_file('System.json') as f:
                    self._system_data = json.load(f)

            return self._system_data

        def common_events_data(self):
            if not hasattr(self, '_common_events_data'):
                with rpgm_data_file('CommonEvents.json') as f:
                    self._common_events_data = json.load(f)

            return self._common_events_data

        def tilesets(self):
            if not hasattr(self, '_tilesets'):
                with rpgm_data_file('Tilesets.json') as f:
                    self._tilesets = json.load(f)

            return self._tilesets

        def plugins(self):
            return rpgm_plugins_loader.json()

        def replace_names(self, text):
            # Replace statements from actor numbers, e.g. \N[2] with their actor name
            text = re.sub(r'\\N\[(\d+)\]', lambda m: self.actors.by_index(int(m.group(1)))['name'], text, flags=re.IGNORECASE)
            # Replace statements from variable ids, e.g. \V[2] with their value
            text = re.sub(r'\\V\[(\d+)\]', lambda m: str(self.variables.value(int(m.group(1)))), text, flags=re.IGNORECASE)
            # Remove statements with image replacements, e.g. \I[314]
            text = re.sub(r'\\I\[(\d+)\]', '', text, flags=re.IGNORECASE)

            # Remove font size increase/decrease statements, e.g. \{ \}
            # Remove "wait for button" e.g. \!
            # Remove other "wait" commands e.g. \. \|
            text = re.sub(r'\\[{}!.|]', '', text)

            # Remove position changing things
            text = re.sub(r'\\p[xy]\[.*?\]\s*', '', text)
            # Remove outline changing things
            text = re.sub(r'\\o[cw]\[.*?\]\s*', '', text)
            # Remove font changing things
            text = re.sub(r'\\fs\[.*?\]\s*', '', text)
            text = re.sub(r'\\fn\<.*?\>\s*', '', text)
            text = re.sub(r'\\f[rbi]\s*', '', text)

            # Remove fancy characters from GALV_VisualNovelChoices.js
            text = re.sub(r'\\C\[(\d+)\]', '', text, flags=re.IGNORECASE)

            # Replace statements from literal strings, e.g. \n<Doug> with that string followed by a colon
            # these names would normally show in a box on top of the message window; the strategy
            # here is to just hoist them to the top of the string
            messagebox_name_regexp = re.compile(r'\\n[cr]?\<(.*?)\>')
            messagebox_name_match = re.search(messagebox_name_regexp, text)
            if messagebox_name_match:
                text = "%s:\n%s" % (messagebox_name_match.group(1), text.lstrip())
                text = re.sub(messagebox_name_regexp, '', text)
                text = re.sub(r'\s*$', '', text)

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

        def function_calls_keymap(self):
            result = []
            if GameIdentifier().is_ics1() or rpgm_game_data.get('enable_inventory_key', None):
                result.append(('i', 'show_inventory'))
            if rpgm_game_data.get('maic_quests', None):
                result.append(('q', 'show_maic_quests'))
            return result

        def queue_common_and_parallel_events(self):
            if len(self.common_events_data()) > 0:
                self.common_events_index = 1
            self.queue_parallel_events()

        def queue_parallel_events(self, keep_relevant_existing = True):
            if not hasattr(self, 'previous_parallel_event_pages'):
                self.previous_parallel_event_pages = []
            parallel_event_pages = self.map.parallel_event_pages()
            if parallel_event_pages not in self.previous_parallel_event_pages:
                self.previous_parallel_event_pages.append(parallel_event_pages)

            new_parallel_events = self.map.parallel_events()
            if len(self.parallel_events) > 0 or keep_relevant_existing:
                # Keep existing events with the same id/page combos to retain pause position,
                # otherwise treat the new parallel events as canon
                for existing_parallel_event in self.parallel_events:
                    id = existing_parallel_event.event_data['id']
                    new_event_with_id = next((e for e in new_parallel_events if e.event_data['id'] == id), None)
                    if new_event_with_id and new_event_with_id.page_index == existing_parallel_event.page_index:
                        new_parallel_events.remove(new_event_with_id)
                        new_parallel_events.append(existing_parallel_event)

            self.parallel_events = new_parallel_events

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

        def show_maic_quests(self):
            scrubbed_quest_data = []
            for quest in self.party.maic_quests_active():
                quest_copy = quest.copy()
                quest_copy['description'] = "\n".join([line.strip() for line in quest_copy['description'].split("\n")])
                scrubbed_quest_data.append(quest_copy)
            result = renpy.call_screen('maic_quests_screen', scrubbed_quest_data)
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
                    tooltip_lines = []
                    for (item_name, count) in items_and_counts:
                        ingredient_item = self.items.by_name(item_name)
                        tooltip_lines.append("%s: %s" % (ingredient_item['name'], self.party.num_items(ingredient_item)))
                        if self.party.num_items(ingredient_item) < count:
                            has_all = False
                    synthesizable = item.copy()
                    synthesizable['tooltip'] = "\n".join(tooltip_lines)
                    synthesizable['synthesizable'] = has_all
                    synthesizables.append(synthesizable)

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
            if GameIdentifier().is_visiting_sara():
                # Near the end, you have to push a box a very long way.
                # The engine is almost capable of doing this, but why bother.
                if self.map.map_id == 4 and self.switches.value(132) == True and not self.switches.value(133) == True:
                    self.switches.set_value(133, True)

        def pause(self):
            self.flush_queued_pictures()
            renpy.pause()

        def set_game_start_events(self):
            self.events = [e for e in [self.map.find_auto_trigger_event()] if e]
            if len(self.events) == 0:
                self.queue_parallel_events()

        def transfer_player(self, transfer_event):
            changing_maps = transfer_event.new_map_id != self.map.map_id
            if noisy_events:
                print "TRANSFERRING PLAYER TO MAP %s: (%s, %s)" % (transfer_event.new_map_id, transfer_event.new_x, transfer_event.new_y)
            if changing_maps:
                self.reset_user_zoom()
                self.map = self.map_registry.get_map(transfer_event.new_map_id)
                self.map.update_for_transfer()
            self.player_x = transfer_event.new_x
            self.player_y = transfer_event.new_y
            if hasattr(transfer_event, 'new_direction') and transfer_event.new_direction > 0:
                self.player_direction = transfer_event.new_direction
            # TODO: probably better handled elsewhere
            if changing_maps:
                self.parallel_events = []
                self.move_routes = []
                self.queue_common_and_parallel_events()

        def queue_common_event(self, event_id):
            common_event = self.common_events_data()[event_id]
            self.events.append(GameEvent(self, common_event, common_event))

        def finish_active_timer(self):
            if self.timer.frames > 0:
                self.timer.finish()
                self.queue_parallel_events(keep_relevant_existing = True)

        def unpause_parallel_events_for_key(self, key, press_count = 1):
            if hasattr(self, 'parallel_events') and len(self.parallel_events) > 0:
                paused_parallel_events = [e for e in self.parallel_events if hasattr(e, 'paused_for_key') and e.paused_for_key == key]
                smallest_unpaused_delay = None
                for e in paused_parallel_events:
                    e.press_count = press_count
                    e.paused_for_key = None

        def unpause_parallel_events(self):
            all_paused_events = []
            if hasattr(self, 'parallel_events') and len(self.parallel_events) > 0:
                all_paused_events += [e for e in self.parallel_events if hasattr(e, 'paused') and e.paused > 0]
            if hasattr(self, 'move_routes') and len(self.move_routes) > 0:
                all_paused_events += [e for e in self.move_routes if hasattr(e, 'paused') and e.paused > 0]

            if len(all_paused_events) > 0:
                smallest_unpaused_delay = None
                for e in sorted(all_paused_events, key=lambda e: e.paused):
                    if smallest_unpaused_delay and e.paused > smallest_unpaused_delay:
                        e.paused -= smallest_unpaused_delay
                    else:
                        smallest_unpaused_delay = e.paused
                        e.paused = 0
                self.queue_parallel_events(keep_relevant_existing = True)

        def requeue_parallel_events_if_changed(self):
            if hasattr(self, 'previous_parallel_event_pages') and len(self.previous_parallel_event_pages) > 0:
                current_parallel_event_pages = self.map.parallel_event_pages()
                seen_event_set_before = False
                for prior_event_page_set in reversed(self.previous_parallel_event_pages):
                    if current_parallel_event_pages == prior_event_page_set:
                        seen_event_set_before = True
                        break
                if not seen_event_set_before:
                    if noisy_events:
                        print "running parallel events changed event pages %s to %s" % (self.previous_parallel_event_pages[-1], current_parallel_event_pages)

                    self.queue_parallel_events(keep_relevant_existing = True)
                    return True

        def paused_move_route_at_page(self, event_id, page_index):
            for existing_move_route in self.move_routes:
                if event_id == existing_move_route.event_data['id']:
                    if page_index == existing_move_route.page_index:
                        return existing_move_route

        def process_move_routes(self):
            if not hasattr(self, 'move_routes'):
                self.move_routes = []
            new_move_routes = []
            for e in self.map.active_events():
                for reverse_page_index, page in enumerate(reversed(e['pages'])):
                    if self.map.meets_conditions(e, page['conditions']):
                        if self.map.has_commands(page['moveRoute']):
                            page_index = (len(e['pages']) - 1) - reverse_page_index
                            event = self.paused_move_route_at_page(e['id'], page_index)
                            if not event:
                                event = GameEvent(self, e, page, page_index)
                            if not hasattr(event, 'paused') or event.paused == 0:
                                event.process_move_route(e['id'], page['moveRoute'], return_on_wait = not page['moveRoute']['wait'])
                                if event.move_route_index >= len(page['moveRoute']['list']) - 1 and page['moveRoute']['repeat']:
                                    event.move_route_index = 0
                            new_move_routes.append(event)
                        break
            self.move_routes = new_move_routes

        def do_next_thing(self, mapdest, keyed_common_event):
            self.ensure_initialized_attributes()
            self.skip_bad_events()
            if len(self.events) > 0:
                self.previous_parallel_event_pages = []

                this_event = self.events[-1]
                new_event = this_event.do_next_thing()
                if new_event:
                    self.events.append(new_event)
                    return True
                if hasattr(self, 'shop_params') and self.shop_params:
                    self.show_shop_ui()
                    return True
                if this_event.new_map_id and this_event.new_map_id == self.map.map_id:
                    self.transfer_player(this_event)
                    this_event.new_map_id = None
                if this_event.done():
                    if this_event.new_map_id:
                        self.transfer_player(this_event)
                    self.events.pop()
                    if len(self.events) == 0 and self.common_events_index == None and len(self.parallel_events) == 0:
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

            if hasattr(self, 'parallel_events') and len(self.parallel_events) > 0:
                first_never_paused_event = next((e for e in self.parallel_events if not hasattr(e, 'has_ever_paused') or not e.has_ever_paused), None)
                if first_never_paused_event:
                    new_event = first_never_paused_event.do_next_thing(allow_pause = True)
                    if new_event:
                        self.events.append(new_event)
                        return True
                    if first_never_paused_event.done():
                        if first_never_paused_event.new_map_id:
                            self.transfer_player(first_never_paused_event)
                        if first_never_paused_event in self.parallel_events:
                            self.parallel_events.remove(first_never_paused_event)
                    return True

                first_has_paused_event = next((e for e in self.parallel_events if hasattr(e, 'has_ever_paused') and e.has_ever_paused and e.ready_to_continue()), None)
                if first_has_paused_event:
                    new_event = first_has_paused_event.do_next_thing(allow_pause = True)
                    if new_event:
                        self.events.append(new_event)
                        return True
                    if first_has_paused_event.done():
                        if first_has_paused_event.new_map_id:
                            self.transfer_player(first_has_paused_event)
                        else:
                            first_has_paused_event.list_index = 0
                            if not (hasattr(first_has_paused_event, 'press_count') and first_has_paused_event.press_count > 0):
                                first_has_paused_event.has_ever_paused = False
                            self.queue_parallel_events(keep_relevant_existing = True)
                    return True

            if self.requeue_parallel_events_if_changed():
                return True

            self.events = [e for e in [self.map.find_auto_trigger_event()] if e]
            if len(self.events) > 0:
                return True

            if hasattr(self, 'map_path') and len(self.map_path) > 0:
                self.player_x, self.player_y, self.player_direction = self.map_path.pop()
                self.queue_parallel_events(keep_relevant_existing = True)
                return True

            if hasattr(self, 'map_path_destination') and self.map_path_destination:
                x, y, self.player_direction = self.map_path_destination
                self.map_path_destination = None

                map_event = self.map.find_event_for_location(x, y) or self.map.find_event_for_location(x, y, only_special = True)
                if map_event:
                    self.events.append(map_event)
                else:
                    print "NO EVENT FOUND FOR %s, %s ???" % (x, y)
                return True

            self.process_move_routes()

            if keyed_common_event:
                common_event = self.common_events_data()[int(keyed_common_event)]
                self.events.append(GameEvent(self, common_event, common_event))
                return True

            if keyed_function_call:
                getattr(self, keyed_function_call)()
                return True

            if rpgm_game_data.get('has_dpad_animations', None) and not mapdest:
                if len(self.shown_pictures) > 0 and self.map.surrounded_by_events(self.player_x, self.player_y):
                    mapdest = MapClickable(
                        self.player_x + 1,
                        self.player_y
                    )
                    self.flush_queued_pictures()
                    renpy.pause()

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
                    if hasattr(mapdest, 'teleport'):
                        self.player_x, self.player_y = mapdest.x, mapdest.y
                    elif hasattr(mapdest, 'reachable') and mapdest.reachable and not self.everything_is_reachable():
                        reachability_grid = self.map.reachability_grid_for_current_position()

                        path_from_destination = None
                        preferred_approach_direction = map_event.preferred_approach_direction()
                        if preferred_approach_direction:
                            delta_x, delta_y = GameDirection.delta_for_direction(GameDirection.reverse_direction(preferred_approach_direction))
                            adjacent_x, adjacent_y, adjacent_direction = mapdest.x + delta_x, mapdest.y + delta_y, preferred_approach_direction
                            if reachability_grid[adjacent_y][adjacent_x] == 3:
                                path_from_adjacent_square = self.map.path_from_destination(self.player_x, self.player_y, adjacent_x, adjacent_y) or []
                                path_from_destination = [(mapdest.x, mapdest.y, preferred_approach_direction)] + path_from_adjacent_square

                        if not path_from_destination:
                            path_from_destination = self.map.path_from_destination(self.player_x, self.player_y, mapdest.x, mapdest.y)
                        adjacent_x, adjacent_y, adjacent_direction = path_from_destination[0]
                        self.map_path_destination = (mapdest.x, mapdest.y, adjacent_direction)
                        if map_event.page['through'] or (map_event.page['priorityType'] != 1 and not self.map.is_impassible(mapdest.x, mapdest.y, adjacent_direction)):
                            self.map_path = path_from_destination
                        else:
                            self.map_path = path_from_destination[1:-1]
                    else:
                        self.player_direction = self.determine_direction(mapdest.x, mapdest.y)
                        if map_event.page['through'] or map_event.page['trigger'] != 0:
                            self.player_x, self.player_y = mapdest.x, mapdest.y
                        else:
                            first_open_square = self.map.first_open_adjacent_square(mapdest.x, mapdest.y)
                            if first_open_square:
                                self.player_x, self.player_y = first_open_square

                if not hasattr(self, 'map_path_destination') or self.map_path_destination == None:
                    self.events.append(map_event)
                if debug_events:
                    print "DEBUG_EVENTS: %d,%d" % (mapdest.x, mapdest.y)
                return True

            return False

        def user_map_zoom(self):
            if not hasattr(self, 'user_map_zoom_factor'):
                self.user_map_zoom_factor = 1
            return self.user_map_zoom_factor

        def reset_user_zoom(self):
            self.user_map_zoom_factor = 1
            viewport_xadjustment.set_value(0)
            viewport_yadjustment.set_value(0)

        def zoom_in(self):
            if not hasattr(self, 'user_map_zoom_factor'):
                self.user_map_zoom_factor = 1
            self.set_user_map_zoom(self.user_map_zoom_factor * 1.5)

        def zoom_out(self):
            if not hasattr(self, 'user_map_zoom_factor'):
                self.user_map_zoom_factor = 1
            new_user_zoom = max(self.user_map_zoom_factor * (1 / 1.5), 1)
            self.set_user_map_zoom(new_user_zoom)

        def set_player_direction(self, direction):
            self.player_direction = direction

        def set_user_map_zoom(self, new_map_zoom_factor):
            map_zoom_ratio = new_map_zoom_factor / self.user_map_zoom_factor

            mousepos = renpy.get_mouse_pos()
            x_zoom_offset = mousepos[0]
            y_zoom_offset = mousepos[1]

            new_full_zoom = new_map_zoom_factor * self.calculate_map_factor()
            existing_x_value = viewport_xadjustment.get_value()
            new_range = (new_full_zoom * self.map.image_width) - config.screen_width
            new_value = ((existing_x_value + x_zoom_offset) * map_zoom_ratio) - x_zoom_offset
            viewport_xadjustment.set_range(new_range if new_range > 0 else 0.0)
            viewport_xadjustment.set_value(new_value if new_value > 0 else 0.0)

            existing_y_value = viewport_yadjustment.get_value()
            new_range = (new_full_zoom * self.map.image_height) - config.screen_height
            new_value = ((existing_y_value + y_zoom_offset) * map_zoom_ratio) - y_zoom_offset
            viewport_yadjustment.set_range(new_range if new_range > 0 else 0.0)
            viewport_yadjustment.set_value(new_value if new_value > 0 else 0.0)

            self.user_map_zoom_factor = new_map_zoom_factor

        def calculate_map_factor(self):
            width, height = (self.map.image_width, self.map.image_height)
            map_width = width
            map_height = height

            screen_width_sans_scrollbar = config.screen_width - 12
            screen_height_sans_scrollbar = config.screen_height - 12

            width_ratio = screen_width_sans_scrollbar / float(map_width)
            height_ratio = screen_height_sans_scrollbar / float(map_height)

            if width_ratio >= 1:
                x_offset = (screen_width_sans_scrollbar - map_width) // 2
                if height_ratio >= 1:
                    # Image smaller than screen, show in native size
                    return 1
                else:
                    # Image too tall, shrink to fit
                    return float(screen_height_sans_scrollbar) / map_height
            else:
                if height_ratio >= 1:
                    # Image too wide, shrink to fit
                    return float(screen_width_sans_scrollbar) / map_width
                else:
                    # Image overflowing in both dimensions
                    if width_ratio > height_ratio:
                        # Overflowing more on map_height
                        return float(screen_height_sans_scrollbar) / map_height
                    else:
                        # Overflowing more on map_width
                        return float(screen_width_sans_scrollbar) / map_width

        def sprite_images_and_positions(self):
            result = []
            for sprite_data in self.map.sprites():
                x, y, img = sprite_data[0:3]
                screen_x = x * rpgm_metadata.tile_width
                screen_y = y * rpgm_metadata.tile_height
                if len(sprite_data) > 3:
                    pw, ph, shift_y = sprite_data[3:6]
                    screen_x += (rpgm_metadata.tile_width / 2) - (pw / 2)
                    screen_y += (rpgm_metadata.tile_height) - (ph + shift_y)
                result.append({
                    'img': img,
                    'x': int(screen_x),
                    'y': int(screen_y)
                })
            return result

        def show_map(self, in_interaction = False):
            coordinates = []
            curated_clickables = []
            if not in_interaction:
                self.flush_queued_pictures()
                coordinates = self.map.map_options(self.player_x, self.player_y)
                if GameIdentifier().is_milfs_control() and GameSpecificCodeMilfsControl().has_curated_clickables(self.map.map_id):
                    curated_clickables = GameSpecificCodeMilfsControl().curated_clickables(coordinates, self.map.map_id)
                    coordinates = []
                else:
                    if not game_state.everything_is_reachable():
                        self.map.assign_reachability(self.player_x, self.player_y, coordinates)
                    if hide_unreachable_events:
                        coordinates = [map_clickable for map_clickable in coordinates if map_clickable.reachable]
                    if not show_noop_events:
                        coordinates = [map_clickable for map_clickable in coordinates if not hasattr(map_clickable, 'has_commands') or map_clickable.has_commands]

            x_offset = 0
            y_offset = 0
            mapfactor = 1

            background_image = self.map.background_image()
            parallax_image = self.map.parallax_image()
            width, height = (self.map.image_width, self.map.image_height)

            if self.map.is_clicky(self.player_x, self.player_y):
                # assume we want to show about 40 tiles wide, 22 tiles high
                # player x, y should be centered in the visible map
                # if they are greater than (19, 12)

                # image_height and image_width don't consider parts of the image on the bottom/right
                # that might not have any tiles; we need to consider the full map width when positioning
                # events on the screen for clicky scenarios
                width = self.map.width() * rpgm_metadata.tile_width
                height = self.map.height() * rpgm_metadata.tile_height

                mapfactor = 0.65

                new_x_range = (mapfactor * width) - config.screen_width
                viewport_xadjustment.set_range(new_x_range if new_x_range > 0 else 0.0)
                new_y_range = (mapfactor * height) - config.screen_height
                viewport_yadjustment.set_range(new_y_range if new_y_range > 0 else 0.0)

                # if there is more screen real-estate available than map, center the map in the screen
                # see Game_Map.prototype.setDisplayPos
                x_tiles_in_screen = config.screen_width / (rpgm_metadata.tile_width * mapfactor)
                if self.map.width() < x_tiles_in_screen:
                    x_offset = int(((x_tiles_in_screen - self.map.width()) / 2.0) * rpgm_metadata.tile_width)
                y_tiles_in_screen = config.screen_height / (rpgm_metadata.tile_height * mapfactor)
                if self.map.height() < y_tiles_in_screen:
                    y_offset = int(((y_tiles_in_screen - self.map.height()) / 2.0) * rpgm_metadata.tile_height)

                if self.player_x > 19:
                    new_x_value = int((self.player_x - 19) * rpgm_metadata.tile_width * mapfactor)
                    viewport_xadjustment.set_value(new_x_value)
                if self.player_y > 12:
                    new_y_value = int((self.player_y - 12) * rpgm_metadata.tile_height * mapfactor)
                    viewport_yadjustment.set_value(new_y_value)
                background_image = None
            else:
                mapfactor = self.calculate_map_factor()

            hud_pics = self.orange_hud_pictures()
            hud_lines = self.orange_hud_lines()
            hud_groups = self.orange_hud_groups()

            if not in_interaction and draw_impassible_tiles:
                impassible_tiles=self.map.impassible_tiles()
            else:
                impassible_tiles = []

            switch_toggler_buttons = []

            common_event_queuers = []
            if GameIdentifier().is_milfs_villa() and not in_interaction:
                common_event_queuers.append({"text": 'Combine Items', "event_id": 1, "ypos": 140})
            if GameIdentifier().is_my_summer() and self.switches.value(1) == True:
                common_event_queuers.append({"text": 'Show Status', "event_id": 1, "ypos": 100})

            key_paused_events = []
            has_paused_events = False
            if hasattr(self, 'parallel_events'):
                has_paused_events = any(e for e in game_state.parallel_events if hasattr(e, 'paused') and e.paused > 0)
                for e in self.parallel_events:
                    if hasattr(e, 'paused_for_key') and e.paused_for_key:
                        key_paused_events.append({
                            "text": ("Press %s" % e.paused_for_key),
                            "key": e.paused_for_key
                        })
            if not has_paused_events and hasattr(self, 'move_routes') and len(self.move_routes) > 0:
                has_paused_events = any(e for e in game_state.move_routes if hasattr(e, 'paused') and e.paused > 0)

            active_timer = None
            if hasattr(self, 'timer') and self.timer.active and self.timer.frames > 0:
                active_timer = {
                    "text": "Finish %ss timer" % self.timer.seconds()
                }

            renpy.show_screen(
                "mapscreen",
                _layer="maplayer",
                mapfactor=mapfactor * self.user_map_zoom(),
                coords=coordinates,
                curated_clickables=curated_clickables,
                player_position=(self.player_x, self.player_y),
                hud_pics=hud_pics,
                hud_lines=hud_lines,
                hud_groups=hud_groups,
                map_name=self.map.name(),
                sprites=None,
                sprite_images_and_positions=self.sprite_images_and_positions(),
                impassible_tiles=impassible_tiles,
                common_events_keymap=self.common_events_keymap(),
                function_calls_keymap=self.function_calls_keymap(),
                background_image=background_image,
                parallax_image=parallax_image,
                width=width,
                height=height,
                child_size=(width, height),
                viewport_xadjustment=viewport_xadjustment,
                viewport_yadjustment=viewport_yadjustment,
                x_offset=x_offset,
                y_offset=y_offset,
                in_interaction=in_interaction,
                switch_toggler_buttons=switch_toggler_buttons,
                common_event_queuers=common_event_queuers,
                has_paused_events=has_paused_events,
                key_paused_events=key_paused_events,
                active_timer=active_timer,
            )
