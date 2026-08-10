import asyncio
from nicegui import app, run, ui
import functions as fn
from init import *
stop_requested = False


def trigger_e_stop():
    global stop_requested
    stop_requested = True
    stop_hardware_immediately()


def stop_hardware_immediately():
    try:
        ch_x = getattr(fn, "CH_X", None)


        if ch_x is not None:
            ch_x.StopImmediate()

    except Exception as e:
        print("Error stopping hardware:", e)


def handle_keyboard_events(e):
    if e.action.keydown and e.key == " ":
        trigger_e_stop()


async def move_stage():
    try:
        ui.notify("Move started", type="info")
        # Run blocking .NET MoveTo call in a thread pool so NiceGUI event loop keeps running
        await run.io_bound(fn.CH_X.MoveTo, fn.Decimal(4.00), 0)
        ui.notify("Move complete", type="positive")
    except Exception as err:
        print("Move error:", err)


def check_stop_notify():
    global stop_requested
    if stop_requested:
        ui.notify("Emergency Stop Triggered!", type="negative")
        stop_requested = False


def build_gui():
    ui.keyboard(on_key=handle_keyboard_events)

    with ui.row():

        ui.button("go", on_click=move_stage)

        # Trigger emergency stop directly on click
        ui.button("STOP", on_click=trigger_e_stop).props("color=red")

        ui.button("HOME", on_click=lambda:fn.connect())


app.on_startup(fn.handle_startup)

build_gui()
ui.run()