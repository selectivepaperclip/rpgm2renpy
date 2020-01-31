init python:
    class MogPictureGallery(RpgmPlugin):
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('MOG_PictureGallery')

        @classmethod
        def show_gallery(cls):
            plugin_params = game_file_loader.plugin_data_exact('MOG_PictureGallery')['parameters']
            thumbnails = []
            thumbnails_for_line = int(plugin_params['Thumbnails For Line'])
            number_of_pictures = int(plugin_params['Number of Pictures'])
            thumbnail_width = (config.screen_width - 100) // thumbnails_for_line
            for i in xrange(number_of_pictures):
                picture_number = i + 1
                if picture_number in game_state.mog_picture_gallery_pictures:
                    image_path = rpgm_path("www/%s%s%s.png" % (plugin_params['File Directory'], plugin_params['File Name'], picture_number))
                    thumbnails.append(MogPictureGalleryThumbnail(image_path, thumbnail_width))
                else:
                    thumbnails.append(MogPictureGalleryThumbnail(None, thumbnail_width))

            renpy.show_screen(
                "mog_picture_gallery",
                title = "Photo Album %s/%s" % (len(game_state.mog_picture_gallery_pictures), number_of_pictures),
                thumbnails = thumbnails,
                thumbnail_height = max([thumbnail.thumbnail_height for thumbnail in thumbnails]),
                thumbnails_for_line = thumbnails_for_line
            )

        @classmethod
        def process_command(cls, event, command, command_args):
            if not cls.plugin_active():
                return False

            if command == 'enable_picture':
                if not hasattr(game_state, 'mog_picture_gallery_pictures'):
                    game_state.mog_picture_gallery_pictures = Set([])
                game_state.mog_picture_gallery_pictures.add(int(command_args[1]))
                return True
            elif command == 'picture_gallery':
                cls.show_gallery()
                return True

            return False

    class MogPictureGalleryThumbnail:
        def __init__(self, image_path, thumbnail_width):
            self.image_path = image_path
            self.thumbnail_width = thumbnail_width
            if self.image_path:
                self.image_size = renpy.image_size(image_path)
                self.image = self.scaled_to_width(thumbnail_width)
                self.thumbnail_height = self.image.height
            else:
                self.thumbnail_height = 15
                self.image = None

        def scaled_to_width(self, width):
            scale_factor = width * 1.0 / self.image_size[0]
            height = int(scale_factor * self.image_size[1])
            return im.Scale(self.image_path, width, height)

screen mog_picture_gallery(
    title,
    thumbnails,
    thumbnail_height,
    thumbnails_for_line
):
    modal True
    frame:
        xpos 50
        ypos 50
        xsize config.screen_width - 100
        ysize config.screen_height - 100
        background Solid(Color("#000"))
        vbox:
            hbox:
                text title xpos 0 ypos 0
                textbutton "Exit":
                    xpos 1.0
                    ypos 0
                    background Solid('#0000cc')
                    action Hide('mog_picture_gallery')

            viewport:
                scrollbars "vertical"
                mousewheel True

                vbox:
                    for i in xrange(0, len(thumbnails), thumbnails_for_line):
                        hbox:
                            for j, thumbnail in enumerate(thumbnails[i:i+thumbnails_for_line]):
                                if thumbnail.image:
                                    button:
                                        background thumbnail.image
                                        xysize (thumbnail.thumbnail_width, thumbnail_height)
                                        xalign 0.5
                                        yalign 0.5
                                        action Show("mog_picture_gallery_image", image_index = str(i + j + 1), thumbnail = thumbnail)
                                else:
                                    fixed:
                                        xysize (thumbnail.thumbnail_width, thumbnail_height)
                                        text str(i + j + 1):
                                            color "#333"
                                            xalign 0.5
                                            yalign 0.5
                                            size 32

screen mog_picture_gallery_image(
    image_index,
    thumbnail
):
    modal True
    frame:
        xpos 0
        ypos 0
        xsize config.screen_width
        ysize config.screen_height
        background Solid(Color("#000"))
        button:
            xalign 0.5
            yalign 0.5
            xysize (thumbnail.scaled_to_width(config.screen_width).width, thumbnail.scaled_to_width(config.screen_width).height)
            background thumbnail.scaled_to_width(config.screen_width)
            action Hide('mog_picture_gallery_image')