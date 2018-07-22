screen inventory_choice_screen(
    items,
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
                    for i in items:
                        textbutton i.caption action i.action

            if allow_cancel:
                textbutton "Cancel":
                    background "#00c"
                    hover_background "#00f"
                    action Return(0)