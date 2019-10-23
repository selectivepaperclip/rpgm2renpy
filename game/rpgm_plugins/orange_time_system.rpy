init python:
    class OrangeTimeSystem:
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('OrangeTimeSystem')

        @classmethod
        def process_script(cls, event, script_string):
            if not cls.plugin_active():
                return False

            # .hour =
            # .minute =
            # .addHours(\d)
            # .refreshTimeSystem
            # .runInDays(\d, \d)
            # .runInHours(\d, \d)
            gre = Re()
            if not gre.match('OrangeTimeSystem\.(.*)', script_string):
                return False

            print gre.last_match.groups()[0]
            return True