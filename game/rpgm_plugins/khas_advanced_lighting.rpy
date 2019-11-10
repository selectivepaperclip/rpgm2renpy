init python:
    class KhasAdvancedLighting(RpgmPlugin):
        COMMANDS = [
            'lighting',
            'ambientlight',
            'autoambientlight',
            'saveambientlight',
            'loadambientlight',
            'playerlantern',
            'setactorlight',
            'setenemylight',
            'battlelighting'
        ]

        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('KhasAdvancedLighting')

        @classmethod
        def process_command(cls, command, command_args):
            if not cls.plugin_active():
                return False

            command = command.lower()
            if command not in KhasAdvancedLighting.COMMANDS:
                return False

            return True