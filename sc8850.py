#!/usr/bin/env python3

import rtmidi
import time

class Instrument(object):
    def __init__(self, cc:int, pc:int):
        self.cc = cc
        self.pc = pc
        self.ch = 0

def midi_cmd(midi_command:int, channel:int):
    result = (midi_command << 4) | channel
    return result

def play_a_note(midi_out:rtmidi.MidiOut, instrument: Instrument):
    note_on = midi_cmd(0x9, instrument.ch) 
    note_off = midi_cmd(0x8, instrument.ch)
    midi_out.send_message([note_on, 60, 80])
    time.sleep(0.5)
    midi_out.send_message([note_off, 60, 0])
    time.sleep(0.1)

def set_instrument(midi_out:rtmidi.MidiOut, instrument: Instrument):
    cc = midi_cmd(0xB, instrument.ch)
    pc = midi_cmd(0xC, instrument.ch)
    midi_out.send_message([pc, instrument.pc])
    midi_out.send_message([cc, 0, instrument.cc])


def list_mididevices():
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    for idx, port in enumerate(ports):
        print(f'{idx}: {port}')

def get_midi_out(device_index: int):
    midiout = rtmidi.MidiOut()
    midiout.open_port(device_index)
    return midiout

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, help='the device id of the midi taret device')
    parser.add_argument('--listdevices', action='store_const', const=True, help='set a specific style to process')
    parser.add_argument('--pc', type=int, help='set a pc value')
    parser.add_argument('--cc', type=int, help='set a cc value')
    args = parser.parse_args()
    if args.listdevices:
        list_mididevices()
    midi_device_index = 0
    if args.device != None:
        midi_device_index = args.device
    cc = 0
    pc = 0
    if args.pc != None:
        pc = args.pc
    if args.cc != None:
        cc = args.cc
    instrument = Instrument(cc, pc)
    midi_out = get_midi_out(midi_device_index)
    set_instrument(midi_out, instrument)
        