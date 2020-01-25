init python:
    class GameSceneBattle():
        def __init__(self, troop_data, event = None, command = None):
            enemies_json = game_file_loader.json_file(rpgm_data_path("Enemies.json"))

            self.troop_data = troop_data
            self.event = event
            self.command = command
            self.battle_turn = 0
            self.battle_event_flags = {}
            self.battle_enemies = [GameEnemy(member, enemies_json[member['enemyId']]) for member in self.troop_data['members']]

        def do_next_thing(self):
            troop_sprites = [
                {
                  "image": rpgm_metadata.enemies_path + enemy.battlerName + '.png',
                  "x": enemy.x,
                  "y": enemy.y
                }
                for enemy in self.battle_enemies
            ]

            renpy.show_screen(
                "battle_screen",
                background = rpgm_metadata.battlebacks1_path + game_state.map.data()['battleback1Name'] + '.png',
                troop_sprites = troop_sprites
            )

            self.process_troop_event(self.troop_data)
            self.battle_turn += 1
            self.process_troop_event(self.troop_data)

            result = renpy.display_menu([
                ("A battle with '%s'!" % game_state.escape_text_for_renpy(self.troop_data['name']), None),
                ("You Win!", 0),
                ("You Escape!", 1),
                ("You Lose!", 2)
            ])

            if result == 0:
                for enemy in self.battle_enemies:
                    enemy.hp = 0

            self.battle_turn += 1
            self.process_troop_event(self.troop_data)

            renpy.hide_screen("battle_screen")

            if result != None:
                if result == 0: # Winning
                    self.gain_fight_rewards()

                # Set the battle result in the triggering event to trigger the appropriate branch
                if self.event and self.command:
                    self.event.branch[self.command['indent']] = result

            return True

        def process_troop_event(self, troop):
            troop_event = None
            for page_index, page in enumerate(troop['pages']):
                if not self.battle_event_flags.get(page_index, False) and self.meets_troop_event_conditions(page):
                    if page['span'] <= 1:
                        self.battle_event_flags[page_index] = True

                    troop_event = GameEvent(game_state, game_state.map.map_id, troop, page, page_index)
                    break

            if troop_event:
                while not troop_event.done():
                    troop_event.do_next_thing()

        def meets_troop_event_conditions(self, page):
            c = page['conditions']
            if (not c['turnEnding'] and not c['turnValid'] and not c['enemyValid'] and not c['actorValid'] and not c['switchValid']):
                return False;  # Conditions not set

            if c['turnEnding']:
                return False
                #if (!BattleManager.isTurnEnd()) {
                #    return false;
                #}

            if c['turnValid']:
                n = self.battle_turn
                a = c['turnA']
                b = c['turnB']
                if b == 0 and n != a:
                    return False

                if b > 0 and (n < 1 or n < a or n % b != a % b):
                    return False

            if c['enemyValid']:
                enemy = self.battle_enemies[c['enemyIndex']]
                if not enemy or (enemy.hp * 1.0 / enemy.mhp * 100) > c['enemyHp']:
                    return False

            if c['actorValid']:
                return False
                #var actor = $gameActors.actor(c.actorId);
                #if (!actor || actor.hpRate() * 100 > c.actorHp) {
                #    return false;
                #}

            if c['switchValid']:
                return game_state.switches.value(c['switchId']) == True

            return True

        def gain_fight_rewards(self):
            enemies_json = game_file_loader.json_file(rpgm_data_path("Enemies.json"))
            troop_members = self.troop_data['members']
            troop_enemies = [enemies_json[enemy['enemyId']] for enemy in troop_members]

            gained_gold = sum([enemy['gold'] for enemy in troop_enemies])
            gained_exp = sum([enemy['exp'] for enemy in troop_enemies])
            gained_items = []
            for enemy in troop_enemies:
                for drop_item in enemy['dropItems']:
                    if drop_item['kind'] == 1:
                        gained_items.append(game_state.items.by_id(drop_item['dataId']))
                    elif drop_item['kind'] == 2:
                        gained_items.append(game_state.weapons.by_id(drop_item['dataId']))
                    elif drop_item['kind'] == 3:
                        gained_items.append(game_state.armors.by_id(drop_item['dataId']))

            gain_message = []
            if gained_gold > 0:
                gain_message.append("Gained Gold: %s" % gained_gold)
                game_state.party.gain_gold(gained_gold)
            if gained_exp > 0:
                gain_message.append("Gained Exp: %s" % gained_exp)
                game_state.party.gain_exp(gained_exp)
            if len(gained_items) > 0:
                gain_message.append("Gained Items: %s" % ', '.join([item['name'] for item in gained_items]))
                for item in gained_items:
                    game_state.party.gain_item(item, 1)
            if len(gain_message) > 0:
                game_state.say_text(None, "\n".join(gain_message))