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

        def replace_names(self, text):
            # Replace statements from actor numbers, e.g. \N[2] with their actor name
            text = re.sub(r'\\N\[(\d+)\]', lambda m: self.state.actors.by_index(int(m.group(1)))['name'], text, flags=re.IGNORECASE)
            # Replace statements from variable ids, e.g. \V[2] with their value
            text = re.sub(r'\\V\[(\d+)\]', lambda m: str(self.state.variables.value(int(m.group(1)))), text, flags=re.IGNORECASE)
            # Replace statements from literal strings, e.g. \n<Doug> with that string followed by a colon
            text = re.sub(r'\\n\<(.*?)\>', lambda m: ("%s: " % m.group(1)), text)
            # Remove statements with image replacements, e.g. \I[314]
            text = re.sub(r'\\I\[(\d+)\]', '', text, flags=re.IGNORECASE)
            # Remove font size increase statements, e.g. \{
            text = re.sub(r'\\{', '', text)
            # Remove fancy characters from GALV_VisualNovelChoices.js
            text = re.sub(r'\\C\[(\d+)\]', '', text, flags=re.IGNORECASE)
            return text

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
                picture_transitions = []
                accumulated_wait = 0
                current_image = None
                picture_id = None
                not_an_animation = False
                for newly_activated_command in newly_activated_event['list']:
                    # TODO: isn't responsive to conditionals in event
                    if newly_activated_command['code'] == 230:
                        accumulated_wait += newly_activated_command['parameters'][0]
                    elif newly_activated_command['code'] == 231:
                        picture_id = newly_activated_command['parameters'][0]
                        image_name = newly_activated_command['parameters'][1]
                        if current_image and accumulated_wait > 0:
                            picture_transitions.append(current_image)
                            picture_transitions.append(accumulated_wait * 1/30.0)
                            picture_transitions.append(None)

                        current_image = image_name
                        accumulated_wait = 0
                    elif newly_activated_command['code'] == 101:
                        not_an_animation = True
                if not_an_animation:
                    continue
                if current_image and accumulated_wait > 0:
                    picture_transitions.append(current_image)
                    picture_transitions.append(accumulated_wait * 1/30.0)
                    picture_transitions.append(None)
                if len(picture_transitions) > 0:
                    game_state.show_picture(picture_id, {"image_name": anim.TransitionAnimation(*picture_transitions)})

        def migrate_global_branch_data(self):
            if not hasattr(self, 'branch') and hasattr(game_state, 'branch'):
                for event in game_state.events:
                    event.branch = game_state.branch
                del game_state.branch

        def do_next_thing(self):
            if not self.done():
                self.migrate_global_branch_data()
                command = self.page['list'][self.list_index]

                if noisy_events:
                    print("map %s, event %s, page %s, command %s (%s)" % (game_state.map.map_id, self.event_data['id'], self.event_data['pages'].index(self.page) if ('pages' in self.event_data) else 'n/a', self.list_index, command['code']))

                # Do nothing
                if command['code'] == 0:
                    pass

                # Show text
                elif command['code'] == 101:
                    accumulated_text = []
                    while len(self.page['list']) > self.list_index + 1 and self.page['list'][self.list_index + 1]['code'] == 401:
                        self.list_index += 1
                        command = self.page['list'][self.list_index]
                        text = self.replace_names(command['parameters'][0])
                        accumulated_text.append(text)
                        if text.endswith(":") or text.endswith('.'):
                            accumulated_text.append("\n")
                        if text.endswith(","):
                            accumulated_text.append(" ")

                    text_to_show = "".join(accumulated_text).strip()
                    if len(text_to_show) > 0:
                        renpy.say(None, re.sub('%', '%%', text_to_show))
                    else:
                        renpy.pause()

                # Show choices
                elif command['code'] == 102:
                    choice_texts = command['parameters'][0]
                    cancel_type = command['parameters'][1]
                    if cancel_type >= len(choice_texts):
                        cancel_type = -2

                    if not hasattr(self, 'choices_to_hide'):
                        self.choices_to_hide = []

                    result = renpy.display_menu([(self.replace_names(text), index) for index, text in enumerate(choice_texts) if index not in self.choices_to_hide])
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
                        result = renpy.display_menu(
                            sorted(item_options, key=lambda opt: opt[0]),
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
                    self.list_index = len(self.page['list']) - 1
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
                        self.list_index = len(self.page['list']) - 1
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
                            #case 5:  // Character
                            #    var character = this.character(param1);
                            #    if (character) {
                            #        switch (param2) {
                            #        case 0:  // Map X
                            #            return character.x;
                            #        case 1:  // Map Y
                            #            return character.y;
                            #        case 2:  // Direction
                            #            return character.direction();
                            #        case 3:  // Screen X
                            #            return character.screenX();
                            #        case 4:  // Screen Y
                            #            return character.screenY();
                            #        }
                            #    }
                            #    break;
                            renpy.say(None, ("Variable control operand 3 not implemented for type %s, plz implement" % game_data_operand_type))
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
                    key = (self.state.map.map_id, self.state.events[-1].event_data['id'], switch_id)
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
                    character_index, route = command['parameters']
                    if character_index < 0: # Player Character
                        if route['wait'] == True:
                          for route_part in route['list']:
                              if route_part['code'] == 12: # Move Forward
                                  print "Moving forward from direction %s" % game_state.player_direction
                                  if game_state.player_direction == GameDirection.UP:
                                      game_state.player_y -= 1
                                  elif game_state.player_direction == GameDirection.DOWN:
                                      game_state.player_y += 1
                                  elif game_state.player_direction == GameDirection.LEFT:
                                      game_state.player_x -= 1
                                  elif game_state.player_direction == GameDirection.RIGHT:
                                      game_state.player_x += 1
                              elif route_part['code'] == 29: # Change Speed
                                  pass
                              elif route_part['code'] == 0:
                                  pass

                # Change Transparency
                elif command['code'] == 211:
                    pass

                # "Show baloon icon"
                elif command['code'] == 213:
                    pass

                # Fade in/out/shake/etc
                elif command['code'] in [221, 222, 223, 225]:
                    pass

                elif command['code'] == 224: # Flash screen
                    renpy.pause()

                # Pause
                elif command['code'] == 230:
                    # Skip to the final pause if there's a series of pauses and audio
                    fast_forwarded = False
                    while self.page['list'][self.list_index + 1]['code'] in [230, 250]:
                        fast_forwarded = True
                        self.list_index += 1
                    if fast_forwarded:
                        self.list_index -= 1

                    if not hasattr(game_state, 'picture_since_last_pause'):
                        # Backfill the boolean for savegames from before this bit was introduced
                        game_state.picture_since_last_pause = True

                    if game_state.picture_since_last_pause and not self.parallel():
                        game_state.picture_since_last_pause = False
                        renpy.pause()

                # Show picture / Move picture
                elif command['code'] == 231 or command['code'] == 232:
                    if command['code'] == 231:
                        game_state.picture_since_last_pause = True
                    picture_id, picture_name, origin = command['parameters'][0:3]
                    x, y = None, None
                    if command['parameters'][3] == 0:
                        x = command['parameters'][4]
                        y = command['parameters'][5]
                    else:
                        x = game_state.variables.value(command['parameters'][4])
                        y = game_state.variables.value(command['parameters'][5])

                    scale_x, scale_y, opacity, blend_mode = command['parameters'][6:10]

                    picture_args = None
                    if command['code'] == 231:
                        picture_args = {'image_name': picture_name}
                    else:
                        picture_args = game_state.shown_pictures[picture_id]

                    picture_args['opacity'] = opacity
                    if x != 0 or y != 0:
                        if command['code'] == 231:
                            picture_args['size'] = renpy.image_size(normal_images[picture_name])
                        if origin == 0: # origin of 0 means x,y is topleft
                            picture_args['x'] = x
                            picture_args['y'] = y
                        else: # origin of 1 means it's screen center
                            picture_args['x'] = x - picture_args['size'][0] / 2
                            picture_args['y'] = y - picture_args['size'][1] / 2

                    game_state.show_picture(picture_id, picture_args)

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
                    renpy.show(command['parameters'][0], tag = "movie")
                    renpy.pause()
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
                    pass

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
                    if command['parameters'][0] == 'OpenSynthesis':
                        self.list_index += 1
                        self.state.show_synthesis_ui()

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

                # TODO: Unknown
                elif command['code'] == 505:
                    pass

                else:
                    renpy.say(None, "Code %d not implemented, plz fix." % command['code'])

                self.list_index += 1

        def done(self):
            return self.list_index == len(self.page['list'])
