# Imports
# for millis
from time import time
# for Event
from types import FunctionType
# for Spawn
from threading import Thread
# for SerialDevice
from serial import Serial
# for Spreadsheet
from xlsxwriter import Workbook
# for QtWindow, Graph, SecondBasedGraph
from pyqtgraph import GraphicsView, GraphicsLayout
from pyqtgraph.Qt import QtGui
from numpy import empty as Empty
# for TkWindow
from tkinter import Tk
from tkinter.ttk import Frame

import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Methods
def millis():
    """
    `return`: the milliseconds passed since epoch
    """
    return round(time() * 1000)


def elapsed_millis(start_time):
    """
    `start_time`: the beging time in milliseconds
    - recommended: millis()

    `return`: the time elapsed since `start_time`
    """
    return millis() - start_time


def dtv(d, vs, dmax=4095):
    """
    `d`: digital value
    `vs`: The maximum voltage of the source
    `dmax`: The max digital value of the adc converter

    `return`: the voltage given a digital value
    """
    return vs/dmax*d


def data_split(data, split_key):
    """
    `data`: the string being split
    `split_key`: the key that splits the string

    `return`: the split(`split_key`) of a string
    if the length of the split is greater than 1
    """
    data_as_string = data
    split = data_as_string.split(split_key)
    return split


def min(table):
    """
    `table`: the table in which you want the minimum value from

    `return`: the minimum value in `table`
    """
    min = table[0]
    for i in table:
        if i < min:
            min = i
    return min


def max(table):
    """
    `table`: the table in which you want the maximum value from

    `return`: the maximum value in `table`
    """
    max = table[0]
    for i in table:
        if i > max:
            max = i
    return max


def spawn(function):
    """
    Will run `function` in a seperate thread

    `function`: the function being run in a seperate thread
    """
    Thread(target=function).start()


def int_input(text, fallback=None):
    """
    Will return an integer from user input. Will now allow user to input a string.
    Will allow the user to input nothing to fallback on a default value (fallback)

    `text`: the text that will be presented to the user via input(text)
    `fallback`: default value that will be returned if the user does not input anything

    `return`: int or `fallback`
    """
    while True:
        text = input(text)
        if not text and fallback:
            return fallback
        try:
            return int(text)
        except ValueError:
            print("Must be an integer!")


def float_input(text, fallback=None):
    """
    Will return a float from user input. Will now allow user to input a string.
    Will allow the user to input nothing to fallback on a default value (fallback)

    `text`: the text that will be presented to the user via input(text)
    `fallback`: default value that will be returned if the user does not input anything

    `return`: float or `fallback`
    """
    while True:
        text = input(text)
        if not text and fallback:
            return fallback
        try:
            return float(text)
        except ValueError:
            print("Must be a number (float)!")


# Classes
class Event:
    """
    An event system that will run a given amount functions when fired.

    `functions`: the functions that will be called when the event is fired
    """

    def __init__(self, *functions):
        self.functions = []
        for func in functions:
            self.connect(func)

    def __len__(self):
        return len(self.functions)

    def __contains__(self, function):
        if function in self.functions:
            return True
        return False

    def fire(self, *args, **kwargs):
        """
        Calls the functions connected to the event when called.

        `args`: args for the functions
        `kwargs`: keyword args for the functions
        """
        for function in self.functions:
            # TODO: make a solution that doesn't involve requiring each function to have args and kwargs
            function(args, kwargs)

    def connect(self, func):
        """
        Connects a function to the event to be called when the event is fired.

        `func`: function to add
        """
        if isinstance(func, FunctionType):
            self.functions.append(func)


class SerialDevice(Serial):
    """
    Sub-class of serial.Serial
    Specifically made to work around the buffer/encoded reads/writes

    `port`: the port of the COM device
    - Ex: `COM4`, `/dev/ttys4`, etc.

    `baudrate`: bits per second transfer-rate of the connection
    - Ex: `9600`, `19200`, `57600`
    """

    def __init__(self, port, baudrate=9600):
        super().__init__(port, baudrate)

    def kill(self):
        self.write('kill')
        super().close()

    def read_timeout(self, timeout=500, bytes=None):
        """
        `bytes`: given number of bytes to read from serial buffer
        `timeout`: time, in milliseconds, alloted before returning none if no data is read
        """
        start_time = millis()
        while elapsed_millis(start_time) < timeout:
            if super().in_waiting:
                data = super().read(bytes or super().in_waiting)
                if data:
                    return data.decode()

    def readline(self):
        """
        `return`: all bits in buffer until `\\n`
        - decodes, and removes `\\n`
        """
        #  `.decode()`: decodes strings via Python's default decode method
        # `[:-1]`: removes the '\n'
        return super().readline().decode()[:-1]

    def write(self, data):
        """
        `data`: data to write to the device
        """
        # `.str()`: turns data into a string so it can be encoded
        # `.encode()`: encodes strings via Python's default encoding method
        super().write(str(data).encode())

    def verify_write(self, data, timeout=500):
        """
        Will write to the device, and wait for the device to return that same value

        `data`: data to write to the device
        `timeout`: time, in milliseconds, alloted before returning none if no data is read
        """
        timeout /= 2  # due to it being used twice
        start_time = millis()
        while elapsed_millis(start_time) < timeout:
            self.write(data)
            val = self.read_timeout(timeout)
            if val == str(data):
                return val

    def verify_read(self, timeout=500):
        """
        Will read from the device, and return that read value back to the device

        `timeout`: time, in milliseconds, alloted before returning none if no data is read
        """
        data = self.read_timeout(timeout)
        self.write(data)
        return data


class Spreadsheet(Workbook):
    """
    Will create a Microsoft Excel spreadsheet

    Has limitations because I don't need them, but because it is a sub-class, they are still possible
    Said limitations:
    - can't do a number and color format in the same cell unless you do it yourself, which is possible

    `title`: title of the file
    `sheet_name`: the title of the sheet within the Workbook
    `constant_memory`: determines whether or not xlsxwriter will use constant_memory or not

    > https://xlsxwriter.readthedocs.io/working_with_memory.html?highlight=#performance-figures
    """

    def __init__(self, title, sheet_name, constant_memory=False):
        title += '.xlsx'
        super().__init__(title, {'constant_memory': constant_memory})
        self.sheet = super().add_worksheet(sheet_name)
        self._formats = {}

    def close(self):
        super().close()

    def num_format(self, name, format):
        """
        Add a number format to log.formats

        `name`: name of the format
        `num_format`: the format for a number in a cell
        - uses Excel's formatting
            - `'XX.XX'` | `'Normal'` | `'00.00'`
        """
        self._formats[name] = super().add_format({'num_format': format})

    def color_format(self, name, fill_color, text_color):
        """
        Add a color format to log.formats.
        Fill and text color.

        `name`: name of the format
        `fill_color`: the color of the cell in hex color code
        `text_color`: the color of the text in hex color code
        - `#000000` | `#FFFFFF` | `#FAFAFA`
        """
        self._formats[name] = super().add_format({'pattern': 1, 'fg_color': fill_color, 'font_color': text_color})

    def write(self, x, y, data, format=None):
        """
        Will write `data` to the cell at `x` and `y`
        If there is a format, it will write with the format

        `x`: X location to write to
        `y`: Y location to write to
        `data`: data to write to cell
        `format_type`: the name of the format made from the following:
        - `add_num_format()` | `add_color_format()`
        """
        if format:
            self.sheet.write(y, x, data, self._formats[format])
        else:
            self.sheet.write(y, x, data)


class QtWindow(GraphicsView):
    """
    Makes a Qt application, and window
    """

    def __init__(self, title):
        self._app = QtGui.QApplication([])
        super().__init__()  # GraphicsView requires a QApplication before it can be made
        super().setWindowTitle(title)

        self.layout = GraphicsLayout()  # for ease of organization
        super().setCentralItem(self.layout)

    def close(self):
        super().close()

    def show(self):
        super().show()


class TkWindow(Tk):
    """
    Makes a Tk window

    `title`: the title of the window
    """

    def __init__(self, title):
        super().__init__()
        super().title(title)

        self.frame = Frame(self)
        self.frame.grid(sticky=('n', 'e', 's', 'w'), padx=8, pady=8)
        self._widgets = []

    def quit(self):
        super().quit()


class Graph:
    """
    Makes a graph via PyQtGraph

    `window`: a Qt GraphicsView, and the parent of the graph
    - must have a layout

    `data`: size of the x-axis
    `title`: title of the graph
    `x_label`: label of the x axis
    `x_unit`: unit in which the x axis is measured
    `y_label`: label of the y axis
    `y_unit`: unit in which the y axis is measured

    > Units will change automagically!
    > Ex: if the unit is 'v' for Voltage it will scale to 'mV', 'uV', 'MV', etc.
    """

    def __init__(self, window, data=[0], title='', x_label='', x_unit='', y_label='', y_unit=''):
        self.window = window
        self.layout = self.window.layout
        self.plot = self.layout.addPlot()
        self.plot.setLabel('bottom', x_label, x_unit)
        self.plot.setLabel('left', y_label, y_unit)
        self.plot.setTitle(title)
        self._data = data
        self.curve = self.plot.plot(self._data)

    def update(self, data, pos=None):
        self._data[:-1] = self._data[1:]  # shift data back one
        self._data[-1] = data  # update the last index
        self.curve.setData(self._data)  # sets the value at x=0
        if pos:  # used if instead of or because the range is variable
            self.curve.setPos(pos, 0)


class SecondBasedGraph:
    """
    Makes a PyQtGraph with the x axis being scaled in seconds negatively

    `window`: a Qt GraphicsView, and the parent of the graph
    - must have a layout

    `title`: title of the graph
    `y_label`: label of the y axis
    `y_unit`: unit in which the y axis is measured
    `max_chunks`: how many curves the plot will have
    - essentially how many seconds will be measured
    - will be determined automagically if None

    `chunk_size`: x range of each curve within the second
    - bigger value = tighter curves and more values measured per second
    - None if timer_interval is set

    `timer_interval`: the value that the update timer will be set to
    - determines how many x values each curve will have

    `x_range`: x range (min, max)
    `y_range`: y range (min, max)
    """

    def __init__(self, window, title='', y_label='', y_unit='', max_chunks=None, chunk_size=None, timer_interval=50, x_range=(-10, 0), y_range=(-5, 5)):
        self.window = window
        self.layout = self.window.layout
        self.plot = self.layout.addPlot()  # makes the graph

        self.plot.setLabel('bottom', 'Time', 's')
        self.plot.setLabel('left', y_label, y_unit)
        self.plot.setTitle(title)
        self.plot.setXRange(x_range[0], x_range[1])
        self.plot.setYRange(y_range[0], y_range[1])

        self._x_range = x_range
        self._curves = []   # will hold the curves that are at each second marker on the graph
        self._max_chunks = max_chunks or abs(x_range[1] - x_range[0]) + 1
        self._chunk_size = chunk_size or round(1000 / timer_interval)
        self._data = Empty((self._chunk_size + 1, 2))  # makes a list of empty arrays ex: [[0, 0]]
        self._i = 0  # just an index
        self._start_time = time()  # the beginning time in seconds since epoch

    def show(self):
        self.window.show()

    def update(self, value):
        now = time()  # current time in seconds since epoch for the purpose of comparison
        for curve in self._curves:  # moves all the curves back every time a second passes
            curve.setPos(self._x_range[1]-(now - self._start_time), 0)

        i = self._i % self._chunk_size  # makes sure all the graphs are the correct size
        if i == 0:  # if the plot is at capacity (dictated by self._chunk_size)
            curve = self.plot.plot()  # makes a new curve
            self._curves.append(curve)  # adds the curve to the list of curves
            last = self._data[-1]  # gets the last value of the data already presented
            self._data = Empty((self._chunk_size + 1, 2))  # same as above... makes the empty arrays
            self._data[0] = last  # moves the data back
            while len(self._curves) > self._max_chunks:  # doesn't keep too many curves
                c = self._curves.pop(0)  # removes the last curve from the list
                self.plot.removeItem(c)  # 'physically' removes the curve
        else:  # if the plot has more capacity (dictated by self._chunk_size)
            curve = self._curves[-1]  # gets the last curve in the list (the curve at 0 on the x axis)
        self._data[i+1, 0] = now - self._start_time  # what will become the x-axis of the curve
        self._data[i+1, 1] = value  # what will become the y-axis of the curve
        curve.setData(x=self._data[:i+2, 0], y=self._data[:i+2, 1])  # udpates y at x=0
        self._i += 1


# Main
if __name__ == '__main__':
    pass
    # the folling is an example of the SecondBasedGraph class

    # from pyqtgraph.Qt import QtCore
    # from random import randint as Random
    # timer_interval = 16.66666  # 60 FPS
    # graph = SecondBasedGraph(QtWindow('Test'), timer_interval=timer_interval, x_range=(-7, 0))
    # graph.show()

    # def update():
    #    graph.update(Random(0, 3))

    # timer = QtCore.QTimer()
    # timer.timeout.connect(update)
    # timer.start(timer_interval)
