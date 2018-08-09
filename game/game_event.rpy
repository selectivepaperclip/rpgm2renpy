init python:
    class GameEvent:
        def __init__(self, state, event_data, page):
            self.state = state
            self.event_data = event_data
            self.page = page
            self.list_index = 0
            self.new_map_id = None
            self.choices_to_hide = []
            self.branch = {}

        def common(self):
            return self.event_data.has_key('switchId')

        def parallel(self):
            return self.page['trigger'] == 4

        def conditional_branch_result(self, params):
            operation = params[0]
            # Switches
            if operation == 0:
                return self.state.switches.value(params[1]) == (params[2] == 0)
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
                    key = (self.state.map.map_id, event_data['id'], params[1])
                    return self.state.self_switches.value(key) == (params[2] == 0)
            # Timer
            elif operation == 3:
                renpy.say(None, "Conditional statements for Timer not implemented")
                return False
                #if ($gameTimer.isWorking()) {
                #    if (this._params[2] === 0) {
                #        result = ($gameTimer.seconds() >= this._params[1]);
                #    } else {
                #        result = ($gameTimer.seconds() <= this._params[1]);
                #    }
                #}
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
                        return actor['name'] == n
                    elif params[2] == 6: # State
                        if hasattr(actor, 'affected_states'):
                            return n in actor['affected_states']
                        return False
                    else:
                        renpy.say(None, ("Operand %s for Actor conditions not implemented!" % params[2]))
                        return False
                #var actor = $gameActors.actor(this._params[1]);
                #if (actor) {
                #    var n = this._params[3];
                #    switch (this._params[2]) {
                #    case 0:  // In the Party
                #        result = $gameParty.members().contains(actor);
                #        break;
                #    case 1:  // Name
                #        result = (actor.name() === n);
                #        break;
                #    case 2:  // Class
                #        result = actor.isClass($dataClasses[n]);
                #        break;
                #    case 3:  // Skill
                #        result = actor.isLearnedSkill(n);
                #        break;
                #    case 4:  // Weapon
                #        result = actor.hasWeapon($dataWeapons[n]);
                #        break;
                #    case 5:  // Armor
                #        result = actor.hasArmor($dataArmors[n]);
                #        break;
                #    case 6:  // State
                #        result = actor.isStateAffected(n);
                #        break;
                #    }
                #}
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
                    renpy.say(None, "Direction checks for non-player Character not implemented")
                    return False
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
                renpy.say(None, "Conditional statements for Button not implemented")
                return False
                #result = Input.isPressed(this._params[1]);
            # Script
            elif operation == 12:
                renpy.say(None, "Conditional statements for Script not implemented")
                return False
                #result = !!eval(this._params[1]);
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
            self.list_index = len(self.page['list']) - 1

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

        def hide_choice(self, choice_id):
            if not hasattr(self, 'choices_to_hide'):
                self.choices_to_hide = []
            self.choices_to_hide.append(choice_id)

        def eval_script(self, script_string):
            xhr_compare_command = re.match(re.compile("var xhr = new XMLHttpRequest\(\);.*if\(.*?\) {\n(.*?)}", re.DOTALL), script_string)

            if xhr_compare_command:
                success_clause = xhr_compare_command.groups()[0]
                self.eval_script(success_clause.strip())
                return

            for line in script_string.split("\n"):
                variable_set_command = re.match("\$gameVariables\.setValue\((\d+),\s*(.+)\);?", line)
                self_switch_set_command = re.match("\$gameSelfSwitches\.setValue\(\[(\d+),(\d+),'(.*?)'\], (\w+)\);?", line)
                hide_choice_command = re.match("hide_choice\((\d+), \"\$gameSwitches\.value\((\d+)\) === (\w+)\"\)", line)

                if 'ImageManager' in line:
                    pass
                elif variable_set_command:
                    groups = variable_set_command.groups()
                    variable_id = int(groups[0])
                    value = self.eval_fancypants_value_statement(groups[1])
                    self.state.variables.set_value(variable_id, value)
                elif hide_choice_command:
                    groups = hide_choice_command.groups()
                    choice_id, switch_id, switch_value = (int(groups[0]), int(groups[1]), groups[2] == 'true')
                    if self.state.switches.value(switch_id) == switch_value:
                        self.hide_choice(choice_id)
                elif self_switch_set_command:
                    groups = self_switch_set_command.groups()
                    map_id, event_id, self_switch_name, self_switch_value = (int(groups[0]), int(groups[1]), groups[2], groups[3] == 'true')
                    self.state.self_switches.set_value((map_id, event_id, self_switch_name), self_switch_value)
                elif line == 'SceneManager.push(Scene_Menu);':
                    self.state.show_inventory()
                elif GameIdentifier().is_milfs_control() and GameSpecificCodeMilfsControl().eval_script(line, script_string):
                    pass
                else:
                    print "Script that could not be evaluated:\n"
                    print script_string
                    renpy.say(None, "Code 355 not implemented to eval script including line '%s'\nSee console for full script" % line.replace("{", "{{"))
                    return

        def eval_fancypants_value_statement(self, script_string):
            while True:
                still_has_variables = re.search('\$gameVariables.value\((\d+)\)', script_string)
                if still_has_variables:
                    script_string = re.sub(r'\$gameVariables.value\((\d+)\)', lambda m: str(self.state.variables.value(int(m.group(1)))), script_string)
                else:
                    break

            # eval the statement in python-land if it looks like it contains only arithmetic expressions
            if re.match('^[\d\s.+\-*()\s]+$', script_string):
                return eval(script_string)
            else:
                renpy.say(None, "Remaining non-evaluatable fancypants value statement: %s" % script_string)
                return 0

        def show_parallel_event_animations(self, switch_id):
            for newly_activated_event in self.state.map.parallel_events_activated_by_switch(switch_id):
                frame_data = {}
                last_picture_id = None
                not_an_animation = False
                for newly_activated_command in newly_activated_event['list']:
                    x, y = None, None
                    if newly_activated_command['code'] in [231]:
                        if newly_activated_command['parameters'][3] == 0:
                            x = newly_activated_command['parameters'][4]
                            y = newly_activated_command['parameters'][5]
                        else:
                            x = game_state.variables.value(newly_activated_command['parameters'][4])
                            y = game_state.variables.value(newly_activated_command['parameters'][5])

                    # TODO: isn't responsive to conditionals in event
                    if newly_activated_command['code'] == 231:
                        last_picture_id = newly_activated_command['parameters'][0]
                        image_name = newly_activated_command['parameters'][1]
                        new_frame_data = {"wait": 0, "image_name": rpgm_picture_name(image_name), "x": x, "y": y}
                        if last_picture_id in frame_data:
                            frame_data[last_picture_id].append(new_frame_data)
                        else:
                            frame_data[last_picture_id] = [new_frame_data]
                    elif newly_activated_command['code'] == 230:
                        frame_data[last_picture_id][-1]['wait'] += newly_activated_command['parameters'][0]
                    elif newly_activated_command['code'] == 101:
                        not_an_animation = True
                if not_an_animation:
                    continue
                    
                for picture_id, picture_frames in frame_data.iteritems():
                    if len(picture_frames) == 1:
                        game_state.shown_pictures[picture_id] = {"image_name": RpgmAnimationBuilder.image_for_picture(picture_frames[0])}
                        continue

                    picture_transitions = RpgmAnimationBuilder(picture_frames).build(loop = True)

                    if len(picture_transitions) > 1:
                        game_state.shown_pictures[picture_id] = {"image_name": RpgmAnimation(*picture_transitions)}

        def migrate_global_branch_data(self):
            if not hasattr(self, 'branch') and hasattr(game_state, 'branch'):
                for event in game_state.events:
                    event.branch = game_state.branch
                del game_state.branch

        def do_next_thing(self):
            if not self.done():
                self.migrate_global_branch_data()
                command = self.page['list'][self.list_index]

                if hasattr(game_state, 'queued_pictures') and len(game_state.queued_pictures) > 0:
                    if command['code'] in [101, 102, 103, 104, 301, 302, 303]:
                        game_state.flush_queued_pictures()
                        return

                if noisy_events:
                    print("map %s, event %s, page %s, command %s (%s)" % (game_state.map.map_id, self.event_data['id'], self.event_data['pages'].index(self.page) if ('pages' in self.event_data) else 'n/a', self.list_index, command['code']))

                # Do nothing
                if command['code'] == 0:
                    pass

                # Show text
                elif command['code'] == 101:
                    ends_with_whitespace_pattern = re.compile("\s$")
                    accumulated_text = []
                    while len(self.page['list']) > self.list_index + 1 and self.page['list'][self.list_index + 1]['code'] == 401:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        text = game_state.replace_names(command['parameters'][0])
                        # If the previous line didn't end with a space, add a space before joining to the next line
                        if len(accumulated_text) > 0 and not re.match(ends_with_whitespace_pattern, accumulated_text[-1]):
                            accumulated_text.append(' ')
                        accumulated_text.append(text)
                        # Always put newlines after colons and periods
                        if text.endswith(":") or text.endswith('.'):
                            accumulated_text.append("\n")

                    text_to_show = "".join(accumulated_text).strip()
                    if len(text_to_show) > 0:
                        renpy.say(None, re.sub('%', '%%', text_to_show))
                    else:
                        game_state.pause()

                # Show choices
                elif command['code'] == 102:
                    choice_texts = command['parameters'][0]
                    cancel_type = command['parameters'][1]
                    if cancel_type >= len(choice_texts):
                        cancel_type = -2

                    if not hasattr(self, 'choices_to_hide'):
                        self.choices_to_hide = []

                    result = renpy.display_menu([(game_state.replace_names(text), index) for index, text in enumerate(choice_texts) if index not in self.choices_to_hide])
                    self.branch[command['indent']] = result
                    self.choices_to_hide = []

                # Input number
                elif command['code'] == 103:
                    variable_id, max_digits = command['parameters']
                    entered_a_number = False
                    while not entered_a_number:
                        try:
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
                        if GameIdentifier().is_my_summer():
                            # only show the cancel button the status screen for my_summer, could be a little fragile
                            current_event = self.state.events[-1]
                            if current_event.common() and current_event.event_data['id'] == 1:
                                screen_args["background"] = False
                                screen_args["allow_cancel"] = True

                        result = renpy.display_menu(
                            sorted(item_options, key=lambda opt: opt[0]),
                            scope = screen_args,
                            screen='inventory_choice_screen'
                        )
                    else:
                        renpy.say(None, "No items to choose...")
                    self.state.variables.set_value(variable_id, result)

                # Comment
                elif command['code'] == 108:
                    pass

                # Conditional branch
                elif command['code'] == 111:
                    branch_result = self.conditional_branch_result(command['parameters'])
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
                    return GameEvent(self.state, common_event, common_event)

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
                            self.jump_to(index, current_indent = command['indent'])

                # Control Switches
                elif command['code'] == 121:
                    start, end, value = command['parameters'][0:3]
                    for i in xrange(start, end + 1):
                        switch_on = (value == 0)
                        self.state.switches.set_value(i, switch_on)
                        if switch_on:
                            self.show_parallel_event_animations(i)

                # Control Variables
                elif command['code'] == 122:
                    start, end, operation_type, operand = command['parameters'][0:4]
                    value = 0
                    if operand == 0:
                        value = command['parameters'][4]
                    elif operand == 1:
                        value = self.state.variables.value(command['parameters'][4])
                    elif operand == 2:
                        value = command['parameters'][4] + random.randint(0, command['parameters'][5] - command['parameters'][4]);
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
                            # var actor = $gameActors.actor(param1);
                            if game_data_operand_param2 == 0: # Level
                                # return actor.level;
                                renpy.say(None, ("Variable control operand 3 not implemented for type 3 (Level), plz implement"))
                            elif game_data_operand_param2 == 1: # EXP
                                # return actor.currentExp();
                                renpy.say(None, ("Variable control operand 3 not implemented for type 3 (EXP), plz implement"))
                            elif game_data_operand_param2 == 1: # HP
                                # return actor.hp;
                                renpy.say(None, ("Variable control operand 3 not implemented for type 3 (HP), plz implement"))
                            elif game_data_operand_param2 == 1: # MP
                                # return actor.mp;
                                renpy.say(None, ("Variable control operand 3 not implemented for type 3 (MP), plz implement"))
                            else: # Parameter
                                # if (param2 >= 4 && param2 <= 11) {
                                #    return actor.param(param2 - 4);
                                # }
                                renpy.say(None, ("Variable control operand 3 not implemented for actor parameter, plz implement"))
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
                                if game_data_operand_param2 == 0: # Map X
                                    value = self.state.map.event_location(self.event_data)[0]
                                elif game_data_operand_param2 == 1: # Map Y
                                    value = self.state.map.event_location(self.event_data)[1]
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
                                value = self.state.map.map_id
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
                        if re.search('\$gameVariables.value\((\d+)\)', script_string):
                            value = self.eval_fancypants_value_statement(script_string)
                        else:
                            renpy.say(None, "Variable control operand 4 not implemented for '%s'" % script_string)
                            value = 0

                    for i in xrange(start, end + 1):
                        self.state.variables.operate_variable(i, operation_type, value)

                # Control Self Switch
                elif command['code'] == 123:
                    switch_id, value = command['parameters']
                    last_non_common_event = next((e for e in reversed(self.state.events) if not e.common()), None)
                    if last_non_common_event:
                        key = (self.state.map.map_id, last_non_common_event.event_data['id'], switch_id)
                        self.state.self_switches.set_value(key, value == 0)

                # Change gold
                elif command['code'] == 125:
                    operation, operand_type, operand = command['parameters']
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    self.state.party.gain_gold(value);

                # Change items
                elif command['code'] == 126:
                    item_id, operation, operand_type, operand = command['parameters']
                    value = self.state.variables.operate_value(operation, operand_type, operand)
                    self.state.party.gain_item(self.state.items.by_id(item_id), value)

                # Change party members -- TODO
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

                # Change save access
                elif command['code'] == 134:
                    pass

                # Toggle menu access
                elif command['code'] == 135:
                    pass

                # Transfer maps
                elif command['code'] == 201:
                    method, self.new_map_id, self.new_x, self.new_y = command['parameters'][0:4]
                    if debug_events:
                        renpy.say(None, "Map %d" % self.new_map_id)
                    if method != 0:
                        renpy.say(None, "Method on transfer was nonzero (%d), plz implement!" % method)

                # Set event location - TODO
                elif command['code'] == 203:
                    pass

                # Scroll map
                elif command['code'] == 204:
                    pass

                # Set movement route
                elif command['code'] == 205:
                    reachability_grid = self.state.map.reachability_grid_for_current_position()

                    character_index, route = command['parameters']
                    target = None
                    player_moving = character_index < 0
                    for route_part in route['list']:
                        delta_x = 0
                        delta_y = 0
                        if route_part['code'] == 1: # Move Down
                            delta_y += 1
                        elif route_part['code'] == 2: # Move Left
                            delta_x -= 1
                        elif route_part['code'] == 3: # Move Right
                            delta_x += 1
                        elif route_part['code'] == 4: # Move Up
                            delta_y -= 1
                        elif route_part['code'] == 12: # Move Forward
                            current_direction = game_state.player_direction
                            if current_direction == GameDirection.UP:
                                delta_y -= 1
                            elif current_direction == GameDirection.DOWN:
                                delta_y += 1
                            elif current_direction == GameDirection.LEFT:
                                delta_x -= 1
                            elif current_direction == GameDirection.RIGHT:
                                delta_x += 1
                        elif route_part['code'] == 29: # Change Speed
                            pass
                        elif route_part['code'] == 37: # Route Through On
                            if player_moving:
                                game_state.everything_reachable = True
                        elif route_part['code'] == 38: # Route Through Off
                            if player_moving:
                                game_state.everything_reachable = False
                        elif route_part['code'] == 41: # Change image
                            if player_moving:
                                new_character_name, new_character_index = route_part['parameters']
                                actor_index = 1
                                self.state.actors.set_property(actor_index, 'characterName', new_character_name)
                                self.state.actors.set_property(actor_index, 'characterIndex', new_character_index)
                            else:
                                # TODO: don't yet support changing other images
                                pass
                        elif route_part['code'] == 0:
                            pass

                        if delta_x != 0 or delta_y != 0:
                            if player_moving:
                                current_x, current_y = game_state.player_x, game_state.player_y
                            else:
                                loc = self.state.map.event_location(self.event_data)
                                if not loc:
                                    break
                                current_x, current_y = loc

                            new_x, new_y = current_x + delta_x, current_y + delta_y
                            if not (player_moving and game_state.everything_reachable):
                                if len(reachability_grid) > new_y and len(reachability_grid[new_y]) > new_x:
                                    if reachability_grid[new_y][new_x] == 2 or not self.state.map.can_move_vector(current_x, current_y, delta_x, delta_y):
                                          break

                            if player_moving: # Player Character
                                game_state.player_x, game_state.player_y = new_x, new_y
                            else:
                                self.state.map.override_event_location(self.event_data, (new_x, new_y))

                # Change Transparency
                elif command['code'] == 211:
                    pass

                # "Show baloon icon"
                elif command['code'] == 213:
                    pass

                # Erase Event
                elif command['code'] == 214:
                    self.state.map.erased_events[self.event_data['id']] = True

                # Fade In / Out
                elif command['code'] in [221, 222]:
                    game_state.wait(24) # 'fadeSpeed' from the RPGM code is 24 frames

                # Shake / etc
                elif command['code'] in [223, 225]:
                    pass

                elif command['code'] == 224: # Flash screen
                    game_state.pause()

                # Pause
                elif command['code'] == 230:
                    game_state.wait(command['parameters'][0])

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
                        picture_args = {'image_name': rpgm_picture_name(picture_name)}
                    else:
                        duration, wait = command['parameters'][10:12]
                        existing_picture_args = game_state.queued_or_shown_picture(picture_id)
                        if existing_picture_args:
                            picture_args = existing_picture_args.copy()
                        else:
                            self.list_index += 1
                            return

                    if picture_args:
                        picture_args['opacity'] = opacity
                        if command['code'] == 231:
                            if not picture_name in picture_image_sizes:
                                picture_image_sizes[picture_name] = renpy.image_size(normal_images[rpgm_picture_name(picture_name)])
                            image_size = picture_image_sizes[picture_name]
                            if scale_x != 100 or scale_y != 100:
                                image_size = (int(image_size[0] * scale_x / 100.0), int(image_size[1] * scale_y / 100.0))
                            if image_size[0] > config.screen_width and image_size[1] > config.screen_height:
                                image_size = (config.screen_width, config.screen_height)
                            picture_args['size'] = image_size
                        if origin == 0: # origin of 0 means x,y is topleft
                            picture_args['x'] = x
                            picture_args['y'] = y
                        else: # origin of 1 means it's screen center
                            picture_args['x'] = x - picture_args['size'][0] / 2
                            picture_args['y'] = y - picture_args['size'][1] / 2

                        if command['code'] == 231:
                            game_state.show_picture(picture_id, picture_args)
                        else:
                            game_state.move_picture(picture_id, picture_args)
                        if wait:
                            game_state.wait(duration)
                            game_state.flush_queued_pictures()

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

                # Audio
                elif command['code'] in [241, 242, 243, 244, 245, 246, 249, 250, 251]:
                    pass

                # Play Movie
                elif command['code'] == 261:
                    renpy.show(rpgm_movie_name(command['parameters'][0]), tag = "movie")
                    game_state.pause()
                    renpy.hide("movie")

                # Change Parallax
                elif command['code'] == 284:
                    pass

                # Battle
                elif command['code'] == 301:
                    result = renpy.display_menu([("A battle is happening!", None), ("You Win!", 0), ("You Escape!", 1), ("You Lose!", 2)])
                    self.branch[command['indent']] = result

                # Shop
                elif command['code'] == 302:
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
                    actor_name = renpy.input("What name should actor %d have?" % actor_index)
                    self.state.actors.set_property(actor_index, 'name', actor_name)

                # Change state
                elif command['code'] == 313:
                    direct = command['parameters'][0] == 0
                    actor_index = command['parameters'][1] if direct else self.state.variables.value(command['parameters'][1])
                    state_to_change = command['parameters'][3]
                    if command['parameters'][2] == 0:
                        self.state.actors.add_state(actor_index, state_to_change)
                    else:
                        self.state.actors.remove_state(actor_index, state_to_change)

                # Recover all
                elif command['code'] == 314:
                    pass

                # Change equipment
                elif command['code'] == 319:
                    print ("command319 (change equipment) called with params: %s" % command['parameters'])

                # Change actor name
                elif command['code'] == 320:
                    actor_index, actor_name = command['parameters'][0:2]
                    self.state.actors.set_property(actor_index, 'name', actor_name)

                # Change class
                elif command['code'] == 321:
                    actor_index, class_index = command['parameters'][0:2]
                    self.state.actors.set_property(actor_index, 'class_index', class_index)

                # Change actor image
                elif command['code'] == 322:
                    actor_index, new_character_name, new_character_index, new_face_name, new_face_index = command['parameters'][0:5]
                    self.state.actors.set_property(actor_index, 'characterName', new_character_name)
                    self.state.actors.set_property(actor_index, 'characterIndex', new_character_index)
                    self.state.actors.set_property(actor_index, 'faceName', new_face_name)
                    self.state.actors.set_property(actor_index, 'faceIndex', new_face_index)

                # Change actor nickname
                elif command['code'] == 324:
                    actor_index, nickname = command['parameters'][0:2]
                    self.state.actors.set_property(actor_index, 'nickname', nickname)

                # Open Save Screen
                elif command['code'] == 352:
                    renpy.say(None, "RPGMaker would show the save screen right now. You can just open it at your leisure.")

                # Return to title
                elif command['code'] == 354:
                    # TODO
                    pass

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
                        self.state.self_switches.set_value((self.state.map.map_id, event_id, character), value)

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

        def done(self):
            return self.list_index == len(self.page['list'])
