import matplotlib.pyplot as plt
import spectra_lib as sp
simulation = True


sp_device = sp.Ocean_Optics(simulation = simulation)
sp_device.set_integration_time(100000)

x = sp_device.get_wavelength()
y = sp_device.get_intensities()

# ==============================
fig, ax = plt.subplots()
fig.tight_layout()
ax.set_xlabel('Wavelengths (nm)')
ax.set_ylabel('Intensity')
plt.plot(x,y)
plt.show()
# ==============================

sp_device.close()