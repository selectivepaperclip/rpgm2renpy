init python:
    class MogChronoEngine(RpgmPlugin):
        COMMANDS = [
            'chrono_mode',
            'tool_collision',
            'tool_turn_end',
            'atb_mode',
            'command_attack',
            'command_shield',
            'command_skill',
            'command_skill_window',
            'command_item_window',
            'action_commands',
            'set_actor_skill',
            'set_actor_item',
            'set_battler_position',
            'set_battler_direction',
            'force_damage',
            'tool_position'
        ]

        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('MOG_ChronoEngine')

        @classmethod
        def process_command(cls, command, command_args):
            if not cls.plugin_active():
                return False

            if command not in MogChronoEngine.COMMANDS:
                return False

            if command == 'chrono_mode':
                # TODO: Farmers Dreams
                return True

            return False