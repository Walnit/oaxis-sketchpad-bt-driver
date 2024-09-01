from bleak import BleakClient, BleakGATTCharacteristic
from enum import Enum
import asyncio

class PenStates(Enum):
    PEN_UP = 0
    PEN_HOVER = 1
    PEN_DOWN = 2

def parseHex(strArr):
    return int("".join(strArr[::-1]), 16)

class Sketchbook:
    KEYSET = ['o', '\"', chr(243), chr(137), 'w', 'Q', 'W', chr(232), 'y', chr(170), '9', 'L', chr(211), 'F', '2', chr(18), chr(17), '3', 'c', 'D']
    UUID_MAIN_SERVICE = "0000fff0-0000-1000-8000-00805f9b34fb"
    CHARACTERISTIC_EVENTS = "fff4"
    CHARACTERISTIC_COMMAND = "fff1"

    @classmethod
    async def create(cls, mac_address: str):
        # Initialize Sketchbook object
        self = cls()
        self.battery_level = -1
        self.draw_mode = False
        self.pen_x = 0
        self.pen_y = 0
        self.pen_pressure = 0
        self.pen_state = PenStates.PEN_UP
        self.pen_button_pressed = False
        self.callback_on_pen_change = None
        self.callback_on_tablet_delete = None
        self.callback_on_pen_up = None
        self.callback_on_pen_hover = None
        self.callback_on_pen_down = None
        self.callback_on_pen_upper_button_pressed = None
        self.callback_on_pen_lower_button_pressed = None

        # Connect to Sketchbook
        self.mac_address = mac_address
        self.client = BleakClient(self.mac_address)
        await self.client.connect()

        # Initialize BLE Characteristics
        self.main_service = self.client.services.get_service(self.UUID_MAIN_SERVICE)
        self.event_characteristic = self.main_service.get_characteristic(self.CHARACTERISTIC_EVENTS)
        self.command_characteristic = self.main_service.get_characteristic(self.CHARACTERISTIC_COMMAND)

        # Begin events callback
        await self.client.start_notify(self.event_characteristic, self.process_event)
        return self

    async def init_draw(self):
        # Makes Sketchbook start reporting pen coordinates
        await self.client.write_gatt_char(self.command_characteristic,  bytearray([ord(self.KEYSET[0])^6]))
        await asyncio.sleep(1)
        await self.client.write_gatt_char(self.command_characteristic,  bytearray([ord(self.KEYSET[0])^2]))
        
    async def close(self):
        await self.client.disconnect()

    async def process_event(self, sender: BleakGATTCharacteristic, data: bytearray):
        # Decrypt data
        strArr = [0 for i in range(len(data))]
        for i in range(len(strArr)):
            xor_result = (data[i] & 0xFF) ^ ord(self.KEYSET[i])
            strArr[i] = "{:02x}".format(xor_result)

        match strArr[0]:
            case '01':
                # Possible cases: Successfully set draw mode [01, 02]
                if strArr[1] == '02':
                    self.draw_mode = True
            case 'ac':
                # Possible cases: Battery report [ac, ac, <batt_lvl>]
                if strArr[1] == 'ac':
                    self.battery_level = int(strArr[2], 16)
            case '0e':
                # Possible cases: Pen detected [0e, 01]
                if strArr[1] == '01':
                    pass
            case 'ff':
                # Possible cases: Upper pen button [ff, ff, dd], Lower pen button [ff, ff, ee],
                # Tablet erase button [ff, ff, ff]
                if strArr[1] == 'ff' and strArr[2] == 'ff':
                    if self.callback_on_tablet_delete is not None: self.callback_on_tablet_delete()
                elif strArr[1] == 'ff' and strArr[2] == 'dd':
                    if self.callback_on_pen_upper_button_pressed is not None: 
                        self.pen_button_pressed = True
                        self.callback_on_pen_upper_button_pressed()
                elif strArr[1] == 'ff' and strArr[2] == 'ee':
                    if self.callback_on_pen_lower_button_pressed is not None: 
                        self.pen_button_pressed = True
                        self.callback_on_pen_lower_button_pressed()
                pass
            case '02':
                # Possible cases: Pen hovering [02, <counter>,
                # <pen_x1_byte2>, <pen_x1_byte1>, <pen_y1_byte2>, <pen_y1_byte1>, 
                # <pen_pressure1_byte2>, <pen_pressure1_byte1>,
                # <pen_x2_byte2>, <pen_x2_byte1>, <pen_y2_byte2>, <pen_y2_byte1>,
                # <pen_pressure2_byte2>, <pen_pressure2_byte1>,
                # <pen_x3_byte2>, <pen_x3_byte1>, <pen_y3_byte2>, <pen_y3_byte1>,
                # <pen_pressure3_byte2>, <pen_pressure3_byte1>]
                # Or pen button pressed

                if self.draw_mode:
                    # Update pen x, y, pressure using only last value
                    self.pen_x = parseHex(strArr[14:16])
                    self.pen_y = parseHex(strArr[16:18])
                    self.pen_pressure = parseHex(strArr[18:20])
                    self.update_pen_positions()
                    self.pen_hover()

            case 'e2':
                # Possible cases: Pen down [e2, <counter>,
                # <pen_x1_byte2>, <pen_x1_byte1>, <pen_y1_byte2>, <pen_y1_byte1>, 
                # <pen_pressure1_byte2>, <pen_pressure1_byte1>,
                # <pen_x2_byte2>, <pen_x2_byte1>, <pen_y2_byte2>, <pen_y2_byte1>,
                # <pen_pressure2_byte2>, <pen_pressure2_byte1>,
                # <pen_x3_byte2>, <pen_x3_byte1>, <pen_y3_byte2>, <pen_y3_byte1>,
                # <pen_pressure3_byte2>, <pen_pressure3_byte1>]

                if self.draw_mode:
                    # Update pen x, y, pressure using only last value
                    self.pen_x = parseHex(strArr[14:16])
                    self.pen_y = parseHex(strArr[16:18])
                    self.pen_pressure = parseHex(strArr[18:20])
                    if self.pen_pressure > 0: 
                        self.pen_button_pressed = False
                        self.pen_hover()
                    self.update_pen_positions()
                    self.pen_down()
            case '22':
                # Possible cases: End drawing, 2 positions [22, <counter>,
                # <pen_x1_byte2>, <pen_x1_byte1>, <pen_y1_byte2>, <pen_y1_byte1>, 
                # <pen_pressure1_byte2>, <pen_pressure1_byte1>,
                # <pen_x2_byte2>, <pen_x2_byte1>, <pen_y2_byte2>, <pen_y2_byte1>,
                # <pen_pressure2_byte2>, <pen_pressure2_byte1>]

                if self.draw_mode:
                    # Update pen x, y, pressure using only last value
                    self.pen_x = parseHex(strArr[8:10])
                    self.pen_y = parseHex(strArr[10:12])
                    self.pen_pressure = parseHex(strArr[12:14])
                    self.update_pen_positions()
                    self.pen_up()

            case '62':
                # Possible cases: End drawing, 1 position [22, <counter>,
                # <pen_x1_byte2>, <pen_x1_byte1>, <pen_y1_byte2>, <pen_y1_byte1>, 
                # <pen_pressure1_byte2>, <pen_pressure1_byte1>]

                if self.draw_mode:
                    # Update pen x, y, pressure using only last value
                    self.pen_x = parseHex(strArr[2:4])
                    self.pen_y = parseHex(strArr[4:6])
                    self.pen_pressure = parseHex(strArr[6:8])
                    self.update_pen_positions()
                    self.pen_up()
            case '82':
                # Possible cases: Pen release, two frames ago [82, <counter>,
                # <pen_x1_byte2>, <pen_x1_byte1>, <pen_y1_byte2>, <pen_y1_byte1>,
                # <pen_pressure1_byte2>, <pen_pressure1_byte1>,
                # <pen_x2_byte2>, <pen_x2_byte1>, <pen_y2_byte2>, <pen_y2_byte1>,
                # 00, 00,
                # <pen_x3_byte2>, <pen_x3_byte1>, <pen_y3_byte2>, <pen_y3_byte1>,
                # 00, 00]

                if self.draw_mode:
                    # Update pen x, y, pressure using only last value
                    self.pen_x = parseHex(strArr[14:16])
                    self.pen_y = parseHex(strArr[16:18])
                    self.pen_pressure = parseHex(strArr[18:20])
                    self.update_pen_positions()
                    self.pen_hover()

            case 'c2':
                # Possible cases: Pen release, one frame ago [c2, <counter>,
                # <pen_x1_byte2>, <pen_x1_byte1>, <pen_y1_byte2>, <pen_y1_byte1>,
                # <pen_pressure1_byte2>, <pen_pressure1_byte1>,
                # <pen_x2_byte2>, <pen_x2_byte1>, <pen_y2_byte2>, <pen_y2_byte1>,
                # <pen_pressure2_byte2>, <pen_pressure2_byte1>,
                # <pen_x3_byte2>, <pen_x3_byte1>, <pen_y3_byte2>, <pen_y3_byte1>,
                # 00, 00]

                if self.draw_mode:
                    # Update pen x, y, pressure using only last value
                    self.pen_x = parseHex(strArr[14:16])
                    self.pen_y = parseHex(strArr[16:18])
                    self.pen_pressure = parseHex(strArr[18:20])
                    self.update_pen_positions()
                    self.pen_hover()
            case _:
                print(strArr)
        


    def update_pen_positions(self):
        if self.pen_button_pressed: self.pen_pressure = 10000
        if self.callback_on_pen_change is not None:
            self.callback_on_pen_change(self.pen_x, self.pen_y, self.pen_pressure);
    def set_pen_event_callback(self, callback):
        self.callback_on_pen_change = callback
    def set_tablet_delete_callback(self, callback):
        self.callback_on_tablet_delete = callback
    def pen_up(self):
        if self.pen_state != PenStates.PEN_UP:
            self.pen_state = PenStates.PEN_UP
            self.pen_button_pressed = False
            if self.callback_on_pen_up is not None: self.callback_on_pen_up()
    def set_pen_up_callback(self, callback):
        self.callback_on_pen_up = callback
    def pen_hover(self):
        if self.pen_state != PenStates.PEN_HOVER:
            self.pen_state = PenStates.PEN_HOVER
            self.pen_button_pressed = False
            if self.callback_on_pen_hover is not None: self.callback_on_pen_hover()
    def set_pen_hover_callback(self, callback):
        self.callback_on_pen_hover = callback
    def pen_down(self):
        if self.pen_state != PenStates.PEN_DOWN:
            self.pen_state = PenStates.PEN_DOWN
            if self.callback_on_pen_down is not None: self.callback_on_pen_down()
    def set_pen_down_callback(self, callback):
        self.callback_on_pen_down = callback
    def set_pen_upper_button_pressed_callback(self, callback):
        self.callback_on_pen_upper_button_pressed = callback
    def set_pen_lower_button_pressed_callback(self, callback):
        self.callback_on_pen_lower_button_pressed = callback