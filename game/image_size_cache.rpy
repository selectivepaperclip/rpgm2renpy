init -99 python:
    class ImageSizeCache(object):
        def __init__(self):
            self.sizes = {}

        def for_picture_name(self, picture_name):
            return self.for_path(normal_images[picture_name])

        def for_path(self, path):
            if not path in self.sizes:
                self.sizes[path] = renpy.image_size(Image(path))
            return self.sizes[path]

        def print_cache(self):
            for (x, y) in self.sizes.iteritems():
                print (x, y)