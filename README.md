# Oaxis myFirst Sketchpad Bluetooth Tablet Driver
This program aims to enable the use of the Oaxis myFirst Sketchpad (or just Sketchpad) as a wireless drawing tablet. This behaviour is already implemented by Oaxis in their propietary application for their 'drawing mode', but since they have not implemented this amazing feature for desktop users, I tried my hand at reverse-engineering this feature.  
Disclaimer: This project was purely educational. I gain nothing but convenience from this.  

## Background
I first discovered that the Sketchpad could act as a drawing tablet a year ago when I plugged it into my laptop to charge. Windows (and also Linux) automatically detected it as a drawing tablet. However, knowing that this was possible drove my desire to make it work over Bluetooth as well.  
  
The Sketchpad uses BLE to communicate with the phone, sending information such as pen position and battery level. The UUIDs for each BLE characteristic is in the source code under `MyFirstSketchbook.py`. The biggest hassle is that the information is somewhat obfuscated and has to be decrypted by a key found within the decompiled Android application code. For more information on the schema, look at the code (or open an issue and ask me to explain it...)  
  
I initially wanted to make it work on Windows, since all my notes are there, I was unable to get past the emotional barrier of installing Visual Studio and hence worked on this PoC instead, on Linux using Python. The BLE communication is done via the Bleak library, while input events are sent via evdev.  
  
As a workaround, I have implemented using the `mouse` library in Python to move the mouse, which will work like pen input except without pressure. If you're familiar enough with Windows APIs for input injection, feel free to port it over. 

## Installation
### Linux
Make sure you have the prerequisites for evdev installed. Refer to https://python-evdev.readthedocs.io/en/latest/install.html for more information.  
Afterwards, just create a new virtual environment and run:  
```pip install -r requirements.txt```  
### Windows
Since there's no evdev nonsense, just create a virtual environment and run:
```pip install -r requirements.txt```

## Usage
Use your preferred Bluetooth manager get the MAC Address of your Sketchbook. Alternatively, use the `discover.py` script provided. Do not connect to your Sketchbook as doing so will result in the code not working.  
Now, on Windows run:  
```python driver_win.py <MAC Address>```  
If you're on Linux, use sudo or run it as root.  
```sudo python driver_linux.py <MAC Address>```  
If all goes well, the code should automatically connect to your Sketchbook. If you see `"Ready!"` printed to your console without any errors, congratulations! The Sketchbook is ready to be used as a drawing tablet.  
If you see any output that looks like an array of hexadecimal digits, put it in issues. These are events from the tablet I have not encountered which could come to be useful.
To stop the code, just hit Ctrl+C.

### Minor Quirks
When the buttons are pressed, the Sketchpad, for whatever reason, will only report the button being pressed, but not released. What's worse is that upon the button being pressed, all pressure readings are set to zero, and the pen will report that it is hovering (even if it isn't). As such, a workaround is included for the Linux version as such:  
- If the button is pressed, assume the pen is down with a pressure of 10000
- If the pen is down and a pressure reading is detected, the button must have been released; release the button.  
This causes the quirk where pressing the bottom button (mapped to erase) will start erasing items even if the cursor is not down. There is probably a more elegant solution to this, but this trade-off feels the most natural and simple to me.  
In the Windows version, button functionality is not implemented.  