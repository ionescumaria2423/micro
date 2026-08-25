#FUNCTIONS FILE


#IMPORTS=======================================================================================================================================
import asyncio
import base64
import io
import os
from pathlib import Path
import time
from nicegui import app, run, ui
import spectra_lib as sp
from merge import *
from System import Decimal, Math
from Thorlabs.MotionControl.GenericPiezoCLI.Piezo import PiezoControlModeTypes
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
import time
import numpy as np
import pandas as pd
import plotly.express as px
from nicegui import ui
import kaleido
import plotly.graph_objects as go


#STATES========================================================================================================================================


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
  "x_live_pos": 0.0,
  "y_live_pos": 0.0,
  "z_live_pos": 0.0,
  "pzt_x_live":0.0,
  "pzt_y_live":0.0,
  "pzt_z_live":0.0,
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
stopScan = False


cam = None
camera_consecutive_errors = 0
camera_timer = None

#INITIALIZATION AND CONNECT======================================================================================================================

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

    for ch in [x, y, z]:
      if ch is not None:
        if not ch.IsConnected:
          ch.Connect(s_step)
        ch.StartPolling(250)
        ch.EnableDevice()
        time.sleep(0.1)

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


#CAMERA========================================================================================================================================


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
    #print(f"Camera frame drop ({camera_consecutive_errors}):", e)

    if camera_consecutive_errors > 5:
      #print("Resetting camera connection...")
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


#STEPPER CONTROLS================================================================================================================================


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


#PIEZO CONTROLS==================================================================================================================================

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

#LIVE POSITIONS==================================================================================================================================

def update_live_positions():
  global CH_X, CH_Y, CH_Z, PiezoCH_X, PiezoCH_Y, PiezoCH_Z
  try:
    if CH_X is not None:
      if hasattr(CH_X, "Position"):
        state["x_live_pos"] = float(str(CH_X.Position))

    if CH_Y is not None:
      if hasattr(CH_Y, "Position"):
        state["y_live_pos"] = float(str(CH_Y.Position))

    if CH_Z is not None:
      if hasattr(CH_Z, "Position"):
        state["z_live_pos"] = float(str(CH_Z.Position))

    if PiezoCH_X is not None and hasattr(PiezoCH_X, "GetPosition"):
      state["pzt_x_live"] = float(str(PiezoCH_X.GetPosition()))

    if PiezoCH_Y is not None and hasattr(PiezoCH_Y, "GetPosition"):
      state["pzt_y_live"] = float(str(PiezoCH_Y.GetPosition()))

    if PiezoCH_Z is not None and hasattr(PiezoCH_Z, "GetPosition"):
      state["pzt_z_live"] = float(str(PiezoCH_Z.GetPosition()))

  except Exception as e:
    print(f"Error with data update: {e}")


#LIVE SPECTROMETER SCAN=================================================================================================================


def StopScan():
  global stopScan
  stopScan = True
  ui.notify(f"stop scan", type="negative")

async def specroScan_live():
  global stopScan
  stopScan = False
  client = ui.context.client
  asyncio.create_task(_run_specro_scan_live_background(client))


async def _run_specro_scan_live_background(client):
  with client:
    global global_scan_data, stopScan
    ui.notify("Scan started", type="info")
    global_scan_data = []

    fig = go.Figure(
        data=[
            go.Scatter(
                x=[],
                y=[],
                mode="markers",
                marker=dict(color=[], colorscale="Inferno", showscale=True),
            )
        ]
    )
    fig.update_layout(
        title="Live 2D Spectrometer Scan Map",
        margin=dict(l=40, r=20, t=40, b=20),
        xaxis=dict(title="X Position", scaleanchor="y", scaleratio=1),
        yaxis=dict(title="Y Position"),
        uirevision="true",
    )

    with ui.dialog() as map_dialog, ui.card().classes("w-[800px] h-[650px]"):
      ui.label("Scan Results Map (Live -> 3D)").classes("text-h6 font-bold")

      dialog_plot = ui.plotly(fig).classes("w-full h-[500px]")

      json_str_ref = {"data": "[]"}

      def download_json():
        ui.run_javascript(f"""
                const blob = new Blob([{json.dumps(json_str_ref['data'])}], {{type: 'application/json'}});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'all_spectrums_data.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            """)

      def download_png():
        try:
          img_bytes = fig.to_image(format="png", width=1000, height=800, scale=2)
          ui.download(img_bytes, filename="spectrometer_scan_map.png")
          ui.notify("Downloading plot image...", type="positive")
        except Exception as e:
          ui.notify(f"Failed to export image: {e}", type="negative")
          print(f"PNG Export Error: {e}")

      with ui.row().classes("w-full justify-end gap-2 mt-auto"):
        ui.button("Save JSON", on_click=download_json).props("color=green")
        ui.button("Save PNG", on_click=download_png).props("color=green")
        ui.button("Close", on_click=map_dialog.close).props("color=red flat")
        ui.button("STOP SCANNING", on_click=stopScan).props("color=red")

      map_dialog.open()

    try:
      current_state = dict(state)
      nx = int(current_state["nx"])
      ny = int(current_state["ny"])
      delta_x = current_state["deltaX"]
      delta_y = current_state["deltaY"]
      device = sp.get_spectrometer(simulation=False)

      def round_dec(dec_val, decimals=4):
        factor = Decimal(1)
        for _ in range(decimals):
          factor = factor * Decimal(10)
        return Decimal.Round(dec_val * factor) / factor

      nx_dec = Decimal(nx) if nx > 0 else Decimal(1)
      ny_dec = Decimal(ny) if ny > 0 else Decimal(1)
      dec_one = Decimal(1)
      dec_hundred = Decimal(100)

      sx = round_dec((Decimal(delta_x) / nx_dec) * (dec_one / dec_hundred), 4)
      sy = round_dec((Decimal(delta_y) / ny_dec) * (dec_one / dec_hundred), 4)

      if delta_x <= 4 or delta_y <= 4:
        step_y = round_dec(Decimal(delta_y) / ny_dec, 4) if ny > 1 else Decimal(0)
        step_x = round_dec(Decimal(delta_x) / nx_dec, 4) if nx > 1 else Decimal(0)

        for i in range(ny):
          if stopScan:
            break

          target_y = round_dec(Decimal(i) * step_y, 4)
          await run.io_bound(PiezoCH_Y.SetPosition, target_y)
          await asyncio.sleep(0.05)

          for j in range(nx):
            if stopScan:
              break

            target_x = round_dec(Decimal(j) * step_x, 4)
            await run.io_bound(PiezoCH_X.SetPosition, target_x)
            await asyncio.sleep(0.05)
            await asyncio.sleep(integr_time * 0.000001 + 0.05)

            wavelengths = await run.io_bound(device.get_wavelengths)
            intensities = await run.io_bound(device.get_intensities)
            peak_intensity = float(np.max(intensities))

            new_point = {
              "x": float(target_x),
              "y": float(target_y),
              "peak_intensity": peak_intensity,
              "wavelengths": wavelengths.tolist(),
              "intensities": intensities.tolist(),
            }
            global_scan_data.append(new_point)
            df = pd.DataFrame(global_scan_data)

            fig.data[0].x = df["x"]
            fig.data[0].y = df["y"]
            fig.data[0].marker.color = df["peak_intensity"]
            dialog_plot.update()
      else:
        for i in range(ny):
          if stopScan:
            break
          for j in range(nx):
            if stopScan:
              break

            wavelengths = await run.io_bound(device.get_wavelengths)
            intensities = await run.io_bound(device.get_intensities)
            peak_intensity = float(np.max(intensities))

            new_point = {
              "x": j,
              "y": i,
              "peak_intensity": peak_intensity,
              "wavelengths": wavelengths.tolist(),
              "intensities": intensities.tolist(),
            }
            global_scan_data.append(new_point)
            df = pd.DataFrame(global_scan_data)

            fig.data[0].x = df["x"]
            fig.data[0].y = df["y"]
            fig.data[0].marker.color = df["peak_intensity"]
            dialog_plot.update()

            await run.io_bound(CH_X.MoveRelative, MotorDirection.Forward, sx, timeout)
            await asyncio.sleep(integr_time * 0.000001 + 0.05)

          await run.io_bound(CH_Y.MoveRelative, MotorDirection.Forward, sy, timeout)

          return_x = round_dec(Decimal(delta_x) * (dec_one / dec_hundred), 4)
          await run.io_bound(CH_X.MoveRelative, MotorDirection.Backward, return_x, timeout)
          await asyncio.sleep(0.05)


        if global_scan_data and not stopScan:
          ui.notify("Scan done! Converting to 3D Surface...", type="positive")
          json_str_ref["data"] = json.dumps(global_scan_data, indent=4)

          df = pd.DataFrame(global_scan_data)
          pivot_df = df.pivot(index="y", columns="x", values="peak_intensity")
          z_data = pivot_df.values
          x_data = pivot_df.columns.tolist()
          y_data = pivot_df.index.tolist()

          new_fig = go.Figure(
            data=[go.Surface(z=z_data, x=x_data, y=y_data, colorscale="Inferno")]
          )
          fig.update_layout(
            title="3D Spectrometer Scan Surface Map",
            scene=dict(
              xaxis_title="X Position",
              yaxis_title="Y Position",
              zaxis_title="Peak Intensity",
              aspectmode="auto",
            ),
            margin=dict(l=20, r=20, t=40, b=20),
          )
          dialog_plot.update_figure(new_fig)
        else:
          ui.notify("Scan finished or stopped, no complete data set.", type="warning")

    except Exception as e:
      print(f"ERROR DURING LIVE SCAN: {e}")
      ui.notify(f"Error during scan: {e}", type="negative")


#SPECTROMETER CONTROL============================================================================================================================


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

global_scan_data = []

