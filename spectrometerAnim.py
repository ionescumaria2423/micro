import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import spectra_lib as sp


simulation = True
integr_time = 10000

# ========================================
class AnimateSpectro:
    global wavelengths
    def __init__(self, ax):
        self.line, = ax.plot([], [], 'b-', linewidth=0.5)
        self.x = wavelengths
        self.ax = ax
        self.ax.grid(True)
        #self.ax.legend([nume_model +', S/N: '+ serial])

    def __call__(self, i):
        # This way the plot can continuously run and we just keep
        # watching new realizations of the process
        if i == 0:
            self.line.set_data([], [])
            return self.line,

        # self.x = sp_device.get_wavelength()
        y = sp_device.get_intensities()
        self.line.set_data(self.x, y)
        # Set up plot parameters
        self.ax.set_xlim(min(self.x), max(self.x))
        self.ax.set_ylim(min(y), max(y))

        return self.line,


# ===============================================================================
# main
# ===============================================================================
sp_device = sp.Ocean_Optics(simulation = simulation)
sp_device.set_integration_time(integr_time)
wavelengths = sp_device.get_wavelength()

# ===========================================
fig, ax = plt.subplots()
fig.tight_layout()
ax.set_xlabel('Wavelengths (nm)')
ax.set_ylabel('Intensity')
# ===========================================

ud = AnimateSpectro(ax)

# ===========================================
print("Achiziționez spectru în timp real...")
anim = FuncAnimation(fig, ud, frames=100, interval=100, blit=True)
plt.show()


# ===========================================
sp_device.close()