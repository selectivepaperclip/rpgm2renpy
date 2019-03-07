init python:
    class TerraxLighting:
        COMMANDS = [
            'Light',
            'Tint',
            'Fire',
            'SetFire'
        ]

        @classmethod
        def is_lighting_command(cls, plugin_command):
            if plugin_command in TerraxLighting.COMMANDS and game_file_loader.plugin_data_exact('TerraxLighting'):
                return True
            return False
