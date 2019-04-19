init python:
    class RpgmAnimation(renpy.display.core.Displayable):
        """
        anim.TransitionAnimation but with the transitions taken out and hopefully fixed to support non-looping animations

        They didn't work in a normal anim.TransitionAnimation because by the time you got to render st/at would
        be way too big and "orig_t % delays" would put you into the last (year-long) frame.

        This version instead records the initial time it was rendered and uses that as the basis for frame second counting.
        """

        @classmethod
        def create(cls, *args, **properties):
            return RpgmAnimation(*args, **properties)

        @classmethod
        def create_from_frames(cls, picture_frames, loop = False):
            picture_transitions = RpgmAnimation.transitions_for_frames(picture_frames, loop = loop)
            return RpgmAnimation.create(*picture_transitions)

        @classmethod
        def image_for_picture(cls, picture_frame):
            return Transform(
                child = picture_frame['image_name'],
                xpos = picture_frame.get('x', 0),
                ypos = picture_frame.get('y', 0),
                size = picture_frame.get('size', None),
            )

        @classmethod
        def filename_for_frames_json(cls, frames_json):
            if len(frames_json) < 2:
                return None
            return "%s.json" % RpgmAnimation.filename_for_frames_base(frames_json)

        @classmethod
        def filename_for_frames_webm(cls, frames_json):
            if len(frames_json) < 2:
                return None
            return "%s.webm" % RpgmAnimation.filename_for_frames_base(frames_json)

        @classmethod
        def filename_for_frames_base(cls, frames_json):
            return "%s-%s-%sframes" % (frames_json[0]['image'], frames_json[-1]['image'], len(frames_json))

        @classmethod
        def transitions_for_frames(cls, picture_frames, loop = False):
            # Creates 3n items if the animation is intended to loop, or 3n - 2 items if it is fixed length

            picture_transitions = []
            for i, picture_frame in enumerate(picture_frames):
                picture_transitions.append(RpgmAnimation.image_for_picture(picture_frame))
                wait_seconds = 0
                if 'wait' in picture_frame:
                    wait_seconds = (picture_frame['wait'] / animation_fps)

                if i + 1 < len(picture_frames):
                    next_picture_frame = picture_frames[i + 1]
                    if 'x' in picture_frame and (next_picture_frame['x'] != picture_frame['x'] or next_picture_frame['y'] != picture_frame['y']):
                        picture_transitions.append(0.0001)
                        picture_transitions.append(MoveTransition(picture_frame.get('wait', 0.001) / animation_fps))
                    else:
                        picture_transitions.append(wait_seconds)
                        picture_transitions.append(None)
                    if not loop and (i + 1 == len(picture_frames) - 1): # Last Frame
                        picture_transitions.append(RpgmAnimation.image_for_picture(next_picture_frame))
                        break
                else:
                    picture_transitions.append(wait_seconds)
                    picture_transitions.append(None)

            return picture_transitions

        def __init__(self, *args, **properties):
            """
            There is one keyword argument, apart from the style properties:

            @param anim_timebase: If True, the default, use the animation
            timebase. Otherwise, use the displayable timebase.
            """

            properties.setdefault('style', 'animation')
            self.anim_timebase = properties.pop('anim_timebase', True)
            self.first_loop_index = properties.pop('first_loop_index', None)
            self.event_command_references = properties.pop('event_command_references', [])

            super(RpgmAnimation, self).__init__(**properties)

            images = [ ]
            delays = [ ]
            transitions = [ ]

            for i, arg in enumerate(args):
                if i % 3 == 0:
                    images.append(renpy.easy.displayable(arg))
                elif i % 3 == 1:
                    delays.append(arg)
                else:
                    transitions.append(arg)

            if len(images) > len(delays):
                delays.append(365.25 * 86400.0)  # One year, give or take.
            if len(images) > len(transitions):
                transitions.append(None)

            self.images = images
            self.prev_images = [ images[-1] ] + images[:-1]
            self.delays = delays
            self.transitions = [ transitions[-1] ] + transitions[:-1]

        def add_transitions(self, transitions):
            print "wanna add %s transitions" % (len(transitions))
            pass

        def freeze(self):
            self.frozen = True
            self.frozen_t = None

        def unfreeze(self):
            self.frozen = False
            self.frozen_t = None

        def reset_frame_delays(self, desired_wait):
            for i in xrange(0, len(self.delays)):
                self.delays[i] = desired_wait / animation_fps

        def render(self, width, height, st, at):
            if hasattr(self, 'frozen_t') and self.frozen_t:
                orig_t = self.frozen_t
            elif self.anim_timebase:
                orig_t = at
            else:
                orig_t = st

            if hasattr(self, 'frozen') and self.frozen and self.frozen_t == None:
                self.frozen_t = orig_t

            if not hasattr(self, 'first_rendered_t'):
                self.first_rendered_t = orig_t

            if hasattr(self, 'past_first_loop_index') and self.past_first_loop_index:
                t = (orig_t - self.first_rendered_t - sum(self.delays[0:self.first_loop_index])) % sum(self.delays[self.first_loop_index:-1])
            else:
                t = (orig_t - self.first_rendered_t) % sum(self.delays)

            for index, (image, prev, delay, trans) in enumerate(zip(self.images, self.prev_images, self.delays, self.transitions)):
                # Mark the animation as having hit the looping part
                if hasattr(self, 'first_loop_index') and self.first_loop_index and index >= self.first_loop_index:
                    self.past_first_loop_index = True

                # Skip the non-looping part of the animation if we've already reached the looping part
                if hasattr(self, 'past_first_loop_index') and self.past_first_loop_index and index < self.first_loop_index:
                    continue

                if t < delay:
                    if not renpy.game.less_updates:
                        renpy.display.render.redraw(self, delay - t)

                    if trans and orig_t >= self.delays[0]:
                        image = trans(old_widget=prev, new_widget=image)

                    im = renpy.display.render.render(image, width, height, t, at)
                    width, height = im.get_size()
                    rv = renpy.display.render.Render(width, height)
                    # TODO: questionable if this is the right way to handle x/y positioning, but it works?!
                    placement = image.get_placement()
                    rv.blit(im, (placement[0], placement[1]))

                    return rv

                else:
                    t = t - delay

        def visit(self):
            return self.images