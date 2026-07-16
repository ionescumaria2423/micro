import numpy as np
import os

# ====================================================================================
# Specificăm folderul de bază unde se află DLL-urile OceanOptics
folder_ooi = r"C:\Program Files\Ocean Optics\OmniDriver\OOI_HOME"
cale_dll = os.path.join(folder_ooi, "NETOmniDriver-NET40.dll")
# ====================================================================================



class Ocean_Optics():
    def __init__(self, simulation = False):
        if simulation:
            print(f"Simulare Spectrometru")
            self.simulation = simulation

        else:
            self.simulation = simulation
            if not os.path.exists(cale_dll):
                print(f"Eroare: Nu am găsit fișierul DLL la calea: {cale_dll}")
            else:
                print("Configurez mediul și încarc biblioteca oficială Ocean Insight...")

                # Pregateste folder pentru NETWrapper
                director_curent = os.getcwd()   # Memoreaza folderul curent
                os.chdir(folder_ooi)            # Schimba in folderul Ocean Optics
                os.environ['PATH'] = folder_ooi + os.pathsep + os.environ.get('PATH', '') # Adauga în PATH

                import clr

                clr.AddReference(cale_dll)
                import OmniDriver

                try:
                    self.wrapper = OmniDriver.NETWrapper()
                    print("Motorul OmniDriver a fost inițializat cu succes!")
                    os.chdir(director_curent)

                    print("Scanat porturi USB pentru spectrometre...")
                    numar_spectrometre = self.wrapper.openAllSpectrometers()
                    print(f"Spectrometre găsite și deschise: {numar_spectrometre}")

                    if numar_spectrometre > 0:
                        self.index_spec = 0
                        nume_model = self.wrapper.getName(self.index_spec)
                        serial = self.wrapper.getSerialNumber(self.index_spec)
                        print(f"\n[CONECTAT CU SUCCES] -> {nume_model} (S/N: {serial})")

                    else:
                        print("\n[EROARE] Aparatul hardware nu a fost detectat pe USB. Verificați conexiunea fizică.")

                except Exception as e:
                    print(f"\nA apărut o eroare la inițializare: {e}")
                    # În caz de eroare ne asigurăm că punem folderul înapoi cum a fost
                    os.chdir(director_curent)


# ==========================================================
    def set_integration_time(self, microsec = 50000):
        if self.simulation:
           print(f"Intergation time = {microsec}")
        else:
            self.wrapper.setIntegrationTime(self.index_spec, microsec)

# ==========================================================
    def get_wavelength(self):
        if self.simulation:
            self.wavelengths = np.linspace(200,800,100)
        else:
            self.wavelengths = list(self.wrapper.getWavelengths(self.index_spec))
        return self.wavelengths

# ==========================================================
    def get_intensities(self):
        if self.simulation:
           self.intensities = np.exp( -(500 - np.linspace(200,800,100))**2/500*2)
        else:
            self.intensities = list(self.wrapper.getSpectrum(self.index_spec))
        return self.intensities

# ==========================================================

    def close(self):
        if self.simulation:
            print("Bye!")
        else:
            self.wrapper.closeAllSpectrometers()
            print("Connection closed!")
# ==========================================================


# ==========================================================
if __name__ == "__main__":
    sp_device = Ocean_Optics(simulation=True)
    sp_device.set_integration_time(100000)
    x = sp_device.get_wavelength()
    y = sp_device.get_intensities()

    import matplotlib.pyplot as plt

    # ==============================
    fig, ax = plt.subplots()
    fig.tight_layout()
    ax.set_xlabel('Wavelengths (nm)')
    ax.set_ylabel('Intensity')
    plt.plot(x, y)
    plt.show()
    # ==============================

    sp_device.close()
