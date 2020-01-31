init python:
    class TerraxLighting(RpgmPlugin):
        COMMANDS = [
            'Light',
            'Tint',
            'Fire',
            'SetFire'
        ]

        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('TerraxLighting')

        @classmethod
        def process_command(cls, event, command, command_args):
            if not cls.plugin_active():
                return False

            if cls.plugin_active() and command in TerraxLighting.COMMANDS:
                return True

            return False
