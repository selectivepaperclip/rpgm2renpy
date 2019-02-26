init -99 python:
    class GameFileLoader(object):
        def __init__(self):
            self.exact_plugin_cache = {}
            self.loose_plugin_cache = {}
            self.full_paths_for_pictures = {}

        def json_file(self, filename):
            if not hasattr(self, '_json_files'):
                self._json_files = {}
            if not filename in self._json_files:
                with renpy.file(filename) as f:
                    self._json_files[filename] = json.load(f)

            return self._json_files[filename]

        def package_json(self):
            if rpgm_metadata.is_pre_mv_version:
                return None

            if not hasattr(self, '_package_json'):
                with rpgm_file('package.json') as f:
                    self._package_json = json.load(f)

            return self._package_json

        def plugins_json(self):
            if rpgm_metadata.is_pre_mv_version:
                return []

            if not hasattr(self, '_plugins_json'):
                with rpgm_file('www/js/plugins.js') as f:
                    # the plugins.js file starts with "var $plugins = ["
                    # delete everything before the first [
                    content = f.read()
                    self._plugins_json = json.loads(content[content.find('['):].rstrip().rstrip(';'))

            return self._plugins_json

        def plugin_data_exact(self, plugin_name):
            if plugin_name in self.exact_plugin_cache:
                return self.exact_plugin_cache[plugin_name]

            self.exact_plugin_cache[plugin_name] = next((plugin_data for plugin_data in self.plugins_json() if plugin_data['name'] == plugin_name), None)
            return self.exact_plugin_cache[plugin_name]

        def plugin_data_startswith(self, plugin_name):
            if plugin_name in self.loose_plugin_cache:
                return self.loose_plugin_cache[plugin_name]

            self.loose_plugin_cache[plugin_name] = next((plugin_data for plugin_data in self.plugins_json() if plugin_data['name'].startswith(plugin_name)), None)
            return self.loose_plugin_cache[plugin_name]

        def full_path_for_picture(self, path):
            if not path in self.full_paths_for_pictures:
                if os.path.exists(path):
                    self.full_paths_for_pictures[path] = path
                else:
                    files = glob.glob(os.path.join(config.basedir, '%s.*' % path))
                    if len(files) > 0:
                        self.full_paths_for_pictures[path] = path + os.path.splitext(files[0])[1]

            return self.full_paths_for_pictures.get(path, None)

        def galv_quest_data(self):
            plugin = self.plugin_data_exact('Galv_QuestLog')
            if not plugin:
                return {}

            if hasattr(self, 'galv_quest_txt'):
                return self.galv_quest_txt

            gre = Re()
            with rpgm_file("www/%s/%s.txt" % (plugin['parameters']['Folder'], plugin['parameters']['File'])) as f:
                lines = re.sub("\r\n", "\n", f.read()).split("\n")
                b_index = 0
                record = False
                self.galv_quest_txt = {};

                for line in lines:
                    if len(line) > 0 and line[0] == '<':
                        if '</quest>' in line:
                            record = False
                        elif '<quest' in line:
                            if gre.search(re.compile("<quest\s*(\d*):(.*)>", re.IGNORECASE), line):
                                b_index = int(gre.last_match.groups()[0])
                                this_quest = {
                                  'name': '???',
                                  'difficulty': '???',
                                  'category': '???'
                                }
                                self.galv_quest_txt[b_index] = this_quest
                                this_quest['desc'] = []

                                s = gre.last_match.groups()[1].split('|')
                                if len(s) > 0:
                                    this_quest['name'] = game_state.escape_text_for_renpy(game_state.replace_names(s[0]))
                                if len(s) > 1:
                                    this_quest['difficulty'] = s[1]
                                if len(s) > 2:
                                    this_quest['category'] = s[2]

                                record = True
                    elif record:
                        self.galv_quest_txt[b_index]['desc'].append(game_state.escape_text_for_renpy(game_state.replace_names(line)))

            return self.galv_quest_txt