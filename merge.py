import time

import pip
import pythonnet
import clr
import keyboard

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

from init import *
from interface import *

def main():
    SimulationManager.Instance.InitializeSimulations()
    DeviceManagerCLI.BuildDeviceList()
    print(DeviceManagerCLI.GetDeviceList())

    CH_X, CH_Y, CH_Z, stepper_device = init_BSC(serial_Stepper)

    # print(CH_X.DeviceID)
    # print(CH_Y.DeviceID)
    # print(CH_Z.DeviceID)
    stepSize = Decimal(0.05)
    timeout = 30000

    while True:
        try:
            if keyboard.is_pressed('esc'):
                print('esc')
                break

            elif keyboard.is_pressed('right'):
                CH_X.MoveRelative(MotorDirection.Forward, stepSize, timeout)
                time.sleep(0.2)

            elif keyboard.is_pressed('left'):
                CH_X.MoveRelative(MotorDirection.Backward, stepSize, timeout)
                time.sleep(0.2)

            elif keyboard.is_pressed('up'):
                CH_Y.MoveRelative(MotorDirection.Forward, stepSize, timeout)
                time.sleep(0.2)

            elif keyboard.is_pressed('down'):
                CH_Y.MoveRelative(MotorDirection.Backward, stepSize, timeout)
                time.sleep(0.2)

            elif keyboard.is_pressed('w'):
                CH_Z.MoveRelative(MotorDirection.Forward, stepSize, timeout)
                time.sleep(0.2)

            elif keyboard.is_pressed('s'):
                CH_Z.MoveRelative(MotorDirection.Backward, stepSize, timeout)
                time.sleep(0.2)

            time.sleep(0.01)

        except Exception as e:
            print(f"error: {e}")
            break


if __name__ == '__main__':
    main()