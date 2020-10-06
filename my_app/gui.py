from threading import Thread
from tkinter import (
    BOTH,  # Enumerations
    Button, Frame, Label, Menu,  # Widgets
    StringVar,  # Special Types
    messagebox,  # Dialog boxes
    E, W  # Grid stuff
)

from pubsub import pub

from my_app.structs import PubSubMessageTypes
from my_app.operator import BackgroundOperation


class Window(Frame):

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.parent = parent

        # initialize some member vars, mostly to None unless it is reasonable to give it a value now
        self.run_button = None
        self.stop_button = None
        self.long_thread = None
        self.label_string = StringVar()
        self.background_operator = None

        # initialize the GUI
        self.init_window()

    def init_window(self):
        # changing the title of our master widget
        self.parent.title("Python Tk+PyPubSub Demo")

        # allowing the widget to take the full space of the root window
        # self.pack()  # fill=BOTH, expand=1)

        pane = Frame(self.parent)
        pane.pack(fill=BOTH, expand=True)

        # create the menu
        menu = Menu(pane)
        self.parent.config(menu=menu)
        file_menu = Menu(menu)
        file_menu.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file_menu)

        # create the widgets
        self.run_button = Button(pane, text="Run", command=self.client_run)
        self.stop_button = Button(pane, text="Stop", command=self.client_stop)
        self.stop_button.configure(state='disabled')
        label = Label(pane, textvariable=self.label_string)
        self.label_string.set("Initialized")
        quit_button = Button(pane, text="Quit", command=self.client_exit)

        # placing the button on my window
        self.run_button.grid(column=0, row=1, sticky=E+W, columnspan=1)
        self.stop_button.grid(column=1, row=1, sticky=E+W)
        label.grid(column=0, row=2, columnspan=2)
        quit_button.grid(column=1, row=3, sticky=E+W)

        # wire up the background thread
        pub.subscribe(self.status_callback, PubSubMessageTypes.STATUS)
        pub.subscribe(self.finished_callback, PubSubMessageTypes.FINISHED)
        pub.subscribe(self.cancelled_callback, PubSubMessageTypes.CANCELLED)

    def set_button_status_for_run(self, is_running: bool):
        if is_running:
            self.run_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
        else:
            self.run_button.configure(state='normal')
            self.stop_button.configure(state='disabled')

    def client_run(self):
        if self.long_thread:
            messagebox.showerror("Cannot run another thread, wait for the current to finish -- how'd you get here?!?")
            return
        self.background_operator = BackgroundOperation()
        self.set_button_status_for_run(True)
        self.long_thread = Thread(target=self.background_operator.run, args=(5,))
        self.long_thread.start()

    def client_stop(self):
        self.label_string.set("Attempting to cancel...")
        self.background_operator.cancel_me = True

    def client_exit(self):
        if self.long_thread:
            messagebox.showerror("Uh oh!", "Cannot exit program while operations are running; abort them then exit")
            return
        exit()

    def client_done(self):
        self.set_button_status_for_run(False)
        self.long_thread = None

    def status_callback(self, status):
        self.label_string.set(f"Hey, status update: {str(status)}")

    def finished_callback(self, results):
        self.label_string.set(f"Hey, all done! Results: {str(results)}")
        self.client_done()

    def cancelled_callback(self):
        self.label_string.set(f"Properly cancelled!")
        self.client_done()
