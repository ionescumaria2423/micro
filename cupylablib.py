from pylablib.devices import uc480

cam = uc480.UC480Camera()

print(cam.get_camera_id())

img = cam.snap()
print(img.shape)

cam.close()
