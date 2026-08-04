import ctypes
import os
import sys
import numpy as np

# ====================================================================================
# Ocean Insight OmniDriver Paths Configuration
# ====================================================================================
FOLDER_OOI = r"C:\Program Files\Ocean Optics\OmniDriver\OOI_HOME"
PATH_DLL = os.path.join(FOLDER_OOI, "NETOmniDriver-NET40.dll")

# Load required native dependencies (C++ binaries, WinUSB drivers, Java Runtime)
if os.path.exists(FOLDER_OOI):
    critical_paths = [
        FOLDER_OOI,
        os.path.join(FOLDER_OOI, "bin"),
        os.path.join(FOLDER_OOI, "jre", "bin"),
        os.path.join(FOLDER_OOI, "jre", "bin", "server"),
    ]

    for p in critical_paths:
        if os.path.exists(p):
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(p)
                except Exception:
                    pass

    # Force Windows DLL loader to look inside OOI_HOME
    try:
        ctypes.windll.kernel32.SetDllDirectoryW(FOLDER_OOI)
    except Exception:
        pass

    # Pre-load jvm.dll into process memory to prevent 0x80004005 exception in C++ wrapper
    jvm_path = os.path.join(FOLDER_OOI, "jre", "bin", "server", "jvm.dll")
    if os.path.exists(jvm_path):
        try:
            ctypes.CDLL(jvm_path)
        except Exception:
            pass


class OceanOptics:
    """Wrapper class for Ocean Insight spectrometers using OmniDriver .NET library."""

    def __init__(self, simulation: bool = False):
        self.simulation = simulation
        self.wrapper = None
        self.spec_index = 0

        if self.simulation:
            print("[INFO] Simulation mode explicitly enabled.")
            return

        if not os.path.exists(PATH_DLL):
            print(f"[ERROR] DLL not found at: {PATH_DLL}")
            print("[INFO] Falling back to Simulation mode.")
            self.simulation = True
            return

        current_dir = os.getcwd()

        try:
            os.chdir(FOLDER_OOI)
            import clr

            clr.AddReference(PATH_DLL)
            from OmniDriver import NETWrapper

            print("Initializing Ocean Insight OmniDriver engine...")
            self.wrapper = NETWrapper()

            print("Scanning USB ports for spectrometers...")
            spectrometer_count = self.wrapper.openAllSpectrometers()

            if spectrometer_count > 0:
                self.spec_index = 0
                model_name = self.wrapper.getName(self.spec_index)
                serial_num = self.wrapper.getSerialNumber(self.spec_index)
                print(f"[CONNECTED] {model_name} (S/N: {serial_num})")
            else:
                print(
                    "[WARNING] No spectrometer detected on USB. Falling back to Simulation mode."
                )
                self.simulation = True

        except Exception as e:
            print(f"[ERROR] Failed to initialize hardware driver: {e}")
            print("[INFO] Falling back to Simulation mode.")
            self.simulation = True
            self.wrapper = None

        finally:
            os.chdir(current_dir)

    def set_integration_time(self, microseconds: int = 50000) -> None:
        """Sets the integration time in microseconds."""
        if self.simulation or self.wrapper is None:
            print(f"[SIMULATION] Integration time set to {microseconds} µs")
        else:
            self.wrapper.setIntegrationTime(self.spec_index, microseconds)

    def get_wavelengths(self) -> list:
        """Returns the array of wavelengths for the connected spectrometer."""
        if self.simulation or self.wrapper is None:
            return list(np.linspace(200, 800, 100))
        else:
            return list(self.wrapper.getWavelengths(self.spec_index))

    def get_intensities(self) -> list:
        """Acquires a spectrum and returns the array of intensities."""
        if self.simulation or self.wrapper is None:
            x = np.linspace(200, 800, 100)
            return list(np.exp(-((500 - x) ** 2) / 1000))
        else:
            return list(self.wrapper.getSpectrum(self.spec_index))

    def close(self) -> None:
        """Closes connection to all spectrometers."""
        if self.simulation or self.wrapper is None:
            print("[SIMULATION] Connection closed.")
        else:
            try:
                self.wrapper.closeAllSpectrometers()
                print("Spectrometer connection closed successfully.")
            except Exception as e:
                print(f"Error while closing connection: {e}")


# ====================================================================================
# Test / Usage Example
# ====================================================================================
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Set simulation=False to connect to real hardware
    sp_device = OceanOptics(simulation=False)

    sp_device.set_integration_time(100000)
    wavelengths = sp_device.get_wavelengths()
    intensities = sp_device.get_intensities()

    # Plot acquired spectrum
    fig, ax = plt.subplots()
    ax.plot(wavelengths, intensities, label="Spectrum")
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Intensity (counts)")
    ax.set_title("Ocean Insight Spectrometer Measurement")
    ax.grid(True)
    plt.show()

    sp_device.close()