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

        def __init__(self, *args, **properties):
            """
            There is one keyword argument, apart from the style properties:

            @param anim_timebase: If True, the default, use the animation
            timebase. Otherwise, use the displayable timebase.
            """

            properties.setdefault('style', 'animation')
            self.anim_timebase = properties.pop('anim_timebase', True)

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

        def render(self, width, height, st, at):
            if self.anim_timebase:
                orig_t = at
            else:
                orig_t = st

            if not hasattr(self, 'first_rendered_t'):
                self.first_rendered_t = orig_t

            t = (orig_t - self.first_rendered_t) % sum(self.delays)

            for image, prev, delay, trans in zip(self.images, self.prev_images, self.delays, self.transitions):
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