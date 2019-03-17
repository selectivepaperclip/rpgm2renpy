init -99 python:
    class RpgmColors():
        def __init__(self):
            self.text_color_cache = {}
            self._window_png = None
            self._window_png_surface = None

        def window_png_pixel(self, px, py):
            if not self._window_png:
                self._window_png_surface = renpy.load_surface(Image(rpgm_metadata.window_png_path))
            return self._window_png_surface.get_at((px, py))

        def text_color(self, n):
            if n not in self.text_color_cache:
                px = 96 + (n % 8) * 12 + 6;
                py = 144 + math.floor(n / 8) * 12 + 6;
                pixel = self.window_png_pixel(px, py)
                self.text_color_cache[n] = ('#%2x%2x%2x%2x' % tuple(pixel))

            return self.text_color_cache[n]