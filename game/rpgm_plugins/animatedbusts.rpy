init python:
    class AnimatedBusts:
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('animatedbusts')

        @classmethod
        def process_script(cls, event, line, script_string):
            if not cls.plugin_active():
                return False

            gre = Re()
            # $game_state.picture(30).setAnim([$gameVariables.value(20)+"0"],2)
            if gre.match(re.compile('\$gameScreen\.picture\((\d+)\)\.setAnim\(\s*\[(.*?)\]\s*,\s*(\d+)\s*\)', re.DOTALL), script_string):
                picture_id = int(gre.last_match.groups()[0])
                frame_images = eval(game_state.eval_fancypants_value_statement(gre.last_match.groups()[1], return_remaining = True))
                interval = int(gre.last_match.groups()[2])

                frames_json = [{'image': frame_image, 'delay': interval} for frame_image in frame_images]
                movie_webm_filename = RpgmAnimation.filename_for_frames_webm(frames_json)
                movie_json_filename = RpgmAnimation.filename_for_frames_json(frames_json)

                if noisy_animations:
                    filename = RpgmAnimation.filename_for_frames_json(frames_json)
                    with open(os.path.join(renpy.config.basedir, rpgm_metadata.rpgm2renpy_movies_path, filename), 'w') as f:
                        json.dump(frames_json, f, sort_keys=True, indent=2)
                        renpy.notify("Wrote %s" % filename)

                picture_frames = []
                for frame_image in frame_images:
                    picture_frames.append({
                        'image_name': normal_images[rpgm_picture_name(frame_image)],
                        'opacity': 255,
                        'blend_mode': 0,
                        'size': (config.screen_width, config.screen_height),
                        'wait': interval
                    })

                if os.path.exists(os.path.join(renpy.config.basedir, rpgm_metadata.rpgm2renpy_movies_path, movie_webm_filename)):
                    full_path = os.path.join(config.basedir, rpgm_metadata.rpgm2renpy_movies_path, movie_webm_filename).replace("\\", "/")
                    image = Movie(
                        play=full_path,
                        start_image=picture_frames[0]['image_name'],
                        image=picture_frames[-1]['image_name']
                    )
                else:
                    image = RpgmAnimation.create_from_frames(picture_frames, loop = True)
                game_state.show_picture(picture_id, {
                    'image_name': image,
                    'opacity': 255,
                    'blend_mode': 0,
                    'size': (config.screen_width, config.screen_height),
                })

                return True
            elif gre.match('\s*\$gameScreen\.picture\((\d+)\)\.setFrozenBmp\([\'"](.*?)[\'"]\);?', script_string):
                return True
            elif gre.match('\s*\$gameScreen\.picture\((\d+)\)\.removeLoopTimes\(\);?', script_string):
                picture_id = int(gre.last_match.groups()[0])
                AnimatedBusts.set_animation_loop(picture_id, True)
                return True
            elif gre.match('\s*\$gameScreen\.picture\((\d+)\)\.setLoopTimes\(1\);?', script_string):
                picture_id = int(gre.last_match.groups()[0])
                AnimatedBusts.set_animation_loop(picture_id, False)
                return True
            elif gre.match('\s*\$gameScreen\.picture\((\d+)\)\.(un)?freeze\(\);?', script_string):
                picture_id = int(gre.last_match.groups()[0])
                animation = AnimatedBusts.movie_or_animation_at_picture_id(picture_id)
                if animation:
                    if isinstance(animation, RpgmAnimation):
                        if gre.last_match.groups()[1]:
                            animation.unfreeze()
                        else:
                            animation.freeze()
                    if isinstance(animation, Movie):
                        pass
                return True
            elif gre.match('\s*\$gameScreen\.(save|restore)Pictures\(\)', script_string):
                return True
            else:
                return False

        @classmethod
        def set_animation_loop(cls, picture_id, loop):
            animation = AnimatedBusts.movie_or_animation_at_picture_id(picture_id)
            if animation:
                if isinstance(animation, RpgmAnimation):
                    #animation.loop = loop
                    pass
                if isinstance(animation, Movie):
                    animation.loop = loop

        @classmethod
        def movie_or_animation_at_picture_id(cls, picture_id):
            displayable = game_state.queued_or_shown_picture(picture_id)['image_name']
            if hasattr(displayable, 'children') and displayable.children != None:
                displayable = displayable.children[0]
            return displayable