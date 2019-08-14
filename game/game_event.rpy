init python:
    class GameEvent:
        PROPERTY_CHARACTER_INDEX = 'characterIndex'
        PROPERTY_CHARACTER_NAME = 'characterName'
        PROPERTY_DIRECTION = 'direction'
        PROPERTY_DIRECTION_FIX = 'directionFix'
        PROPERTY_MOVE_FREQUENCY = 'moveFrequency'
        PROPERTY_MOVE_SPEED = 'moveSpeed'
        PROPERTY_PATTERN = 'pattern'
        PROPERTY_STEP_ANIME = 'stepAnime'
        PROPERTY_THROUGH = 'through'
        PROPERTY_TRANSPARENT = 'transparent'

        IMAGE_STORED_PROPERTIES = (
            PROPERTY_CHARACTER_INDEX,
            PROPERTY_CHARACTER_NAME,
            PROPERTY_DIRECTION,
            PROPERTY_PATTERN
        )

        def __init__(self, state, map_id, event_data, page, page_index = None):
            self.state = state
            self.map_id = map_id
            self.event_data = event_data
            self.page = page
            self.page_index = page_index
            self.list_index = 0
            self.move_route_index = 0
            self.new_map_id = None
            self.choices_to_hide = []
            self.choices_to_disable = []
            self.branch = {}

        @classmethod
        def page_solid(cls, event_data, page, page_index):
            return (page['priorityType'] == 1) and not game_state.map.event_page_property(event_data, page, page_index, GameEvent.PROPERTY_THROUGH)

        def common(self):
            return self.event_data.has_key('switchId')

        def parallel(self):
            return self.page['trigger'] == 4 or (self.common() and self.page['trigger'] == 2)

        def get_map_id(self):
            if hasattr(self, 'map_id') and self.map_id:
                return self.map_id
            return self.state.map.map_id

        def slowmo_map(self):
            return self.get_map_id() in rpgm_game_data.get('slowmo_maps', ())

        def realtime_map(self):
            return self.get_map_id() in rpgm_game_data.get('realtime_maps', ())

        def slowmo_or_realtime_map(self):
            return self.slowmo_map() or self.realtime_map()

        def get_page_index(self):
            if hasattr(self, 'page_index') and self.page_index != None:
                return self.page_index
            if self.common():
                return None
            for index, page in enumerate(self.event_data['pages']):
                if page == self.page:
                    self.page_index = index
                    return self.page_index

        def page_property(self, map, property):
            return map.event_page_property(self.event_data, self.page, self.page_index, property)

        def override_page(self, map, property, value):
            return map.override_event_page(self.event_data, self.page, self.page_index, property, value)

        def get_random_int(self, lower, upper):
            if hasattr(game_state, 'ask_for_random') and game_state.ask_for_random:
                user_result = renpy.call_screen("random_int_selection_screen", lower, upper)
                return int(user_result)
            else:
                return lower + random.randint(0, upper - lower)

        def preferred_approach_direction(self):
            for command in self.page['list'][0:2]:
                if command['code'] == 111 and command['parameters'][0] == 6:
                    character_id, direction = command['parameters'][1:3]
                    if character_id == -1:
                        return direction

        def conditional_branch_result(self, params):
            operation = params[0]
            # Switches
            if operation == 0:
                switch_id = params[1]
                if self.parallel():
                    game_state.parallel_event_metadata().register_interest_in_switch_id(self.event_data['id'], switch_id)

                return self.state.switches.value(switch_id) == (params[2] == 0)
            # Variable
            elif operation == 1:
                value1 = self.state.variables.value(params[1])
                value2 = None
                if params[2] == 0:
                    value2 = params[3]
                else:
                    value2 = self.state.variables.value(params[3])

                if params[4] == 0:
                    return value1 == value2
                elif params[4] == 1:
                    return value1 >= value2
                elif params[4] == 2:
                    return value1 <= value2
                elif params[4] == 3:
                    return value1 > value2
                elif params[4] == 4:
                    return value1 < value2
                elif params[4] == 5:
                    return value1 != value2

            # Self Switches
            elif operation == 2:
                if len(self.state.events) > 0:
                    key = (self.get_map_id(), self.event_data['id'], params[1])
                    return self.state.self_switches.value(key) == (params[2] == 0)
            # Timer
            elif operation == 3:
                if self.state.timer.active:
                    if params[2] == 0:
                        return self.state.timer.seconds() >= params[1]
                    else:
                        return self.state.timer.seconds() <= params[1]
                return False
            # Actor
            elif operation == 4:
                actor = self.state.actors.by_index(params[1])
                if actor:
                    n = None
                    if len(params) > 3:
                        n = params[3]
                    if params[2] == 0: # In the Party
                        return self.state.party.has_actor(actor)
                    elif params[2] == 1: # Name
                        return actor.get_property('name') == n
                    elif params[2] == 2: # Class
                        # TODO
                        return actor.is_class(n)
                    elif params[2] == 3: # Skill
                        return actor.is_learned_skill(n)
                    elif params[2] == 4: # Weapon
                        return actor.has_weapon(n)
                    elif params[2] == 5: # Armor
                        return actor.has_armor(n)
                    elif params[2] == 6: # State
                        return actor.is_state_affected(n)
                    else:
                        renpy.say(None, ("Operand %s for Actor conditions not implemented!" % params[2]))
                        return False
            # Enemy
            elif operation == 5:
                renpy.say(None, "Conditional statements for Enemy not implemented")
                return False
                #var enemy = $gameTroop.members()[this._params[1]];
                #if (enemy) {
                #    switch (this._params[2]) {
                #    case 0:  // Appeared
                #        result = enemy.isAlive();
                #        break;
                #    case 1:  // State
                #        result = enemy.isStateAffected(this._params[3]);
                #        break;
                #    }
                #}
            # Character
            elif operation == 6:
                character_id = params[1]
                direction = params[2]
                if character_id < 0:
                    if hasattr(game_state, 'player_direction'):
                        return game_state.player_direction == direction
                else:
                    event = self.state.map.find_event_at_index(character_id)
                    character_direction = self.state.map.event_sprite_data(event.event_data, event.page, event.get_page_index())['direction']
                    return character_direction == direction
            # Gold
            elif operation == 7:
                value = params[1]
                gold_operation = params[2]
                if gold_operation == 0: # Greater than or equal to
                    return self.state.party.gold >= value
                elif gold_operation == 1: # Less than or equal to
                    return self.state.party.gold <= value
                elif gold_operation == 2: # Less than
                    return self.state.party.gold < value
            # Item
            elif operation == 8:
                return self.state.party.has_item(self.state.items.by_id(params[1]))
            # Weapon
            elif operation == 9:
                if params[2]:
                    # TODO: include_equip option is not implemented, because equipping is not implemented
                    pass
                return self.state.party.has_item(self.state.weapons.by_id(params[1]))
            # Armor
            elif operation == 10:
                if params[2]:
                    # TODO: include_equip option is not implemented, because equipping is not implemented
                    pass
                return self.state.party.has_item(self.state.armors.by_id(params[1]))
            # Button
            elif operation == 11:
                if hasattr(self, 'press_count') and self.press_count > 0:
                    self.press_count -= 1
                    return True
                elif str(self.map_id) in rpgm_game_data.get('ask_for_key_events', []) and self.event_data['id'] in rpgm_game_data.get('ask_for_key_events', [])[str(self.map_id)]:
                    return renpy.display_menu([("Press '%s'?" % params[1], None), ("Yes", True), ("No", False)])
                else:
                    self.has_ever_paused = True
                    self.paused_for_key = params[1]
                    return -1
            # Script
            elif operation == 12:
                gre = Re()
                if GameIdentifier().is_milfs_control():
                    return GameSpecificCodeMilfsControl().conditional_eval_script(params[1])
                elif gre.match("Input\.isTriggered\('(\w+)'\)", params[1]):
                    if hasattr(self, 'press_count') and self.press_count > 0:
                        self.press_count -= 1
                        return True
                    else:
                        self.has_ever_paused = True
                        self.paused_for_key = gre.last_match.groups()[0]
                        return -1
                elif gre.match("Proxy\.inprox_?d?\?\(@event_id,(\d+),.*\)", params[1]):
                    desired_distance = int(gre.last_match.groups()[0])
                    event_x, event_y = self.state.map.event_location(self.event_data)
                    distance = abs(self.state.player_x - event_x) + abs(self.state.player_y - event_y)
                    return distance <= desired_distance
                elif gre.match("Galv\.DETECT\.event\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(true|false)\s*\)", params[1]):
                    event_id = int(gre.last_match.groups()[0])
                    desired_distance = int(gre.last_match.groups()[1])
                    line_of_sight = gre.last_match.groups()[2] != 'false'

                    event_data = self.state.map.data()['events'][event_id]
                    event_x, event_y = self.state.map.event_location(event_data)
                    distance = math.sqrt((self.state.player_x - event_x) ** 2 + (self.state.player_y - event_y) ** 2)

                    if distance <= desired_distance:
                        if line_of_sight:
                            event = self.state.map.find_event_at_index(event_id)
                            if not event:
                                return False
                            event_direction = self.state.map.event_sprite_data(event.event_data, event.page, event.get_page_index())['direction']
                            if event_direction == GameDirection.DOWN:
                                if event_y > self.state.player_y:
                                    return False
                            elif event_direction == GameDirection.LEFT:
                                if event_x < self.state.player_x:
                                    return False
                            elif event_direction == GameDirection.RIGHT:
                                if event_x > self.state.player_x:
                                    return False
                            elif event_direction == GameDirection.UP:
                                if event_y < self.state.player_y:
                                    return False

                            # TODO: the more complicated line of sight calculation
                            return False
                        else:
                            return True

                    return False

                elif gre.match("Galv\.PUZ\.isAt\((.*?)\)", params[1]):
                    args_string = gre.last_match.groups()[0]
                    if re.match("^[0-9\[\],]+$", args_string):
                        args = eval(gre.last_match.groups()[0])
                        if isinstance(args, tuple):
                            target = args[0]
                            event_id = args[1]
                        else:
                            target = args
                            event_id = self.event_data['id']

                        if event_id > 0:
                            event = self.state.map.find_event_at_index(event_id)
                            event_location = self.state.map.event_location(event.event_data)
                        else:
                            event_location = (self.state.player_x, self.state.player_y)

                        if not isinstance(target, list):
                            if target == 0:
                                # Hack: if the event is coming toward the player, assume it will inevitably reach
                                if event.page['moveType'] == 2:
                                    return True

                                target = (self.state.player_x, self.state.player_y)
                            else:
                                target_event = self.state.map.find_event_at_index(target)
                                target = self.state.map.event_location(target_event.event_data)
                        return tuple(event_location) == tuple(target)
                    else:
                        renpy.say(None, "Args too sketch to eval at '%s'" % script_string)
                elif GameusQuestManager.conditional_eval_script(params[1]) != None:
                    return GameusQuestManager.conditional_eval_script(params[1])
                else:
                    fancypants_eval = self.state.eval_fancypants_value_statement(params[1], event = self)
                    if fancypants_eval in [True, False]:
                        return fancypants_eval

                    renpy.say(None, "Conditional statements for Script not implemented\nSee console for full script.")
                    print "Script that could not be evaluated:\n"
                    print params[1]
                    return False
            # Vehicle
            elif operation == 13:
                renpy.say(None, "Conditional statements for Vehicle not implemented")
                return False
                #result = ($gamePlayer.vehicle() === $gameMap.vehicle(this._params[1]));
            else:
                renpy.say(None, "Unknown operation %s" % operation)
                return False

        def skip_branch(self, current_indent):
            while self.page['list'][self.list_index + 1]['indent'] > current_indent:
                self.list_index += 1

        def finish_event(self):
            self.list_index = len(self.page['list'])

        def jump_to(self, index, current_indent):
            current_index = self.list_index
            start_index = min(index, current_index)
            end_index = max(index, current_index)
            indent = current_indent
            for i in xrange(start_index, end_index + 1):
                new_indent = self.page['list'][i]['indent']
                if new_indent != indent:
                    self.branch[indent] = None
                    indent = new_indent
            self.list_index = index

        def disable_choice(self, choice_id):
            if not hasattr(self, 'choices_to_disable'):
                self.choices_to_disable = []
            self.choices_to_disable.append(choice_id)

        def hide_choice(self, choice_id):
            if not hasattr(self, 'choices_to_hide'):
                self.choices_to_hide = []
            self.choices_to_hide.append(choice_id)

        def eval_maic_quests_script(self, script_string, line):
            gre = Re()
            if gre.match("quest\((\d+)\)", line):
                game_state.party.maic_quest_manager().start(int(gre.last_match.groups()[0]))
            elif gre.match("manually_complete_quest\((\d+)\)", line):
                game_state.party.maic_quest_manager().complete(int(gre.last_match.groups()[0]))
            elif gre.match("reveal_objective\((\d+),\s*(\d+)\)", line):
                quest_id = int(gre.last_match.groups()[0])
                objective_index = int(gre.last_match.groups()[1])
                game_state.party.maic_quest_manager().reveal_objective(quest_id, objective_index)
            elif gre.match("complete_objective\((\d+),\s*(\d+)\)", line):
                quest_id = int(gre.last_match.groups()[0])
                objective_index = int(gre.last_match.groups()[1])
                game_state.party.maic_quest_manager().complete_objective(quest_id, objective_index)
            else:
                return False

            return True

        def eval_galv_quests_script(self, script_string, line):
            gre = Re()
            if not gre.match("Galv\.QUEST", line.strip()):
                return False

            line = line.strip()
            if gre.match("Galv\.QUEST\.activate\((\d+)(,.*)?\)", line):
                status = int(gre.last_match.groups()[0])
                hide_popup = gre.last_match.groups()[1]
                game_state.party.galv_quest_manager().activate(status, hide_popup)
            elif gre.match("Galv\.QUEST\.complete\((\d+)(,.*)?\)", line):
                status = int(gre.last_match.groups()[0])
                hide_popup = gre.last_match.groups()[1]
                game_state.party.galv_quest_manager().complete(status, hide_popup)
            elif gre.match("Galv\.QUEST\.fail\((\d+)(,.*)?\)", line):
                status = int(gre.last_match.groups()[0])
                hide_popup = gre.last_match.groups()[1]
                game_state.party.galv_quest_manager().fail(status, hide_popup)
            elif gre.match("Galv\.QUEST\.catStatus\((\d+),(.*)\)", line):
                game_state.party.galv_quest_manager().cat_status(int(gre.last_match.groups()[0]), gre.last_match.groups()[1] == 'true')
            elif gre.match("Galv\.QUEST\.objective\((\d+),(.*?),(.*?)(,.*)?\)", line):
                quest_id = int(gre.last_match.groups()[0])
                objective_index = int(gre.last_match.groups()[1])
                status = gre.last_match.groups()[2]
                hide_popup = gre.last_match.groups()[3]
                game_state.party.galv_quest_manager().objective(quest_id, objective_index, status, hide_popup)
            elif gre.match("Galv\.QUEST\.resolution\((\d+),(\d+)(,\d+)?\)", line):
                quest_id = int(gre.last_match.groups()[0])
                resolution = int(gre.last_match.groups()[1])
                game_state.party.galv_quest_manager().resolution(quest_id, resolution)
            else:
                return False

            return True

        def eval_galv_puz_script(self, script_string):
            gre = Re()
            if gre.match("Galv\.PUZ\.switch\('event','(\w+)','(\w+)',(\d+)\)", script_string):
                groups = gre.last_match.groups()
                map_id, self_switch_name, self_switch_value, event_id = (self.get_map_id(), groups[0], groups[1] == 'on', int(groups[2]))
                self.state.self_switches.set_value((map_id, event_id, self_switch_name), self_switch_value)
                return True

        def eval_script(self, script_string):
            xhr_compare_command = re.match(re.compile("var xhr = new XMLHttpRequest\(\);.*if\(.*?\) {\n(.*?)}", re.DOTALL), script_string)

            gre = Re()
            if xhr_compare_command:
                success_clause = xhr_compare_command.groups()[0]
                self.eval_script(success_clause.strip())
                return
            elif gre.match("\$game_self_switches\[\[\$game_map\.map_id\s*,\s*(\d+)\s*,\s*'(.*?)'\]\] = (\w+)", script_string):
                groups = gre.last_match.groups()
                map_id, event_id, self_switch_name, self_switch_value = (self.get_map_id(), int(groups[0]), groups[1], groups[2] == 'true')
                self.state.self_switches.set_value((map_id, event_id, self_switch_name), self_switch_value)
                return
            elif script_string.startswith('Galv.PUZ'):
                result = self.eval_galv_puz_script(script_string)
                if result:
                    return
            elif GameIdentifier().is_lust_epidemic() and GameSpecificCodeLustEpidemic().eval_full_script(script_string):
                return
            elif GameIdentifier().is_milfs_control() and GameSpecificCodeMilfsControl().eval_full_script(script_string):
                return
            elif AnimatedBusts.process_script(script_string):
                return

            for line in script_string.split("\n"):
                mv_self_switch_set_command = re.match("\$gameSelfSwitches\.setValue\(\[(\d+),(\d+),'(.*?)'\], (\w+)\);?", line)
                ace_self_switch_set_command = re.match("\$game_self_switches\[\[(\d+)\s*,\s*(\d+)\s*,\s*'(.*?)'\]\] = (\w+)", line)

                if gre.search("^\s*\/\/", line): # Comments, e.g. // Hello world
                    continue

                if rpgm_game_data.get('maic_quests', None):
                    result = self.eval_maic_quests_script(script_string, line)
                    if result:
                        continue

                if game_file_loader.plugin_data_exact('Galv_QuestLog'):
                    result = self.eval_galv_quests_script(script_string, line)
                    if result:
                        continue

                if AnimatedBusts.process_script(line):
                    continue

                if GalvScreenButtons.process_script(script_string):
                    continue

                if GalvEventSpawnTimers.process_script(self, script_string):
                    continue

                if GalvMapProjectiles.process_script(self, script_string):
                    continue

                if game_file_loader.plugin_data_exact('YEP_X_MessageSpeedOpt'):
                    if gre.search("ConfigManager\.messageSpeed", line):
                        continue
                    elif gre.search("Yanfly\.Param\.MsgSpeedOptDefault", line):
                        continue

                if game_file_loader.plugin_data_exact('YEP_X_ExtMesPack1'):
                    if gre.match("\$gameSystem\.clearChoiceSettings", line):
                        del self.choices_to_hide[:]
                        continue
                    elif gre.match("\$gameSystem\.hideChoice\((\d+)", line):
                        choice_id = int(gre.last_match.groups()[0])
                        self.hide_choice(choice_id)
                        continue

                if game_file_loader.plugin_data_exact('YSP_VideoPlayer'):
                    if gre.search("ysp\.VideoPlayer\.loadVideo", line):
                        continue
                    elif gre.search("ysp\.VideoPlayer\.releaseVideo", line):
                        continue
                    elif gre.search("ysp\.VideoPlayer\.newVideo\(['\"](.*?)['\"],(\d+)\)", line):
                        id = int(gre.last_match.groups()[1])
                        path = gre.last_match.groups()[0]
                        self.state.ysp_videos().new_video(id, path)
                        continue
                    elif gre.search("ysp\.VideoPlayer\.playVideoById\((\d+)\)", line):
                        id = int(gre.last_match.groups()[0])
                        video_file = self.state.ysp_videos().video_by_id(id)
                        if video_file:
                            full_path = os.path.join(config.basedir, rpgm_metadata.movies_path, video_file).replace("\\", "/")
                            args = {
                                'image_name': Movie(play=full_path)
                            }
                            self.state.shown_pictures[1000 + id] = args
                        continue
                    elif gre.search("ysp\.VideoPlayer\.setLoopById\((\d+)\)", line):
                        continue
                    elif gre.search("ysp\.VideoPlayer\.stopVideoById\((\d+)\)", line):
                        id = int(gre.last_match.groups()[0])
                        game_state.hide_picture(1000 + id)
                        continue

                handler_matched = False
                for handler in game_file_loader.game_specific_handlers():
                    if handler.eval_script(line, script_string):
                        handler_matched = True
                        break
                if handler_matched:
                    continue

                if 'ImageManager' in line:
                    pass
                elif line == 'Cache.clear':
                    pass
                elif line.startswith('$game_player.no_dash'):
                    pass
                elif line.startswith('$game_scr_lock'):
                    pass
                elif line.startswith('cam_set('):
                    pass
                elif gre.match("\$gameVariables\.setValue\((\d+),\s*(.+)\);?", line):
                    groups = gre.last_match.groups()
                    variable_id = int(groups[0])
                    value = self.state.eval_fancypants_value_statement(groups[1], event = self)
                    self.state.variables.set_value(variable_id, value)
                elif gre.match("hide_choice\((\d+),\s*\"([^\"]+)\"\s*\)", line):
                    groups = gre.last_match.groups()
                    choice_id, expression = (int(groups[0]), groups[1])
                    if self.state.eval_fancypants_value_statement(expression, event = self):
                        self.hide_choice(choice_id)
                elif mv_self_switch_set_command or ace_self_switch_set_command:
                    matching_command = mv_self_switch_set_command or ace_self_switch_set_command
                    groups = matching_command.groups()
                    map_id, event_id, self_switch_name, self_switch_value = (int(groups[0]), int(groups[1]), groups[2], groups[3] == 'true')
                    self.state.self_switches.set_value((map_id, event_id, self_switch_name), self_switch_value)
                elif line == 'auto_save_game()':
                    pass
                elif line.startswith('DataManager.saveGame'):
                    pass
                elif line == 'combine_choices':
                    # From the more_choices plugin -- technically a toggle
                    # to prevent automatically combining menu choice items,
                    # but there doesn't seem to be any flaw in letting them auto combine all the time
                    pass
                elif line == 'SceneManager.push(Scene_Menu);':
                    self.state.show_inventory()
                elif GameIdentifier().is_milfs_control() and GameSpecificCodeMilfsControl().eval_script(line, script_string):
                    pass
                elif GameIdentifier().is_incest_adventure() and GameSpecificCodeIncestAdventure().eval_script(line, script_string):
                    pass
                elif GameIdentifier().is_ics1() and GameSpecificCodeICS1().eval_script(line, script_string):
                    pass
                elif GameIdentifier().is_robots_touch() and GameSpecificCodeRobotsTouch().eval_script(line, script_string):
                    pass
                elif gre.search("\$game_map\..*?start_anim_loop", line):
                    pass
                else:
                    print "Script that could not be evaluated:\n"
                    print script_string
                    clean_line = line.replace("{", "{{").replace("[", "[[")
                    renpy.say(None, "Code 355 not implemented to eval script including line '%s'\nSee console for full script" % clean_line)
                    return

        def show_parallel_event_animations(self, switch_id):
            for newly_activated_event in self.state.parallel_event_metadata().events_activated_by_switch(switch_id):
                # TODO: only want to show parallel event animations if the event is a 'pure' animation, e.g. no text showing or menus etc
                # so there's probably more conditions that can go here other than 'code' == 101
                if not any(command['code'] == 101 for command in newly_activated_event['list']):
                    if noisy_events:
                        print "EVENT ACTIVATED BY SWITCH: %s" % newly_activated_event['id']
                    e = GameEvent(self.state, None, newly_activated_event, newly_activated_event)
                    # TODO: probably is better to append to parallel_events, but this seems to not work for the purposes of showing animations
                    self.state.events.append(e)

        def direction_to_face_player(self, event_location):
            return GameDirection.direction_for_a_to_face_b(event_location, (game_state.player_x, game_state.player_y))

        def process_move_route(self, event_id, route, return_on_wait = False):
            if not hasattr(self, 'move_route_index'):
                self.move_route_index = 0

            event = None
            event_page_index = None
            player_moving = event_id < 0
            if event_id == 0:
                event_id = self.event_data['id']
            if event_id == self.event_data['id']:
                event_page_index = self.get_page_index()
                event = self
                if event.common():
                    event = next((e for e in reversed(self.state.events) if not e.common()), None)
            if event_id > 0:
                if not event:
                    event = self.state.map.find_event_at_index(event_id)

                if not event:
                    print "Wanted to process move route but couldn't find the moving event %s!" % event_id
                    self.list_index += 1
                    return

                if event_page_index == None:
                    event_page_index = event.get_page_index()

            for route_part in route['list'][self.move_route_index:]:
                if noisy_events:
                    print "MOVEMENT ROUTE: %s, event %s, page %s, command %s, target %s, rc %s (%s)" % (
                        "common" if self.common() else ("map %s" % self.get_map_id()),
                        self.event_data['id'],
                        self.get_page_index(),
                        self.list_index,
                        event_id,
                        route_part['code'],
                        RpgmConstants.ROUTE_COMMAND_NAMES[route_part['code']]
                    )
                direction_delta = (0, 0)
                new_direction = None
                new_direction_fix = None
                new_through = None
                new_transparent = None
                direction_order = [GameDirection.DOWN, GameDirection.LEFT, GameDirection.RIGHT, GameDirection.UP]
                if route_part['code'] in [1, 2, 3, 4]: # Move Down / Left / Right / Up
                    new_direction = direction_order[route_part['code'] - 1]
                    direction_delta = GameDirection.delta_for_direction(new_direction)
                elif route_part['code'] in [5, 6, 7, 8]: # Move Diagonally
                    if route_part['code'] == 5: # Move Lower Left
                        horz = GameDirection.LEFT
                        vert = GameDirection.DOWN
                    elif route_part['code'] == 6: # Move Lower Right
                        horz = GameDirection.RIGHT
                        vert = GameDirection.DOWN
                    elif route_part['code'] == 7: # Move Upper Left
                        horz = GameDirection.LEFT
                        vert = GameDirection.UP
                    else: # Move Upper Right
                        horz = GameDirection.RIGHT
                        vert = GameDirection.UP

                    horiz_delta = GameDirection.delta_for_direction(horz)
                    vert_delta = GameDirection.delta_for_direction(vert)
                    direction_delta = tuple(map(sum, zip(horiz_delta, vert_delta)))

                    if player_moving:
                        x = game_state.player_x
                        y = game_state.player_y
                        current_direction = game_state.player_direction
                    else:
                        x, y = self.state.map.event_location(event.event_data)
                        current_direction = self.state.map.event_sprite_data(event.event_data, event.page, event_page_index)['direction']

                    if current_direction == GameDirection.reverse_direction(horz):
                        new_direction = horz
                    if current_direction == GameDirection.reverse_direction(vert):
                        new_direction = vert

                    map_event = self.state.map.find_event_for_location(x, y)
                    # TODO: may need to account for through-ness of events being moved into
                    if ((not map_event or not self.state.map.event_through(map_event.event_data, map_event.page, map_event.page_index))) and (not self.state.map.can_pass_diagonally(x, y, horz, vert)) and not route['skippable']:
                        return
                elif route_part['code'] == 9: # Move Random
                    random_direction = GameDirection.random_direction()
                    if player_moving:
                        x = game_state.player_x
                        y = game_state.player_y
                    else:
                        x, y = self.state.map.event_location(event.event_data)
                    map_event = self.state.map.find_event_for_location(x, y)
                    if map_event.page_property(self.state.map, GameEvent.PROPERTY_THROUGH) or self.state.map.can_pass(x, y, random_direction):
                        new_direction = random_direction
                        direction_delta = GameDirection.delta_for_direction(random_direction)
                elif route_part['code'] in [10, 11]: # Move Toward / Away
                    loc = self.state.map.event_location(self.event_data)
                    new_direction = self.direction_to_face_player(loc)

                    if route_part['code'] == 10:
                        direction_delta = GameDirection.delta_for_direction(new_direction)
                    else:
                        direction_delta = GameDirection.delta_for_direction(GameDirection.reverse_direction(new_direction))

                    delta_x, delta_y = direction_delta
                    keep_moving = self.move_route_move_object(delta_x, delta_y, player_moving = False, event = self, skippable = route['skippable'])
                    if not keep_moving:
                        self.move_route_index = len(route)
                        return
                    self.move_route_index += 1
                    continue
                elif route_part['code'] in [12, 13]: # Move Forward / Backward
                    if player_moving:
                        current_direction = game_state.player_direction
                    else:
                        current_direction = self.state.map.event_sprite_data(event.event_data, event.page, event_page_index)['direction']
                    if route_part['code'] == 12:
                        direction_delta = GameDirection.delta_for_direction(current_direction)
                    else:
                        direction_delta = GameDirection.delta_for_direction(GameDirection.reverse_direction(current_direction))
                elif route_part['code'] == 14: # Jump
                    direction_delta = route_part['parameters'][0:2]
                elif route_part['code'] == 15: # Wait
                    if return_on_wait:
                        self.move_route_index += 1
                        self.paused = route_part['parameters'][0]
                        return
                elif route_part['code'] in [16, 17, 18, 19]: # Turn Down / Left / Right / Up
                    new_direction = direction_order[route_part['code'] - 16]
                elif route_part['code'] in [20, 21]: # Turn 90deg R or L
                    if player_moving:
                        current_direction = game_state.player_direction
                    else:
                        current_direction = self.state.map.event_sprite_data(event.event_data, event.page, event_page_index)['direction']
                    clockwise_directions = [GameDirection.LEFT, GameDirection.UP, GameDirection.RIGHT, GameDirection.DOWN]
                    current_index = clockwise_directions.index(current_direction)
                    if route_part['code'] == 20: # 90 degrees right
                        rotation_integer = 1
                    else: # 90 degrees left
                        rotation_integer = -1

                    new_direction = clockwise_directions[(current_index + rotation_integer) % 4]
                elif route_part['code'] == 22: # Turn 180deg
                    if player_moving:
                        current_direction = game_state.player_direction
                    else:
                        current_direction = self.state.map.event_sprite_data(event.event_data, event.page, event_page_index)['direction']
                    new_direction = GameDirection.reverse_direction(current_direction)
                elif route_part['code'] in [23, 24]: # Turn Random 90deg, Turn Random
                    renpy.say(None, "Move Route random turn commands not supported!")
                elif route_part['code'] == [25, 26]: # Turn Toward / Turn Away
                    loc = self.state.map.event_location(self.event_data)
                    if route_part['code'] == 25:
                        new_direction = self.direction_to_face_player(loc)
                    else:
                        new_direction = GameDirection.reverse_direction(self.direction_to_face_player(loc))
                    self.move_route_set_direction(new_direction, event = self)
                    self.move_route_index += 1
                    continue
                elif route_part['code'] == 27: # Route Switch On
                    self.state.switches.set_value(route_part['parameters'][0], True)
                elif route_part['code'] == 28: # Route Switch Off
                    self.state.switches.set_value(route_part['parameters'][0], False)
                elif route_part['code'] == 29: # Change Speed
                    pass
                elif route_part['code'] == 35: # Route Direction Fix On
                    new_direction_fix = True
                elif route_part['code'] == 36: # Route Direction Fix Off
                    new_direction_fix = False
                elif route_part['code'] == 37: # Route Through On
                    new_through = True
                elif route_part['code'] == 38: # Route Through Off
                    new_through = False
                elif route_part['code'] == 39: # Route Transparent On
                    new_transparent = True
                elif route_part['code'] == 40: # Route Transparent Off
                    new_transparent = False
                elif route_part['code'] == 41: # Change image
                    new_character_name, new_character_index = route_part['parameters']
                    if player_moving:
                        actor_index = self.state.party.leader()
                        actor = self.state.actors.by_index(actor_index)
                        actor.set_property('characterName', new_character_name)
                        actor.set_property('characterIndex', new_character_index)
                    else:
                        event.override_page(self.state.map, GameEvent.PROPERTY_CHARACTER_NAME, new_character_name)
                        event.override_page(self.state.map, GameEvent.PROPERTY_CHARACTER_INDEX, new_character_index)
                elif route_part['code'] == 45: # Route Script
                    route_script = route_part['parameters'][0]
                    gre = Re()
                    if gre.match('\$game_switches\[(\d+)\] = (\w+)', route_script):
                        groups = gre.last_match.groups()
                        switch_id = int(groups[0])
                        switch_value = groups[1] == 'true'
                        self.state.self_switches.set_value(switch_id, switch_value)
                    elif gre.match("\$game_self_switches\[\[(\d+)\s*,\s*(\d+)\s*,\s*'(.*?)'\]\] = (\w+)", route_script) or gre.match("\$gameSelfSwitches\.setValue\(\[(\d+),(\d+),'(.*?)'\], (\w+)\);?", route_script):
                        groups = gre.last_match.groups()
                        map_id, event_id, self_switch_name, self_switch_value = (int(groups[0]), int(groups[1]), groups[2], groups[3] == 'true')
                        self.state.self_switches.set_value((map_id, event_id, self_switch_name), self_switch_value)
                    elif gre.match('MOVE TO: (\d+), (\d+)', route_script):
                        # Special commands from YEP_MoveRouteCore
                        # Normmally these would do the proper pathfinding, but for expedience sake just jump to the destination
                        if player_moving:
                            x = game_state.player_x
                            y = game_state.player_y
                        else:
                            x, y = self.state.map.event_location(event.event_data)
                        groups = gre.last_match.groups()
                        destination_x, destination_y = (int(groups[0]), int(groups[1]))
                        direction_delta = (destination_x - x, destination_y - y)
                    elif route_script.startswith('$game_player.no_dash'):
                        pass
                    elif gre.match('this.setBlendMode\(\d+\)', route_script):
                        pass
                    elif gre.match('end_anim_loop', route_script):
                        pass
                    elif GalvEventSpawnTimers.process_move_route(self, route_script):
                        pass
                    else:
                        print "Script that could not be evaluated:\n"
                        print route_script
                        renpy.say(None, "Movement route Script commands not implemented\nSee console for full script.")

                elif route_part['code'] == 0:
                    pass

                if new_direction_fix != None:
                    if player_moving:
                        self.state.player_direction_fix = new_direction_fix
                    else:
                        event.override_page(self.state.map, GameEvent.PROPERTY_DIRECTION_FIX, new_direction_fix)

                if new_direction:
                    self.move_route_set_direction(new_direction, player_moving = player_moving, event = event)

                if new_transparent != None:
                    if player_moving:
                        # TODO: player transparency
                        pass
                    else:
                        event.override_page(self.state.map, GameEvent.PROPERTY_TRANSPARENT, new_transparent)

                if new_through != None:
                    if player_moving:
                        game_state.everything_reachable = new_through
                    else:
                        event.override_page(self.state.map, GameEvent.PROPERTY_THROUGH, new_through)

                delta_x, delta_y = direction_delta
                if delta_x != 0 or delta_y != 0:
                    keep_moving = self.move_route_move_object(delta_x, delta_y, player_moving = player_moving, event = event, skippable = route['skippable'])
                    if not keep_moving:
                        self.move_route_index = len(route)
                        return

                    if self.parallel() and self.slowmo_or_realtime_map():
                        self.move_route_index += 1

                        move_speed = event.page_property(self.state.map, GameEvent.PROPERTY_MOVE_SPEED)
                        move_frequency = event.page_property(self.state.map, GameEvent.PROPERTY_MOVE_FREQUENCY)

                        distance_per_frame = (2 ** move_speed) / 256.0

                        move_frames = int(1.0 / distance_per_frame)
                        stop_frames = 30 * (5 - move_frequency)

                        self.paused = move_frames + stop_frames
                        return

                self.move_route_index += 1

        def move_route_set_direction(self, new_direction, player_moving = False, event = None):
            if player_moving:
                game_state.set_player_direction(new_direction)
            elif not event.page_property(self.state.map, GameEvent.PROPERTY_DIRECTION_FIX):
                event.override_page(self.state.map, GameEvent.PROPERTY_DIRECTION, new_direction)

        def move_route_move_object(self, delta_x, delta_y, player_moving = False, event = None, skippable = False):
            if player_moving:
                current_x, current_y = game_state.player_x, game_state.player_y
            else:
                loc = self.state.map.event_location(event.event_data)
                if not loc:
                    return
                current_x, current_y = loc

            new_x, new_y = current_x + delta_x, current_y + delta_y
            if new_x < 0 or new_y < 0 or new_x > self.state.map.width() - 1 or new_y > self.state.map.height() - 1:
                return

            moving_object_does_not_collide = (player_moving and game_state.everything_is_reachable()) or (event and event.page_property(self.state.map, GameEvent.PROPERTY_THROUGH))
            if not moving_object_does_not_collide:
                map_event = self.state.map.find_event_for_location(new_x, new_y)
                if not map_event or (not map_event.page_property(self.state.map, GameEvent.PROPERTY_THROUGH)):
                    old_map_event = self.state.map.find_event_for_location(current_x, current_y)
                    if not old_map_event or (not old_map_event.page_property(self.state.map, GameEvent.PROPERTY_THROUGH)):
                        move_distance = abs(delta_x) + abs(delta_y)
                        if (map_event and GameEvent.page_solid(map_event.event_data, map_event.page, map_event.page_index)) or (move_distance == 1 and not self.state.map.can_move_vector(current_x, current_y, delta_x, delta_y)):
                              if noisy_events:
                                  print "MOVEMENT COLLIDED AT %s, %s!!!" % (new_x, new_y)
                              if skippable:
                                  return True
                              else:
                                  return False

            if player_moving: # Player Character
                game_state.player_x, game_state.player_y = new_x, new_y
            else:
                self.state.map.override_event_location(event.event_data, (new_x, new_y))

        def migrate_global_branch_data(self):
            if not hasattr(self, 'branch') and hasattr(game_state, 'branch'):
                for event in game_state.events:
                    event.branch = game_state.branch
                del game_state.branch

        def get_canned_answer(self, variable_id):
            # Aunt's cabinet code
            if GameIdentifier().is_milfs_villa() and self.get_map_id() == 48 and variable_id == 109:
                return 32

        def hide_if_unpleasant_moving_obstacle(self):
            if GameIdentifier().is_ics1() or GameIdentifier().is_the_artifact_part_3():
                if self.page['image']['characterName'] and self.page['image']['characterName'].startswith('car'):
                    self.state.map.erased_events[self.event_data['id']] = True

        def merge_show_choice_commands(self):
            command_index = self.list_index
            first_choice_command = self.page['list'][command_index]
            while self.page['list'][command_index] and self.page['list'][command_index]['code'] == 102:
                show_choice_command = self.page['list'][command_index]
                if show_choice_command != first_choice_command:
                    choice_offset = len(first_choice_command['parameters'][0])
                    first_choice_command['parameters'][0] += show_choice_command['parameters'][0]
                    if show_choice_command['parameters'][1] == 5:
                        renpy.say(None, "merge_show_choice_commands does not support 'branch' option")

                    i = command_index + 1
                    while self.page['list'][i] and ((self.page['list'][i]['code'] in [402, 403, 404]) or self.page['list'][i]['indent'] != first_choice_command['indent']):
                        if self.page['list'][i]['code'] == 402 and self.page['list'][i]['indent'] == first_choice_command['indent']:
                            # Increment the "when" param by the number of existing available choices
                            self.page['list'][i]['parameters'][0] += choice_offset
                        i += 1

                    self.page['list'].remove(show_choice_command)
                else:
                    command_index += 1

                # Skip choice branches
                while self.page['list'][command_index] and ((self.page['list'][command_index]['code'] in [402, 403, 404]) or self.page['list'][command_index]['indent'] != first_choice_command['indent']):
                    command_index += 1

        def request_actor_name(self, actor_index):
            actor = self.state.actors.by_index(actor_index)
            self.state.set_side_image(actor.get_property('faceName'), actor.get_property('faceIndex'))
            if hasattr(game_state, 'last_said_text') and game_state.last_said_text:
                prompt = game_state.last_said_text
            else:
                prompt = "What name should actor %d have?" % actor_index
            actor_name_default = ''
            if 'suggested_actor_names' in rpgm_game_data:
                actor_name_default = rpgm_game_data['suggested_actor_names'].get(str(actor_index), '')
            elif actor.get_property('name'):
                actor_name_default = actor.get_property('name')
            actor_name = renpy.input("{i}%s{/i}" % prompt, default = actor_name_default)
            actor.set_property('name', actor_name)

        def ready_to_continue(self):
            if hasattr(self, 'paused'):
                return not self.paused
            if hasattr(self, 'paused_for_key'):
                return not self.paused_for_key
            return True

        def do_next_thing(self, allow_pause = False):
            if not self.done():
                self.migrate_global_branch_data()
                command = self.page['list'][self.list_index]

                recently_rendered_animation_duration = 0

                interaction_codes = [101, 102, 103, 104, 301, 302, 303, 354]
                if command['code'] in interaction_codes:
                    if hasattr(game_state, 'queued_pictures') and len(game_state.queued_pictures) > 0:
                        recently_rendered_animation_duration = game_state.flush_queued_pictures()
                        game_state.show_map(True)
                    game_state.flush_queued_sound()

                if noisy_events:
                    print "%sCOMMAND: %s, event %s, page %s - %s, command %s (%s)" % (
                        ' ' * command['indent'],
                        "common" if self.common() else ("map %s" % self.get_map_id()),
                        self.event_data['id'],
                        self.event_data['pages'].index(self.page) if ('pages' in self.event_data) else 'n/a',
                        self.list_index,
                        command['code'],
                        RpgmConstants.COMMAND_NAMES[command['code']]
                    )

                # Do nothing
                if command['code'] == 0:
                    pass

                # Show text
                elif command['code'] == 101:
                    face_name, face_index, background, position_type = command['parameters']
                    ends_with_whitespace_pattern = re.compile("\s$")
                    accumulated_text = []
                    while len(self.page['list']) > self.list_index + 1 and self.page['list'][self.list_index + 1]['code'] == 401:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        text = command['parameters'][0].lstrip()
                        # If the previous line didn't end with a space, add a space before joining to the next line
                        if len(accumulated_text) > 0 and not re.search(ends_with_whitespace_pattern, accumulated_text[-1]):
                            accumulated_text.append(' ')
                        accumulated_text.append(text)
                        # Always put newlines after colons and periods
                        if text.endswith(":") or text.endswith('.'):
                            accumulated_text.append("\n")

                    text_to_show = game_state.replace_names("".join(accumulated_text).strip())
                    if len(text_to_show) > 0:
                        try:
                            escaped_text = game_state.escape_text_for_renpy(text_to_show)
                            self.state.say_text_with_possible_speaker(escaped_text, face_name, face_index)
                        except renpy.game.CONTROL_EXCEPTIONS:
                            raise
                        except:
                            print "Text that failed to show:\n%s" % text_to_show
                            raise
                    else:
                        game_state.pause()

                # Show choices
                elif command['code'] == 102:
                    if rpgm_metadata.has_large_choices_plugin or game_file_loader.plugin_data_exact('YEP_X_ExtMesPack1'):
                        self.merge_show_choice_commands()

                    choice_texts, cancel_type, background_type, position_type = command['parameters'][0:4]
                    if cancel_type >= len(choice_texts):
                        cancel_type = -2

                    position_type = 0
                    should_display_on_right = False
                    if len(command['parameters']) > 3:
                        position_type = command['parameters'][3]
                        if rpgm_game_data.get('allow_choice_positions', False) and position_type == 2 and len(game_state.srd_hud_lines()) > 0:
                            should_display_on_right = True

                    if not hasattr(self, 'choices_to_hide'):
                        self.choices_to_hide = []

                    if not hasattr(self, 'choices_to_disable'):
                        self.choices_to_disable = []

                    if recently_rendered_animation_duration > 300:
                        renpy.pause()

                    self.state.show_map(in_interaction = True, fade_map = should_display_on_right)

                    options = [(game_state.escape_text_for_renpy(game_state.replace_names(text)), index) for index, text in enumerate(choice_texts) if index + 1 not in self.choices_to_hide and len(text) > 0]
                    if len(options) > 10 or should_display_on_right:
                        choice_options = []
                        for option_text, option_index in options:
                            choice_options.append({
                                'id': option_index,
                                'text': option_text,
                                'disabled': True if (option_index + 1) in self.choices_to_disable else False
                            })

                        if len(options) > 10:
                            result = renpy.call_screen("scrollable_show_choices_screen", choice_options)
                        elif should_display_on_right:
                            result = renpy.call_screen("right_aligned_show_choices_screen", choice_options)
                    else:
                        result = renpy.display_menu(options)
                    self.branch[command['indent']] = result
                    del self.choices_to_hide[:]
                    del self.choices_to_disable[:]

                # Input number
                elif command['code'] == 103:
                    variable_id, max_digits = command['parameters']
                    entered_a_number = False
                    while not entered_a_number:
                        try:
                            canned_answer = self.get_canned_answer(variable_id)
                            if canned_answer:
                                result = canned_answer
                            else:
                                result = renpy.input("Input number:", length=max_digits)

                            self.state.variables.set_value(variable_id, int(result))
                            entered_a_number = True
                        except ValueError:
                            pass

                # Choose item
                elif command['code'] == 104:
                    variable_id = command['parameters'][0]
                    item_type = command['parameters'][1] or 2
                    choices = self.state.party.item_choices(item_type)
                    result = None
                    if len(choices) > 0:
                        item_options = [(text, index) for text, index in choices]
                        screen_args = {}
                        if GameIdentifier().is_my_summer() or GameIdentifier().is_lust_epidemic():
                            # only show the cancel button the status screen for NLT games, could be a little fragile
                            current_event = self.state.events[-1]
                            if current_event.common() and current_event.event_data['id'] == 1:
                                screen_args["background"] = False
                                screen_args["allow_cancel"] = True
                            screen_args["xsize"] = 1.0
                            screen_args["xpos"] = 0
                            screen_args["ypos"] = 30
                            screen_args["ysize"] = 150
                            screen_args["rows"] = int(math.ceil(len(item_options) / 4.0))
                            screen_args["cols"] = 4
                        else:
                            screen_args["rows"] = len(item_options)

                        result = renpy.display_menu(
                            sorted(item_options, key=lambda opt: opt[0]),
                            scope = screen_args,
                            screen='inventory_choice_screen'
                        )
                    else:
                        game_state.say_text(None, "No items to choose...")
                    self.state.variables.set_value(variable_id, result)

                # Show Scrolling Text
                elif command['code'] == 105:
                    accumulated_text = []
                    while len(self.page['list']) > self.list_index + 1 and self.page['list'][self.list_index + 1]['code'] == 405:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        accumulated_text.append(command['parameters'][0])
                    self.list_index += 1
                    renpy.call_screen("scrolling_textbox_screen", game_state.escape_text_for_renpy("\n".join(accumulated_text)))

                # Comment
                elif command['code'] == 108:
                    pass

                # Conditional branch
                elif command['code'] == 111:
                    branch_result = self.conditional_branch_result(command['parameters'])
                    if branch_result == -1:
                        return

                    if noisy_events:
                        print "%sconditional: %s, result: %s" % (
                            ' ' * command['indent'],
                            command['parameters'],
                            branch_result
                        )

                    self.branch[command['indent']] = branch_result
                    if not branch_result:
                        self.skip_branch(command['indent'])

                # Loop -- TODO: this is not good enough
                elif command['code'] == 112:
                    pass

                elif command['code'] == 115: # Exit Event Processing
                    self.finish_event()
                    return

                # Common Event
                elif command['code'] == 117:
                    common_event = self.state.common_events_data()[command['parameters'][0]]
                    self.list_index += 1
                    return GameEvent(self.state, None, common_event, common_event)

                # Repeat Above
                elif command['code'] == 413:
                    if self.parallel():
                        # This might be an endlessly looping animation in a parallel
                        # event. Bail out of the event.
                        self.finish_event()
                        return

                    while self.list_index > 0:
                        self.list_index -= 1
                        if self.page['list'][self.list_index]['indent'] == command['indent']:
                            break

                # Break Loop
                elif command['code'] == 113:
                    current_indent = command['indent']
                    while self.list_index < len(self.page['list']) - 1:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        if command['code'] == 413 and command['indent'] < current_indent:
                            break

                # Label
                elif command['code'] == 118:
                    pass

                # Jump to Label
                elif command['code'] == 119:
                    label_name = command['parameters'][0]
                    for index, other_command in enumerate(self.page['list']):
                        if other_command['code'] == 118 and other_command['parameters'][0] == label_name:
                            if self.parallel() and index < self.list_index:
                                # This might be an endlessly looping animation in a parallel
                                # event. Bail out of the event.
                                self.finish_event()
                                return

                            self.jump_to(index, current_indent = command['indent'])

                # Control Switches
                elif command['code'] == 121:
                    start, end, value = command['parameters'][0:3]
                    for i in xrange(start, end + 1):
                        switch_on = (value == 0)
                        self.state.switches.set_value(i, switch_on)
                        if switch_on:
                            self.show_parallel_event_animations(i)

                    if not self.parallel():
                        self.state.queue_parallel_events(keep_relevant_existing = True)

                # Control Variables
                elif command['code'] == 122:
                    if noisy_events:
                        print "%scontrol vars: %s" % (
                            ' ' * command['indent'],
                            command['parameters']
                        )

                    was_random = False
                    start, end, operation_type, operand = command['parameters'][0:4]
                    value = 0
                    if operand == 0:
                        value = command['parameters'][4]
                    elif operand == 1:
                        value = self.state.variables.value(command['parameters'][4])
                    elif operand == 2:
                        was_random = True
                        value = self.get_random_int(command['parameters'][4], command['parameters'][5])
                    elif operand == 3:
                        game_data_operand_type = command['parameters'][4]
                        game_data_operand_param1 = command['parameters'][5]
                        game_data_operand_param2 = command['parameters'][6]
                        if game_data_operand_type == 0: # Item
                            value = self.state.party.num_items(self.state.items.by_id(game_data_operand_param1))
                        elif game_data_operand_type == 1: # Weapon
                            value = self.state.party.num_items(self.state.weapons.by_id(game_data_operand_param1))
                        elif game_data_operand_type == 2: # Armor
                            value = self.state.party.num_items(self.state.armors.by_id(game_data_operand_param1))
                        elif game_data_operand_type == 3: # Actor
                            actor_index = game_data_operand_param1
                            actor = self.state.actors.by_index(actor_index)
                            if game_data_operand_param2 == 0: # Level
                                value = actor.get_property('level')
                            elif game_data_operand_param2 == 1: # EXP
                                value = actor.current_exp()
                            elif game_data_operand_param2 == 2: # HP
                                value = actor.hp()
                            elif game_data_operand_param2 == 3: # MP
                                value = actor.mp()
                            else: # Parameter
                                if game_data_operand_param2 >= 4 and game_data_operand_param2 <= 11:
                                    value = actor.param(game_data_operand_param2 - 4)
                        elif game_data_operand_type == 4: # Enemy
                            #    var enemy = $gameTroop.members()[param1];
                            #    if (enemy) {
                            #        switch (param2) {
                            #        case 0:  // HP
                            #            return enemy.hp;
                            #        case 1:  // MP
                            #            return enemy.mp;
                            #        default:    // Parameter
                            #            if (param2 >= 2 && param2 <= 9) {
                            #                return enemy.param(param2 - 2);
                            #            }
                            #        }
                            #    }
                            #    break;
                            renpy.say(None, ("Variable control operand 3 not implemented for type %s, plz implement" % game_data_operand_type))
                        elif game_data_operand_type == 5: # Character
                            # param1 is character ID
                            if game_data_operand_param1 >= 0:
                                if game_data_operand_param1 == 0:
                                    e = self.event_data
                                else:
                                    e = self.state.map.find_event_data_at_index(game_data_operand_param1)
                                if game_data_operand_param2 == 0: # Map X
                                    value = self.state.map.event_location(e)[0]
                                elif game_data_operand_param2 == 1: # Map Y
                                    value = self.state.map.event_location(e)[1]
                                elif game_data_operand_param2 == 2: # Direction
                                    # return character.direction();
                                    renpy.say(None, ("Variable control operand 3 not implemented for param 5-%s, plz implement" % game_data_operand_param2))
                                elif game_data_operand_param2 == 3: # Screen X
                                    # return character.screenX();
                                    renpy.say(None, ("Variable control operand 3 not implemented for param 5-%s, plz implement" % game_data_operand_param2))
                                elif game_data_operand_param2 == 4: # Screen Y
                                    # return character.screenY();
                                    renpy.say(None, ("Variable control operand 3 not implemented for param 5-%s, plz implement" % game_data_operand_param2))
                            else:
                                if game_data_operand_param2 == 0: # Map X
                                    value = game_state.player_x
                                elif game_data_operand_param2 == 1: # Map Y
                                    value = game_state.player_y
                                elif game_data_operand_param2 == 2: # Direction
                                    # return character.direction();
                                    renpy.say(None, ("Variable control operand 3 not implemented for param 5-%s, plz implement" % game_data_operand_param2))
                                elif game_data_operand_param2 == 3: # Screen X
                                    # return character.screenX();
                                    renpy.say(None, ("Variable control operand 3 not implemented for param 5-%s, plz implement" % game_data_operand_param2))
                                elif game_data_operand_param2 == 4: # Screen Y
                                    # return character.screenY();
                                    renpy.say(None, ("Variable control operand 3 not implemented for param 5-%s, plz implement" % game_data_operand_param2))
                        elif game_data_operand_type == 6: # Party
                            #    actor = $gameParty.members()[param1];
                            #    return actor ? actor.actorId() : 0;
                            renpy.say(None, ("Variable control operand 3 not implemented for type %s, plz implement" % game_data_operand_type))
                        elif game_data_operand_type == 7: # Other
                            if game_data_operand_param1 == 0: # Map ID
                                value = self.get_map_id()
                            elif game_data_operand_param1 == 1: # Party Members
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                            elif game_data_operand_param1 == 2: # Gold
                                value = self.state.party.gold
                            elif game_data_operand_param1 == 3: # Steps
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                            elif game_data_operand_param1 == 4: # Play Time
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                            elif game_data_operand_param1 == 5: # Timer
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                            elif game_data_operand_param1 == 6: # Save Count
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                            elif game_data_operand_param1 == 7: # Battle Count
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                            elif game_data_operand_param1 == 8: # Win Count
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                            elif game_data_operand_param1 == 9: # Escape COunt
                                renpy.say(None, ("Variable control operand 7 not implemented for param %s, plz implement" % game_data_operand_param1))
                        else:
                            value = 0
                    elif operand == 4:
                        script_string = command['parameters'][4]
                        value = self.state.eval_fancypants_value_statement(script_string, event = self)

                    changed_any_variable = False
                    for i in xrange(start, end + 1):
                        changed_this_variable = self.state.variables.operate_variable(i, operation_type, value)
                        changed_any_variable = (changed_any_variable or changed_this_variable)

                    if changed_any_variable and not was_random and not self.parallel() and not self.common():
                        self.state.queue_parallel_events(keep_relevant_existing = True)

                # Control Self Switch
                elif command['code'] == 123:
                    switch_id, value = command['parameters']
                    if self in self.state.events:
                        running_events = self.state.events
                    else:
                        running_events = self.state.events + [self]

                    changed_switch = False
                    last_non_common_event = next((e for e in reversed(running_events) if not e.common()), None)
                    if last_non_common_event:
                        key = (last_non_common_event.map_id, last_non_common_event.event_data['id'], switch_id)
                        changed_switch = self.state.self_switches.set_value(key, value == 0)

                    if changed_switch and not self.parallel():
                        self.state.queue_parallel_events(keep_relevant_existing = True)

                # Control Timer
                elif command['code'] == 124:
                    start_timer = command['parameters'][0] == 0
                    if start_timer:
                        self.state.timer.start(command['parameters'][1])
                    else:
                        self.state.timer.stop()

                # Change gold
                elif command['code'] == 125:
                    operation, operand_type, operand = command['parameters']
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    self.state.party.gain_gold(value);

                # Change items, weapons, armors
                elif command['code'] in [126, 127, 128]:
                    item_id, operation, operand_type, operand = command['parameters'][0:4]
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    if command['code'] == 126:
                        self.state.party.gain_item(self.state.items.by_id(item_id), value)
                    elif command['code'] == 127:
                        self.state.party.gain_item(self.state.weapons.by_id(item_id), value)
                    elif command['code'] == 128:
                        self.state.party.gain_item(self.state.armors.by_id(item_id), value)

                # Change party members
                elif command['code'] == 129:
                    actor_index = command['parameters'][0]
                    actor = self.state.actors.by_index(actor_index)
                    if actor:
                        if command['parameters'][1] == 0:
                            # Initialize actor - I don't think this is needed outside of combat, mostly
                            if command['parameters'][2]:
                                pass
                            self.state.party.add_actor(actor_index)
                        else:
                            self.state.party.remove_actor(actor_index)

                # Change battle BGM / Change victory ME
                elif command['code'] in [132, 133]:
                    pass

                # Change save access
                elif command['code'] == 134:
                    pass

                # Toggle menu access
                elif command['code'] == 135:
                    pass

                # Transfer maps
                elif command['code'] == 201:
                    method = command['parameters'][0]
                    if method == 0: # Direct designation
                        self.new_map_id, self.new_x, self.new_y = command['parameters'][1:4]
                    else: # Designation with variables
                        self.new_map_id = self.state.variables.value(command['parameters'][1])
                        self.new_x = self.state.variables.value(command['parameters'][2])
                        self.new_y = self.state.variables.value(command['parameters'][3])
                    self.new_direction = command['parameters'][4]
                    if debug_events:
                        print "DEBUG_EVENTS: Map %d" % self.new_map_id

                # Set event location
                elif command['code'] == 203:
                    event_id, operation, vx, vy, direction = command['parameters']
                    if event_id < 0:
                        renpy.say(None, "Command 203 not supported for player! Plz fix.")
                    if event_id == 0:
                        event_data = self.event_data
                    else:
                        event_data = self.state.map.find_event_data_at_index(event_id)
                    if operation == 0: # Direct Designation
                        self.state.map.override_event_location(event_data, (vx, vy))
                    elif operation == 1: # Designation with variables
                        x = self.state.variables.value(vx)
                        y = self.state.variables.value(vy)
                        self.state.map.override_event_location(event_data, (x, y))
                    else: # Exchange with another event
                        renpy.say(None, "Command 203 exchange with another event not implemented, plz implement!")
                    if direction > 0:
                        event = self.state.map.find_event_at_index(event_data['id'])
                        if event: # intro to the artifact 1
                            event.override_page(self.state.map, GameEvent.PROPERTY_DIRECTION, direction)

                # Scroll map
                elif command['code'] == 204:
                    pass

                # Set movement route
                elif command['code'] == 205:
                    event_id, route = command['parameters']
                    can_pause = self.parallel() and allow_pause
                    self.process_move_route(event_id, route, return_on_wait = can_pause)

                    if hasattr(self, 'paused') and self.paused:
                        if noisy_events:
                            print "WAIT DURING PARALLEL EVENT!! MOVE ROUTE AT INDEX %s PAUSED FOR %s" % (self.move_route_index, self.paused)
                        self.has_ever_paused = True
                        return
                    else:
                        self.move_route_index = 0

                # Change Transparency
                elif command['code'] == 211:
                    pass

                # Show character animation
                elif command['code'] == 212:
                    pass

                # "Show balloon icon"
                elif command['code'] == 213:
                    if self.parallel() and self.slowmo_or_realtime_map():
                        # Balloon wait time _duration is Sprite_Balloon.prototype.setup:
                        # (8 * Sprite_Balloon.prototype.speed) + Sprite_Balloon.prototype.waitTime
                        # == (8 * 8) + 12
                        # == 76
                        if noisy_events:
                            print "WAIT FOR BALLOON EVENT!! %s" % 76
                        self.list_index += 1
                        self.has_ever_paused = True
                        self.paused = 76
                        return

                # Erase Event
                elif command['code'] == 214:
                    self.state.map.erased_events[self.event_data['id']] = True

                # Change Player Followers
                elif command['code'] == 216:
                    pass

                # Gather followers
                elif command['code'] == 217:
                    pass

                # Fade In / Out
                elif command['code'] == 221:
                    game_state.faded_out = True
                    game_state.wait(24) # 'fadeSpeed' from the RPGM code is 24 frames

                elif command['code'] == 222:
                    game_state.faded_out = False
                    game_state.wait(24) # 'fadeSpeed' from the RPGM code is 24 frames

                # Shake / etc
                elif command['code'] in [223, 225]:
                    pass

                elif command['code'] == 224: # Flash screen
                    game_state.pause()

                # Pause
                elif command['code'] == 230:
                    wait_time = command['parameters'][0]
                    if self.parallel():
                        if allow_pause and (wait_time >= rpgm_game_data.get('pause_wait_time', 45) or self.slowmo_or_realtime_map() and not (rpgm_game_data.get('has_dpad_animations', None) and self.state.map.surrounded_by_events(self.state.player_x, self.state.player_y))):
                            if noisy_events:
                                print "WAIT DURING PARALLEL EVENT!! %s" % wait_time
                            self.list_index += 1
                            self.has_ever_paused = True
                            self.paused = wait_time
                            return
                        else:
                            self.state.requeue_parallel_events_if_changed()

                    game_state.wait(wait_time, source_event = self)

                # Show picture / Move picture
                elif command['code'] == 231 or command['code'] == 232:
                    picture_id, picture_name, origin = command['parameters'][0:3]
                    x, y = None, None
                    if command['parameters'][3] == 0:
                        x = command['parameters'][4]
                        y = command['parameters'][5]
                    else:
                        x = game_state.variables.value(command['parameters'][4])
                        y = game_state.variables.value(command['parameters'][5])

                    scale_x, scale_y, opacity, blend_mode = command['parameters'][6:10]
                    duration, wait = None, None

                    picture_args = None
                    if command['code'] == 231:
                        if len(picture_name) == 0:
                            game_state.hide_picture(picture_id)
                            self.list_index += 1
                            return
                        picture_args = {
                            'image_name': rpgm_picture_name(picture_name),
                            'picture_name': picture_name
                        }
                    else:
                        duration, wait = command['parameters'][10:12]
                        existing_picture_args = game_state.queued_or_shown_picture_frame(picture_id)
                        if existing_picture_args:
                            picture_args = existing_picture_args.copy()
                        else:
                            self.list_index += 1
                            return

                    if picture_args:
                        picture_args['opacity'] = opacity
                        picture_args['blend_mode'] = blend_mode
                        if command['code'] == 231 and not game_state.occluded():
                            iavra_gif_details = self.iavra_gif_details(picture_name)
                            olivia_animated_picture_details = self.olivia_animated_picture_details(picture_name)
                            if iavra_gif_details:
                                image_size = image_size_cache.for_picture_name(rpgm_picture_name(picture_name))
                                frame_count, frame_delay = iavra_gif_details
                                self.bake_filmstrip_image(
                                  picture_args,
                                  image = normal_images[rpgm_picture_name(picture_name)],
                                  image_size = image_size,
                                  horiz_cells = frame_count,
                                  vert_cells = 1,
                                  frame_delay = frame_delay
                                )
                            elif olivia_animated_picture_details:
                                image_size = image_size_cache.for_picture_name(rpgm_picture_name(picture_name))
                                horiz_cells, vert_cells = olivia_animated_picture_details
                                self.bake_filmstrip_image(
                                  picture_args,
                                  image = normal_images[rpgm_picture_name(picture_name)],
                                  image_size = image_size,
                                  horiz_cells = horiz_cells,
                                  vert_cells = vert_cells,
                                  frame_delay = 4
                                )
                            else:
                                picture_args['scale_x'] = scale_x
                                picture_args['scale_y'] = scale_y
                        if origin == 0: # origin of 0 means x,y is topleft
                            picture_args['x'] = x
                            picture_args['y'] = y
                        else: # origin of 1 means x,y is image center
                            game_state.add_image_size_to_frame(picture_args)
                            picture_args['x'] = x - picture_args['size'][0] / 2
                            picture_args['y'] = y - picture_args['size'][1] / 2

                        if self.parallel():
                            picture_args['loop'] = True

                        picture_args['event_command_reference'] = self.event_command_reference()

                        if command['code'] == 231:
                            game_state.show_picture(picture_id, picture_args)
                        else:
                            game_state.move_picture(picture_id, picture_args, wait, duration)

                # Tint picture - TODO ?
                elif command['code'] == 234:
                    pass

                # Erase picture
                elif command['code'] == 235:
                    picture_id = command['parameters'][0]
                    game_state.hide_picture(picture_id)

                # Weather Effect
                elif command['code'] == 236:
                    pass

                # Play BGM (background music)
                elif command['code'] == 241:
                    game_state.queue_background_music(command['parameters'][0]['name'], command['parameters'][0]['volume'])

                # Fadeout BGM
                elif command['code'] == 242:
                    game_state.queue_background_music(None)

                # Save BGM
                elif command['code'] == 243:
                    pass

                # Resume BGM
                elif command['code'] == 244:
                    pass

                # Play BGS (background sound)
                elif command['code'] == 245:
                    game_state.queue_background_sound(command['parameters'][0]['name'], command['parameters'][0]['volume'])

                # Fadeout BGS
                elif command['code'] == 246:
                    game_state.queue_background_sound(None)

                # Play ME (effects music)
                elif command['code'] == 249:
                    pass

                # Play SE (sound effect)
                elif command['code'] == 250:
                    game_state.queue_sound_effect(command['parameters'][0]['name'], command['parameters'][0]['volume'])

                # Stop SE
                elif command['code'] == 251:
                    game_state.queue_sound_effect(None)

                # Play Movie
                elif command['code'] == 261:
                    renpy.show(rpgm_movie_name(command['parameters'][0]), tag = "movie", layer = "maplayer")
                    game_state.pause()
                    renpy.hide("movie", layer = "maplayer")

                # Change Tileset
                elif command['code'] == 282:
                    self.state.map.override_tileset(command['parameters'][0])

                # Change Parallax
                elif command['code'] == 284:
                    pass

                # Get Location Info
                elif command['code'] == 285:
                    variable_id = command['parameters'][0]
                    operation = command['parameters'][1]
                    x, y, value = None, None, None
                    if command['parameters'][2] == 0:
                        x = command['parameters'][3]
                        y = command['parameters'][4]
                    else:
                        x = game_state.variables.value(command['parameters'][3])
                        y = game_state.variables.value(command['parameters'][4])

                    if operation == 0: # Terrain Tag
                        value = self.state.map.terrain_tag(x, y)
                    elif operation == 1: # Event ID
                        event = self.state.map.find_event_for_location(x, y)
                        if event:
                            value = event.event_data['id']
                        else:
                            value = 0
                    elif operation in [2,3,4,5]: # Tile ID
                        value = self.state.map.tile_id(x, y, operation - 2)
                    else: # Region ID
                        value = self.state.map.tile_region(x, y)

                    self.state.variables.set_value(variable_id, value)

                # Battle
                elif command['code'] == 301:
                    troop_id = None
                    if command['parameters'][0] == 0:
                        troop_id = command['parameters'][1]
                    elif command['parameters'][0] == 1:
                        troop_id = self.state.variables.value(command['parameters'][1])
                    else:
                        troop_id = self.state.map.random_encounter_troop_id(self.state.player_x, self.state.player_y)

                    result = self.fight_troop(troop_id)
                    if result != None:
                        if result == 0: # Winning
                            self.gain_fight_rewards(troop_id)

                        self.branch[command['indent']] = result

                # Shop
                elif command['code'] == 302:
                    if hasattr(self.state, 'shop_params'):
                        self.state.shop_params.clear()
                    else:
                        self.state.shop_params = {}
                    self.state.shop_params['goods'] = [command['parameters']]
                    self.state.shop_params['purchase_only'] = command['parameters'][4]
                    while self.page['list'][self.list_index + 1]['code'] in [605]:
                        self.list_index += 1
                        next_command = self.page['list'][self.list_index]
                        self.state.shop_params['goods'].append(next_command['parameters'])

                # Get actor name
                elif command['code'] == 303:
                    actor_index = command['parameters'][0]
                    self.request_actor_name(actor_index)

                # Change HP / MP
                elif command['code'] in [311, 312]:
                    operation, operand_type, operand = command['parameters'][2:5]
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    actor_indices = self.actor_indices_for_ex_iteration(command['parameters'][0], command['parameters'][1])
                    for actor_index in actor_indices:
                        actor = self.state.actors.by_index(actor_index)
                        if command['code'] == 311:
                            allow_death = command['parameters'][5]
                            # TODO: process death by HP change, I guess?
                            actor.change_hp(value)
                        elif command['code'] == 312:
                            print "Change MP by %s" % value
                            actor.change_mp(value)

                # Change state
                elif command['code'] == 313:
                    actor_indices = self.actor_indices_for_ex_iteration(command['parameters'][0], command['parameters'][1])
                    for actor_index in actor_indices:
                        actor = self.state.actors.by_index(actor_index)
                        state_to_change = command['parameters'][3]
                        if command['parameters'][2] == 0:
                            actor.add_state(state_to_change)
                        else:
                            actor.remove_state(state_to_change)

                # Recover all
                elif command['code'] == 314:
                    actor_indices = self.actor_indices_for_ex_iteration(command['parameters'][0], command['parameters'][1])
                    for actor_index in actor_indices:
                        actor = self.state.actors.by_index(actor_index)
                        actor.recover_all()

                # Change EXP / Change Level
                elif command['code'] in [315, 316]:
                    operation, operand_type, operand = command['parameters'][2:5]
                    value = self.state.variables.operate_value(operation, operand_type, operand)

                    actor_indices = self.actor_indices_for_ex_iteration(command['parameters'][0], command['parameters'][1])
                    for actor_index in actor_indices:
                        actor = self.state.actors.by_index(actor_index)
                        if command['code'] == 315:
                            actor.add_exp(value)
                        elif command['code'] == 316:
                            actor.add_level(value)

                # Change Parameter
                elif command['code'] == 317:
                    operation, operand_type, operand = command['parameters'][3:6]
                    value = self.state.variables.operate_value(operation, operand_type, operand)

                    actor_indices = self.actor_indices_for_ex_iteration(command['parameters'][0], command['parameters'][1])
                    for actor_index in actor_indices:
                        actor = self.state.actors.by_index(actor_index)
                        actor.add_param(command['parameters'][2], value)

                # Change skills
                elif command['code'] == 318:
                    actor_indices = self.actor_indices_for_ex_iteration(command['parameters'][0], command['parameters'][1])
                    for actor_index in actor_indices:
                        actor = self.state.actors.by_index(actor_index)
                        skill_to_change = command['parameters'][3]
                        if command['parameters'][2] == 0:
                            actor.learn_skill(skill_to_change)
                        else:
                            actor.forget_skill(skill_to_change)

                # Change equipment
                elif command['code'] == 319:
                    print ("command319 (change equipment) called with params: %s" % command['parameters'])

                # Change actor name
                elif command['code'] == 320:
                    actor_index, actor_name = command['parameters'][0:2]
                    actor = self.state.actors.by_index(actor_index)
                    actor.set_property('name', actor_name)

                # Change class
                elif command['code'] == 321:
                    actor_index, class_index = command['parameters'][0:2]
                    actor = self.state.actors.by_index(actor_index)
                    actor.set_property('class_index', class_index)

                # Change actor image
                elif command['code'] == 322:
                    actor_index, new_character_name, new_character_index, new_face_name, new_face_index = command['parameters'][0:5]
                    actor = self.state.actors.by_index(actor_index)
                    actor.set_property('characterName', new_character_name)
                    actor.set_property('characterIndex', new_character_index)
                    actor.set_property('faceName', new_face_name)
                    actor.set_property('faceIndex', new_face_index)

                # Change actor nickname
                elif command['code'] == 324:
                    actor_index, nickname = command['parameters'][0:2]
                    actor = self.state.actors.by_index(actor_index)
                    actor.set_property('nickname', nickname)

                # Enemy / Battle commands
                elif command['code'] in [331, 332, 333, 334, 335, 336, 337, 339, 340, 342]:
                    pass

                # Open Save Screen
                elif command['code'] == 352:
                    renpy.say(None, "RPGMaker would show the save screen right now. You can just open it at your leisure.")

                # Game Over
                elif command['code'] == 353:
                    renpy.pause()
                    renpy.full_restart()

                # Return to title
                elif command['code'] == 354:
                    if rpgm_game_data.get('ignore_return_to_title', False):
                        self.list_index += 1
                        return
                    renpy.pause()
                    renpy.full_restart()

                # 'Script'
                elif command['code'] == 355:
                    if len(command['parameters']) != 1:
                      renpy.say(None, "More than one parameter in script eval starting with '%s'" % command['parameters'][0])
                      return
                    script_lines = [command['parameters'][0]]
                    while self.page['list'][self.list_index + 1]['code'] in [655]:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        if len(command['parameters']) != 1:
                          renpy.say(None, "More than one parameter in script eval starting with '%s'" % command['parameters'][0])
                          return
                        script_lines.append(command['parameters'][0])
                    self.eval_script("\n".join(script_lines))

                # On Battle Win
                elif command['code'] == 601:
                    if self.branch[command['indent']] != 0:
                        self.skip_branch(command['indent'])

                # On Battle Escape
                elif command['code'] == 602:
                    if self.branch[command['indent']] != 1:
                        self.skip_branch(command['indent'])

                # On Battle Lose
                elif command['code'] == 603:
                    if self.branch[command['indent']] != 2:
                        self.skip_branch(command['indent'])

                # Dunno, probably battle related?
                elif command['code'] == 604:
                    pass

                # 'Plugin'
                elif command['code'] == 356:
                    split_params = command['parameters'][0].split(' ')
                    plugin_command, plugin_command_args = split_params[0], split_params[1:]
                    if plugin_command == 'OpenSynthesis':
                        self.list_index += 1
                        self.state.show_synthesis_ui()
                    elif plugin_command == 'OuterSelfSwitch':
                        value = plugin_command_args[0] == 'on'
                        event_id = int(plugin_command_args[1])
                        character = plugin_command_args[2]
                        self.state.self_switches.set_value((self.get_map_id(), event_id, character), value)
                    elif plugin_command == 'ChainCommand':
                        def represents_int(s):
                            try:
                                int(s)
                                return True
                            except ValueError:
                                return False

                        if represents_int(plugin_command_args[0]) and represents_int(plugin_command_args[1]):
                            result = renpy.display_menu([("A QTE is happening!", None), ("Succeed!", True), ("Fail!", False)])
                            self.state.switches.set_value(int(plugin_command_args[1]), result)
                    elif plugin_command in ['HideMiniLabel', 'ShowMiniLabel', 'JUMPACTION']:
                        pass
                    elif plugin_command.upper() in ['HIDE_CHOICE', 'HIDECHOICE']:
                        self.hide_choice(int(plugin_command_args[0]))
                    elif TerraxLighting.is_lighting_command(plugin_command):
                        pass
                    elif plugin_command in ['SmartPath']:
                        pass
                    elif plugin_command in ['MobileUI']:
                        pass
                    elif plugin_command in ['Flashlight']:
                        pass
                    elif YepXExtMesPack1.valid_command(plugin_command):
                        pass
                    elif plugin_command in ['MobileDirPad', 'BUST']:
                        pass
                    elif plugin_command in ['CAM']:
                        pass
                    elif plugin_command in ['AnimatedPicture']:
                        picture_id = int(plugin_command_args[0])
                        if plugin_command_args[1] == 'Speed':
                            desired_delay = int(plugin_command_args[2])
                            picture = self.state.queued_or_shown_picture(picture_id)
                            picture['image_name'].reset_frame_delays(desired_delay)
                    elif plugin_command in ['ShowGab', 'ClearGab'] or plugin_command.startswith('GabText'):
                        pass
                    elif plugin_command in ['FocusCamera', 'ResetFocus', 'WaitForCamera']:
                        pass
                    elif YepQuestManager.valid_command(plugin_command):
                        self.state.party.yep_quest_manager().process_command(plugin_command_args)
                    elif GameusQuestManager.valid_command(plugin_command):
                        self.state.party.gameus_quest_manager().process_command(plugin_command_args)
                    elif plugin_command in ['AutoSave', 'LAYER', 'LAYER_S']:
                        pass
                    elif plugin_command in ['question'] and game_file_loader.plugin_data_exact('RedHatAugust - Q&A'):
                        word_count_of_question = plugin_command_args[0]
                        question_typed_without_quotes = plugin_command_args[1]
                        word_count_of_answer = plugin_command_args[2]
                        answer_typed_without_quotes = plugin_command_args[3]
                        word_count_of_correct_response = plugin_command_args[4]
                        correct_response_typed_without_quotes = plugin_command_args[5]
                        correct_answer_switchID = plugin_command_args[6]
                        correct_answer_switchID_status = plugin_command_args[7]
                        word_count_of_incorrect_response = plugin_command_args[8]
                        incorrect_response_typed_without_quotes = plugin_command_args[9]

                        answer = renpy.input("{i}%s{/i}" % question_typed_without_quotes)
                        if answer == answer_typed_without_quotes:
                            game_state.say_text(None, correct_response_typed_without_quotes)
                            self.state.switches.set_value(int(correct_answer_switchID), correct_answer_switchID_status == 'true')
                        else:
                            game_state.say_text(None, incorrect_response_typed_without_quotes)
                    elif plugin_command in ['enable_picture']:
                        # MOG_PictureGallery
                        pass
                    elif plugin_command.startswith('textInput'):
                        actor_index = int(plugin_command_args[0])
                        self.request_actor_name(actor_index)
                    else:
                        renpy.say(None, "Plugin command not implemented: '%s'" % plugin_command)

                # When [**]
                elif command['code'] == 402:
                    if self.branch[command['indent']] != command['parameters'][0]:
                        self.skip_branch(command['indent'])

                # When Cancel
                elif command['code'] == 403:
                    if self.branch[command['indent']] >= 0:
                        self.skip_branch(command['indent'])

                # TODO: unknown
                elif command['code'] == 404:
                    pass

                # Some mouse hover thingie
                elif command['code'] == 408:
                    pass

                # Else
                elif command['code'] == 411:
                    if self.branch[command['indent']] != False:
                        self.skip_branch(command['indent'])

                # Seems unimplemented?
                elif command['code'] == 412:
                    pass

                # TODO: Something related to movement (friends with command 205)
                elif command['code'] == 505:
                    # Skip all contiguous 505s to reduce log spam with noisy_events
                    while self.page['list'][self.list_index + 1]['code'] == 505:
                        self.list_index += 1

                else:
                    renpy.say(None, "Code %d not implemented, plz fix." % command['code'])

                self.list_index += 1

        def event_command_reference(self):
            return (
                'common' if self.common() else self.map_id,
                self.event_data['id'],
                None if self.common() else self.page_index,
                self.list_index
            )

        # replicates iterateActorEx in rpgm code
        def actor_indices_for_ex_iteration(self, param1, param2):
            if param1 == 0:
                if param2 == 0:
                    return self.state.party.members
                else:
                    return [param2]
            else:
                return [self.state.variables.value(param2)]

        def fight_troop(self, troop_id):
            troop_json = game_file_loader.json_file(rpgm_data_path("Troops.json"))
            if troop_id > 0 and troop_id < len(troop_json):
                troop_data = troop_json[troop_id]

                return renpy.display_menu([
                    ("A battle with '%s'!" % game_state.escape_text_for_renpy(troop_data['name']), None),
                    ("You Win!", 0),
                    ("You Escape!", 1),
                    ("You Lose!", 2)
                ])

        def gain_fight_rewards(self, troop_id):
            troop_json = game_file_loader.json_file(rpgm_data_path("Troops.json"))
            enemies_json = game_file_loader.json_file(rpgm_data_path("Enemies.json"))
            troop_members = troop_json[troop_id]['members']
            troop_enemies = [enemies_json[enemy['enemyId']] for enemy in troop_members]

            gained_gold = sum([enemy['gold'] for enemy in troop_enemies])
            gained_exp = sum([enemy['exp'] for enemy in troop_enemies])
            gained_items = []
            for enemy in troop_enemies:
                for drop_item in enemy['dropItems']:
                    if drop_item['kind'] == 1:
                        gained_items.append(self.state.items.by_id(drop_item['dataId']))
                    elif drop_item['kind'] == 2:
                        gained_items.append(self.state.weapons.by_id(drop_item['dataId']))
                    elif drop_item['kind'] == 3:
                        gained_items.append(self.state.armors.by_id(drop_item['dataId']))

            gain_message = []
            if gained_gold > 0:
                gain_message.append("Gained Gold: %s" % gained_gold)
                self.state.party.gain_gold(gained_gold)
            if gained_exp > 0:
                gain_message.append("Gained Exp: %s" % gained_exp)
                self.state.party.gain_exp(gained_exp)
            if len(gained_items) > 0:
                gain_message.append("Gained Items: %s" % ', '.join([item['name'] for item in gained_items]))
                for item in gained_items:
                    self.state.party.gain_item(item, 1)
            if len(gain_message) > 0:
                game_state.say_text(None, "\n".join(gain_message))

        def iavra_gif_details(self, image_name):
            iavra_gif_plugin = game_file_loader.plugin_data_exact('iavra_gif')
            if iavra_gif_plugin:
                gre = Re()
                if gre.search(iavra_gif_plugin['parameters']['File Name Format'], image_name):
                    frame_count, frame_delay = gre.last_match.groups()
                    return (int(frame_count), int(frame_delay))
            return None

        def olivia_animated_picture_details(self, image_name):
            olivia_animated_picture_plugin = game_file_loader.plugin_data_exact('Olivia_AnimatedPictures')
            if olivia_animated_picture_plugin:
                gre = Re()
                if gre.search('\[(\d+)x(\d+)\]', image_name):
                    horiz_cells, vert_cells = gre.last_match.groups()
                    return (int(horiz_cells), int(vert_cells))

        def bake_filmstrip_image(self, picture_args, image = None, image_size = None, horiz_cells = 0 , vert_cells = 0, frame_delay = 4):
            picture_frames = []
            for y in xrange(0, vert_cells):
                for x in xrange(0, horiz_cells):
                    frame_width = image_size[0] / horiz_cells
                    frame_height = image_size[1] / vert_cells
                    frame_img = im.Crop(
                        image,
                        (
                            x * frame_width,
                            y * frame_height,
                            frame_width,
                            frame_height
                        )
                    )
                    picture_frames.append({"size": (frame_width, frame_height), "image_name": frame_img, "wait": frame_delay})
            picture_args["image_name"] = RpgmAnimation.create_from_frames(picture_frames, loop = True)
            picture_args["size"] = (frame_width, frame_height)

        def done(self):
            return self.list_index == len(self.page['list'])
