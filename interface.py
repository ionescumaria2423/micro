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

#FUNCTIONS_________________________________________________________________________________________________________________________________

async def handle_startup():
    print("UI layer successfully loaded. Initializing Thorlabs Simulations...")
    SimulationManager.Instance.InitializeSimulations()

app.on_startup(handle_startup)

CH_X = None
CH_Y = None
CH_Z = None
stepper_device = None
timeout = 30000
simulation = True

def connect():
    global CH_X, CH_Y, CH_Z, stepper_device, spectrometer
    CH_X, CH_Y, CH_Z, stepper_device = init_BSC(serial_Stepper)

    spectrometer = sp.Ocean_Optics()
    spectrometer.initSp(simulation=simulation)

#__________________________________________________________________________________________________________________________________________

state = {
    'chx': False, 'chy': False, 'chz': False,
    'xRel': 0.0,  'yRel': 0.0,  'zRel': 0.0,
    'xAbs': 0.0,
    'yAbs': 0.0,
    'zAbs': 0.0
}

def moverelpos():
        if state['chx']:
            CH_X.MoveRelative(
                MotorDirection.Forward,
                Decimal(state['xRel']),
                timeout,
            )

        if state['chy']:
            CH_Y.MoveRelative(
                MotorDirection.Forward,
                Decimal(state['yRel']),
                timeout,
            )

        if state['chz']:
            CH_Z.MoveRelative(
                MotorDirection.Forward,
                Decimal(state['zRel']),
                timeout,
            )

def moverelneg():
    if state['chx']:
        CH_X.MoveRelative(
            MotorDirection.Backward,
            Decimal(state['xRel']),
            timeout,
        )

    if state['chy']:
        CH_Y.MoveRelative(
            MotorDirection.Backward,
            Decimal(state['yRel']),
            timeout,
        )

    if state['chz']:
        CH_Z.MoveRelative(
            MotorDirection.Backward,
            Decimal(state['zRel']),
            timeout,
        )

#__________________________________________________________________________________________________________________________________________

def moveabs():
        if state['chx']:
            CH_X.MoveTo(Decimal(state['xAbs']), timeout)

        if state['chy']:
            CH_Y.MoveTo(Decimal(state['yAbs']), timeout)

        if state['chz']:
            CH_Z.MoveTo(Decimal(state['zAbs']), timeout)

#__________________________________________________________________________________________________________________________________________

def homeLaComanda():
    if state['chx']:
        CH_X.Home(60000)

    if state['chy']:
        CH_Y.Home(60000)

    if state['chz']:
        CH_Z.Home(60000)

#__________________________________________________________________________________________________________________________________________

async def noMoreMove():
    print("EMERGENCY STOP")

    try:
        if CH_X:
            CH_X.StopImmediate()
        if CH_Y:
            CH_Y.StopImmediate()
        if CH_Z:
            CH_Z.StopImmediate()
    except Exception as e:
        print(e)

    await asyncio.sleep(0.1)

    app.shutdown()

#TAKE PIC__________________________________________________________________________________________________________________________________________

def takePic():
    global cap
    try:
        downloads_path = str(Path.home() / "Downloads")

        if cap is None or not cap.isOpened():
            ui.notify("Error: Camera stream is not active.", type='negative')
            return

        ret, frame = cap.read()

        if not ret or frame is None:
            ui.notify("Error: Could not grab frame from active stream.", type='negative')
            return

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filepath = os.path.join(downloads_path, f"snapshot_{timestamp}.jpg")

        success = cv2.imwrite(filepath, frame)

        if success:
            ui.notify(f"SUCCESS! Saved to your Downloads folder!", type='positive')
            print(f"Saved directly to absolute path: {filepath}")
        else:
            ui.notify("Write failed. Laptop disk permissions issue.", type='negative')

    except Exception as e:
        ui.notify(f"Snapshot Error: {e}", type='negative')

#UI BUILD__________________________________________________________________________________________________________________________________________

ui.label('Control').classes('text-h4')

with ui.row():

    with ui.card():
        ui.label("Camera")
        camera_image = ui.interactive_image().style("width:620px;height:480px;")
        ui.button('TAKE PIC', on_click=takePic).classes('w-full')

    with ui.card():
        ui.label("MATPLOTLIB")
        ui.image("https://placehold.co/640x480?text=matplot").style(
            "width:640px;height:480px")

    with ui.card().style("width:300px;height:480px;"):
        ui.label("telemetry")
        ui.button('START', on_click=lambda:connect())
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
            ui.button("HOME", on_click=lambda:homeLaComanda()).style("width:120px;height:40px;")
            ui.button("STOP", on_click=lambda:noMoreMove()).style("width:120px;height:40px;")
    with ui.card():
        ui.label("Piezo Control")
        ui.label("not yetttt")

    with ui.card():
        ui.label("Spectrometer")
        ui.button('INTEG.TIME').style('width:200px;height:60px;')
        ui.button('TAKE.BKG').style('width:200px;height:60px;')
        ui.button("TAKE.SP").style('width:200px;height:60px;')

#THORCAM__________________________________________________________________________________________________________________________________

# cam = None

# def get_camera():
#     global cam
#     if cam is None:
#         cam = uc480.UC480Camera()
#     return cam
#
# def update_camera():
#     global cam
#
#     try:
#         cam = get_camera()
#         frame = cam.snap()
#
#         frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
#         frame = frame.astype(np.uint8)
#         frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
#
#         _, jpg = cv2.imencode('.jpg', frame)
#         encoded = base64.b64encode(jpg).decode("utf-8")
#
#         camera_image.set_source(f"data:image/jpeg;base64,{encoded}")
#
#     except Exception as e:
#         print("Camera error:", e)
#
#
#         try:
#             cam.close()
#         except:
#             pass
#
#         cam = None

#WEBCAM________________________________________________________________________________________________________________________________

cap = None

def get_camera():
    global cap
    if cap is None:
        cap = cv2.VideoCapture(0)
    return cap

def update_camera():
    try:
        camera = get_camera()
        ret, frame = camera.read()

        if not ret:
            print("Failed to grab frame from webcam")
            return


        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        _, jpg = cv2.imencode('.jpg', frame)
        encoded = base64.b64encode(jpg).decode("utf-8")

        camera_image.set_source(f"data:image/jpeg;base64,{encoded}")

    except Exception as e:
        print(f"Error updating camera: {e}")

#CAMERA UPDATE TIMER________________________________________________________________________________________________________________________

ui.timer(0.05, update_camera)

#RUN_UI_____________________________________________________________________________________________________________________________________

ui.run()