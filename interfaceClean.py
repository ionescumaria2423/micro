import base64
import cv2
import spectrometerLib as sp
from nicegui import ui, app, run
from merge import *
from System import Decimal
import os
import asyncio
import time
from pathlib import Path
import keyboard
import threading
from numba.core.utils import chain_exception
from pylablib.devices import uc480
from pyqtgraph.examples.relativity import Simulation
import clr
import pythonnet
import numpy as np

# THORLABS IMPORTS __________________________________________________________________________________________________________________________

from Thorlabs.MotionControl.GenericPiezoCLI.Piezo import PiezoControlModeTypes

# FUNCTIONS _________________________________________________________________________________________________________________________________

async def handle_startup():
    print("UI layer successfully loaded.")

app.on_startup(handle_startup)

CH_X = None
CH_Y = None
CH_Z = None
stepper_device = None

PiezoCH_X = None
PiezoCH_Y = None
PiezoCH_Z = None
piezo_device = None

timeout = 30000

# CAMERA GLOBALS & RECOVERY ________________________________________________________________________________________________________________

cam = None
camera_consecutive_errors = 0
camera_timer = None

def get_camera():
    global cam
    if cam is None:
        cam = uc480.UC480Camera()
    return cam

def update_camera():
    global cam, camera_consecutive_errors

    try:
        camera = get_camera()
        frame = camera.snap()

        if frame is not None and frame.size > 0:
            frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
            frame = frame.astype(np.uint8)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            _, jpg = cv2.imencode('.jpg', frame)
            encoded = base64.b64encode(jpg).decode("utf-8")

            camera_image.set_source(f"data:image/jpeg;base64,{encoded}")
            camera_consecutive_errors = 0

    except Exception as e:
        camera_consecutive_errors += 1
        print(f"Camera frame drop ({camera_consecutive_errors}):", e)

        if camera_consecutive_errors > 5:
            print("Resetting camera connection...")
            try:
                if cam:
                    cam.close()
            except:
                pass
            cam = None
            camera_consecutive_errors = 0

# THREAD-SAFE NON-BLOCKING CONNECT ___________________________________________________________________________________________________________

async def connect():
    global CH_X, CH_Y, CH_Z, stepper_device
    global PiezoCH_X, PiezoCH_Y, PiezoCH_Z, piezo_device

    if camera_timer:
        camera_timer.deactivate()

    ui.notify("Connecting to motion hardware...", type='info')

    def _hardware_init():
        try:
            from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
            DeviceManagerCLI.BuildDeviceList()
            time.sleep(0.2)
        except Exception as dev_err:
            print("DeviceManager CLI issue:", dev_err)

        x, y, z, step_dev = init_BSC(serial_Stepper)
        px, py, pz, pz_dev = init_BPC(serial_Piezo)

        # Connect Steppers
        for ch in [x, y, z]:
            if ch is not None:
                if not ch.IsConnected:
                    ch.Connect(serial_Stepper)
                ch.StartPolling(250)
                ch.EnableDevice()
                time.sleep(0.1)

        # Connect Piezos
        for ch in [px, py, pz]:
            if ch is not None:
                if not ch.IsConnected:
                    ch.Connect(serial_Piezo)
                ch.StartPolling(250)
                ch.EnableDevice()
                time.sleep(0.1)

        return x, y, z, step_dev, px, py, pz, pz_dev

    try:
        CH_X, CH_Y, CH_Z, stepper_device, PiezoCH_X, PiezoCH_Y, PiezoCH_Z, piezo_device = await run.io_bound(_hardware_init)
        ui.notify("Hardware connected successfully!", type='positive')

    except Exception as e:
        print(f"Connection Error: {e}")
        ui.notify(f"Connection Failed: {e}", type='negative')

    finally:
        await asyncio.sleep(0.5)
        if camera_timer:
            camera_timer.activate()

# STATE AND MOVEMENT _______________________________________________________________________________________________________________________

state = {
    'chx': False, 'chy': False, 'chz': False,
    'xRel': 0.0,  'yRel': 0.0,  'zRel': 0.0,
    'xAbs': 0.0,  'yAbs': 0.0,  'zAbs': 0.0,
    'pzt_x_val': 0.0, 'pzt_y_val': 0.0, 'pzt_z_val': 0.0
}

def moverelpos():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to connect hardware first!", type='warning')
        return

    if state['chx'] and CH_X:
        CH_X.MoveRelative(MotorDirection.Forward, Decimal(state['xRel']), timeout)
    if state['chy'] and CH_Y:
        CH_Y.MoveRelative(MotorDirection.Forward, Decimal(state['yRel']), timeout)
    if state['chz'] and CH_Z:
        CH_Z.MoveRelative(MotorDirection.Forward, Decimal(state['zRel']), timeout)

def moverelneg():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to connect hardware first!", type='warning')
        return

    if state['chx'] and CH_X:
        CH_X.MoveRelative(MotorDirection.Backward, Decimal(state['xRel']), timeout)
    if state['chy'] and CH_Y:
        CH_Y.MoveRelative(MotorDirection.Backward, Decimal(state['yRel']), timeout)
    if state['chz'] and CH_Z:
        CH_Z.MoveRelative(MotorDirection.Backward, Decimal(state['zRel']), timeout)

def moveabs():
    if state['chx'] and CH_X:
        CH_X.MoveTo(Decimal(state['xAbs']), timeout)
    if state['chy'] and CH_Y:
        CH_Y.MoveTo(Decimal(state['yAbs']), timeout)
    if state['chz'] and CH_Z:
        CH_Z.MoveTo(Decimal(state['zAbs']), timeout)

def homeLaComanda():
    if state['chx'] and CH_X:
        CH_X.Home(60000)
    if state['chy'] and CH_Y:
        CH_Y.Home(60000)
    if state['chz'] and CH_Z:
        CH_Z.Home(60000)

async def noMoreMove():
    print("EMERGENCY STOP")
    try:
        if CH_X: CH_X.StopImmediate()
        if CH_Y: CH_Y.StopImmediate()
        if CH_Z: CH_Z.StopImmediate()
    except Exception as e:
        print(e)

    await asyncio.sleep(0.1)
    app.shutdown()

# PIEZO CONTROL FUNCTIONS __________________________________________________________________________________________________________________

def set_piezo(axis, mode):
    channels = {'X': PiezoCH_X, 'Y': PiezoCH_Y, 'Z': PiezoCH_Z}
    ch = channels.get(axis)

    if ch is None:
        ui.notify(f"Piezo Axis {axis} not connected!", type='warning')
        return

    val = state.get(f'pzt_{axis.lower()}_val', 0.0)

    try:
        if mode == 'Position (µm)':
            ch.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
            ch.SetPosition(Decimal(val))
            ui.notify(f"Piezo {axis} set to {val} µm", type='positive')
        else:
            ch.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
            ch.SetOutputVoltage(Decimal(val))
            ui.notify(f"Piezo {axis} set to {val} V", type='positive')

    except Exception as e:
        ui.notify(f"Piezo {axis} Error: {e}", type='negative')

def set_piezo_all(mode):
    set_piezo('X', mode)
    set_piezo('Y', mode)
    set_piezo('Z', mode)

def zero_piezo_all(mode='Voltage (V)'):
    state['pzt_x_val'] = 0.0
    state['pzt_y_val'] = 0.0
    state['pzt_z_val'] = 0.0
    set_piezo_all(mode)

# TAKE PIC _________________________________________________________________________________________________________________________________

def takePic():
    try:
        downloads_path = str(Path.home() / "Downloads")

        camera = get_camera()
        if camera is None:
            ui.notify("Error: Camera initialization failed.", type='negative')
            return

        frame = camera.snap()

        if frame is None or frame.size == 0:
            ui.notify("Error: Could not grab frame from active stream.", type='negative')
            return

        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
        frame = frame.astype(np.uint8)

        if len(frame.shape) == 2 or frame.shape[2] == 1:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filepath = os.path.join(downloads_path, f"snapshot_{timestamp}.jpg")

        success = cv2.imwrite(filepath, frame)

        if success:
            ui.notify("SUCCESS! Saved to your Downloads folder!", type='positive')
            print(f"Saved directly to absolute path: {filepath}")
        else:
            ui.notify("Write failed. Disk permissions issue.", type='negative')

    except Exception as e:
        ui.notify(f"Snapshot Error: {e}", type='negative')

# UI BUILD _________________________________________________________________________________________________________________________________

ui.label('Control').classes('text-h4')

with ui.row():
    with ui.card():
        ui.label("Camera")
        camera_image = ui.interactive_image().style("width:620px;height:480px;")
        ui.button('TAKE PIC', on_click=takePic).classes('w-full')

    with ui.card():
        ui.label("MATPLOTLIB")
        ui.image("https://placehold.co/640x480?text=matplot").style("width:640px;height:480px")

    with ui.card().style("width:300px;height:480px;"):
        ui.label("telemetry")
        ui.button('START', on_click=connect)
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
            ui.number(label='xRel').bind_value(state, 'xRel')
            ui.checkbox().bind_value(state, 'chx')
            ui.number(label='xAbs').bind_value(state, 'xAbs')

        with ui.row():
            ui.label("Y")
            ui.number(label='yRel').bind_value(state, 'yRel')
            ui.checkbox().bind_value(state, 'chy')
            ui.number(label='yAbs').bind_value(state, 'yAbs')

        with ui.row():
            ui.label("Z")
            ui.number(label='zRel').bind_value(state, 'zRel')
            ui.checkbox().bind_value(state, 'chz')
            ui.number(label='zAbs').bind_value(state, 'zAbs')

        with ui.row():
            ui.label("        ")
            ui.button('<', on_click=moverelneg).style("width:40px;height:40px;")
            ui.button('>', on_click=moverelpos).style("width:40px;height:40px;")
            ui.label("        ")
            ui.label("        ")
            ui.label("        ")
            ui.button("ABS", on_click=moveabs).style("width:40px;height:40px;")

        with ui.row():
            ui.button("HOME", on_click=homeLaComanda).style("width:120px;height:40px;")
            ui.button("STOP", on_click=noMoreMove).style("width:120px;height:40px;")

    with ui.card():
        ui.label("Piezo Control")

        mode_toggle = ui.toggle(['Voltage (V)', 'Position (µm)'], value='Voltage (V)')

        with ui.row():
            ui.label("Axis")
            ui.label("Target Value")

        with ui.row():
            ui.label("X")
            ui.number(label='X Target', value=0.0, format='%.2f').bind_value(state, 'pzt_x_val')
            ui.button("SET X", on_click=lambda: set_piezo('X', mode_toggle.value)).style("width:70px;")

        with ui.row():
            ui.label("Y")
            ui.number(label='Y Target', value=0.0, format='%.2f').bind_value(state, 'pzt_y_val')
            ui.button("SET Y", on_click=lambda: set_piezo('Y', mode_toggle.value)).style("width:70px;")

        with ui.row():
            ui.label("Z")
            ui.number(label='Z Target', value=0.0, format='%.2f').bind_value(state, 'pzt_z_val')
            ui.button("SET Z", on_click=lambda: set_piezo('Z', mode_toggle.value)).style("width:70px;")

        with ui.row():
            ui.button("ZERO ALL", on_click=lambda: zero_piezo_all(mode_toggle.value)).style("width:110px; height:40px;").props('color=warning')
            ui.button("SET ALL", on_click=lambda: set_piezo_all(mode_toggle.value)).style("width:110px; height:40px;")

    with ui.card():
        ui.label("Spectrometer")
        ui.button('INTEG.TIME').style('width:200px;height:60px;')
        ui.button('TAKE.BKG').style('width:200px;height:60px;')
        ui.button("TAKE.SP").style('width:200px;height:60px;')

# INITIALIZE TIMER _________________________________________________________________________________________________________________________

camera_timer = ui.timer(0.05, update_camera)

# RUN UI ___________________________________________________________________________________________________________________________________

ui.run()