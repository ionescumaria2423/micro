import base64
import cv2
import numpy as np
from nicegui import ui
from pylablib.devices import uc480

# ---------------- UI ----------------
ui.label('Control').classes('text-h4')

with ui.row():

    with ui.card():
        ui.label("Camera")
        camera_image = ui.interactive_image().style("width:640px;height:480px;")

    with ui.column():

        with ui.row():
            ui.button("↑")

        with ui.row():
            ui.button("←")
            ui.button("HOME ALL")
            ui.button("→")

        with ui.row():
            ui.button("↓")

        ui.button("Z +")
        ui.button("Z -")

cam = None

def get_camera():
    global cam
    if cam is None:
        cam = uc480.UC480Camera()
    return cam

def update_camera():
    global cam

    try:
        cam = get_camera()
        frame = cam.snap()

        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
        frame = frame.astype(np.uint8)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

        _, jpg = cv2.imencode('.jpg', frame)
        encoded = base64.b64encode(jpg).decode("utf-8")

        camera_image.set_source(f"data:image/jpeg;base64,{encoded}")

    except Exception as e:
        print("Camera error:", e)


        try:
            cam.close()
        except:
            pass

        cam = None


ui.timer(0.05, update_camera)

ui.run()