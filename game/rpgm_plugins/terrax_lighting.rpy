init python:
    class TerraxLighting:
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
        def is_lighting_command(cls, plugin_command):
            if cls.plugin_active() and plugin_command in TerraxLighting.COMMANDS:
                return True
            return False
