import time
import rainbowio

from hardware import Hardware, Pads
import tmidi

hw = Hardware()

midi_chan = 1
midi_velocity = 100
midi_octave = 3


def midi_receive():
    while msg := midi_usb.receive():
        print("hi", msg)
        if msg.type == tmidi.NOTE_ON:
            notei = msg.note - midi_octave*12
            if notei > 0 and notei < num_leds:
                leds[notei] = rainbowio.colorwheel(time.monotonic()*150)
                pressed_notes[notei] = msg.note
        elif msg.type == tmidi.NOTE_OFF:
            notei = msg.note - midi_octave*12
            if notei > 0 and notei < num_leds:
                #pressed_notes[notei] = msg.note
                pass



hw.startup_demo()

# fixme:
mod_speed_ms = 10
mod_inc_default = 2
mod_inc = 0
mod_val = 0
mod_last_ms = 0


last_debug_time = 0
dim_by = 5
touch_state = [ False ] * hw.num_pads  # our simple debouncer
pressed_notes = [ 0 ] * hw.num_leds  # FIXME: should be 'num_note_pads' or similar
select_held = False

while True:
    if select_held:
        hw.leds.fill(0x330033)
    hw.leds[:] = [[max(i-dim_by,0) for i in l] for l in hw.leds] # dim LEDs by (dim_by,dim_by,dim_by)
    hw.leds.show()

    #for i,t in enumerate(touches):
    #    t.update()
    for i,t in enumerate(hw.touch_ins):
        tval = t.value
        traw = t.raw_value
        pressed = tval and not touch_state[i]  # press event
        released = not tval and touch_state[i]  # release event
        touch_state[i] = tval
        #if t.rose:
        if pressed:
            print(time.monotonic(), i, "press", traw)
            if i < hw.num_leds:  # num pad
                hw.leds[i] = rainbowio.colorwheel(time.monotonic()*150)
                notenum = midi_octave*12 + i
                pressed_notes[i] = notenum
                msg_on = tmidi.Message(tmidi.NOTE_ON, midi_chan - 1, notenum, midi_velocity)
                hw.midi_usb.send(msg_on)
            elif i == Pads.PAD_SELECT:
                select_held = True
            elif i == Pads.PAD_B_UP:   # pitch bend
                print("pitch up!")
                hw.leds.fill(0x000055)
                msg_pb_up = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, 8191)
                #msg_pb_up.pitch_bend = 8191
                hw.midi_usb.send(msg_pb_up)
            elif i == Pads.PAD_B_DOWN:  # pitch bend
                print("pitch down!")
                hw.leds.fill(0x000055)
                msg_pb_dn = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, -8191)
                #msg_pb_dn.pitch_bend = -8191
                hw.midi_usb.send(msg_pb_dn)
            elif i == Pads.PAD_A_UP:  # mod wheel
                print("mod up!")
                mod_inc = mod_inc_default
            elif i == Pads.PAD_A_DOWN: # mod wheel
                print("mod down!")
                mod_inc = -mod_inc_default
            elif i == Pads.PAD_C_LEFT: # octave down
                midi_octave = max(midi_octave-1, 0)
                hw.leds.fill(0x550000)
            elif i == Pads.PAD_C_RIGHT: # octove up
                midi_octave = min(midi_octave+1, 8)
                hw.leds.fill(0x550000)
        #if t.fell:
        if released:
            print(time.monotonic(), i, "release", traw)
            if i < hw.num_leds:  # num pad
                notenum = pressed_notes[i]
                msg_off = tmidi.Message(tmidi.NOTE_OFF, midi_chan - 1, notenum, midi_velocity)
                hw.midi_usb.send(msg_off)
            elif i == Pads.PAD_SELECT:
                select_held = False
            elif i == Pads.PAD_A_UP:  # mod wheel
                mod_inc = 0
            elif i == Pads.PAD_A_DOWN:  # mod wheel
                mod_inc = 0
            elif i == Pads.PAD_B_DOWN:
                msg_pb_dn = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, 0)
                hw.midi_usb.send(msg_pb_dn)
            elif i == Pads.PAD_B_UP:
                msg_pb_up = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, 0)
                hw.midi_usb.send(msg_pb_up)
                
            else:
                pass
    
