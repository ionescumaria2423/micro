import time
import pythonnet
import clr

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericPiezoCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.Benchtop.PiezoCLI.dll")


from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import *
from Thorlabs.MotionControl.GenericPiezoCLI import *
from Thorlabs.MotionControl.Benchtop.PiezoCLI import *
from System import Decimal
from Thorlabs.MotionControl.GenericPiezoCLI.Piezo import *
from Thorlabs.MotionControl.GenericPiezoCLI.Settings import *
from Thorlabs.MotionControl.GenericPiezoCLI.ControlParameters import *


serial_Stepper = "70809127"
serial_Piezo = "71809070"

def init_BSC(serial_Stepper):
    try:

        stepper_device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial_Stepper)
        stepper_device.Connect(serial_Stepper)
        time.sleep(0.25)

        CH_X = stepper_device.GetChannel(1)
        CH_Y = stepper_device.GetChannel(2)
        CH_Z = stepper_device.GetChannel(3)


        if not CH_X.IsSettingsInitialized():
            CH_X.WaitForSettingsInitialized(1000)
            assert CH_X.IsSettingsInitialized() is True
        if not CH_Y.IsSettingsInitialized():
            CH_Y.WaitForSettingsInitialized(1000)
            assert CH_Y.IsSettingsInitialized() is True
        if not CH_Z.IsSettingsInitialized():
            CH_Z.WaitForSettingsInitialized(1000)
            assert CH_Z.IsSettingsInitialized() is True

        CH_X.StartPolling(250)
        CH_Y.StartPolling(250)
        CH_Z.StartPolling(250)

        time.sleep(1)
        CH_X.EnableDevice()
        CH_Y.EnableDevice()
        CH_Z.EnableDevice()
        time.sleep(0.25)


        device_info = CH_X.GetDeviceInfo()
        print('Stepper Device:', device_info.Description)

        CH_X_config = CH_X.LoadMotorConfiguration(CH_X.DeviceID)
        CH_X_settings = CH_X.MotorDeviceSettings
        CH_X.GetSettings(CH_X_settings)
        CH_X_config.DeviceSettingsName = 'NanoMax 300 X'
        CH_X_config.UpdateCurrentConfiguration()
        CH_X.SetSettings(CH_X_settings, True, False)

        CH_Y_config = CH_Y.LoadMotorConfiguration(CH_Y.DeviceID)
        CH_Y_settings = CH_Y.MotorDeviceSettings
        CH_Y.GetSettings(CH_Y_settings)
        CH_Y_config.DeviceSettingsName = 'NanoMax 300 Y'
        CH_Y_config.UpdateCurrentConfiguration()
        CH_Y.SetSettings(CH_Y_settings, True, False)

        CH_Z_config = CH_Z.LoadMotorConfiguration(CH_Z.DeviceID)
        CH_Z_settings = CH_Z.MotorDeviceSettings
        CH_Z.GetSettings(CH_Z_settings)
        CH_Z_config.DeviceSettingsName = 'NanoMax 300 Z'
        CH_Z_config.UpdateCurrentConfiguration()
        CH_Z.SetSettings(CH_Z_settings, True, False)

        print('homing stepper')

        CH_X.Home(60000)
        CH_Y.Home(60000)
        CH_Z.Home(60000)

        print('homing stepper done')

        print(CH_X_config)
        print(CH_X_settings)


        return CH_X,CH_Y,CH_Z, stepper_device

    except Exception as e:
        print('Error handler!')
        print(e)




def init_BPC(serial_Piezo):
    piezo_device = BenchtopPiezo.CreateBenchtopPiezo(serial_Piezo)
    piezo_device.Connect(serial_Piezo)
    PiezoCH_X = piezo_device.GetChannel(1)
    PiezoCH_Y = piezo_device.GetChannel(2)
    PiezoCH_Z = piezo_device.GetChannel(3)


    if not PiezoCH_X.IsSettingsInitialized():
        PiezoCH_X.WaitForSettingsInitialized(1000)
        assert PiezoCH_X.IsSettingsInitialized() is True

    if not PiezoCH_Y.IsSettingsInitialized():
        PiezoCH_Y.WaitForSettingsInitialized(1000)  # 1 second timeout
        assert PiezoCH_Y.IsSettingsInitialized() is True
    if not PiezoCH_Z.IsSettingsInitialized():
        PiezoCH_Z.WaitForSettingsInitialized(1000)  # 1 second timeout
        assert PiezoCH_Z.IsSettingsInitialized() is True

    PiezoCH_X_config = PiezoCH_X.GetPiezoConfiguration(PiezoCH_X.DeviceID)
    currentDeviceSettings = PiezoCH_X.PiezoDeviceSettings
    PiezoCH_X_config.UpdateCurrentConfiguration()

    PiezoCH_Y_config = PiezoCH_Y.GetPiezoConfiguration(PiezoCH_Y.DeviceID)
    currentDeviceSettings = PiezoCH_Y.PiezoDeviceSettings
    PiezoCH_Y_config.UpdateCurrentConfiguration()

    PiezoCH_Z_config = PiezoCH_Z.GetPiezoConfiguration(PiezoCH_Z.DeviceID)
    currentDeviceSettings = PiezoCH_Z.PiezoDeviceSettings
    PiezoCH_Z_config.UpdateCurrentConfiguration()

    ctrlSetX = PiezoCH_X.PiezoDeviceSettings.Control.PositionStepSize
    propertyListX = PiezoCH_X.PiezoDeviceSettings.Control
    print(propertyListX)

    Piezo_info = PiezoCH_X.GetDeviceInfo()
    print('Piezo Device:', Piezo_info.Description)

    PiezoCH_X.StartPolling(250)
    PiezoCH_Y.StartPolling(250)
    PiezoCH_Z.StartPolling(250)

    time.sleep(1)
    PiezoCH_X.EnableDevice()
    PiezoCH_Y.EnableDevice()
    PiezoCH_Z.EnableDevice()
    time.sleep(0.25)

    def home_piezo_all():
        channels = [PiezoCH_X, PiezoCH_Y, PiezoCH_Z]

        state = {
            'pzt_x_val': 0.0, 'pzt_y_val': 0.0, 'pzt_z_val': 0.0
        }

        for ch in channels:
            if ch is not None:
                try:
                    # 1. Drive output voltage back to 0V
                    ch.SetOutputVoltage(Decimal(0.0))

                    # 2. Re-calibrate position strain gauge zero point (if supported)
                    if hasattr(ch, 'Zero'):
                        ch.Zero()

                except Exception as e:
                    print(f"Error homing piezo channel: {e}")

        print('homing piezo')

        state['pzt_x_val'] = 0.0
        state['pzt_y_val'] = 0.0
        state['pzt_z_val'] = 0.0
        print('homing piezo done')

    home_piezo_all()


    return PiezoCH_X,PiezoCH_Y,PiezoCH_Z, piezo_device