import asyncio
from nicegui import app, run, ui
import fn2 as fn

stop_requested = False


# --- EMERGENCY STOP MECHANICS (ALL CHANNELS) ---

def trigger_e_stop():
    """Triggers the E-stop sequence instantly across all stepper and piezo axes."""
    global stop_requested
    stop_requested = True
    stop_hardware_immediately()


def stop_hardware_immediately():
    """Halts all stepper motors and resets active piezo outputs."""
    try:
        # 1. Stop all Stepper Channels
        for channel_name in ['CH_X', 'CH_Y', 'CH_Z']:
            ch = getattr(fn, channel_name, None)
            if ch is not None:
                ch.StopImmediate()
                ch.DisableChannel()
                ch.EnableChannel()  # Re-enable drive current for future command processing

        # 2. Reset / Stop all Piezo Channels
        for pzt_name in ['PZT_X', 'PZT_Y', 'PZT_Z']:
            pzt = getattr(fn, pzt_name, None)
            if pzt is not None:
                try:
                    # Set voltage to 0 V instantly for safety
                    pzt.SetOutputVoltage(fn.Decimal(0))
                except Exception:
                    pass

    except Exception as e:
        print("Error stopping hardware:", e)


def handle_keyboard_events(e):
    """Fires E-stop when Spacebar is pressed anywhere in the app."""
    if e.action.keydown and e.key == " ":
        trigger_e_stop()


def check_stop_notify():
    """UI notification hook to alert when E-stop triggers."""
    global stop_requested
    if stop_requested:
        ui.notify("EMERGENCY STOP TRIGGERED!", type="negative")
        stop_requested = False


# --- APPLICATION LAYOUT ---

app.on_startup(fn.handle_startup)

# Global keyboard listener for Spacebar E-Stop
ui.keyboard(on_key=handle_keyboard_events)

ui.label('Control').classes('text-h4')

with ui.row():
    with ui.card():
        ui.label("Camera")
        camera_image = ui.interactive_image().style("width:620px;height:480px;")
        ui.button('TAKE PIC', on_click=fn.takePic).classes('w-full')

    with ui.card():
        ui.label("MATPLOTLIB")
        ui.image("https://placehold.co/640x480?text=matplot").style("width:640px;height:480px")

    with ui.card().style("width:300px;height:480px;"):
        ui.label("telemetry")
        ui.button('START', on_click=fn.connect)
        ui.label('info care vine mai tarziu')

with ui.row():
    with ui.card():
        ui.label("Stepper Control")
        with ui.row():
            ui.label("        ")
            ui.label("Relative").classes('text-h5')
            ui.label("        ")
            ui.label("        ")
            ui.label("        ")
            ui.label("Absolute").classes('text-h5')

        with ui.row():
            ui.label("X")
            ui.number(label='xRel').bind_value(fn.state, 'xRel')
            ui.checkbox().bind_value(fn.state, 'chx')
            ui.number(label='xAbs').bind_value(fn.state, 'xAbs')

        with ui.row():
            ui.label("Y")
            ui.number(label='yRel').bind_value(fn.state, 'yRel')
            ui.checkbox().bind_value(fn.state, 'chy')
            ui.number(label='yAbs').bind_value(fn.state, 'yAbs')

        with ui.row():
            ui.label("Z")
            ui.number(label='zRel').bind_value(fn.state, 'zRel')
            ui.checkbox().bind_value(fn.state, 'chz')
            ui.number(label='zAbs').bind_value(fn.state, 'zAbs')

        with ui.row():
            ui.label("        ")
            ui.button('<', on_click=fn.moverelneg).style("width:40px;height:40px;")
            ui.button('>', on_click=fn.moverelpos).style("width:40px;height:40px;")
            ui.label("        ")
            ui.label("        ")
            ui.label("        ")
            ui.button("ABS", on_click=fn.moveabs).style("width:40px;height:40px;")

        with ui.row():
            ui.button("HOME", on_click=fn.homeLaComanda).style("width:120px;height:40px;")
            # STOP button linked directly to the E-stop routine
            ui.button("STOP", on_click=trigger_e_stop).style("width:120px;height:40px;").props('color=red')

    with ui.card():
        ui.label("Piezo Control")

        mode_toggle = ui.toggle(['Voltage (V)', 'Position (µm)'], value='Voltage (V)')

        with ui.row():
            ui.label("Axis")
            ui.label("Target Value")

        with ui.row():
            ui.label("X")
            ui.number(label='X Target', value=0.0, format='%.2f').bind_value(fn.state, 'pzt_x_val')
            ui.button("SET X", on_click=lambda: fn.set_piezo('X', mode_toggle.value)).style("width:70px;")

        with ui.row():
            ui.label("Y")
            ui.number(label='Y Target', value=0.0, format='%.2f').bind_value(fn.state, 'pzt_y_val')
            ui.button("SET Y", on_click=lambda: fn.set_piezo('Y', mode_toggle.value)).style("width:70px;")

        with ui.row():
            ui.label("Z")
            ui.number(label='Z Target', value=0.0, format='%.2f').bind_value(fn.state, 'pzt_z_val')
            ui.button("SET Z", on_click=lambda: fn.set_piezo('Z', mode_toggle.value)).style("width:70px;")

        with ui.row():
            ui.button("ZERO ALL", on_click=lambda: fn.zero_piezo_all(mode_toggle.value)).style("width:110px; height:40px;").props('color=warning')
            ui.button("SET ALL", on_click=lambda: fn.set_piezo_all(mode_toggle.value)).style("width:110px; height:40px;")

    with ui.card():
        ui.label("Spectrometer")
        ui.button('INTEG.TIME').style('width:200px;height:60px;')
        ui.button('TAKE.BKG').style('width:200px;height:60px;')
        ui.button("TAKE.SP").style('width:200px;height:60px;')


# UI Update Timers
camera_timer = ui.timer(0.05, lambda: fn.update_camera(camera_image))
notify_timer = ui.timer(0.1, check_stop_notify)

ui.run()