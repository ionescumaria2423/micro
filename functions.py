import asyncio
import base64
import io
import os
from pathlib import Path
import time
from nicegui import app, run, ui
import spectra_lib as sp
from merge import *
from System import Decimal
from Thorlabs.MotionControl.GenericPiezoCLI.Piezo import PiezoControlModeTypes
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
# from pylab import Thorlabs
# from decimal import Decimal
import json
import time
import numpy as np
import pandas as pd
import plotly.express as px
from nicegui import ui


try:
  from pylablib.devices import uc480
except ImportError:
  uc480 = None

state = {
    "chx": False,
    "chy": False,
    "chz": False,
    "xRel": 0.0,
    "yRel": 0.0,
    "zRel": 0.0,
    "xAbs": 0.0,
    "yAbs": 0.0,
    "zAbs": 0.0,
    "pzt_x_val": 0.0,
    "pzt_y_val": 0.0,
    "pzt_z_val": 0.0,
    "deltaX":0.0,
    "deltaY":0.0,
    "nx":0.0,
    "ny":0.0,
}


CH_X = None
CH_Y = None
CH_Z = None
stepper_device = None


PiezoCH_X = None
PiezoCH_Y = None
PiezoCH_Z = None
piezo_device = None

timeout = 30000
stop_requested = False


cam = None
camera_consecutive_errors = 0
camera_timer = None



def handle_startup():
  print("Application initialized.")


async def connect():
  global CH_X, CH_Y, CH_Z, stepper_device
  global PiezoCH_X, PiezoCH_Y, PiezoCH_Z, piezo_device

  if camera_timer:
    camera_timer.deactivate()

  ui.notify("Init in progress", type="info")

  def _hardware_init():
    try:
      from Thorlabs.MotionControl.DeviceManagerCLI import (
          DeviceManagerCLI,
          SimulationManager,
      )

      SimulationManager.Instance.InitializeSimulations()
      DeviceManagerCLI.BuildDeviceList()
      time.sleep(0.2)
    except Exception as dev_err:
      print("DeviceManager CLI issue:", dev_err)

    s_step = globals().get("serial_Stepper", "")
    s_piezo = globals().get("serial_Piezo", "")

    x, y, z, step_dev = init_BSC(s_step)
    px, py, pz, pz_dev = init_BPC(s_piezo)

    # Connect Steppers
    for ch in [x, y, z]:
      if ch is not None:
        if not ch.IsConnected:
          ch.Connect(s_step)
        ch.StartPolling(250)
        ch.EnableDevice()
        time.sleep(0.1)

    # Connect Piezos
    for ch in [px, py, pz]:
      if ch is not None:
        if not ch.IsConnected:
          ch.Connect(s_piezo)
        ch.StartPolling(250)
        ch.EnableDevice()
        time.sleep(0.1)

    return x, y, z, step_dev, px, py, pz, pz_dev

  try:
    (
        CH_X,
        CH_Y,
        CH_Z,
        stepper_device,
        PiezoCH_X,
        PiezoCH_Y,
        PiezoCH_Z,
        piezo_device,
    ) = await run.io_bound(_hardware_init)
    ui.notify("Init done!", type="positive")

  except Exception as e:
    print(f"Connection Error: {e}")
    ui.notify(f"Connection Failed: {e}", type="negative")

  finally:
    await asyncio.sleep(0.5)
    if camera_timer:
      camera_timer.activate()



def get_camera():
  global cam
  if cam is None and uc480 is not None:
    cam = uc480.UC480Camera()
  return cam


def update_camera(camera_image):
  global cam, camera_consecutive_errors

  try:
    camera = get_camera()
    if camera is None:
      return

    frame = camera.snap()

    if frame is not None and frame.size > 0:
      frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
      frame = frame.astype(np.uint8)
      frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

      _, jpg = cv2.imencode(".jpg", frame)
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
      except Exception:
        pass
      cam = None
      camera_consecutive_errors = 0


def takePic():
  try:
    downloads_path = str(Path.home() / "Downloads")

    camera = get_camera()
    if camera is None:
      ui.notify("Error: Camera initialization failed.", type="negative")
      return

    frame = camera.snap()

    if frame is None or frame.size == 0:
      ui.notify(
          "Error: Could not grab frame from active stream.", type="negative"
      )
      return

    frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
    frame = frame.astype(np.uint8)

    if len(frame.shape) == 2 or frame.shape[2] == 1:
      frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filepath = os.path.join(downloads_path, f"snapshot_{timestamp}.jpg")

    success = cv2.imwrite(filepath, frame)

    if success:
      ui.notify("Saved in Downloads!", type="positive")
    else:
      ui.notify("Could not save.", type="negative")

  except Exception as e:
    ui.notify(f"Snapshot Error: {e}", type="negative")



def moverelpos():
  if CH_X is None or CH_Y is None or CH_Z is None:
    ui.notify("Please click START to init first!", type="warning")
    return

  if state["chx"] and CH_X:
    CH_X.MoveRelative(MotorDirection.Forward, Decimal(state["xRel"]), timeout)
  if state["chy"] and CH_Y:
    CH_Y.MoveRelative(MotorDirection.Forward, Decimal(state["yRel"]), timeout)
  if state["chz"] and CH_Z:
    CH_Z.MoveRelative(MotorDirection.Forward, Decimal(state["zRel"]), timeout)


def moverelneg():
  if CH_X is None or CH_Y is None or CH_Z is None:
    ui.notify("Please click START to init first!", type="warning")
    return

  if state["chx"] and CH_X:
    CH_X.MoveRelative(MotorDirection.Backward, Decimal(state["xRel"]), timeout)
  if state["chy"] and CH_Y:
    CH_Y.MoveRelative(MotorDirection.Backward, Decimal(state["yRel"]), timeout)
  if state["chz"] and CH_Z:
    CH_Z.MoveRelative(MotorDirection.Backward, Decimal(state["zRel"]), timeout)


def moveabs():
  if CH_X is None or CH_Y is None or CH_Z is None:
    ui.notify("Please click START to init first!", type="warning")
    return
  if state["chx"] and CH_X:
    CH_X.MoveTo(Decimal(state["xAbs"]), timeout)
  if state["chy"] and CH_Y:
    CH_Y.MoveTo(Decimal(state["yAbs"]), timeout)
  if state["chz"] and CH_Z:
    CH_Z.MoveTo(Decimal(state["zAbs"]), timeout)


def homeLaComanda():
  if CH_X is None or CH_Y is None or CH_Z is None:
    ui.notify("Please click START to init first!", type="warning")
    return
  if state["chx"] and CH_X:
    CH_X.Home(60000)
  if state["chy"] and CH_Y:
    CH_Y.Home(60000)
  if state["chz"] and CH_Z:
    CH_Z.Home(60000)


async def noMoreMove():
  if CH_X is None or CH_Y is None or CH_Z is None:
    ui.notify("Please click START to init first!", type="warning")
    return
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


def set_piezo(axis, mode):
  channels = {"X": PiezoCH_X, "Y": PiezoCH_Y, "Z": PiezoCH_Z}
  ch = channels.get(axis)

  if ch is None:
    ui.notify(
        f"Piezo Axis {axis} not connected! Please click START to init first!",
        type="warning",
    )
    return

  val = state.get(f"pzt_{axis.lower()}_val", 0.0)

  try:
    if mode == "Position (µm)":
      ch.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
      ch.SetPosition(Decimal(val))
    else:
      ch.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
      ch.SetOutputVoltage(Decimal(val))

  except Exception as e:
    ui.notify(f"Piezo {axis} Error: {e}", type="negative")


def set_piezo_all(mode):
  set_piezo("X", mode)
  set_piezo("Y", mode)
  set_piezo("Z", mode)


def zero_piezo_all(mode="Voltage (V)"):
  state["pzt_x_val"] = 0.0
  state["pzt_y_val"] = 0.0
  state["pzt_z_val"] = 0.0
  set_piezo_all(mode)



integr_time = 10000
_device_instance = None
_wavelengths_instance = None

background_spectrum = None
saved_spectra = []


def _get_spec_resources():
  global _device_instance, _wavelengths_instance
  if _device_instance is None:
    _device_instance = sp.get_spectrometer()
    _wavelengths_instance = _device_instance.get_wavelengths()
  return _device_instance, _wavelengths_instance


def set_integration_time_dialog():
  device, _ = _get_spec_resources()

  async def apply_time():
    val = time_input.value
    if val and val > 0:
      device.set_integration_time(int(val))
      ui.notify(f"Integration time set to {val} µs", type="positive")
      dialog.close()

  with ui.dialog() as dialog, ui.card():
    ui.label("Set Integration Time (microseconds):").classes("text-bold")
    time_input = ui.number(label="µs", value=integr_time, min=1000, step=5000)
    with ui.row():
      ui.button("Cancel", on_click=dialog.close).props("flat")
      ui.button("Apply", on_click=apply_time)

  dialog.open()


def take_bkg():
  global background_spectrum
  device, _ = _get_spec_resources()
  background_spectrum = np.array(device.get_intensities())
  ui.notify("Background spectrum stored!", type="positive")


def take_sp():
  global background_spectrum
  device, wavelengths = _get_spec_resources()
  raw_y = np.array(device.get_intensities())

  if background_spectrum is not None and len(background_spectrum) == len(
      raw_y
  ):
    processed_y = raw_y - background_spectrum
  else:
    processed_y = raw_y

  saved_spectra.append({
      "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
      "wavelengths": wavelengths,
      "raw": raw_y,
      "corrected": processed_y,
  })

  try:
    downloads_path = str(Path.home() / "Downloads")
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filepath = os.path.join(downloads_path, f"spectrum_{timestamp}.csv")

    data = np.column_stack((wavelengths, raw_y, processed_y))
    header = "Wavelength_nm,Raw_Intensity,Corrected_Intensity"
    np.savetxt(filepath, data, delimiter=",", header=header, comments="")

    ui.notify(
        f"Spectrum #{len(saved_spectra)} saved to Downloads!", type="positive"
    )
  except Exception as e:
    ui.notify(f"Saved to memory, CSV write failed: {e}", type="warning")


def update_plot(plot_ui_element):
  global background_spectrum
  try:
    device, wavelengths = _get_spec_resources()
    raw_y = np.array(device.get_intensities())

    if background_spectrum is not None and len(background_spectrum) == len(
        raw_y
    ):
      y = raw_y - background_spectrum
      y_axis_title = 'Corrected Intensity (counts)'
    else:
      y = raw_y
      y_axis_title = 'Intensity (counts)'


    plot_ui_element.figure['data'] = [{
        'x': wavelengths.tolist(),
        'y': y.tolist(),
        'type': 'scatter',
        'mode': 'lines',
        'line': {'color': 'blue', 'width': 1},
    }]
    plot_ui_element.figure['layout']['yaxis']['title'] = y_axis_title

    plot_ui_element.update()

  except Exception as e:
    print(f'Error updating plot: {e}')


# def specroScan():
#   nx = int(state['nx'])
#   ny = int(state['ny'])
#
#   delta_x = state['deltaX']
#   delta_y = state['deltaY']
#
#   step_x = Decimal(delta_x/nx)
#   step_y = Decimal(delta_y/ny)
#
#   sx = Decimal(float(delta_x/nx)*0.01)
#   sy = Decimal(float(delta_y/ny)*0.01)
#
#   s=Decimal(float(delta_x//3))
#   d=Decimal(float(delta_y//3))
#
#   a=Decimal(float(delta_x%3))
#   b=Decimal(float(delta_y%3))
#
#   print(f"Starting Scan: nx={nx}, ny={ny}, deltaX={delta_x}, deltaY={delta_y}")
#
#
#   if delta_x <= 4 or delta_y <= 4:
#     for i in range(ny):
#
#
#       for j in range(nx):
#         target_x = Decimal(j * (delta_x / nx if nx > 1 else 0))
#         print(f" -> Moving Piezo X to: {target_x}")
#         PiezoCH_X.SetPosition(target_x)
#         time.sleep(0.05)
#
#       target_y = Decimal(i * (delta_y / ny if ny > 1 else 0))
#       print(f"Moving Piezo Y to: {target_y}")
#       PiezoCH_Y.SetPosition(target_y)
#       time.sleep(0.05)
#
#
#
# elif delta_x > 4 and delta_y > 4 and sx>=0.6 and sy>=0.6:
  # else:
  #   for i in range(ny):
  #     for j in range(nx):
  #
  #       CH_X.MoveRelative(MotorDirection.Forward, sx, timeout)
  #       time.sleep(0.05)
  #
  #     CH_Y.MoveRelative(MotorDirection.Forward, sy, timeout)
  #
  #     CH_X.MoveRelative(MotorDirection.Backward, Decimal(float(delta_x) * 0.01), timeout)
  #     time.sleep(0.05)


  #else:
  #   n=PiezoCH_X.get_position()
  #   m=PiezoCH_Y.get_position()
  #   s=CH_X.get_position
  #   for i in range (ny):
  #     for j in range (nx):
  #
  #       if (PiezoCH_X.get_position() + step_x)>3:
  #         a=3-PiezoCH_X.get_position()
  #         PiezoCH_X.SetPosition(n)
  #         CH_X.MoveRelative(MotorDirection.Forward, 0.03, timeout)
  #         PiezoCH_X.SetPosition(PiezoCH_X.get_position() + step_x - a)
  #         time.sleep(0.05)
  #
  #       elif(CH_X.get_position() * 0.01 + step_x > delta_x):
  #         PiezoCH_X.SetPosition(n)
  #         CH_X.MoveTo(s, timeout)
  #         time.sleep(0.05)
  #
  #       else:
  #         PiezoCH_X.SetPosition(PiezoCH_X.get_position + step_x)
  #         time.sleep(0.05)

global_scan_data = []


def _run_heavy_scan(current_state):
  scan_data = []
  nx = int(current_state["nx"])
  ny = int(current_state["ny"])
  delta_x = current_state["deltaX"]
  delta_y = current_state["deltaY"]
  device = sp.get_spectrometer(simulation=False)



  sx = Decimal(float(delta_x / nx) * 0.01)
  sy = Decimal(float(delta_y / ny) * 0.01)

  if delta_x <= 4 or delta_y <= 4:
    for i in range(ny):
      target_y = Decimal(i * (delta_y / ny if ny > 1 else 0))
      PiezoCH_Y.SetPosition(target_y)
      time.sleep(0.05)

      for j in range(nx):
        target_x = Decimal(j * (delta_x / nx if nx > 1 else 0))
        PiezoCH_X.SetPosition(target_x)
        time.sleep(0.05)

        time.sleep(integr_time * 0.001 + 0.05)

        wavelengths = device.get_wavelengths()
        intensities = device.get_intensities()
        peak_intensity = float(np.max(intensities))

        scan_data.append({
            "x": float(target_x),
            "y": float(target_y),
            "peak_intensity": peak_intensity,
            "wavelengths": wavelengths.tolist(),
            "intensities": intensities.tolist(),
        })
  else:
    for i in range(ny):
      for j in range(nx):
        CH_X.MoveRelative(MotorDirection.Forward, sx, timeout)
        time.sleep(integr_time * 0.001 + 0.05)

        wavelengths = device.get_wavelengths()
        intensities = device.get_intensities()
        peak_intensity = float(np.max(intensities))

        scan_data.append({
            "x": j,
            "y": i,
            "peak_intensity": peak_intensity,
            "wavelengths": wavelengths.tolist(),
            "intensities": intensities.tolist(),
        })

      CH_Y.MoveRelative(MotorDirection.Forward, sy, timeout)
      CH_X.MoveRelative(
          MotorDirection.Backward, Decimal(float(delta_x) * 0.01), timeout
      )
      time.sleep(0.05)

  return scan_data


async def specroScan():
  global global_scan_data
  ui.notify("Scan started...", type="info")

  try:
    current_state = dict(state)

    global_scan_data = await run.io_bound(_run_heavy_scan, current_state)

    if global_scan_data:
      ui.notify("Scan complete! Generating map...", type="positive")
      show_map_dialog()
    else:
      ui.notify("Scan finished, but no data was collected.", type="warning")

  except Exception as e:
    print(f"ERROR DURING SCAN: {e}")
    ui.notify(f"Error during scan: {e}", type="negative")


def show_map_dialog():
  df = pd.DataFrame(global_scan_data)

  fig = px.scatter(
      df,
      x="x",
      y="y",
      color="peak_intensity",
      color_continuous_scale="Viridis",
      title="2D Spectrometer Scan Map",
      labels={
          "x": "X Position",
          "y": "Y Position",
          "peak_intensity": "Peak Intensity",
      },
  )
  fig.update_layout(
      xaxis=dict(scaleanchor="y", scaleratio=1),
      margin=dict(l=20, r=20, t=40, b=20),
  )

  with ui.dialog() as map_dialog, ui.card().classes("w-[800px] h-[650px]"):
    ui.label("Scan Results Map").classes("text-h6 font-bold")
    ui.plotly(fig).classes("w-full h-[500px]")

    with ui.row().classes("w-full justify-end gap-2 mt-auto"):
      # Robust download trigger using a data URI and JavaScript
      json_str = json.dumps(global_scan_data, indent=4)

      def download_json():
        ui.run_javascript(f"""
                const blob = new Blob([{json.dumps(json_str)}], {{type: 'application/json'}});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'all_spectrums_data.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            """)

      ui.button("Save JSON", on_click=download_json).props("color=green")
      ui.button("Close", on_click=map_dialog.close).props("color=red flat")

    map_dialog.open()