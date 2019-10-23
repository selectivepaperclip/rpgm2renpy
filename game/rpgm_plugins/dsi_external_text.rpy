init python:
    # Special code only for Farmer's Dreams, yay. They wrote their own kooky grammar to avoid having to edit in RPGM,
    # and a whole parser that turns it back into RPGM code. The snake grows ever longer.
    class DsiExternalText:
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('DSI-ExternalText')

        @classmethod
        def process_content(cls, json_content, filename):
            pages = []
            if re.match('CommonEvents.json', filename):
                pages = json_content
            elif re.search('Map\d+.json', filename):
                for event in json_content['events']:
                    if event:
                        pages.extend(event['pages'])

            pages_to_replace = []
            for page in pages:
                if page:
                    for command in page['list']:
                        if command['code'] == 108:
                            gre = Re()
                            if gre.match(re.compile('<Text:\s*(.+)>', re.IGNORECASE), command['parameters'][0]):
                                filename = gre.last_match.groups()[0]
                                print "Replacing %s" % (command['parameters'][0])
                                pages_to_replace.append((page, DsiExternalText.translate_text_file_to_event_list(filename)))
                                break

            for page, new_list in pages_to_replace:
                page['list'] = new_list

        @classmethod
        def translate_text_file_to_event_list(cls, filename):
            text_file_lines = []
            with open(os.path.join(renpy.config.basedir, 'rpgmdata', 'www', 'data', 'external', filename + '.fd').replace('\\', '/')) as text_file:
                text_file_lines = text_file.readlines()

            translated_event_directory = os.path.join('rpgmcache', 'dsi_external_text').replace('\\', '/')
            if not os.path.exists(os.path.join(renpy.config.basedir, translated_event_directory)):
                os.makedirs(os.path.join(renpy.config.basedir, translated_event_directory))
            translate_script_filename = os.path.join(config.basedir, translated_event_directory, 'translate_script.js').replace("\\", "/")

            full_script = None
            with rpgm_file('www/js/plugins/DSI-ExternalText.js') as external_text_file:
                # Remove any 'console.log' statements from the plugin JS to ensure the only output is the resultant command list
                plugin_js = external_text_file.read().replace('console.log', '')
                full_script = """
                    var $plugins = [{
                        "name": "DSI-ExternalText",
                        "status": true,
                        "description": "With this plugin you can create Event list by using txt file. <DSI External System>",
                        "parameters": {
                            "fileList": "[]"
                        }
                    }];

                    String.prototype.contains = function(string) {
                        return this.indexOf(string) >= 0;
                    };

                    DataManager = {
                        loadDatabase: function () {}
                    };

                    Scene_Map = function () {
                    };

                    Scene_Map.prototype.isReady = function () {
                    };

                    Game_Event = function () {
                    };

                    Game_Event.prototype.setupPage = function () {
                    };

                    %s

                    console.log(JSON.stringify(DataManager.translateTextFileToEventList(%s), null, 2));
                """ % (plugin_js, json.dumps(text_file_lines))
                with open(translate_script_filename, 'w') as translate_script_file:
                    translate_script_file.write(full_script)
            try:
                CREATE_NO_WINDOW = 0x08000000
                output = subprocess.check_output(
                    ['node', translate_script_filename],
                    creationflags = CREATE_NO_WINDOW,
                    stderr=subprocess.STDOUT
                )
                return json.loads(output)
            except subprocess.CalledProcessError as e:
                print "Unable to eval external text file %s" % filename
                print e.output
                return