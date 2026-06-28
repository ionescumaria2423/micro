from nicegui import ui

ui.label('Control').classes('text-h4')

with ui.row():

    # Camera area
    with ui.card():
        ui.label("Camera")
        ui.image("https://placehold.co/640x480?text=Camera").style(
            "width:640px;height:480px"
        )

    # Controls
    with ui.column():

        with ui.row():
            ui.button("↑")

        with ui.row():
            ui.button("←")
            ui.button("HOME")
            ui.button("→")

        with ui.row():
            ui.button("↓")


        ui.button("Z +")
        ui.button("Z -")


ui.run()