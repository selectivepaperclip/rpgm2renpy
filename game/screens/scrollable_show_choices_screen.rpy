screen scrollable_show_choices_screen(
    choices,
    background = True,
    allow_cancel = False
):
    modal True
    if background:
        add Solid(Color("#000", alpha = 0.75))
    frame:
        area (15, 15, 600, 400)
        vbox:
            viewport:
                scrollbars "vertical"
                mousewheel True
                vbox:
                    for choice in choices:
                        textbutton choice['text']:
                            if choice['disabled']:
                                text_color "#333"
                            action Return(choice['id'])

            if allow_cancel:
                textbutton "Cancel":
                    background "#00c"
                    hover_background "#00f"
                    action Return(0)