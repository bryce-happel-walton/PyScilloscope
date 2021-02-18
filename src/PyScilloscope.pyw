# TODO: use more concise naming conventions
# for DeviceSelection
from serial.tools.list_ports import comports
from tkinter.ttk import Combobox
# for DeviceSelection, MainClass
from module import SerialDevice, TkWindow
from tkinter.ttk import Style, Frame, Button, Label, Entry  # Combobox used aswell, but already imported above
from tkinter import StringVar
# for __main__
import modes as Modes
from inspect import getmembers, isclass

# Finals
inf = float('inf')
application_title = 'PyScilloscope'

# Default Values
d_timer_interval = 2  # default timer interval in milliseconds
d_second_graph = 3  # default value for the seconds logged via graphing
d_voltage = 3.29  # measured voltage of the pyboard

# Ranges
r_timer_interval = (1, 5)  # range of timer intervals the user is able to choose
r_second_graph = (1, 5)  # read above, but for the seconds logged via graphing


# Special Case Classes
class DeviceSelection(TkWindow):  # Not necessarily a special case, and could fit just as well in `module`
    """
    A serial device selection prompt that will close itself upon selection
    """

    def __init__(self):
        super().__init__('Device Select')
        self.value = StringVar()
        ports = comports()
        self._string_values = [f'{port.device}: {port.description}' for port in ports]
        self._real_values = [port.device for port in ports]
        self.selected_device = None

        self.selection_box = Combobox(self.frame, values=self._string_values, textvariable=self.value, state='readonly', width=40)
        self.selection_box.set('Select a device')
        self.selection_box.grid(row=0, column=0)
        self.selection_box.bind('<<ComboboxSelected>>', self._enable_confirm)

        self.buffer_frame = Frame(self.frame, height=8)
        self.buffer_frame.grid(row=1, column=0)

        self.confirm_button = Button(self.frame, text='Confirm', command=self._confirm, state='disabled')
        self.confirm_button.grid(row=2, column=0)
        super().mainloop()

    def _enable_confirm(self, event):
        """
        Enables the confirmation button to select the device.
        > Called automagically when a device is selected in the combobox
        """
        self.confirm_button.configure(state='enabled')

    def _confirm(self):
        """
        destroys the application and sets the `selected_device` to be read from a third party
        > called automagically
        """
        value = self.value.get()
        if value in self._string_values:
            self.selected_device = SerialDevice(self._real_values[self._string_values.index(value)], 128000)
            super().destroy()


class MainClass(TkWindow):

    def __init__(self, title, device, modes):
        if not device:
            raise Exception
        # should only happen if the device selection window is force closed without a device being selected
        # TODO: make proper exception class to deal with that

        super().__init__(application_title)

        # init variables
        self._frame_buffer_size = 8
        self._options_box_width = 5

        self._running = False

        self._selected_mode = None
        self._timer_interval = d_timer_interval
        self._seconds_range = d_second_graph
        self._mode_vars = {}

        self._variable_state_widgets = []

        self.device = device

        self._string_modes = []
        self._mode_classes = []

        for v in modes:
            self._string_modes.append(v)
            self._mode_classes.append(modes[v])

        # indicator style
        self._indicator_style = Style()
        self._indicator_style.configure('indicator_bad.TLabel', foreground='Red')
        self._indicator_style.configure('indicator_good.TLabel', foreground='Green')

        # options selection
        self._options_frame = Frame

        # build
        self._build_indicator_section()
        self._build_start_section()
        self._build_options_section()

    # user interface build Methods
    # these methods are specifically for building the user interface and making each element work
    def _build_indicator_section(self):
        self._indicator_frame = Frame(self.frame)
        self._indicator_frame.grid(row=1, column=1, sticky=('n', 'e', 's', 'w'))

        self.start_indicator_frame_buffer = Frame(self.frame, height=self._frame_buffer_size)
        self.start_indicator_frame_buffer.grid(row=2, column=1)

        _frame = self._indicator_frame

        self.connection_status_label = Label(_frame, text='Status:')
        self.connection_status_label.grid(row=1, column=1)

        self.connection_indicator_label = Label(_frame, text='Connected', style='indicator_good.TLabel')
        self.connection_indicator_label.grid(row=1, column=2)

    def _build_start_section(self):
        self._start_frame = Frame(self.frame)
        self._start_frame.grid(row=3, column=1, sticky=('n', 'e', 's', 'w'))

        _frame = self._start_frame

        self.mode_value = StringVar()
        self._mode_select_box = Combobox(_frame, values=self._string_modes, textvariable=self.mode_value, state='readonly', width=11)
        self._mode_select_box.set('Select Mode')
        self._mode_select_box.grid(row=1, column=1, sticky=('n', 'e', 's', 'w'))
        self._mode_select_box.bind('<<ComboboxSelected>>', self._mode_selected)

        self._select_start_buffer = Frame(_frame, width=self._frame_buffer_size)
        self._select_start_buffer.grid(row=1, column=2)

        # the start button is not a 'variable widget' because it is controlled by the mode selection box
        # TODO: make it disableable in case the selection box is disabled while the start button is disabled
        self.start_button = Button(_frame, text='Start', state='disabled', command=self._start_command)
        self.start_button.grid(row=1, column=3, columnspan=2, sticky=('n', 'e', 's', 'w'))

    def _build_options_section(self):
        # options section
        self._options_frame_buffer = Frame(self.frame, width=self._frame_buffer_size)
        self._options_frame_buffer.grid(row=1, column=2)

        self._options_frame = Frame(self.frame)
        self._options_frame.grid(row=1, column=3, rowspan=3)

        _frame = self._options_frame

        def _timer_validate(value):
            try:
                value = int(value)
                if value >= r_timer_interval[0] and value <= r_timer_interval[1]:
                    self._timer_interval = value
                    return True
            except Exception:
                if value == '':
                    return True
            return False

        def _seconds_validate(value):
            try:
                value = int(value)
                if value >= r_second_graph[0] and value <= r_second_graph[1]:
                    self._seconds_range = value
                    return True
            except Exception:
                if value == '':
                    return True
            return False

        _v_t = super().register(_timer_validate)
        _v_s = super().register(_seconds_validate)

        self._timer_interval_label = Label(_frame, text='Timer interval (ms):')
        self._timer_interval_label.grid(row=1, column=1, sticky='e')

        self._timer_interval_box = Entry(_frame, width=self._options_box_width, validate='all', validatecommand=(_v_t, '%P'))
        self._timer_interval_box.grid(row=1, column=2, sticky='e')
        self._timer_interval_box.insert(0, d_timer_interval)

        self._option_buffer = Frame(_frame, height=self._frame_buffer_size/2)
        self._option_buffer.grid(row=2, column=1)

        self._graph_log_label = Label(_frame, text='Seconds Graphed:')
        self._graph_log_label.grid(row=3, column=1, sticky='e')

        self._graph_log_box = Entry(_frame, width=self._options_box_width, validate='all', validatecommand=(_v_s, '%P'))
        self._graph_log_box.grid(row=3, column=2, sticky='e')
        self._graph_log_box.insert(0, d_second_graph)

    # UI Control
    # TODO: Implement this... the only reason it is here is for the indicator things going on, but I have not found a good way to implement this yet
    def _add_variable_widget(self, widget):
        self._variable_state_widgets.append(widget)
        return widget

    def _change_variable_state(self):
        for i in self._variable_state_widgets:
            if isinstance(i, Combobox):
                i.configure(state='readonly')
            else:
                i.configure(state='enabled')

    # Event methods
    # These are methods that are called by .bind() or command calls in tk
    def _mode_selected(self, event):
        mode = self.mode_value.get()
        if mode in self._string_modes:
            self._selected_mode = self._mode_classes[self._string_modes.index(mode)]

        self.start_button.configure(state='enabled')

    def _start_command(self, a=None, kw=None):
        if self._running:
            self.start_button.configure(text='Start')
            self._running = False
            self._current_mode.stop()
            self.quit()
        elif not self._running:
            self.start_button.configure(text='Stop')
            mode = self._selected_mode
            self._current_mode = mode(device=self.device, timer_interval=self._timer_interval, seconds_range=self._seconds_range)
            self._current_mode.Over.connect(self._start_command)
            self._current_mode.start()
            self._running = True


# Main
if __name__ == '__main__':
    members = getmembers(Modes, isclass)
    modes = {}
    for c in members:
        if not c[0] == 'Main':
            modes[c[0]] = c[1]

    device = DeviceSelection().selected_device
    MainClass(application_title, device, modes).mainloop()
