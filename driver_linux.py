# With help from https://github.com/LinusCDE/rmTabletDriver/blob/master/tabletDriver.py

from evdev.uinput import UInput
from evdev.device import AbsInfo
from evdev import ecodes

from MyFirstSketchbook import Sketchbook
import asyncio
import time
import sys

if len(sys.argv) != 2: 
    print("Usage: sudo python driver.py <MAC Address of Sketchbook>")
    sys.exit()

TABLET_SIZE = (10751, 17380)
TABLET_ACTUAL_SIZE = (135, 220)
TABLET_MAX_PRESSURE = 41850

capabilities = {    
	ecodes.EV_KEY: [ecodes.BTN_TOOL_PEN, ecodes.BTN_TOUCH, ecodes.BTN_TOOL_RUBBER, ecodes.BTN_RIGHT],
	ecodes.EV_ABS: [
		(ecodes.ABS_PRESSURE, AbsInfo(value=0, min=0, max=TABLET_MAX_PRESSURE, fuzz=0, flat=0, resolution=0)),
		(ecodes.ABS_Y, AbsInfo(value=0, min=0, max=TABLET_SIZE[0], fuzz=0, flat=0, resolution=int(TABLET_SIZE[0]/TABLET_ACTUAL_SIZE[0]))),
		(ecodes.ABS_X, AbsInfo(value=0, min=0, max=TABLET_SIZE[1], fuzz=0, flat=0, resolution=int(TABLET_SIZE[1]/TABLET_ACTUAL_SIZE[1]))),
	]
}

global ui
ui = UInput(events=capabilities, name='myFirstSketchbook-Tablet', vendor=0x0123, product=0xfff0, phys='sketchbook-emulated-input')
print("Created device:", ui)

def uinput_peninfo_callback(pen_x, pen_y, pen_pressure):
    # print(pen_x, pen_y, pen_pressure)
    global ui
    ui.write(ecodes.EV_ABS, ecodes.ABS_X, TABLET_SIZE[1]-pen_y)
    ui.write(ecodes.EV_ABS, ecodes.ABS_Y, pen_x)
    ui.write(ecodes.EV_ABS, ecodes.ABS_PRESSURE, pen_pressure)
    ui.syn()

def uinput_penhover_callback():
    global ui
    uinput_pen_reset()
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_PEN, 1)
    ui.syn()

def uinput_pen_bottom_pressed_callback():
    global ui
    uinput_pen_reset()
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_RUBBER, 1)
    ui.syn()

def uinput_pen_upper_pressed_callback():
    global ui
    uinput_pen_reset()
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_PEN, 1)
    ui.syn()


def uinput_pen_reset():
    global ui
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_PEN, 0)
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOUCH, 0)
    ui.write(ecodes.EV_KEY, ecodes.BTN_TOOL_RUBBER, 0)
    ui.write(ecodes.EV_KEY, ecodes.BTN_RIGHT, 0)
    ui.syn()

async def async_main():
    device = await Sketchbook.create(sys.argv[1])
    await device.init_draw()
    device.set_pen_event_callback(uinput_peninfo_callback)
    device.set_pen_hover_callback(uinput_penhover_callback)
    device.set_pen_upper_button_pressed_callback(uinput_pen_upper_pressed_callback)
    device.set_pen_lower_button_pressed_callback(uinput_pen_bottom_pressed_callback)
    print("Ready!")

    loop = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(1)

try:
    asyncio.run(async_main())
except KeyboardInterrupt:
    print("Stopping!")
    ui.close()
