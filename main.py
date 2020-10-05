
from subprocess import check_call
from threading import Thread
from tkinter import (
    BOTH,  # Enumerations
    Button, Frame, Label, Menu,  # Widgets
    StringVar,  # Special Types
    Tk  # Root Tk namespace
)

from pubsub import pub


class PubSubMessageTypes:
    STATUS = '10'
    FINISHED = '20'
    CANCELLED = '30'


class BackgroundOperation:

    def __init__(self):
        self.cancel_me = False

    def run(self, number_iterations: int):
        for i in range(1, number_iterations+1):
            if self.cancel_me:
                pub.sendMessage(PubSubMessageTypes.CANCELLED)
                return
            check_call(['sleep', '1'])
            pub.sendMessage(PubSubMessageTypes.STATUS, status=f"{i}/{number_iterations} of the way there")
        pub.sendMessage(PubSubMessageTypes.FINISHED, results='PRETEND I AM RESULTS')


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
        self.pack(fill=BOTH, expand=1)

        # create the menu
        menu = Menu(self.parent)
        self.parent.config(menu=menu)
        file_menu = Menu(menu)
        file_menu.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file_menu)

        # create the widgets
        self.run_button = Button(self, text="Run", command=self.client_run)
        self.stop_button = Button(self, text="Stop", command=self.client_stop)
        self.stop_button.configure(state='disabled')
        label = Label(self, textvariable=self.label_string)
        self.label_string.set("Initialized")
        quit_button = Button(self, text="Quit", command=self.client_exit)

        # placing the button on my window
        self.run_button.grid(row=1)
        self.stop_button.grid(row=2)
        label.grid(row=3)
        quit_button.grid(row=4)

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
            print("Cannot run another thread instance, wait for the current to finish -- how'd you get here?!?")
            return
        self.background_operator = BackgroundOperation()
        self.set_button_status_for_run(True)
        self.long_thread = Thread(target=self.background_operator.run, args=(5,))
        self.long_thread.start()

    def client_stop(self):
        self.label_string.set("Attempting to cancel...")
        self.background_operator.cancel_me = True

    def client_exit(self):
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


root = Tk()
root.geometry("400x300")
root.option_add('*tearOff', False)  # keeps file menus from looking weird
app = Window(root)
root.mainloop()
