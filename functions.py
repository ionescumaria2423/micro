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
from pylablib.devices import uc480
import numpy as np
from Thorlabs.MotionControl.GenericPiezoCLI.Piezo import PiezoControlModeTypes
#from decimal import Decimal
import time
import threading

stop_event = threading.Event()


def handle_startup():
    print("Application initialized.")





async def handle_startup():
    print("UI layer successfully loaded.")

CH_X = None
CH_Y = None
CH_Z = None
stepper_device = None

PiezoCH_X = None
PiezoCH_Y = None
PiezoCH_Z = None
piezo_device = None

timeout = 30000

cam = None
camera_consecutive_errors = 0
camera_timer = None

def get_camera():
    global cam
    if cam is None:
        cam = uc480.UC480Camera()
    return cam

def update_camera(camera_image):
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


async def connect():
    global CH_X, CH_Y, CH_Z, stepper_device
    global PiezoCH_X, PiezoCH_Y, PiezoCH_Z, piezo_device

    if camera_timer:
        camera_timer.deactivate()

    ui.notify("Init in progress", type='info')

    def _hardware_init():
        try:
            from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
            SimulationManager.Instance.InitializeSimulations()

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
        ui.notify("Init done!", type='positive')

    except Exception as e:
        print(f"Connection Error: {e}")
        ui.notify(f"Connection Failed: {e}", type='negative')

    finally:
        await asyncio.sleep(0.5)
        if camera_timer:
            camera_timer.activate()

state = {
    'chx': False, 'chy': False, 'chz': False,
    'xRel': 0.0,  'yRel': 0.0,  'zRel': 0.0,
    'xAbs': 0.0,  'yAbs': 0.0,  'zAbs': 0.0,
    'pzt_x_val': 0.0, 'pzt_y_val': 0.0, 'pzt_z_val': 0.0
}

def moverelpos():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return

    if state['chx'] and CH_X:
        CH_X.MoveRelative(MotorDirection.Forward, Decimal(state['xRel']), timeout)
    if state['chy'] and CH_Y:
        CH_Y.MoveRelative(MotorDirection.Forward, Decimal(state['yRel']), timeout)
    if state['chz'] and CH_Z:
        CH_Z.MoveRelative(MotorDirection.Forward, Decimal(state['zRel']), timeout)

def moverelneg():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return

    if state['chx'] and CH_X:
        CH_X.MoveRelative(MotorDirection.Backward, Decimal(state['xRel']), timeout)
    if state['chy'] and CH_Y:
        CH_Y.MoveRelative(MotorDirection.Backward, Decimal(state['yRel']), timeout)
    if state['chz'] and CH_Z:
        CH_Z.MoveRelative(MotorDirection.Backward, Decimal(state['zRel']), timeout)

def moveabs():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return
    if state['chx'] and CH_X:
        CH_X.MoveTo(Decimal(state['xAbs']), timeout)
    if state['chy'] and CH_Y:
        CH_Y.MoveTo(Decimal(state['yAbs']), timeout)
    if state['chz'] and CH_Z:
        CH_Z.MoveTo(Decimal(state['zAbs']), timeout)

def homeLaComanda():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return
    if state['chx'] and CH_X:
        CH_X.Home(60000)
    if state['chy'] and CH_Y:
        CH_Y.Home(60000)
    if state['chz'] and CH_Z:
        CH_Z.Home(60000)

async def noMoreMove():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return
    print("EMERGENCY STOP")
    try:
        if CH_X: CH_X.StopImmediate()
        if CH_Y: CH_Y.StopImmediate()
        if CH_Z: CH_Z.StopImmediate()
    except Exception as e:
        print(e)

    await asyncio.sleep(0.1)
    app.shutdown()

def set_piezo(axis, mode):
    channels = {'X': PiezoCH_X, 'Y': PiezoCH_Y, 'Z': PiezoCH_Z}
    ch = channels.get(axis)

    if ch is None:
        ui.notify(f"Piezo Axis {axis} not connected! Please click START to init first!", type='warning')
        return

    val = state.get(f'pzt_{axis.lower()}_val', 0.0)

    try:
        if mode == 'Position (µm)':
            ch.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
            ch.SetPosition(Decimal(val))
        else:
            ch.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
            ch.SetOutputVoltage(Decimal(val))


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
            ui.notify("Saved in Downloads!", type='positive')
            print(f"Saved directly to absolute path: {filepath}")
        else:
            ui.notify("Could not save.", type='negative')

    except Exception as e:
        ui.notify(f"Snapshot Error: {e}", type='negative')





def trigger_e_stop():
    global stop_requested
    stop_requested = True
    stop_hardware_immediately()


def stop_hardware_immediately():
    try:
        # ch_x = getattr("CH_X", None)
        # ch_y = getattr("CH_Y", None)
        # ch_z = getattr("CH_Z", None)

        if CH_X is not None:
            CH_X.StopImmediate()

        if CH_Y is not None:
            CH_Y.StopImmediate()

        if CH_Z is not None:
            CH_Z.StopImmediate()

    except Exception as e:
        print("Error stopping hardware:", e)


def handle_keyboard_events(e):
    if e.action.keydown and e.key == " ":
        trigger_e_stop()


async def move_stage():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return

    try:
        ui.notify("Move started", type="info")

        tasks = []

        if state['chx'] and CH_X:
            tasks.append(run.io_bound(CH_X.MoveTo, Decimal(state['xAbs']), timeout))

        if state['chy'] and CH_Y:
            tasks.append(run.io_bound(CH_Y.MoveTo, Decimal(state['yAbs']), timeout))

        if state['chz'] and CH_Z:
            tasks.append(run.io_bound(CH_Z.MoveTo, Decimal(state['zAbs']), timeout))

        await asyncio.gather(*tasks)

        ui.notify("Move complete", type="positive")

    except Exception as err:
        print("Move error:", err)
        ui.notify(f"Move failed: {err}", type="negative")


def check_stop_notify():
    global stop_requested
    if stop_requested:
        ui.notify("Emergency Stop Triggered!", type="negative")
        stop_requested = False


async def moverelneg_1():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return

    try:
        ui.notify("Move started", type="info")

        tasks = []

        if state['chx'] and CH_X:
            tasks.append(run.io_bound(
                CH_X.MoveRelative,
                MotorDirection.Backward,
                Decimal(state['xRel']),
                timeout
            ))

        if state['chy'] and CH_Y:
            tasks.append(run.io_bound(
                CH_Y.MoveRelative,
                MotorDirection.Backward,
                Decimal(state['yRel']),
                timeout
            ))

        if state['chz'] and CH_Z:
            tasks.append(run.io_bound(
                CH_Z.MoveRelative,
                MotorDirection.Backward,
                Decimal(state['zRel']),
                timeout
            ))

        await asyncio.gather(*tasks)

        ui.notify("Move complete", type="positive")

    except Exception as err:
        print("Move error:", err)
        ui.notify(f"Move failed: {err}", type="negative")

async def moverelpos_1():
    if CH_X is None or CH_Y is None or CH_Z is None:
        ui.notify("Please click START to init first!", type='warning')
        return

    try:
        ui.notify("Move started", type="info")

        tasks = []

        if state['chx'] and CH_X:
            tasks.append(run.io_bound(
                CH_X.MoveRelative,
                MotorDirection.Forward,
                Decimal(state['xRel']),
                timeout
            ))

        if state['chy'] and CH_Y:
            tasks.append(run.io_bound(
                CH_Y.MoveRelative,
                MotorDirection.Forward,
                Decimal(state['yRel']),
                timeout
            ))

        if state['chz'] and CH_Z:
            tasks.append(run.io_bound(
                CH_Z.MoveRelative,
                MotorDirection.Forward,
                Decimal(state['zRel']),
                timeout
            ))

        await asyncio.gather(*tasks)

        ui.notify("Move complete", type="positive")

    except Exception as err:
        print("Move error:", err)
        ui.notify(f"Move failed: {err}", type="negative")



async def set_piezo_1(axis, mode):
    channels = {'X': PiezoCH_X, 'Y': PiezoCH_Y, 'Z': PiezoCH_Z}
    ch = channels.get(axis)

    if ch is None:
        ui.notify(f"Piezo Axis {axis} not connected! Please click START to init first!", type='warning')
        return

    val = state.get(f'pzt_{axis.lower()}_val', 0.0)

    try:
        if mode == 'Position (µm)':
            await run.io_bound(ch.SetPositionControlMode, PiezoControlModeTypes.CloseLoop)
            await run.io_bound(ch.SetPosition, Decimal(val))
        else:
            await run.io_bound(ch.SetPositionControlMode, PiezoControlModeTypes.OpenLoop)
            await run.io_bound(ch.SetOutputVoltage, Decimal(val))

    except Exception as e:
        ui.notify(f"Piezo {axis} Error: {e}", type='negative')

async def set_piezo_all_1(mode):
    await asyncio.gather(
        set_piezo_1('X', mode),
        set_piezo_1('Y', mode),
        set_piezo_1('Z', mode),
    )


async def zero_piezo_all_1(mode='Voltage (V)'):
    state['pzt_x_val'] = 0.0
    state['pzt_y_val'] = 0.0
    state['pzt_z_val'] = 0.0

    await set_piezo_all(mode)


# cam = None
# camera_consecutive_errors = 0
# camera_timer = None
#
#
# def get_camera():
#     global cam
#     if cam is None:
#         cam = cv2.VideoCapture(0)
#     return cam
#
#
# def update_camera(camera_image):
#     global cam, camera_consecutive_errors
#
#     try:
#         camera = get_camera()
#
#         ret, frame = camera.read()
#
#         if ret and frame is not None and frame.size > 0:
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#
#             _, jpg = cv2.imencode('.jpg', frame)
#             encoded = base64.b64encode(jpg).decode("utf-8")
#
#             camera_image.set_source(f"data:image/jpeg;base64,{encoded}")
#             camera_consecutive_errors = 0
#         else:
#             raise Exception("Failed to grab frame from webcam")
#
#     except Exception as e:
#         camera_consecutive_errors += 1
#         print(f"Camera frame drop ({camera_consecutive_errors}):", e)
#
#         if camera_consecutive_errors > 5:
#             print("Resetting camera connection...")
#             try:
#                 if cam:
#                     cam.release()
#             except:
#                 pass
#             cam = None
#             camera_consecutive_errors = 0
#