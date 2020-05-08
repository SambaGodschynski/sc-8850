#!/usr/bin/env python3

import rtmidi
from rtmidi import MidiOut

json_instrument_map = 'instruments-map.sc8850.json'

class InstrumentLibrary(object):
    def __init__(self, jsonfile: str):
        import json
        jsObj = None
        self.instruments = {}
        with open(jsonfile) as f:
            jsObj = json.load(f)
        for group in jsObj:
            instruments = []
            self.instruments[group] = instruments
            for instrument in jsObj[group]:
                name = list(instrument.keys())[0]
                cc = instrument[name]['cc']
                pc = instrument[name]['pc']
                instruments.append(Instrument(name, cc, pc))
    def groups(self):
        return list(self.instruments.keys())

class Instrument(object):
    def __init__(self, name: str, cc:int, pc:int):
        self.name = name
        self.cc = cc
        self.pc = pc
        self.ch = 0
    def __repr__(self):
        return self.name

def midi_cmd(midi_command:int, channel:int):
    result = (midi_command << 4) | channel
    return result

def play_a_note(midi_out:MidiOut, instrument: Instrument):
    import time
    note_on = midi_cmd(0x9, instrument.ch) 
    note_off = midi_cmd(0x8, instrument.ch)
    midi_out.send_message([note_on, 60, 80])
    time.sleep(0.5)
    midi_out.send_message([note_off, 60, 0])
    time.sleep(0.1)

def set_instrument(midi_out:MidiOut, instrument: Instrument):
    cc = midi_cmd(0xB, instrument.ch)
    pc = midi_cmd(0xC, instrument.ch)
    midi_out.send_message([pc, instrument.pc])
    midi_out.send_message([cc, 0, instrument.cc])


def list_mididevices():
    midiout = MidiOut()
    ports = midiout.get_ports()
    for idx, port in enumerate(ports):
        print(f'{idx}: {port}')

def get_midi_out(device_index: int):
    midiout = MidiOut()
    midiout.open_port(device_index)
    return midiout

class SelectionView(object):
    def __init__(self, library: InstrumentLibrary):
        from blessed import Terminal
        self.term = Terminal()
        self.library = library
        self.current_group_idx = 0
        self.current_instrument_idx = 0
        self.header_size = 1
        self.init_resize_listener()
        self.selected_insrtument = self.current_instrument
    
    def init_resize_listener(self):
        import signal
        signal.signal(signal.SIGWINCH, lambda sig, action: self.render())

    @property
    def current_group(self):
        return self.library.groups()[self.current_group_idx]
    
    @property
    def current_instruments(self):
        return self.library.instruments[self.current_group]

    @property
    def current_instrument(self):
        return self.current_instruments[self.current_instrument_idx]

    def set_next_group(self):
        self.current_group_idx +=1
        self.current_instrument_idx = 0
        if self.current_group_idx >= len(self.library.groups()):
            self.current_group_idx = 0

    def set_prev_group(self):
        self.current_group_idx -=1
        self.current_instrument_idx = 0
        if self.current_group_idx < 0:
            self.current_group_idx = len(self.library.groups()) - 1

    def set_next_instrument(self):
        self.current_instrument_idx +=1
        if self.current_instrument_idx >= len(self.current_instruments):
            self.current_instrument_idx = 0     

    def set_prev_instrument(self):
        self.current_instrument_idx -=1
        if self.current_instrument_idx < 0:
            self.current_instrument_idx = len(self.current_instruments) - 1               

    def render_header(self):
        term = self.term
        header = term.center(term.bold(f'{self.current_group.upper()}'))
        header = term.black_on_orange(header)
        print(term.move_xy(0,0) + header)

    def render_grid(self):
        term = self.term
        instruments = self.library.instruments[self.current_group]
        current_instrument = self.current_instrument
        instr_idx = 0
        cell_width = 12
        for x in range(0, term.width, cell_width):
            for y in range(self.header_size, term.height-1):
                instrument = instruments[instr_idx]
                instr_str = '[' + str(instrument)[:cell_width-4] + '..] '
                if instrument == current_instrument:
                    instr_str = term.white_on_green(instr_str)
                print(term.move_xy(x, y) + str(instr_str))
                instr_idx += 1
                if instr_idx >= len(instruments):
                    return

    def render(self):
        print(term.home + term.clear)
        self.render_header()
        self.render_grid()



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

    library = InstrumentLibrary(json_instrument_map)
    instrument = Instrument("", cc, pc)
    midi_out = get_midi_out(midi_device_index)
    set_instrument(midi_out, instrument)

    view = SelectionView(library)
    term = view.term
    while True:
        view.render()
        with term.cbreak(), term.hidden_cursor():
            inp = term.inkey()
            if inp == 'q':
                print(term.clear)
                break
            if inp == 'd':
                view.set_next_group()
            if inp == 'a':
                view.set_prev_group()
            if inp == 's':
                view.set_next_instrument()
            if inp == 'w':
                view.set_prev_instrument()                
    