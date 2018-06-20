screen inventory_choice_screen(items):
    frame:
        side 'c':
            area (5, 5, 400, 600)
            viewport:
                scrollbars "vertical"
                mousewheel True
                vbox:
                    for i in items:
                        textbutton i.caption action i.action
