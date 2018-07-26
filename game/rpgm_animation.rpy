init python:
    class RpgmAnimation(renpy.display.core.Displayable):
        """
        anim.TransitionAnimation but with the transitions taken out and hopefully fixed to support non-looping animations

        They didn't work in a normal anim.TransitionAnimation because by the time you got to render st/at would
        be way too big and "orig_t % delays" would put you into the last (year-long) frame.

        This version instead records the initial time it was rendered and uses that as the basis for frame second counting.
        """

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

            for i, arg in enumerate(args):

                if i % 2 == 0:
                    images.append(renpy.easy.displayable(arg))
                else:
                    delays.append(arg)

            if len(images) > len(delays):
                delays.append(365.25 * 86400.0)  # One year, give or take.

            self.images = images
            self.delays = delays

        def render(self, width, height, st, at):
            if self.anim_timebase:
                orig_t = at
            else:
                orig_t = st

            if not hasattr(self, 'first_rendered_t'):
                self.first_rendered_t = orig_t

            t = (orig_t - self.first_rendered_t) % sum(self.delays)

            for image, delay, in zip(self.images, self.delays):
                if t < delay:
                    if not renpy.game.less_updates:
                        renpy.display.render.redraw(self, delay - t)

                    im = renpy.display.render.render(image, width, height, t, at)
                    width, height = im.get_size()
                    rv = renpy.display.render.Render(width, height)
                    rv.blit(im, (0, 0))

                    return rv

                else:
                    t = t - delay

        def visit(self):
            return self.images