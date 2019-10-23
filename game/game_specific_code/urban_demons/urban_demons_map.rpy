screen urban_demons_map(
    background,
    locations,
    location_icon
):
    add background
    for location in locations:
        button:
            xpos location.x_loc - (43 / 2)
            ypos location.y_loc - (65 / 2)
            xsize 43
            ysize 65
            background location_icon
            hover_background Color("#00f", alpha = 0.5)
            tooltip location.name
            action Function(GameSpecificCodeUrbanDemonsLocation.transfer, location), Jump("game")

    $ tooltip = GetTooltip()
    if tooltip:
        $ mousepos = renpy.get_mouse_pos()
        text tooltip:
            xpos mousepos[0]
            ypos mousepos[1]
            outlines [ (2, "#000", 0, 0) ]