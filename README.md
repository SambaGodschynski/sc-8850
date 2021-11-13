# SC-8850 Instruments browser
This is a console based instruments browser for the Roland SC-8850.

# Dependencies
* python-rtmidi
* blessed

# How to use

## list all your midi devices
`python sc8850-browser.py --listdevices`
This will list all your connected MIDI devices: `[DEVICE_INDEX]: [DEVICENAME]`

## installation
`pip install .`

## run the browser
`python -m sc8850-browser --device=[DEVICE_INDEX]`

You can naviagte via `WASD` keys.

Press `shift+d` for next instrument group. Press `shift+a` for previous instument group.

Navigate the instruments with `wasd`.