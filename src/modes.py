"""
Just add a new class, and it will be detected. Easy as pie!
"""

# Imports
# DO NOT IMPORT CLASSES!!! They will interfere with the whole reason this works at all
# for Main
from ast import literal_eval
import module  # for Event
import datetime  # for datetime
from pyqtgraph.Qt import QtCore
from module import dtv, millis, elapsed_millis, min, max
from math import sqrt, floor
from statistics import mean, median, variance, stdev


# Classes
class Main:
    """
    Basis for the included modes.

    `device`: the serial device
    - Must be from `module`

    `timer_interval`: how quickly (in ms) new data will be collected
    `seconds_range`: the range of seconds that will be displayed on the x axis of each graph
    `voltage`: (not really needed, as it does not change) the voltage source supplied to the PyBoard's external devices... i.e. the ADC

    ___
    __Events:__
    `Over`: (Required) unused by user
    `Kill`: (Required) Connected to force close
    `Ended`: Fired when force closed
    `Began`: (for sub-classes, not required) Fired when `start` is called

    ___
    __Explicit Sub-Class Methods:__
    `make_log`: makes an Excel file for logging the data read

    ___
    __Implicit Sub-Class Methods:__
    By implicit I mean that they should be used with the same name, and connected via super()
    Example:

        in Main:

        def method():
          thing

        in Sub-Class:

        def method():
          super().method()

    Methods:

    `update`
    `start`
    `stop`

    Details not included because they are implicit and can be used however seen fit
    Of course all methods can be used in this manor, but I recommend these for the core of all modes.
    ___
    > For making your own mode:
    >> Required:
    >> - `__init__` variables obviously
    >> - `Over`, and `Kill` events respectively
    >> - `start` and `stop` methods respectively

    >> That's about it
    >> Don't import classes, else the user interface in `main.py` will see them in the mode selection menu
    """

    def __init__(self, device, timer_interval=5, seconds_range=3, voltage=3.29):
        self.device = device
        if not self.device.is_open:
            self.device.open()
        self._running = False

        self.timer_interval = timer_interval
        self.seconds_range = seconds_range
        self.voltage_source = voltage

        self.graphs = {}

        self.Over = module.Event()
        self.Ended = module.Event()
        self.Kill = module.Event(self.stop)
        self.Began = module.Event()

        self.qwindow = module.QtWindow('PyScilloscope Graphs')  # The window that holds the graphs
        self.timer = QtCore.QTimer()  # Timer that updates the graphs, and collects data
        self.timer.timeout.connect(self.update)

        self.i = 0

    def _make_graphs(self):
        column = 0
        gpr = floor(sqrt(len(self.pins)))  # graphs-per-row... the graphs in each row to make a grid
        for i, v in enumerate(self.pins):
            if column < gpr:
                column += 1
            else:
                self.qwindow.layout.nextRow()
                column = 1
            self.graphs[v] = module.SecondBasedGraph(self.qwindow, title=v, timer_interval=self.timer_interval, x_range=(-(self.seconds_range), 0), y_range=(0, self.voltage_source))

    def _update_graphs(self):
        for pin in self.dataset:
            self.graphs[pin].update(self.dataset[pin])  # dtv turns the ADC value into a voltage

    def update(self):
        try:
            if self._running:
                if self.device.readline() == 'newset':
                    d_table = {}
                    while True:
                        data = self.device.readline()
                        if data == 'endset':
                            break
                        data = literal_eval('{'+data+'}')
                        pin = list(data.keys())[0]
                        d_table[pin] = dtv(data[pin], self.voltage_source)
                    self.dataset = d_table
                    self._update_graphs()
                    return self.dataset
        except Exception:
            pass

    def start(self):
        self._running = True
        self.Began.fire()
        self.device.verify_write('start')
        self.pins = literal_eval(self.device.read_timeout())
        self.device.write(50000)

        self._make_graphs()

        self.qwindow.show()
        self.timer.start(self.timer_interval)

    def stop(self, a=None, kw=None):
        self._running = False
        self.timer.stop()
        self.Ended.fire()
        self.device.kill()

    def make_log(self, mode, constant_memory=True):
        """
        Makes an Excel file for logging purposes

        `mode`: name of the mode making the file
        `constant_memory`: determines whether or not xlsxwriter will use constant_memory or not

        > https://xlsxwriter.readthedocs.io/working_with_memory.html?highlight=#performance-figures
        """
        date_string = str(datetime.datetime.today()).replace(':', '-')[:-7]
        string_split = date_string.split(' ')
        log = module.Spreadsheet(f'[{mode}] - {string_split[0]} [{string_split[1]}]', 'ADC Reads')
        log.num_format('voltage', '0.000V')
        log.color_format('pin', '#9C27B0', '#FAFAFA')
        log.color_format('data_type', '#1976d2', '#FAFAFA')
        log.color_format('black', '#000000', '#000000')
        log.color_format('error', '#FF3D00', '#000000')
        return log


class Normal(Main):
    """
    Normal mode for those who want a concise file, while saving data at the same time for only $5.99

    Will log the data collected in an excel spreadsheet
    """

    def __init__(self, device, timer_interval=50, seconds_range=10):
        super().__init__(device, timer_interval, seconds_range)
        self.log = super().make_log('Normal', constant_memory=False)
        self.i = 0

        # Add (or remove) a method that will return a single value from a table if you'd like more data
        self.log_methods = {
            'min': min,
            'max': max,
            'mean': mean,
            'median': median,
            'variance': variance,
            'std dev': stdev
        }

    def set_values(self):
        for i in self.pin_values:
            table = self.pin_reads[i]
            values = {}
            for j in self.log_methods:
                method = self.log_methods[j]
                values[j] = method(table)
            self.pin_values[i] = values

    def start(self):
        super().start()
        self.pin_reads = {i: [] for i in self.pins}
        self.pin_values = {i: [] for i in self.pins}
        self.start_time = millis()
        self.log.sheet.freeze_panes(1, 1)
        self.log.write(0, 0, '', 'pin')
        for i in self.pins:
            self.log.write(self.pins.index(i)+1, 0, i, 'pin')
        for i, v in enumerate(self.log_methods):
            self.log.write(0, i+1, v+':', 'data_type')

    def stop(self, a=None, kw=None):
        self.set_values()
        for i, v in enumerate(self.pin_values):
            for j, k in enumerate(self.log_methods):
                self.log.write(i+1, j+1, self.pin_values[v][k], 'voltage')
        self.log.close()
        super().stop()

    def update(self):
        self.i += 1
        self.dataset = super().update()
        if not self.dataset:
            return

        for i in self.dataset:
            v = self.dataset[i]
            self.pin_reads[i].append(v)


class Verbose(Main):
    """
    Logs all reads every second.
    """

    def __init__(self, device, timer_interval=50, seconds_range=10):
        super().__init__(device, timer_interval, seconds_range)
        self.current_data = []
        self.log = super().make_log('Verbose', constant_memory=True)

    def start(self):
        super().start()
        self.log.sheet.freeze_panes(1, 1)
        self.log.write(0, 0, '', 'pin')  # makes the corning cell blank, but colored
        self.start_time = millis()
        self.current_data = {i: [] for i in self.pins}  # creates a empty lists for the pins
        self.level = 1
        for i in self.pins:
            self.log.write(self.pins.index(i)+1, 0, i, 'pin')  # writes all the pins in the file for easy reading

    def stop(self, a=None, kw=None):
        self.log.close()
        super().stop()

    def update(self):
        self.dataset = super().update()
        if elapsed_millis(self.start_time) >= 1000:  # if a second has passed
            self.start_time = millis()  # reset the start time
            self.log.write(0, self.level, str(datetime.datetime.now().time())[:-7], 'data_type')  # write the current time to the log
            for i, v in enumerate(self.current_data):
                self.log.write(i+1, self.level, mean(self.current_data[v]), 'voltage')  # writes the mean voltage of all samples collected in the second to the log
            self.current_data = {i: [] for i in self.pins}  # resets the data collection list
            self.level += 1
        else:
            if not self.dataset:
                return
            for i in self.dataset:
                self.current_data[i].append(self.dataset[i])
