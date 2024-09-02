import mouse

from MyFirstSketchbook import Sketchbook
import asyncio
import time
import sys

if len(sys.argv) != 2: 
    print("Usage: sudo python driver.py <MAC Address of Sketchbook>")
    sys.exit()

TABLET_SIZE = (10751, 17380)
TABLET_MAX_PRESSURE = 41850

TARGET_RESOLUTION = (1080, 1920)
RESOLUTION = (TARGET_RESOLUTION[0]/TABLET_SIZE[0], TARGET_RESOLUTION[1]/TABLET_SIZE[1])

def mouse_peninfo_callback(pen_x, pen_y, pen_pressure):
    mouse.move((TABLET_SIZE[1]-pen_y)*RESOLUTION[1], pen_x*RESOLUTION[0])
    if pen_pressure/TABLET_MAX_PRESSURE > 0.1: mouse.press(button='left')
    else: mouse.release(button='left')

def mouse_penhover_callback():
    pass

def mouse_pen_bottom_pressed_callback():
    pass

def mouse_pen_upper_pressed_callback():
    pass


def mouse_pen_reset():
    pass

async def async_main():
    device = await Sketchbook.create(sys.argv[1])
    await device.init_draw()
    device.set_pen_event_callback(mouse_peninfo_callback)
    device.set_pen_hover_callback(mouse_penhover_callback)
    device.set_pen_upper_button_pressed_callback(mouse_pen_upper_pressed_callback)
    device.set_pen_lower_button_pressed_callback(mouse_pen_bottom_pressed_callback)
    print("Ready!")

    loop = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(1)

try:
    asyncio.run(async_main())
except KeyboardInterrupt:
    print("Stopping!")
