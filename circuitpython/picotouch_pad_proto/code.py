# picotouch_pad_proto code.py -- demo for picotouch_pad_proto
# 1 Sep 2024 - @todbot / Tod Kurt
# Part of https://github.com/todbot/picotouch_pad

import time
import board
import touchio
import rainbowio
import usb_midi
import neopixel
import tmidi
from adafruit_debouncer import Debouncer

print("picotouch_pad_proto!")

midi_chan = 1
midi_velocity = 100
midi_octave = 5

num_leds = 16
touch_threshold_adjust = 30  # or 300

midi_usb = tmidi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])

leds_pin = board.GP28
#led_pin = board.GP25
touch_pins = (board.GP15, board.GP14, board.GP13, board.GP12,
              board.GP11, board.GP10, board.GP9, board.GP8,
              board.GP7, board.GP6, board.GP5, board.GP4,
              board.GP3, board.GP2, board.GP1, board.GP0,
              #
              board.GP16, board.GP17, board.GP18, board.GP19,
              board.GP20,  board.GP21, board.GP22)
PAD_SELECT = 16
PAD_B_UP = 17
PAD_B_DOWN = 18
PAD_C_RIGHT = 19
PAD_C_LEFT = 21
PAD_A_DOWN = 20
PAD_A_UP = 22


leds = neopixel.NeoPixel(leds_pin, num_leds, brightness=0.2, auto_write=False)

touch_ins = []  # maybe don't need debouncer
touches = [] 
for pin in touch_pins:
    touchin = touchio.TouchIn(pin)
    touchin.threshold += touch_threshold_adjust
    touch = Debouncer(touchin, interval=0.001)
    print("pin:", pin)
    touch_ins.append(touchin)
    touches.append(touch)
num_pads = len(touch_ins)


### startup demo
for i in range(num_leds):
    for j in range(num_leds):
        leds[j] = rainbowio.colorwheel( j*(255/num_leds) + time.monotonic()*50)
    leds[i] = 0xffffff
    leds.show()
    i = (i+1) % num_leds
    time.sleep(0.03)

## go to bootloader test
#if True:
if touch_ins[0].raw_value > 1200:  # hold down "1" key
    import microcontroller
    print("Booting up in bootloader mode in 3 secs")
    do_abort = False
    for i in range(3,0,-1):
        if touch_ins[0].raw_value < 1000:
            print("  aborted")
            do_abort = True
            break
        print(i, end="...")
        leds.fill((30*i, 0, 0))
        leds.show()
        time.sleep(1)
    leds.fill(0)
    leds.show()
    if not do_abort:
        print("\n going into bootloader...")
        microcontroller.on_next_reset(microcontroller.RunMode.UF2)
    else:
        print("aborted going into bootloader")
    microcontroller.reset()
    
########

print("picotouch_pad_proto: started")

    
last_time = 0
dim_by = 5
touch_state = [ False ] * num_pads  # our simple debouncer
pressed_notes = [ 0 ] * num_leds  # FIXME: should be 'num_note_pads' or similar
select_held = False

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


while True:
    midi_receive()
    
    if select_held:
        leds.fill(0x330033)
    leds[:] = [[max(i-dim_by,0) for i in l] for l in leds] # dim LEDs by (dim_by,dim_by,dim_by)
    leds.show()
    
    #for i,t in enumerate(touches):
    #    t.update()
    for i,t in enumerate(touch_ins):
        tval = t.value
        traw = t.raw_value
        pressed = tval and not touch_state[i]  # press event
        released = not tval and touch_state[i]  # release event
        touch_state[i] = tval
        #if t.rose:
        if pressed:
            print(time.monotonic(), i, "press", traw)
            if i < num_leds:  # num pad
                leds[i] = rainbowio.colorwheel(time.monotonic()*150)
                notenum = midi_octave*12 + i
                pressed_notes[i] = notenum
                msg_on = tmidi.Message(tmidi.NOTE_ON, midi_chan - 1, notenum, midi_velocity)
                midi_usb.send(msg_on)
            elif i == PAD_SELECT:
                select_held = True
            elif i == PAD_B_UP:   # pitch bend
                print("pitch up!")
                leds.fill(0x000055)
                leds.show()
                msg_pb_up = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, 8191)
                #msg_pb_up.pitch_bend = 8191
                midi_usb.send(msg_pb_up)
            elif i == PAD_B_DOWN:  # pitch bend
                print("pitch down!")
                leds.fill(0x000055)
                leds.show()
                msg_pb_dn = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, -8191)
                #msg_pb_dn.pitch_bend = -8191
                midi_usb.send(msg_pb_dn)
            elif i == PAD_A_UP:  # mod wheel
                leds.fill(0x005555)
                leds.show()
                midi_usb.send(tmidi.Message(tmidi.CC, midi_chan-1, 1, 127))
            elif i == PAD_A_DOWN: # mod wheel
                leds.fill(0x005555)
                leds.show()
                midi_usb.send(tmidi.Message(tmidi.CC, midi_chan-1, 1, 0))
            elif i == PAD_C_LEFT: # octave down
                midi_octave = max(midi_octave-1, 0)
                leds.fill(0x550000)
            elif i == PAD_C_RIGHT: # octove up
                midi_octave = min(midi_octave+1, 8)
                leds.fill(0x550000)
        #if t.fell:
        if released:
            print(time.monotonic(), i, "release", traw)
            if i < num_leds:  # num pad
                notenum = pressed_notes[i]
                msg_off = tmidi.Message(tmidi.NOTE_OFF, midi_chan - 1, notenum, midi_velocity)
                midi_usb.send(msg_off)
            elif i == PAD_SELECT:
                select_held = False
            elif i == PAD_B_DOWN:
                msg_pb_dn = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, 0)
                midi_usb.send(msg_pb_dn)
            elif i == PAD_B_UP:
                msg_pb_up = tmidi.Message(tmidi.PITCH_BEND, midi_chan-1, 0)
                midi_usb.send(msg_pb_up)
                
            else:
                pass


########################

i = 0
last_time = 0
while True:
    for j in range(num_leds):
        leds[j] = rainbowio.colorwheel( j*(255/num_leds) + time.monotonic()*50)
        
    leds[i] = 0xffffff
    leds.show()
    
    if time.monotonic() - last_time > 0.2:
        last_time = time.monotonic()
        i = (i+1) % num_leds
    time.sleep(0.01)
    
