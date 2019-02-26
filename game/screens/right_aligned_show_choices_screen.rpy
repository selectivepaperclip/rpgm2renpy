screen right_aligned_show_choices_screen(
    choices,
    allow_cancel = False
):
    modal True
    frame:
        xalign 1.0
        yalign 0.5
        background Color("#000", alpha = 0.9)
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