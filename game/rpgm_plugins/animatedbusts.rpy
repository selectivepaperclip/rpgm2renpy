init python:
    class AnimatedBusts:
        @classmethod
        def process_script(cls, script_string):
            plugin = game_file_loader.plugin_data_exact('animatedbusts')
            if not plugin:
                return False
            if not plugin['status']:
                return False

            gre = Re()
            # $game_state.picture(30).setAnim([$gameVariables.value(20)+"0"],2)
            if gre.match('\$gameScreen\.picture\((\d+)\)\.setAnim\(\s*\[(.*?)\]\s*,\s*(\d+)\s*\)', script_string):
                picture_id = int(gre.last_match.groups()[0])
                frame_images = eval(game_state.eval_fancypants_value_statement(gre.last_match.groups()[1], return_remaining = True))
                interval = int(gre.last_match.groups()[2])

                picture_frames = []
                for frame_image in frame_images:
                    picture_frames.append({
                        'image_name': normal_images[rpgm_picture_name(frame_image)],
                        'opacity': 255,
                        'blend_mode': 0,
                        'size': (config.screen_width, config.screen_height),
                        'wait': interval
                    })
                animation = RpgmAnimation.create_from_frames(picture_frames, loop = True)
                game_state.show_picture(picture_id, {
                    'image_name': animation,
                    'opacity': 255,
                    'blend_mode': 0,
                    'size': (config.screen_width, config.screen_height),
                })

                return True
            elif gre.match('\s*\$gameScreen\.picture\((\d+)\)\.(un)?freeze\(\);?', script_string):
                picture_id = int(gre.last_match.groups()[0])
                animation = game_state.shown_pictures[picture_id]['image_name'].children[0]
                if gre.last_match.groups()[1]:
                    animation.unfreeze()
                else:
                    animation.freeze()
                return True
            elif gre.match('\s*\$gameScreen\.(save|restore)Pictures\(\)', script_string):
                return True
            else:
                return False