from nicegui import app, ui
import functions as fn

stop_requested = False


def trigger_e_stop():
    global stop_requested
    stop_requested = True


def handle_keyboard_events(e):
    if e.action.keydown and e.key == ' ':
        trigger_e_stop()


def move_stage():
    """Safety wrapper to ensure move only fires once per click."""
    try:
        fn.CH_Y.MoveTo(
             fn.Decimal(1.00), 0
        )
    except Exception as err:
        print("Move error:", err)


def check_stop_notify():
    global stop_requested
    if stop_requested:
        ui.notify('Stop', type='negative')
        try:
            ch_x = getattr(fn, 'CH_X', None)
            ch_y = getattr(fn, 'CH_Y', None)
            ch_z = getattr(fn, 'CH_Z', None)

            if ch_x is not None:
                ch_x.StopImmediate()
            if ch_y is not None:
                ch_y.StopImmediate()
            if ch_z is not None:
                ch_z.StopImmediate()

        except Exception as e:
            print("Error stopping hardware:", e)

        stop_requested = False



def build_gui():
    ui.keyboard(on_key=handle_keyboard_events)

    with ui.row():
        with ui.card():
            ui.label("Camera")
            camera_image = ui.interactive_image().style(
                "width:620px;height:480px;"
            )

        # Point directly to move_stage function without inline execution
        ui.button('go', on_click=move_stage)
        ui.button('stop', on_click=lambda: fn.connect())

    camera_timer = ui.timer(0.05, lambda: fn.update_camera(camera_image))
    notify_timer = ui.timer(0.1, check_stop_notify)


app.on_startup(fn.handle_startup)

build_gui()
ui.run()