#!/usr/bin/env python3

from rtmidi import MidiOut
import threading
import time
import os

IS_WINDOWS = True if os.name == 'nt' else False

json_instrument_map = 'instruments-map.sc8850.json'


class InstrumentLibrary:
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
                pc -= 1
                instruments.append(Instrument(name, cc, pc))
    def groups(self):
        return list(self.instruments.keys())

class Instrument:
    def __init__(self, name: str, cc:int, pc:int):
        self.name = name
        self.cc = cc
        self.pc = pc
        self.ch = 0
    def __repr__(self):
        return f'{self.name} cc={self.cc} pc={self.pc}'

def midi_cmd(midi_command:int, channel:int):
    result = (midi_command << 4) | channel
    return result

def play_a_note(midi_out: MidiOut, instrument: Instrument):
    note_on = midi_cmd(0x9, instrument.ch) 
    note_off = midi_cmd(0x8, instrument.ch)
    midi_out.send_message([note_on, 60, 80])
    time.sleep(0.5)
    midi_out.send_message([note_off, 60, 0])
    time.sleep(0.1)

def set_instrument(midi_out: MidiOut, instrument: Instrument):
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
        self.columns = 12
    
    def init_resize_listener(self):
        if IS_WINDOWS:
            return
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
        instrstr = str(self.current_instrument)
        header = instrstr + term.center( term.move_left(len(instrstr)) + term.bold(self.current_group.upper()))
        header = term.black_on_orange(header)
        print(term.move_xy(0,0) + header)

    def render_grid(self):
        term = self.term
        instruments = self.library.instruments[self.current_group]
        current_instrument = self.current_instrument
        instr_idx = 0
        cell_width = max(4, term.width // self.columns)
        margin = 3
        for x in range(0, term.width, cell_width):
            for y in range(self.header_size, term.height - 1):
                instrument = instruments[instr_idx]
                instr_str = instrument.name
                if len(instr_str) < cell_width - margin:
                    instr_str += ((cell_width - margin) - len(instr_str)) * ' '
                if len(instr_str) > cell_width - margin:
                    instr_str = instr_str[:cell_width - margin]
                line = '[' + instr_str + ']' + margin * ' '
                if instrument == current_instrument:
                    line = term.black_on_green('[' + instr_str + ']') + margin * ' '
                print(term.move_xy(x, y) + str(line))
                instr_idx += 1
                if instr_idx >= len(instruments):
                    return

    def render(self):
        print(term.home + term.clear)
        self.render_header()
        self.render_grid()



if __name__ == "__main__":
    import argparse
    import sys
    import os
    import os.path as path
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, help='the device id of the midi taret device')
    parser.add_argument('--listdevices', action='store_const', const=True, help='set a specific style to process')
    parser.add_argument('--pc', type=int, help='set a pc value')
    parser.add_argument('--cc', type=int, help='set a cc value')
    parser.add_argument('--columns', type=int, default=12, help='set the number of columns. Default is 12')
    args = parser.parse_args()
    if args.listdevices:
        list_mididevices()
        sys.exit(0)
    midi_device_index = 0
    if args.device != None:
        midi_device_index = args.device
    midi_out = get_midi_out(midi_device_index)
    if args.pc != None or args.cc != None:
        pc = args.pc if args.pc != None else 0
        cc = args.cc if args.pc != None else 0
        set_instrument(midi_out, Instrument("", cc, pc))
        sys.exit(0)
    json_path = json_instrument_map
    root_path = os.path.dirname(os.path.abspath(__file__ ))
    json_path = path.join(root_path, json_path)
    library = InstrumentLibrary(json_path)
    view = SelectionView(library)
    view.columns = args.columns
    term = view.term
    set_instrument(midi_out, view.current_instrument)
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
            # why I have to send it twice?
            # (dosen't work otherwise, the right instrument is always one step behind then)
            instr = view.current_instrument
            if view.current_group == "drums":
                instr.ch = 9
            set_instrument(midi_out, instr)
            set_instrument(midi_out, instr)
