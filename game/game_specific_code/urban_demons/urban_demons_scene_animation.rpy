init python:
    def sorted_nicely( l ):
        """ Sort the given iterable in the way that humans expect."""
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        return sorted(l, key = alphanum_key)

    class GameSpecificCodeUrbanDemonsSceneAnimation():
        def __init__(self, scene_name, folder_name, folder_name_ext, dialogue_level, actor_id):
            self.folder = folder_name
            self.dialogue_level = dialogue_level
            self.scene = scene_name
            self.dialogue_scene_ext = folder_name_ext
            self.actor_id = actor_id

            self.disable_loop = False
            self.final_loop = False
            self.scene_end = False

            if self.dialogue_scene_ext == 0:
              self.dialogue_scene_ext = ""

            self.picture_id = 999
            self.dialogue_path = "Data/Dialogues/%s/%s/%s.txt" % (self.folder, self.scene + self.dialogue_scene_ext, self.dialogue_level)

            gre = Re()
            with rpgm_file(self.dialogue_path) as f:
                data = re.sub("\r\n", "\n", f.read())
                lines = data.split("\n")

                self.dialogue_groups = self.get_dialogue_groups(data)
                self.current_dialogue_group = 0
                self.current_dialogue_lines = self.get_lines_from_group(self.dialogue_groups[self.current_dialogue_group])
                self.current_dialogue_index = 0

                for line in lines:
                    if gre.match("<initialise:scene:(.+)>", line):
                        self.image_path = gre.last_match.groups()[0]

                        glob_string = os.path.join(config.basedir, rpgm_path("Graphics/Scenes/%s/%s" % (self.folder, self.image_path)), '%s*' % self.image_path)
                        frame_images = sorted_nicely(glob.glob(glob_string))

                        interval = 2
                        picture_frames = []
                        for frame_image in frame_images:
                            picture_frames.append({
                                'image_name': frame_image.replace('\\', '/'),
                                'opacity': 255,
                                'blend_mode': 0,
                                'size': (config.screen_width, config.screen_height),
                                'wait': interval
                            })

                        self.animation_image = RpgmAnimation.create_from_frames(picture_frames, loop = True)

                # TODO: is this doing actor names right?
                line = self.current_dialogue_lines[self.current_dialogue_index]
                renpy.say(game_state.replace_names(line[0]), game_state.replace_names(line[1]))
                self.current_dialogue_index += 1

        def get_dialogue_groups(self, data):
            dialogue_groups = []
            gre = Re()

            loop = True
            i = 1

            while loop:
                print data
                if gre.search(re.compile("<DialogueGroup%s>(.+)</DialogueGroup%s>" % (i, i), re.DOTALL), data):
                    dialogue_groups.append(gre.last_match.groups()[0])
                else:
                    loop = False
                i = i + 1

            return dialogue_groups

        def get_lines_from_group(self, group):
            # format is actor:line
            return re.findall("<dialogue:(.+):(.+)>", group, re.MULTILINE)

        def do_next_thing(self):
            game_state.show_picture(self.picture_id, {
                'image_name': self.animation_image,
                'opacity': 255,
                'blend_mode': 0,
                'size': (config.screen_width, config.screen_height),
            })
            game_state.pause()
            game_state.hide_picture(self.picture_id)

            return True
