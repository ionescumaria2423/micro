import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import spectra_lib as sp

simulation = False
integr_time = 10000

sp_device = sp.OceanOptics(simulation=simulation)
sp_device.set_integration_time(integr_time)

wavelengths = sp_device.get_wavelengths()


class AnimateSpectro:

    def __init__(self, ax):
        self.ax = ax
        self.line, = ax.plot([], [], lw=0.5)

    def __call__(self, frame):

        y = sp_device.get_intensities()

        self.line.set_data(wavelengths, y)

        self.ax.set_xlim(wavelengths.min(), wavelengths.max())
        self.ax.set_ylim(y.min(), y.max())

        return self.line,


fig, ax = plt.subplots()

ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel("Intensity")
ax.grid(True)

ani = FuncAnimation(
    fig,
    AnimateSpectro(ax),
    interval=100,
    blit=True
)

plt.show()

sp_device.close()