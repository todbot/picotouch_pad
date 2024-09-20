import time
import board
import touchio
import rainbowio
import usb_midi
import neopixel
import tmidi

print("Hello World!")

midi_chan = 1
midi_velocity = 100
midi_base_note = 60

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

leds = neopixel.NeoPixel(leds_pin, num_leds, brightness=0.2, auto_write=False)

touch_ins = []  # maybe don't need debouncer
for pin in touch_pins:
    touchin = touchio.TouchIn(pin)
    touchin.threshold += touch_threshold_adjust
    print("pin:", pin)
    touch_ins.append(touchin)
num_pads = len(touch_ins)


### startup demo
for i in range(num_leds):
    for j in range(num_leds):
        leds[j] = rainbowio.colorwheel( j*(255/num_leds) + time.monotonic()*50)
    leds[i] = 0xffffff
    leds.show()
    i = (i+1) % num_leds
    time.sleep(0.05)

## go to bootloader test
#if True:
if touch_ins[0].raw_value > 1200:  # hold down "1" key
    import microcontroller
    print("Booting up in bootloader mode in 5 secs")
    do_abort = False
    for i in range(5,0,-1):
        if touch_ins[0].raw_value < 1000:
            print("  aborted")
            do_abort = True
            break
        print(i, end="...")
        leds.fill((30*i, 30*i, 30*i))
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
print("starting code")

def midi_receive():
     if msg := midi_usb.receive():
         print("hi", msg)
    
last_time = 0
dim_by = 5
touch_state = [ False ] * num_pads

while True:
    leds[:] = [[max(i-dim_by,0) for i in l] for l in leds] # dim LEDs by (dim_by,dim_by,dim_by)
    leds.show()
    
    for i,t in enumerate(touch_ins):
        tval = t.value
        traw = t.raw_value
        
        if tval and not touch_state[i]:  # press event
            print(time.monotonic(), i, "press", traw)
            if i < num_leds:  # num pad
                leds[i] = rainbowio.colorwheel(time.monotonic()*150)
                notenum = midi_base_note + i
                msg_on = tmidi.Message(tmidi.NOTE_ON, midi_chan - 1, notenum, midi_velocity)
                midi_usb.send(msg_on)
            else:
                leds[i-num_leds] = 0xffffff
        elif not t.value and touch_state[i]:  # release event
            print(time.monotonic(), i, "release", traw)
            if i < num_leds:  # num pad
                notenum = midi_base_note + i
                msg_off = tmidi.Message(tmidi.NOTE_OFF, midi_chan - 1, notenum, midi_velocity)
                midi_usb.send(msg_off)

        touch_state[i] = tval

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
    
