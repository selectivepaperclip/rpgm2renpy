init python:
    class GalvMapProjectiles(RpgmPlugin):
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('GALV_MapProjectiles')

        @classmethod
        def process_script(cls, event, line, script_string):
            if not cls.plugin_active():
                return False

            gre = Re()
            if gre.match('Galv\.PROJ\.(dir|atTarget)', script_string):
                return True
            else:
                return False

        @classmethod
        def is_projectile_page(cls, page):
            if not cls.plugin_active():
                return False

            for command in page['list']:
                if command['code'] == 108 and command['parameters'][0] == '<projEffect>':
                    return True

            return False
