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
            else:
                raise(RuntimeError("Unknown direction! %s" % direction))

        @classmethod
        def random_direction(cls):
            return random.choice([GameDirection.UP, GameDirection.DOWN, GameDirection.LEFT, GameDirection.RIGHT])

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

    class YepRegionRestrictions(object):
        def __init__(self, data):
            self.data = data
            self.player_restrict = int(data["Player Restrict"])
            self.all_restrict = int(data["All Restrict"])
            self.player_allow = int(data["Player Allow"])
            self.all_allow = int(data["All Allow"])
            self.player_restricted_regions = [r_id for r_id in [self.player_restrict, self.all_restrict] if r_id != 0]
            self.player_allowed_regions = [r_id for r_id in [self.player_allow, self.all_allow] if r_id != 0]

    class GameState(SelectivelyPickle):
        def __init__(self):
            self.common_events_index = None
            self.events = []
            self.parallel_events = []
            self.starting_map_id = self.system_data()['startMapId']
            self.map_registry = GameMapRegistry(self)
            self.map = self.map_registry.get_map(self.starting_map_id)
            self.player_x = self.system_data()['startX']
            self.player_y = self.system_data()['startY']
            self.player_direction_fix = False
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
            self.focus_zoom_rect_on_next_map_render = True

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

        def flush_queued_content(self):
            self.flush_queued_pictures()
            self.flush_queued_sound()

        def queue_background_music(self, name, volume = None):
            if debug_sound:
                print "QUEUE BG MUSIC: %s" % name
            if not name or len(name) == 0:
                self.next_background_music = {'name': None}
            else:
                self.next_background_music = {'name': name, 'volume': volume}

        def queue_background_sound(self, name, volume = None):
            if debug_sound:
                print "QUEUE BG SOUND: %s" % name
            if not name or len(name) == 0:
                self.next_background_sound = {'name': None}
            else:
                self.next_background_sound = {'name': name, 'volume': volume}

        def queue_sound_effect(self, name, volume = None):
            if debug_sound:
                print "QUEUE SOUND EFFECT: %s" % name
            if not name:
                self.next_sound_effect = {'name': None}
            else:
                self.next_sound_effect = {'name': name, 'volume': volume}

        def flush_queued_sound(self):
            if not hasattr(self, 'next_background_music'):
                self.next_background_music = None
            if not hasattr(self, 'next_background_sound'):
                self.next_background_sound = None
            if not hasattr(self, 'next_sound_effect'):
                self.next_sound_effect = None
            if not hasattr(self, 'current_background_music'):
                self.current_background_music = None
            if not hasattr(self, 'current_background_sound'):
                self.current_background_sound = None

            if debug_sound:
                if self.next_background_music:
                    print "FLUSH BG MUSIC!! %s, %s" % (self.current_background_music, self.next_background_music)
                if self.next_background_sound:
                    print "FLUSH BG SOUND!! %s, %s" % (self.current_background_music, self.next_background_music)
                if self.next_sound_effect:
                    print "FLUSH SOUND EFFECT!! %s" % (self.next_sound_effect)

            if self.next_background_music:
                if self.next_background_music['name']:
                    if self.current_background_music and self.current_background_music['name'] == self.next_background_music['name']:
                        renpy.music.set_volume(self.next_background_music['volume'] / 100.0, channel = 'music')
                    else:
                        self.play_on_channel(rpgm_metadata.background_music_path, self.next_background_music, 'music')
                else:
                    renpy.music.stop(channel = 'music')
                self.current_background_music = self.next_background_music
            self.next_background_music = None

            if self.next_background_sound:
                if self.next_background_sound['name']:
                    if self.current_background_sound and self.current_background_sound['name'] == self.next_background_sound['name']:
                        renpy.music.set_volume(self.next_background_sound['volume'] / 100.0, channel = 'background_sound')
                    else:
                        self.play_on_channel(rpgm_metadata.background_sound_path, self.next_background_sound, 'background_sound')
                else:
                    renpy.music.stop(channel = 'background_sound')
                self.current_background_sound = self.next_background_sound
            self.next_background_sound = None

            if self.next_sound_effect:
                if self.next_sound_effect['name']:
                    self.play_on_channel(rpgm_metadata.sound_effects_path, self.next_sound_effect, 'sound')
                else:
                    renpy.music.stop(channel = 'sound')
                self.next_sound_effect = None

        def play_on_channel(self, sound_path, sound_data, channel):
            filenames = glob.glob(os.path.join(config.basedir, sound_path, sound_data['name'] + '.*'))
            if len(filenames) > 0:
                renpy.music.set_volume(sound_data['volume'] / 100.0, channel = channel)
                renpy.music.play(filenames[0].replace('\\', '/'), channel = channel)

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
                return 0

            longest_animation = 0

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
                    "final_size": last_frame.get('final_size', None) or last_frame.get('size', None),
                    "opacity": picture_frames[-1].get('opacity', 255),
                    "size": None
                }
                if len(picture_frames) == 1:
                    picture_args['image_name'] = RpgmAnimationBuilder.image_for_picture(picture_frames[0])
                else:
                    should_loop = 'loop' in last_frame and last_frame['loop']
                    picture_transitions = RpgmAnimationBuilder(picture_frames).build(loop = should_loop)
                    picture_args['image_name'] = RpgmAnimation.create(*picture_transitions, anim_timebase = True)
                    longest_animation = max(longest_animation, sum(picture_args['image_name'].delays))
                self.shown_pictures[picture_id] = picture_args

            self.queued_pictures = []

            return longest_animation

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
            return game_file_loader.json_file(rpgm_data_path("System.json"))

        def common_events_data(self):
            return game_file_loader.json_file(rpgm_data_path("CommonEvents.json"))

        def tilesets(self):
            return game_file_loader.json_file(rpgm_data_path("Tilesets.json"))

        def plugins(self):
            return game_file_loader.plugins_json()

        def escape_text_for_renpy(self, text):
            escaped_text = re.sub('%', '%%', text)
            escaped_text = re.sub('\[', '[[', escaped_text)
            return re.sub('\{', '{{', escaped_text)

        def replace_names(self, text):
            # Replace statements from actor numbers, e.g. \N[2] with their actor name
            text = re.sub(r'\\N\[(\d+)\]', lambda m: (self.actors.actor_name(int(m.group(1)))), text, flags=re.IGNORECASE)
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

        def yep_region_restriction_data(self):
            if hasattr(self, '_yep_region_restriction_data'):
                return self._yep_region_restriction_data

            region_restriction_data = game_file_loader.plugin_data_exact('YEP_RegionRestrictions')
            if region_restriction_data:
                self._yep_region_restriction_data = region_restriction_data['parameters']
            else:
                self._yep_region_restriction_data = None
            return self._yep_region_restriction_data

        def yep_region_restrictions(self):
            if hasattr(self, '_yep_region_restrictions'):
                return self._yep_region_restrictions

            yep_region_restriction_data = self.yep_region_restriction_data()
            if not yep_region_restriction_data:
                return None

            self._yep_region_restrictions = YepRegionRestrictions(yep_region_restriction_data)
            return self._yep_region_restrictions

        def orange_hud_group_map(self):
            if hasattr(self, '_orange_hud_group_map'):
                return self._orange_hud_group_map

            plugins = self.plugins()
            group_data_list = [plugin_data for plugin_data in plugins if plugin_data['name'].startswith('OrangeHudGroup')]

            groups = {}
            for group_data in group_data_list:
                groups[group_data['parameters']['GroupName']] = group_data
            main_group = game_file_loader.plugin_data_exact('OrangeHud')
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

                    pics.append({
                        'X': x,
                        'Y': y,
                        'image': picture_name,
                        'size': image_size_cache.for_picture_name(picture_name)
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

        def srd_hud_lines(self, in_interaction = False):
            plugin = game_file_loader.plugin_data_exact('SRD_HUDMaker')
            if not plugin:
                return []

            if plugin['parameters']["Show During Events"] == 'hide' and in_interaction:
                return []

            hud_items = game_file_loader.json_file(rpgm_data_path("MapHUD.json"))
            lines = []
            for hud_item in hud_items:
                if hud_item['type'] in ['Text', 'Gauge']:
                    if len(hud_item['Condition']) > 0 and not self.eval_fancypants_value_statement(hud_item['Condition']):
                        continue

                    if hud_item['type'] == 'Gauge':
                        value = "%s / %s" % (
                            self.eval_fancypants_value_statement(hud_item['Cur. Value']),
                            hud_item['Max Value']
                        )
                        x = hud_item['x'] - int(hud_item['Width']) // 2
                        y = hud_item['y']
                    else:
                        value = hud_item['Value']
                        x = hud_item['x'] - int(hud_item['Max Width']) // 2
                        y = hud_item['y']

                        result_parts = []
                        interpolation_start = None
                        left_braces = None
                        string_index = 0
                        while string_index < len(value):
                            if value[string_index:string_index+2] == '${':
                                left_braces = 1
                                string_index = string_index + 1
                                interpolation_start = string_index + 1
                            elif value[string_index] == '{':
                                if left_braces != None:
                                    left_braces = left_braces + 1
                            elif value[string_index] == '}':
                                if left_braces != None:
                                    left_braces = left_braces - 1
                                if left_braces == 0:
                                    script_string = value[interpolation_start:string_index]
                                    interpolation_start = None
                                    left_braces = None
                                    result_parts.append(str(self.eval_fancypants_value_statement(script_string)))
                            elif left_braces == None:
                                result_parts.append(value[string_index])
                            string_index = string_index + 1

                        value = ''.join(result_parts)

                    lines.append({
                        'layer': hud_item['Layer'],
                        'X': x,
                        'Y': y,
                        'text': self.escape_text_for_renpy(value)
                    })
            return sorted(lines, key=lambda p: int(p['layer']))

        def srd_hud_pictures(self, in_interaction = False):
            plugin = game_file_loader.plugin_data_exact('SRD_HUDMaker')
            if not plugin:
                return []

            if plugin['parameters']["Show During Events"] == 'hide' and in_interaction:
                return []

            hud_items = game_file_loader.json_file(rpgm_data_path("MapHUD.json"))
            pictures = []
            for hud_item in hud_items:
                if hud_item['type'] == 'Picture' or hud_item['type'] == 'Picture EX' or hud_item['type'] == 'Image Numbers':
                    if len(hud_item['Condition']) > 0 and not self.eval_fancypants_value_statement(hud_item['Condition']):
                        continue

                    image_name = hud_item['Image']
                    image_type_folder = 'pictures'
                    if hud_item['type'] == 'Picture EX':
                        image_name = self.eval_fancypants_value_statement(hud_item['Image'])
                    elif hud_item['type'] == 'Image Numbers':
                        image_type_folder = 'numbers'

                    hud_image_folder = rpgm_game_data.get('hud_image_folder', 'img/SumRndmDde/hud')
                    picture_path = game_file_loader.full_path_for_picture(rpgm_path('www/%s/%s/%s' % (hud_image_folder, image_type_folder, image_name)))
                    size = image_size_cache.for_path(picture_path)
                    if hud_item['type'] == 'Image Numbers':
                        size = (size[0] // 10, size[1])
                        value = self.eval_fancypants_value_statement(hud_item['Value'])
                        image = im.Crop(picture_path, (size[0] * value, 0, size[0], size[1]))
                    else:
                        image = picture_path

                    if hud_item['Scale X'] != '1' or hud_item['Scale Y'] != '1':
                        size = (int(float(hud_item['Scale X']) * size[0]), int(float(hud_item['Scale Y']) * size[1]))

                    picture_data = {
                        'layer': hud_item['Layer'],
                        'X': hud_item['x'] - size[0] // 2,
                        'Y': hud_item['y'] - size[1] // 2,
                        'image': image,
                        'size': size
                    }

                    if hud_item['Scale X'] == '-1':
                        picture_data['image'] = im.Flip(picture_data['image'], horizontal = True)

                    pictures.append(picture_data)

            return sorted(pictures, key=lambda p: int(p['layer']))

        def ysp_videos(self):
            if not hasattr(self, 'ysp_video_data'):
                self.ysp_video_data = YspVideoData()
            return self.ysp_video_data

        def eval_fancypants_value_statement(self, script_string):
            gre = Re()
            if gre.match('\$gameActors\.actor\((\d+)\)\.name\(\)', script_string):
                return self.actors.actor_name(int(gre.last_match.groups()[0]))
            elif gre.match('\$gameActors\.actor\((\d+)\)\.nickname\(\)', script_string):
                return self.actors.by_index(int(gre.last_match.groups()[0])).get_property('nickname')

            while True:
                variables_regexp = r'\$gameVariables.value\((\d+)\)'
                still_has_variables = re.search(variables_regexp, script_string)
                if still_has_variables:
                    only_this_variable_remained = gre.match(variables_regexp, script_string)
                    if only_this_variable_remained:
                        return self.variables.value(int(gre.last_match.groups()[0]))
                    script_string = re.sub(variables_regexp, lambda m: str(self.variables.value(int(m.group(1)))), script_string)
                else:
                    break

            while True:
                still_has_switches = re.search('\$gameSwitches.value\((\d+)\)', script_string)
                if still_has_switches:
                    script_string = re.sub(r'\$gameSwitches.value\((\d+)\)', lambda m: str(self.switches.value(int(m.group(1)))), script_string)
                else:
                    break

            script_string = re.sub(r'\btrue\b', 'True', script_string)
            script_string = re.sub(r'\bfalse\b', 'False', script_string)
            script_string = re.sub(r'===', '==', script_string)
            script_string = re.sub(r'&&', ' and ', script_string)
            script_string = re.sub(r'\|\|', ' or ', script_string)

            if gre.match('"([^"]+)"', script_string):
                return gre.last_match.groups()[0]
            elif gre.match("'([^']+)'", script_string):
                return gre.last_match.groups()[0]

            # eval the statement in python-land if it looks like it contains only arithmetic expressions
            if re.match('^([\d\s.+\-*<>=()\s]|True|False|and|or)+$', script_string):
                return eval(script_string)
            else:
                renpy.say(None, "Remaining non-evaluatable fancypants value statement: '%s'" % script_string)
                print "Remaining non-evaluatable fancypants value statement:"
                print "'%s'" % script_string
                return 0

        def common_events_keymap(self):
            yepp_common_events = game_file_loader.plugin_data_exact('YEP_ButtonCommonEvents')
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
            if game_file_loader.plugin_data_exact('Galv_QuestLog'):
                result.append(('q', 'show_galv_quests'))
            elif game_file_loader.plugin_data_exact('YEP_QuestJournal'):
                result.append(('q', 'show_yep_quests'))
            elif game_file_loader.plugin_data_exact('GameusQuestSystem'):
                result.append(('q', 'show_gameus_quests'))
            elif rpgm_game_data.get('maic_quests', None):
                result.append(('q', 'show_maic_quests'))
            elif rpgm_game_data.get('molegato_quests', None):
                result.append(('q', 'show_molegato_quests'))
            return result

        def queue_common_and_parallel_events(self):
            if len(self.common_events_data()) > 0:
                self.common_events_index = 1
            self.queue_parallel_events()

        def queue_parallel_events(self, keep_relevant_existing = True, only_if_conditionals = False):
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

            if only_if_conditionals:
                if not any([e for e in new_parallel_events if self.map.has_conditional(e.page)]):
                    new_parallel_events = []

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
            self.events.append(GameEvent(self, None, common_event, common_event))
            return True

        def show_molegato_quests(self):
            unsolved_quests = []
            solved_quests = []
            for quest in rpgm_game_data['molegato_quests']:
                var_value = game_state.variables.value(quest['var'])
                if var_value >= 3:
                    solved_quests.insert(0, quest)
                elif var_value >= 1:
                    unsolved_quests.append(quest)
            result = renpy.call_screen('molegato_quests_screen', unsolved_quests, solved_quests)
            return True

        def show_maic_quests(self):
            scrubbed_quest_data = []
            for quest in self.party.maic_quest_manager().quest_data():
                quest_copy = quest.copy()
                quest_copy['description'] = "\n".join([line.strip() for line in quest_copy['description'].split("\n")])
                scrubbed_quest_data.append(quest_copy)
            result = renpy.call_screen('maic_quests_screen', scrubbed_quest_data)
            return True

        def show_galv_quests(self):
            result = renpy.call_screen('galv_quests_screen', self.party.galv_quest_manager().presented_quests())
            return True

        def show_yep_quests(self):
            result = renpy.call_screen('yep_quests_screen', self.party.yep_quest_manager().presented_quests())
            return True

        def show_gameus_quests(self):
            result = renpy.call_screen('gameus_quests_screen', self.party.gameus_quest_manager().presented_quests())
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
                recipe_match = re.match('<Item Recipe: ([\d+\s,]+)>', item['note'])
                if recipe_match:
                    for recipe_item_part in recipe_match.groups()[0].split(','):
                        recipe_item_id = int(recipe_item_part)
                        if recipe_item_id not in recipes:
                            recipes.append(recipe_item_id)

            synthesizables = []
            for item_id in recipes:
                item = self.items.by_id(item_id)
                items_and_counts = self.synthesis_ingredients(item)
                if items_and_counts:
                    has_all = True
                    tooltip_lines = []
                    for (item_id, count) in items_and_counts:
                        ingredient_item = self.items.by_id(item_id)
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
                    item_desc, count_str = ingredient.split(": ")
                    gre = Re()
                    if gre.match('item (\d+)', item_desc):
                        items_and_count.append((int(gre.last_match.groups()[0]), int(count_str)))
                    else:
                        ingredient_item = self.items.by_name(item_desc)
                        if ingredient_item:
                            items_and_count.append((ingredient_item['id'], int(count_str)))
                return items_and_count
            return None

        def synthesize_item(self, item):
            for (item_id, count) in self.synthesis_ingredients(item):
                ingredient_item = self.items.by_id(item_id)
                self.party.gain_item(ingredient_item, -1)
            self.party.gain_item(item, 1)

        def determine_direction(self, new_x, new_y):
            if new_y > self.player_y:
                return GameDirection.DOWN
            else:
                return GameDirection.UP

        def skip_bad_events(self):
            switch_triggers = rpgm_game_data.get('switch_triggers', None)
            if GameIdentifier().is_milfs_villa():
                if self.map.map_id == 64 and not self.self_switches.value((64, 1, "B")):
                    self.self_switches.set_value((64, 1, "A"), True)
                    self.self_switches.set_value((64, 1, "B"), True)
                if self.map.map_id == 27 and self.switches.value(129) == True and not self.self_switches.value((27, 14, "B")):
                    self.self_switches.set_value((27, 14, "A"), True)
                    self.self_switches.set_value((27, 14, "B"), True)
            elif GameIdentifier().is_visiting_sara():
                # Near the end, you have to push a box a very long way.
                # The engine is almost capable of doing this, but why bother.
                if self.map.map_id == 4 and self.switches.value(132) == True and not self.switches.value(133) == True:
                    self.switches.set_value(133, True)
            elif switch_triggers:
                triggers_for_map = switch_triggers.get(str(self.map.map_id))
                if not triggers_for_map:
                    return

                for trigger in triggers_for_map:
                    if 'activation_switch' in trigger:
                        activation_switches = [trigger['activation_switch']]
                    else:
                        activation_switches = trigger.get('activation_switches', [])

                    if any(self.switches.value(id) == True for id in activation_switches) or any(self.self_switches.value(tuple(id)) for id in trigger.get('activation_self_switches', [])):
                        for switch_id in trigger.get('switches_off', []):
                            self.switches.set_value(switch_id, False)
                        for self_switch_id in trigger.get('self_switches_off', []):
                            self.self_switches.set_value(tuple(self_switch_id), False)
                        for switch_id in trigger.get('switches_on', []):
                            self.switches.set_value(switch_id, True)
                        for self_switch_id in trigger.get('self_switches_on', []):
                            self.self_switches.set_value(tuple(self_switch_id), True)
                        for variable_id, value in trigger.get('variables', []):
                            self.variables.set_value(variable_id, value)

        def set_side_image(self, face_name, face_index):
            game_state.rpgm_bust_image = None
            if face_name and len(face_name) > 0:
                side_image_size = None
                if rpgm_metadata.is_pre_mv_version:
                    side_image_size = 96
                else:
                    side_image_size = 144

                game_state.rpgm_side_image = im.Crop(
                    face_images[rpgm_face_name(face_name)],
                    (
                        (face_index % 4) * side_image_size,
                        (face_index / 4) * side_image_size,
                        side_image_size,
                        side_image_size
                    )
                )
            else:
                game_state.rpgm_side_image = None

        def set_bust_image(self, face_name, face_index):
            game_state.rpgm_side_image = None
            game_state.rpgm_bust_image = None
            if face_name and len(face_name) > 0:
                image_name = rpgm_picture_name(face_name) + '_' + str(face_index + 1)
                if image_name in normal_images:
                    game_state.rpgm_bust_image = normal_images[image_name]

        def say_text_with_possible_speaker(self, text, face_name, face_index):
            gre = Re()
            if gre.match(re.compile("([^\n]+?):\s\s*(.+)", re.DOTALL), text):
                speaker, spoken_text = gre.last_match.groups()
                if len(speaker) < 60:
                    return self.say_text(speaker, spoken_text, face_name, face_index)

            self.say_text(None, text, face_name, face_index)

        def say_text(self, speaker, spoken_text, face_name = None, face_index = None):
            self.show_map(True)
            gre = Re()
            if game_file_loader.plugin_data_exact('GALV_MessageBusts'):
                all_busty_text = []
                busty_text = spoken_text
                bust_index = face_index
                while gre.search("(.*?)\\\\BST\[\[(\d+)](.*)", busty_text):
                    self.set_bust_image(face_name, bust_index)
                    before_bust_change, bust_index, after_bust_change = gre.last_match.groups()
                    bust_index = int(bust_index) - 1
                    all_busty_text.append(before_bust_change)
                    renpy.say(speaker, ' '.join(all_busty_text))
                    busty_text = after_bust_change
                self.set_bust_image(face_name, bust_index)
                all_busty_text.append(busty_text)
                self.last_said_text = ' '.join(all_busty_text)
                renpy.say(speaker, ' '.join(all_busty_text))
            else:
                self.set_side_image(face_name, face_index)
                if game_file_loader.plugin_data_exact('GALV_TimedMessagePopups') and gre.search("<c:.*?>(.*)", spoken_text):
                    # EX: "<c:800|800,90,0>\\C[11]\\fb   YOU HAVE MET JANE   "
                    notification_text = gre.last_match.groups()[0]
                    renpy.notify(notification_text)
                else:
                    self.last_said_text = spoken_text
                    renpy.say(speaker, spoken_text)

        def pause(self):
            self.flush_queued_content()
            self.show_map(True)
            renpy.pause()

        def set_game_start_events(self):
            self.events = [e for e in [self.map.find_auto_trigger_event()] if e]
            if len(self.events) == 0:
                self.queue_parallel_events()

        def set_player_direction(self, new_direction):
            if not hasattr(self, 'player_direction_fix') or self.player_direction_fix == False:
                self.player_direction = new_direction

        def cancel_map_path_walk(self):
            self.map_path = []
            self.map_path_destination = None

        def transfer_player(self, transfer_event):
            self.cancel_map_path_walk()
            changing_maps = transfer_event.new_map_id != self.map.map_id
            if noisy_events:
                print "TRANSFERRING PLAYER TO MAP %s: (%s, %s)" % (transfer_event.new_map_id, transfer_event.new_x, transfer_event.new_y)
            if changing_maps:
                self.reset_user_zoom()
                self.focus_zoom_rect_on_next_map_render = True
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
            self.events.append(GameEvent(self, None, common_event, common_event))

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

        def requeue_parallel_events_if_changed(self, always_run_conditionals = False):
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
                if always_run_conditionals and any([len(page_data) > 2 and page_data[2] == True for page_data in current_parallel_event_pages]):
                    self.queue_parallel_events(keep_relevant_existing = True, only_if_conditionals = True)
                    return True

        def unpaused_parallel_events(self):
            if hasattr(self, 'parallel_events') and len(self.parallel_events) > 0:
                return [e for e in self.parallel_events if (not hasattr(e, 'paused') or e.paused == 0) and not hasattr(e, 'paused_for_key')]
            else:
                return []

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
                        if self.map.interesting_move_route(page['moveRoute']):
                            page_index = (len(e['pages']) - 1) - reverse_page_index
                            event = self.paused_move_route_at_page(e['id'], page_index)
                            if not event:
                                event = GameEvent(self, self.map.map_id, e, page, page_index)
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

            if len(self.events) > 0:
                self.previous_parallel_event_pages = []

                this_event = self.events[-1]
                new_event = this_event.do_next_thing()
                if new_event:
                    if len(self.events) >= 50:
                        raise RuntimeError("Event stack too big!")
                    self.events.append(new_event)
                    return True
                if hasattr(self, 'shop_params') and self.shop_params:
                    self.show_shop_ui()
                    return True
                if this_event.new_map_id:
                    self.transfer_player(this_event)
                    this_event.new_map_id = None
                if this_event.done():
                    self.events.pop()
                    if len(self.events) == 0 and self.common_events_index == None and len(self.unpaused_parallel_events()) == 0:
                        self.flush_queued_pictures()
                        self.show_map(True)
                        self.queue_common_and_parallel_events()
                if this_event.common() and hasattr(this_event, 'paused_for_key') and this_event.paused_for_key:
                    # Ignore common events that are waiting on keypress, for now.
                    self.events.pop()
                return True

            if self.common_events_index != None and self.common_events_index < len(self.common_events_data()):
                for event in xrange(self.common_events_index, len(self.common_events_data())):
                    common_event = self.common_events_data()[self.common_events_index]
                    self.common_events_index += 1
                    if common_event['id'] in rpgm_game_data.get('erased_common_events', []):
                        continue
                    if common_event['trigger'] > 0 and self.switches.value(common_event['switchId']) == True:
                        self.events.append(GameEvent(self, None, common_event, common_event))
                        return True
            self.common_events_index = None

            if self.requeue_parallel_events_if_changed():
                return True

            self.events = [e for e in [self.map.find_auto_trigger_event()] if e]
            if len(self.events) > 0:
                self.cancel_map_path_walk()
                return True

            if hasattr(self, 'map_path') and len(self.map_path) > 0:
                self.player_x, self.player_y, new_direction = self.map_path.pop()
                self.set_player_direction(new_direction)
                self.requeue_parallel_events_if_changed(always_run_conditionals = True)
                return True

            if hasattr(self, 'map_path_destination') and self.map_path_destination:
                x, y, new_direction = self.map_path_destination
                self.set_player_direction(new_direction)
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
                self.events.append(GameEvent(self, None, common_event, common_event))
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
                    self.pause()

            if mapdest:
                # convert old-style mapdests that were x, y tuples to MapClickable objects
                if not hasattr(mapdest, 'x'):
                    mapdest =  MapClickable(
                        mapdest[0],
                        mapdest[1]
                    )

                if mapdest.is_projectile_target():
                    map_event = self.map.find_event_for_location(mapdest.x, mapdest.y)
                    self.self_switches.set_value((self.map.map_id, map_event.event_data['id'], "A"), True)
                    self.queue_common_and_parallel_events()
                    return True

                if mapdest.is_walk_destination():
                    new_x, new_y = mapdest.x, mapdest.y
                    self.set_player_direction(self.determine_direction(new_x, new_y))
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
                            if hasattr(mapdest, 'reachable_via_counter'):
                                before_counter_x, before_counter_y = mapdest.reachable_via_counter
                                path_from_destination = self.map.path_from_destination(self.player_x, self.player_y, before_counter_x, before_counter_y)
                            else:
                                path_from_destination = self.map.path_from_destination(self.player_x, self.player_y, mapdest.x, mapdest.y)

                        adjacent_x, adjacent_y, adjacent_direction = path_from_destination[0]
                        self.map_path_destination = (mapdest.x, mapdest.y, adjacent_direction)

                        if hasattr(mapdest, 'reachable_via_counter') or map_event.page['through'] or (map_event.page['priorityType'] != 1 and not self.map.is_impassible(mapdest.x, mapdest.y, adjacent_direction)):
                            self.map_path = path_from_destination
                        else:
                            self.map_path = path_from_destination[1:-1]
                    else:
                        self.set_player_direction(self.determine_direction(mapdest.x, mapdest.y))
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

        def ensure_user_map_zoom_exists(self):
            if not hasattr(self, 'user_map_zoom_factor'):
                self.user_map_zoom_factor = 1

        def user_map_zoom(self):
            self.ensure_user_map_zoom_exists()
            return self.user_map_zoom_factor

        def reset_user_zoom(self):
            self.user_map_zoom_factor = 1
            viewport_xadjustment.set_value(0)
            viewport_yadjustment.set_value(0)

        def zoom_in(self):
            self.ensure_user_map_zoom_exists()
            self.set_user_map_zoom(self.user_map_zoom_factor * 1.5)

        def zoom_out(self):
            self.ensure_user_map_zoom_exists()
            new_user_zoom = max(self.user_map_zoom_factor * (1 / 1.5), 1)
            self.set_user_map_zoom(new_user_zoom)

        def go_direction(self, direction):
            self.set_player_direction(direction)
            reachability_grid = self.map.reachability_grid_for_current_position()
            delta = GameDirection.delta_for_direction(direction)
            new_x = self.player_x + delta[0]
            new_y = self.player_y + delta[1]
            if new_x >= 0 and new_y >= 0 and new_y < len(reachability_grid) and new_x < len(reachability_grid[new_y]) and reachability_grid[new_y][new_x] == 3:
                self.player_x = new_x
                self.player_y = new_y
                self.queue_common_and_parallel_events()

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

        def show_map(self, in_interaction = False, fade_map = False):
            coordinates = []
            curated_clickables = []
            if not in_interaction:
                self.flush_queued_content()
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
                        coordinates = [map_clickable for map_clickable in coordinates if not map_clickable.is_noop_event()]

            x_offset = 0
            y_offset = 0
            mapfactor = 1

            background_image = self.map.background_image()
            parallax_image = self.map.parallax_image()
            overlay_ground_image = self.map.overlay_image('ground')
            overlay_parallax_image = self.map.overlay_image('par')
            width, height = (self.map.image_width, self.map.image_height)
            map_zoom_rect = rpgm_game_data.get('map_zoom_rects', {}).get(str(self.map.map_id), None)

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
                self.reset_user_zoom()

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

                if map_zoom_rect and hasattr(self, 'focus_zoom_rect_on_next_map_render') and self.focus_zoom_rect_on_next_map_render:
                    zoom_rect_ul = (map_zoom_rect[0], map_zoom_rect[1])
                    zoom_rect_lr = (map_zoom_rect[2], map_zoom_rect[3])
                    rect_size = (zoom_rect_lr[0] - zoom_rect_ul[0], zoom_rect_lr[1] - zoom_rect_ul[1])
                    user_zoom = min(self.map.width() / float(rect_size[0]), self.map.height() / float(rect_size[1]))

                    # Don't zoom in so far that the pixels are bigger than their natural size
                    user_zoom = min(1 / mapfactor, user_zoom)

                    self.set_user_map_zoom(user_zoom)

                    centering_nudge_x = max(0, (config.screen_width - (rect_size[0] * rpgm_metadata.tile_width * mapfactor * user_zoom)) / 2)
                    centering_nudge_y = max(0, (config.screen_height - (rect_size[1] * rpgm_metadata.tile_height * mapfactor * user_zoom)) / 2)

                    viewport_xadjustment.set_value(max(0, (zoom_rect_ul[0] * rpgm_metadata.tile_width * mapfactor * user_zoom) - centering_nudge_x))
                    viewport_yadjustment.set_value(max(0, (zoom_rect_ul[1] * rpgm_metadata.tile_height * mapfactor * user_zoom) - centering_nudge_y))
                self.focus_zoom_rect_on_next_map_render = False

            hud_pics = self.orange_hud_pictures() + self.srd_hud_pictures(in_interaction = in_interaction)
            hud_lines = self.orange_hud_lines() + self.srd_hud_lines(in_interaction = in_interaction)
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

            galv_screen_buttons = self.galv_screen_buttons if hasattr(self, 'galv_screen_buttons') else {}

            paused_events = []
            key_paused_events = []
            if hasattr(self, 'parallel_events'):
                paused_events.extend([e for e in game_state.parallel_events if hasattr(e, 'paused') and e.paused > 0])
                for e in self.parallel_events:
                    if hasattr(e, 'paused_for_key') and e.paused_for_key:
                        key_paused_events.append({
                            "text": ("Press %s" % e.paused_for_key),
                            "key": e.paused_for_key
                        })
            if hasattr(self, 'move_routes') and len(self.move_routes) > 0:
                paused_events.extend([e for e in game_state.move_routes if hasattr(e, 'paused') and e.paused > 0])
            paused_events_delay = next((e.paused for e in sorted(paused_events, key=lambda e: e.paused)), None)

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
                fade_map=fade_map,
                map_name=self.map.name(),
                sprites=None,
                sprite_images_and_positions=self.sprite_images_and_positions(),
                impassible_tiles=impassible_tiles,
                common_events_keymap=self.common_events_keymap(),
                function_calls_keymap=self.function_calls_keymap(),
                background_image=background_image,
                overlay_ground_image=overlay_ground_image,
                overlay_parallax_image=overlay_parallax_image,
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
                galv_screen_buttons=galv_screen_buttons,
                has_paused_events=len(paused_events) > 0,
                paused_events_delay=paused_events_delay,
                key_paused_events=key_paused_events,
                active_timer=active_timer,
                event_timers=GalvEventSpawnTimers.event_timers(self.map),
                faded_out=hasattr(self, 'faded_out') and self.faded_out,
            )
