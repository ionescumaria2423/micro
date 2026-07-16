import base64
import cv2
import clr
import pythonnet
import numpy as np
from nicegui import ui, app
from numba.core.utils import chain_exception
from pylablib.devices import uc480
from pyqtgraph.examples.relativity import Simulation
from merge import *
from System import Decimal

async def handle_startup():
    print("UI layer successfully loaded. Initializing Thorlabs Simulations...")
    SimulationManager.Instance.InitializeSimulations()

app.on_startup(handle_startup)

CH_X = None
CH_Y = None
CH_Z = None
stepper_device = None
timeout = 30000

def connect():
    global CH_X, CH_Y, CH_Z, stepper_device
    CH_X, CH_Y, CH_Z, stepper_device = init_BSC(serial_Stepper)

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



def moveabs():
        if state['chx']:
            CH_X.MoveTo(Decimal(state['xAbs']), timeout)

        if state['chy']:
            CH_Y.MoveTo(Decimal(state['yAbs']), timeout)

        if state['chz']:
            CH_Z.MoveTo(Decimal(state['zAbs']), timeout)


ui.label('Control').classes('text-h4')

with ui.row():

    with ui.card():
        ui.label("Camera")
        camera_image = ui.interactive_image().style("width:620px;height:480px;")

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
            # ui.button("<",).style("width:40px;height:40px;")
            # ui.button(">").style("width:40px;height:40px;")
            ui.label("        ")
            ui.label("        ")
            ui.label("        ")
            ui.button("ABS", on_click=moveabs).style("width:40px;height:40px;")

        with ui.row():
            ui.button("HOME").style("width:120px;height:40px;")
            ui.button("STOP").style("width:120px;height:40px;")
    with ui.card():
        ui.label("Piezo Control")
        ui.label("not yetttt")

    with ui.card():
        ui.label("Spectrometer")
        ui.button('INTEG.TIME').style('width:200px;height:60px;')
        ui.button('TAKE.BKG').style('width:200px;height:60px;')
        ui.button("TAKE.SP").style('width:200px;height:60px;')

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

ui.timer(0.05, update_camera)

ui.run()