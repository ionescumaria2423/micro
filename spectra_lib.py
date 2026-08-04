from io import BytesIO
import os
import sys
import clr
import matplotlib.pyplot as plt
import numpy as np

# ==========================================================
# OmniDriver Setup
# ==========================================================

DLL_PATH = (
    r"C:\Program Files\Ocean Optics\OmniDriver\OOI_HOME\NETOmniDriver-NET40.dll"
)

if not os.path.exists(DLL_PATH):
  raise FileNotFoundError(DLL_PATH)

DLL_DIR = os.path.dirname(DLL_PATH)

if DLL_DIR not in sys.path:
  sys.path.insert(0, DLL_DIR)

if hasattr(os, "add_dll_directory"):
  os.add_dll_directory(DLL_DIR)

clr.AddReference(DLL_PATH)

from OmniDriver import NETWrapper


# ==========================================================
# Ocean Optics Spectrometer
# ==========================================================


class OceanOptics:

  def __init__(self, simulation=False):
    self.simulation = simulation
    self.wrapper = None
    self.spec_index = 0

    if simulation:
      print("[SIMULATION] Spectrometer simulation enabled.")
      return

    print("Initializing Ocean Optics spectrometer...")
    self.wrapper = NETWrapper()

    try:
      self.wrapper.closeAllSpectrometers()
    except:
      pass

    count = self.wrapper.openAllSpectrometers()

    try:
      count = self.wrapper.getNumberOfSpectrometersFound()
    except:
      pass

    if count <= 0:
      raise RuntimeError("No Ocean Optics spectrometer detected.")

    self.model = self.wrapper.getName(0)
    self.serial = self.wrapper.getSerialNumber(0)

    print("Driver: NatUSBWin_64")
    print(f"Detected {count} spectrometer(s)")
    print(f"Model : {self.model}")
    print(f"Serial: {self.serial}")

  def set_integration_time(self, integration_time):
    if self.simulation:
      return
    self.wrapper.setIntegrationTime(self.spec_index, int(integration_time))

  def get_wavelengths(self):
    if self.simulation:
      return np.linspace(350, 1000, 1024)
    return np.asarray(
        self.wrapper.getWavelengths(self.spec_index), dtype=float
    )

  def get_intensities(self):
    if self.simulation:
      x = np.linspace(350, 1000, 1024)
      return 2000 * np.exp(-((x - 650) / 25) ** 2) + np.random.normal(
          0, 10, len(x)
      )
    return np.asarray(self.wrapper.getSpectrum(self.spec_index), dtype=float)

  def close(self):
    if self.simulation:
      return
    try:
      self.wrapper.closeAllSpectrometers()
    except:
      pass


# ==========================================================
# Plot Class
# ==========================================================


class SpectrometerPlot:

  def __init__(self, spectrometer):
    self.sp = spectrometer
    self.wavelengths = self.sp.get_wavelengths()
    self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
    self.line, = self.ax.plot(
        self.wavelengths,
        np.zeros_like(self.wavelengths),
        color="blue",
        linewidth=0.8,
    )
    self.ax.set_xlabel("Wavelength (nm)")
    self.ax.set_ylabel("Intensity")
    self.ax.grid(True)
    self.fig.tight_layout()

  def update(self):
    y = self.sp.get_intensities()
    self.line.set_ydata(y)
    self.ax.set_xlim(self.wavelengths.min(), self.wavelengths.max())
    ymin, ymax = np.min(y), np.max(y)
    if ymin == ymax:
      ymax += 1
    self.ax.set_ylim(ymin, ymax)
    self.fig.canvas.draw()

  def get_png(self):
    self.update()
    buffer = BytesIO()
    self.fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
    buffer.seek(0)
    return buffer.read()

  def show(self):
    plt.show()

  def close(self):
    plt.close(self.fig)


# ==========================================================
# Singleton instances
# ==========================================================

_device = None
_plot = None


def get_spectrometer(simulation=False):
  global _device
  if _device is None:
    _device = OceanOptics(simulation)
    _device.set_integration_time(10000)
  return _device


def get_plot(simulation=False):
  global _plot
  if _plot is None:
    _plot = SpectrometerPlot(get_spectrometer(simulation))
  return _plot


def close():
  global _device, _plot
  if _plot is not None:
    _plot.close()
    _plot = None
  if _device is not None:
    _device.close()
    _device = None