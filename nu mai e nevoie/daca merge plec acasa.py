import time
import clr

# -----------------------------
# 1. PATH TO KINESIS DLLs
# -----------------------------
KINESIS_PATH = r"C:\Program Files\Thorlabs\Kinesis"

clr.AddReference(KINESIS_PATH + r"\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference(KINESIS_PATH + r"\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference(KINESIS_PATH + r"\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor


# -----------------------------
# 2. CONFIG
# -----------------------------
SERIAL = "70809127"


# -----------------------------
# 3. DEVICE DISCOVERY
# -----------------------------
DeviceManagerCLI.BuildDeviceList()
time.sleep(1.0)

devices = DeviceManagerCLI.GetDeviceList()
count = DeviceManagerCLI.GetDeviceListSize()

print("Device count:", count)
print("Devices:", list(devices))

if count == 0:
    raise Exception(
        "No devices found. "
        "Simulator is not running OR device is not STARTED in Kinesis."
    )


# -----------------------------
# 4. CONNECT DEVICE
# -----------------------------
def connect_stepper(serial):
    print(f"Connecting to: {serial}")

    stepper = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)

    stepper.Connect(serial)
    time.sleep(0.5)

    if not stepper.IsConnected:
        raise Exception("Device failed to connect (not ready in simulator).")

    print("Stepper connected successfully")

    # Basic safe setup
    stepper.StartPolling(200)
    time.sleep(1.0)

    return stepper


# -----------------------------
# 5. MAIN
# -----------------------------
def main():
    stepper = connect_stepper(SERIAL)

    info = stepper.GetDeviceInfo()
    print("Device:", info.Description)
    print("Device ID:", stepper.DeviceID)


if __name__ == "__main__":
    main()