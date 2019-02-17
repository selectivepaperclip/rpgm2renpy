screen scrolling_textbox_screen(text_to_show):
    modal True
    add Solid(Color("#000", alpha = 0.75))
    frame:
        xpadding 0.1
        ypadding 0.1
        xalign 0.5
        yalign 0.5

        vbox:
            viewport:
                scrollbars "vertical"
                mousewheel True
                vbox:
                    frame:
                        xpadding 10
                        text text_to_show

            textbutton "Done":
                background "#00c"
                hover_background "#00f"
                xalign 1.0
                action Return(0)