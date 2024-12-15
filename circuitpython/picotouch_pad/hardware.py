import time
import board
import busio
import touchio
import usb_midi
import microcontroller
import rainbowio
import neopixel
import tmidi
from adafruit_debouncer import Debouncer

touch_threshold_adjust = 30  # or 300

num_leds = 19

leds_pin = board.GP27      # neopixel
uart_tx_pin = board.GP28   # midi out

touch_pins = (
    # grid pads
    board.GP15, board.GP14, board.GP13, board.GP12,
    board.GP11, board.GP10, board.GP9, board.GP8,
    board.GP7, board.GP6, board.GP5, board.GP4,
    board.GP3, board.GP2, board.GP1, board.GP0,
    # special pads
    board.GP16, board.GP17, board.GP18, board.GP19, 
    board.GP20, board.GP21, board.GP22, board.GP26,
    )

# index into touch_pins for non-grid pads
class Pads:
    PAD_SELECT = 16
    PAD_PLAY = 16
    PAD_B_UP = 17
    PAD_B_DOWN = 18
    PAD_C_RIGHT = 19
    PAD_C_LEFT = 21
    PAD_A_DOWN = 20
    PAD_A_UP = 22

num_pads = len(touch_pins)

class Hardware():
    def __init__(self):
        self.uart = busio.UART(rx=None, tx=uart_tx_pin, baudrate=31250, timeout=0.001)
        self.midi_uart = tmidi.MIDI(midi_out=self.uart)
        self.midi_usb = tmidi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])
        self.leds = neopixel.NeoPixel(leds_pin, num_leds, brightness=0.2, auto_write=False)
        self.num_leds = num_leds
        
        self.touch_ins = []  # maybe don't need debouncer
        self.touches = [] 
        for pin in touch_pins:
            touchin = touchio.TouchIn(pin)
            touchin.threshold += touch_threshold_adjust
            touch = Debouncer(touchin, interval=0.001)
            print("pin:", pin)
            self.touch_ins.append(touchin)
            self.touches.append(touch)
        self.num_pads = len(self.touch_ins)
        print("hardware init done")

    def bootloader_test(self):
        ## go to bootloader test
        #if True:
        if self.touch_ins[0].raw_value > 1200:  # hold down "1" key
            print("Booting up in bootloader mode in 3 secs")
            do_abort = False
            for i in range(3,0,-1):
                if self.touch_ins[0].raw_value < 1000:
                    print("  aborted")
                    do_abort = True
                    break
                print(i, end="...")
                self.leds.fill((30*i, 0, 0))
                self.leds.show()
                time.sleep(1)
            self.leds.fill(0)
            self.leds.show()
            if not do_abort:
                print("\n going into bootloader...")
                microcontroller.on_next_reset(microcontroller.RunMode.UF2)
            else:
                print("aborted going into bootloader")
            microcontroller.reset()

    def startup_demo(self):
        for i in range(num_leds):
            for j in range(num_leds):
                self.leds[j] = rainbowio.colorwheel( j*(255/num_leds) + time.monotonic()*50)
            self.leds[i] = 0xffffff
            self.leds.show()
            i = (i+1) % num_leds
            time.sleep(0.03)

