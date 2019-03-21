screen inventory_choice_screen(
    items,
    background = True,
    allow_cancel = False,
    xpos = 15,
    ypos = 15,
    xsize = 600,
    ysize = 400,
    cols = 1,
    rows = None
):
    modal True
    if background:
        add Solid(Color("#000", alpha = 0.75))
    frame:
        xsize xsize
        xpos xpos
        ypos ypos
        ysize ysize
        vbox:
            viewport:
                scrollbars "vertical"
                mousewheel True
                vbox:
                    grid cols rows:
                        for i in items:
                            textbutton i.caption action i.action:
                                xsize config.screen_width / cols
                        for i in xrange(0, cols * rows - len(items)):
                            null

            if allow_cancel:
                textbutton "Cancel":
                    xalign 1.0
                    background "#00c"
                    hover_background "#00f"
                    action Return(0)