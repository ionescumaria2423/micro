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
# from Thorlabs.MotionControl.GenericPiezoCLI.Piezo.IGenericPiezo import *
# ========================================================================================

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

        # Ensure that the device settings have been initialized
        if not CH_X.IsSettingsInitialized():
            CH_X.WaitForSettingsInitialized(1000)  # 1 second timeout
            assert CH_X.IsSettingsInitialized() is True
        if not CH_Y.IsSettingsInitialized():
            CH_Y.WaitForSettingsInitialized(1000)  # 1 second timeout
            assert CH_Y.IsSettingsInitialized() is True
        if not CH_Z.IsSettingsInitialized():
            CH_Z.WaitForSettingsInitialized(1000)  # 1 second timeout
            assert CH_Z.IsSettingsInitialized() is True

        CH_X.StartPolling(250)  # 250ms polling rate
        CH_Y.StartPolling(250)  # 250ms polling rate
        CH_Z.StartPolling(250)  # 250ms polling rate

        time.sleep(1)
        CH_X.EnableDevice()
        CH_Y.EnableDevice()
        CH_Z.EnableDevice()
        time.sleep(0.25)  # Wait for device to enable


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

        print(CH_X_config)
        print(CH_X_settings)
        return CH_X,CH_Y,CH_Z, stepper_device

    except Exception as e:
        print('Error handler!')
        #   this can be bad practice: It sometimes obscures the error source

        print(e)
# ========================================================================================



# ========================================================================================
def init_BPC(serial_Piezo):
    piezo_device = BenchtopPiezo.CreateBenchtopPiezo(serial_Piezo)
    piezo_device.Connect(serial_Piezo)
    PiezoCH_X = piezo_device.GetChannel(1)
    PiezoCH_Y = piezo_device.GetChannel(2)
    PiezoCH_Z = piezo_device.GetChannel(3)

    # Ensure that the device settings have been initialized
    if not PiezoCH_X.IsSettingsInitialized():
        PiezoCH_X.WaitForSettingsInitialized(1000)  # 1 second timeout
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

    PiezoCH_X.StartPolling(250)  # 250ms polling rate
    PiezoCH_Y.StartPolling(250)  # 250ms polling rate
    PiezoCH_Z.StartPolling(250)  # 250ms polling rate

    time.sleep(1)
    PiezoCH_X.EnableDevice()
    PiezoCH_Y.EnableDevice()
    PiezoCH_Z.EnableDevice()
    time.sleep(0.25)  # Wait for device to enable
    # print(PiezoCH_X.LoadPiezoConfiguration(PiezoCH_X.DeviceID))
    #
    # PiezoCH_X_config = PiezoCH_X.LoadMotorConfiguration(CH_X.DeviceID)
    # PiezoCH_X_settings = PiezoCH_X.MotorDeviceSettings



    return PiezoCH_X,PiezoCH_Y,PiezoCH_Z, piezo_device

    # except Exception as e:
    #     print('Error handler!')
    #     #   this can be bad practice: It sometimes obscures the error source
    #     print(e)

# ========================================================================================

# def setPiezoFeedbackPI(PiezoCH_X,PiezoCH_Y,PiezoCH_Z):
#     FeedbackLoopConstants = PiezoCH_X.GetFeedbackLoopPIconsts()
#     FeedbackLoopConstants.ProportionalTerm = 30  # max 255
#     FeedbackLoopConstants.IntegralTerm = 20  # max 255
#     PiezoCH_X.SetFeedbackLoopPIconsts(FeedbackLoopConstants)
#
#     FeedbackLoopConstants = PiezoCH_Y.GetFeedbackLoopPIconsts()
#     FeedbackLoopConstants.ProportionalTerm = 30  # max 255
#     FeedbackLoopConstants.IntegralTerm = 20  # max 255
#     PiezoCH_Y.SetFeedbackLoopPIconsts(FeedbackLoopConstants)
#
#     FeedbackLoopConstants = PiezoCH_Z.GetFeedbackLoopPIconsts()
#     FeedbackLoopConstants.ProportionalTerm = 30  # max 255
#     FeedbackLoopConstants.IntegralTerm = 20  # max 255
#     PiezoCH_Z.SetFeedbackLoopPIconsts(FeedbackLoopConstants)
#


# ========================================================================================
# def getState_BSC(CH_X,CH_Y,CH_Z):
#     print('==================')
#     print('Channels:\t\t{}\t{}\t{}'.format(    CH_X.DeviceID,        CH_Y.DeviceID,        CH_Z.DeviceID))
#     print('State:\t\t\t{}\t\t{}\t\t{}'.format( CH_X.State,           CH_Y.State,           CH_Z.State))
#     print('IsHomed :\t\t{}\t\t{}\t\t{}'.format(CH_X.Status.IsHomed,  CH_Y.Status.IsHomed,  CH_Z.Status.IsHomed))
#     print('IsMoving:\t\t{}\t\t{}\t\t{}'.format(CH_X.Status.IsMoving, CH_Y.Status.IsMoving, CH_Z.Status.IsMoving))
#     print('Position:\t\t{}\t\t\t{}\t\t\t{}'.format(CH_X.Status.Position, CH_Y.Status.Position, CH_Z.Status.Position))
#     print('MaxVel.[mm/s]:\t{:}\t\t\t{:}\t\t\t{:}'.format(CH_X.GetVelocityParams().MaxVelocity,
#                                                 CH_Y.GetVelocityParams().MaxVelocity,
#                                                 CH_Z.GetVelocityParams().MaxVelocity))
#     print(
#         'Acc.[mm/s2]:\t{:}\t\t\t{:}\t\t\t{:}'.format(CH_X.GetVelocityParams().Acceleration,
#                                            CH_Y.GetVelocityParams().Acceleration,
#                                            CH_Z.GetVelocityParams().Acceleration))
#     print(
#         'JogStep[mm]:\t{:}\t\t{:}\t\t{:}'.format(CH_X.GetJogStepSize(),
#                                                 CH_Y.GetJogStepSize(),
#                                                 CH_Z.GetJogStepSize()))
#     print(
#         'Backlash[um]:\t{:}\t\t{:}\t\t{:}'.format(CH_X.GetBacklash(),
#                                                 CH_Y.GetBacklash(),
#                                                 CH_Z.GetBacklash()))
#
#     print('==================\n')
# ========================================================================================
#
#
# ========================================================================================
# def getState_BPC(PiezoCH_X,PiezoCH_Y,PiezoCH_Z):
#     print('==================')
#     print('Channels:\t\t{}\t{}\t{}'.format(    PiezoCH_X.DeviceID,   PiezoCH_Y.DeviceID,   PiezoCH_Z.DeviceID))
#
#
#
#     PiezoCH_X.RequestMaxOutputVoltage()
#     PiezoCH_Y.RequestMaxOutputVoltage()
#     PiezoCH_Z.RequestMaxOutputVoltage()
#     print('MaxVoltage[V]:\t{:}\t\t\t{:}\t\t\t{:}'.format(PiezoCH_X.GetMaxOutputVoltage(),
#                                                  PiezoCH_Y.GetMaxOutputVoltage(),
#                                                  PiezoCH_Z.GetMaxOutputVoltage()))
#     PiezoCH_X.RequestMaxTravel()
#     PiezoCH_Y.RequestMaxTravel()
#     PiezoCH_Z.RequestMaxTravel()
#     print('MaxTravel[um]:\t{:}\t\t\t{:}\t\t\t{:}'.format(PiezoCH_X.GetMaxTravel(),
#                                                  PiezoCH_Y.GetMaxTravel(),
#                                                  PiezoCH_Z.GetMaxTravel()))
#     print('JogStep[um]:\t{:}\t\t\t{:}\t\t\t{:}'.format(PiezoCH_X.GetJogSteps().PositionStepSize,
#                                                  PiezoCH_Y.GetJogSteps().PositionStepSize,
#                                                  PiezoCH_Z.GetJogSteps().PositionStepSize))
#
#     print('IsClosedLoop:\t{:}\t\t{:}\t\t{:}'.format(PiezoCH_X.IsClosedLoop(),
#                                                  PiezoCH_Y.IsClosedLoop(),
#                                                  PiezoCH_Z.IsClosedLoop()))
#
#     PiezoCH_X.RequestStatus()
#     PiezoCH_Y.RequestStatus()
#     PiezoCH_Z.RequestStatus()
#     time.sleep(0.1)
#     print('IsZeroed:\t\t{}\t\t{}\t\t{}'.format(PiezoCH_X.Status.IsZeroed,
#                                                  PiezoCH_Y.Status.IsZeroed,
#                                                  PiezoCH_Z.Status.IsZeroed))
#
#
#     print('Feedback.P:\t\t{:}\t\t\t{:}\t\t\t{:}'.format(PiezoCH_X.GetFeedbackLoopPIconsts().ProportionalTerm,
#                                                     PiezoCH_Y.GetFeedbackLoopPIconsts().ProportionalTerm,
#                                                     PiezoCH_Z.GetFeedbackLoopPIconsts().ProportionalTerm))
#
#     print('Feedback.I:\t\t{:}\t\t\t{:}\t\t\t{:}'.format(PiezoCH_X.GetFeedbackLoopPIconsts().IntegralTerm,
#                                                     PiezoCH_Y.GetFeedbackLoopPIconsts().IntegralTerm,
#                                                     PiezoCH_Z.GetFeedbackLoopPIconsts().IntegralTerm))
#
#     PiezoCH_X.RequestVoltage()
#     PiezoCH_Y.RequestVoltage()
#     PiezoCH_Z.RequestVoltage()
#     time.sleep(0.1)
#     print('Voltage[V]:\t\t{:6.3f}\t\t{:6.3f}\t\t{:6.3f}'.format(float(str(PiezoCH_X.GetOutputVoltage())),
#                                                    float(str(PiezoCH_Y.GetOutputVoltage())),
#                                                    float(str(PiezoCH_Z.GetOutputVoltage()))))
#
#     PiezoCH_X.RequestPosition()
#     PiezoCH_Y.RequestPosition()
#     PiezoCH_Z.RequestPosition()
#     time.sleep(0.1)
#     print('Position[um]:\t{:6.3f}\t\t{:6.3f}\t\t{:6.3f}'.format(float(str(PiezoCH_X.GetPosition())),
#                                                     float(str(PiezoCH_Y.GetPosition())),
#                                                     float(str(PiezoCH_Z.GetPosition()))))
#
#     print('==================\n')
# ========================================================================================
def main():
    SimulationManager.Instance.InitializeSimulations()
    DeviceManagerCLI.BuildDeviceList()
    print(DeviceManagerCLI.GetDeviceList())

    CH_X, CH_Y, CH_Z, stepper_device = init_BSC(serial_Stepper)

    print(CH_X.DeviceID)
    print(CH_Y.DeviceID)
    print(CH_Z.DeviceID)
    # Uncomment this line if you are using
    # SimulationManager.Instance.InitializeSimulations()
    # timeout = 60000
    # DeviceManagerCLI.BuildDeviceList()
    # print(DeviceManagerCLI.GetDeviceList())
    #
  #  ==================
    # create and init BSC device
    # serial_Stepper = "70809127"
    # CH_X, CH_Y, CH_Z , stepper_device = init_BSC(serial_Stepper)     # init BSC device
    # getState_BSC(CH_X, CH_Y, CH_Z)                    # Get parameters related to homing/zeroing/other
    # ==================
    #
    # ==================
    # serial_Piezo = "71809070"
    # PiezoCH_X, PiezoCH_Y, PiezoCH_Z, piezo_device = init_BPC(serial_Piezo)  # init BPC device
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)  # Get parameters related to zeroing/other
    # ==================
    #
    #
    #
    # Home or Zero the device (if a motor/piezo)
    # print("Homing Motor X")
    # CH_X.Home(timeout)
    # print("Homing Motor Y")
    # CH_Y.Home(timeout)
    # print("Homing Motor Z")
    # CH_Z.Home(timeout)
    # print("Done")
    #
    # Move the device to a new position
    # dist = Decimal(0.50)
    # print("Moving ... ")
    # print("Moving n times")
    # for i in range(1):
    #     CH_X.SetMoveRelativeDistance(dist)
    #     CH_X.MoveRelative(2000)
    #     time.sleep(0.5)
    #     CH_X.SetMoveRelativeDistance(-dist)
    #     CH_X.MoveRelative(2000)
    #     time.sleep(0.5)
    # print("Done")
    # print(CH_X.GetPosition())
    # status = device.Status
    # print(status.Position)
    # time.sleep(0.5)

    #
    #
    # print('Limits:',CH_X.LimitData())
    # print(CH_X.Status.Velocity)
    #
    #
    # print('Move To..')
    # velocity = Decimal(0.5)
    # acceleration = Decimal(1.5)
    # CH_X.SetVelocityParams(velocity, acceleration)
    # CH_X.MoveTo(Decimal(1.2), timeout)
    # while CH_X.Status.IsMoving:
    #     print(CH_X.Status.Position)
    #
    # getState_BSC(CH_X, CH_Y, CH_Z)
    #
    #
    #
    # ===================================================================
    #
    # test Piezo ==================
    # print('======= Test Piezo ========\n')
    #
    #
    # test SetZero ===========
    # print('Test SetZero - CloseLoop')
    # PiezoCH_X.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # PiezoCH_Y.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # PiezoCH_Z.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # time.sleep(1)
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)
    # PiezoCH_X.SetZero()
    # PiezoCH_Y.SetZero()
    # PiezoCH_Z.SetZero()
    # time.sleep(3)
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)
    #
    # print('Test SetZeroOutput - OpenLoop')
    # PiezoCH_X.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
    # PiezoCH_Y.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
    # PiezoCH_Z.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
    # PiezoCH_X.SetZeroOutput()
    # PiezoCH_Y.SetZeroOutput()
    # PiezoCH_Z.SetZeroOutput()
    # time.sleep(1)
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)
    # time.sleep(1)
    #
    #
    #
    #
    #
    # test OutputVoltage ===========
    # print('Test SetOutputVoltage - OpenLoop')
    # PiezoCH_X.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
    # PiezoCH_Y.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
    # PiezoCH_Z.SetPositionControlMode(PiezoControlModeTypes.OpenLoop)
    #
    # PiezoCH_X.SetOutputVoltage(Decimal(10))
    # PiezoCH_Y.SetOutputVoltage(Decimal(5))
    # PiezoCH_Z.SetOutputVoltage(Decimal(15))
    # time.sleep(1)
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)
    #
    #
    #
    #
    # test SetPosition ===========
    # print('Test SetPosition - CloseLoop')
    # PiezoCH_X.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # PiezoCH_Y.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # PiezoCH_Z.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    #
    # PiezoCH_X.SetPosition(Decimal(4))
    # PiezoCH_Y.SetPosition(Decimal(4))
    # PiezoCH_Z.SetPosition(Decimal(8))
    # time.sleep(1)
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)
    #
    #
    #
    # test Jog ===========
    # print('Test Jog')
    # PiezoCH_X.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # PiezoCH_Y.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # PiezoCH_Z.SetPositionControlMode(PiezoControlModeTypes.CloseLoop)
    # jogParam = PiezoCH_X.GetJogSteps()
    # jogParam.PositionStepSize = Decimal(2)
    # PiezoCH_X.SetJogSteps(jogParam)
    # print(jogParam.VoltageStepSize)
    #
    # step = Decimal(2)
    # dir = ControlSettings.PiezoJogDirection.Increase
    #
    # PiezoCH_X.Jog(step, dir)
    #
    #
    #
    #
    # PiezoCH_X.Jog(jogParam.PositionStepSize)
    # PiezoCH_X.Jog(ThorlabsGenericPiezoCLI.Piezo.Settings.ControlSettings.PiezoJogDirection.Increase)
    # PiezoCH_X.Jog(ThorlabsGenericPiezoCLI.PiezoJogDirection.Increase)
    #
    #
    # time.sleep(1)
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)
    #
    #
    #
    #
    # test LUT ===========
    # print('Test LUT')
    # LUTwaveParams = LUTWaveParameters()
    # LUTwaveParams.Mode = LUTWaveParameters.PiezoOutputLUTModes.Continuous
    # LUTwaveParams.CycleLength = 8
    # LUTwaveParams.LUTValDelay = 500
    # LUTwaveParam.SetLUTwaveParams(LUTwaveParams)
    # LUTwaveParams.SetLUTwaveSample(0, 3.9)
    # LUTwaveParams.SetLUTwaveSample(1, 3.8)
    # LUTwaveParams.SetLUTwaveSample(2, 3.5)
    # LUTwaveParams.SetLUTwaveSample(3, 3.1)
    # LUTwaveParams.SetLUTwaveSample(4, 2.2)
    # LUTwaveParams.SetLUTwaveSample(5, 2.5)
    # LUTwaveParams.SetLUTwaveSample(6, 2.9)
    # LUTwaveParams.SetLUTwaveSample(7, 3.8)
    #
    # PiezoCH_X.LUTWaveParameters.StartLUTwave()
    # PiezoCH_X.LUTWaveParameters.StopLUTwave()
    # PiezoCH_X.SetZeroOutput()
    # END test Piezo ==================
    #
    # time.sleep(1)
    # getState_BPC(PiezoCH_X, PiezoCH_Y, PiezoCH_Z)
    #
    #
    #
    # status = device.Status
    # print(status.Position)
    #
    # PiezoCH_X.PersistSettings()
    #
    #
    #
    # Stop Polling and Disconnect
    # CH_X.StopPolling()
    # CH_Y.StopPolling()
    # CH_Z.StopPolling()
    # PiezoCH_X.StopPolling()
    # PiezoCH_Y.StopPolling()
    # PiezoCH_Z.StopPolling()
    #
    # stepper_device.Disconnect()
    # piezo_device.Disconnect()
#
# except Exception as e:
#     print('Error handler!')
#     this can be bad practice: It sometimes obscures the error source
#     print(e)

# Uncomment this line if you are using Simulations
# SimulationManager.Instance.UninitializeSimulations()
# ...
#
#
# if __name__ == "__main__":
#      main()
if __name__ == '__main__':
    main()