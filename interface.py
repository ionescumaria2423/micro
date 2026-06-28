from nicegui import ui

ui.label('Microscope Control').classes('text-h4')

with ui.row():

    # Camera area
    with ui.card():
        ui.label("Camera")
        ui.image("https://placehold.co/640x480?text=Camera").style(
            "width:640px;height:480px"
        )

    # Controls
    with ui.column():

        ui.label("Movement")

        with ui.row():
            ui.button("↑")

        with ui.row():
            ui.button("←")
            ui.button("HOME")
            ui.button("→")

        with ui.row():
            ui.button("↓")

        ui.separator()

        ui.label("Focus")

        ui.button("Z +")
        ui.button("Z -")

        ui.separator()

        ui.label("Step Size")

        ui.slider(min=0.01, max=1, value=0.05)

        ui.separator()

        ui.button("Capture Image")

ui.run()