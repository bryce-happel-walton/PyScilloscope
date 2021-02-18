from pyb import LED, ADC, USB_VCP, Pin
from pyb import millis, elapsed_millis, delay, Timer
from pyb import hard_reset
from array import array

# User Variables
pin_strings = (
    'X1',
    'X2',
    'X3',
    'X4',
    'X5',
    'X6',
    'X7',
    'X8',
    'Y11',
    'Y12',
    'X19',
    'X20',
    'X21',
    'X22',
    'X11',
    'X12'
)
# Objects
usb = USB_VCP()
indicator_light = LED(4)
# Finals
inf = 10**100

# Classes
class VCP(USB_VCP):

    def __init__(self):
        super().__init__()

    def read_timeout(self, timeout=5000):
        start_time = millis()
        while elapsed_millis(start_time) < timeout:
            data = self.read()
            if data:
                return data.decode()

    def write_encode(self, data):
        self.write(bytearray(str(data).encode()))

    def verify_write(self, data, timeout=500):
        timeout /= 2
        start_time = millis()
        while elapsed_millis(start_time) < timeout:
            self.write_encode(data)
            val = self.read_timeout(timeout)
            if val == str(data):
                return val

    def verify_read(self, timeout=500):
        data = self.read_timeout(timeout)
        self.write_encode(data)
        return data

# Methods
def mean(table):
    total = 0
    for i in table:
        total += i
    return total / len(table)


def main():
    """
    The method that controls everything.

    Initialization procedure:
    1: Wait for bytes from PC are specifically 'start'
        1a: Dim the indicator light
    2: Write the array of pins, `pin_strings`, so that the PC knows what it's working with
    """
    # Objects
    usb = VCP()

    # Initial
    while True:
        read = usb.read_timeout(inf)
        if read == 'start':
            usb.write_encode('start')
            break

    # Object manipulation
    indicator_light.intensity(32)  # dim the indicator light
    # Writes
    usb.write_encode(pin_strings)
    # Reads
    timer_frequency = int(usb.verify_read(inf))
    # Post init variables
    pins = tuple(Pin(i) for i in pin_strings)
    adc_pins = tuple(ADC(p) for p in pins)
    adc_arrays = tuple(array('H', [0]) for j in adc_pins)
    timer = Timer(8, freq=timer_frequency)
    # Loop
    while True:
        start_time = millis()
        ADC.read_timed_multi(adc_pins, adc_arrays, timer)

        if usb.read_timeout(1) == 'kill':
            hard_reset()

        write_table = {}
        usb.write_encode('newset\n')
        for i, v in enumerate(adc_arrays):
            usb.write_encode('\'{pin}\': {value}\n'.format(pin=pin_strings[i], value=v[0]))
            #write_table[pin_strings[i]] = v[0]
        usb.write_encode('endset\n')

        write_table['duration'] = elapsed_millis(start_time)
        #usb.write_encode(str(write_table)+'\n')
        #print(write_table)


# Main
if __name__ == '__main__':
    main()
