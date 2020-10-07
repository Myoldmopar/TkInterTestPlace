from threading import Thread
from tkinter import (
    Tk, ttk,  # Core pieces
    Button, Frame, Label, Listbox, Menu, PanedWindow, Scrollbar,  # Widgets
    StringVar,  # Special Types
    messagebox,  # Dialog boxes
    E, W,  # Cardinal directions N, S,
    X, Y, BOTH,  # Orthogonal directions (for fill)
    END, TOP, LEFT, CENTER,  # relative directions (RIGHT)
    GROOVE,  # relief type (for panedwindow sash)
)

from pubsub import pub

from my_app.structs import PubSubMessageTypes
from my_app.operator import BackgroundOperation


class MyApp(Frame):

    def __init__(self):
        self.root = Tk()
        Frame.__init__(self, self.root)

        self.root.geometry('600x500')
        self.root.resizable(width=1, height=1)
        self.root.option_add('*tearOff', False)  # keeps file menus from looking weird
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # initialize some member vars, mostly to None unless it is reasonable to give it a value now
        self.run_button = None
        self.stop_button = None
        self.long_thread = None
        self.label_string = StringVar()
        self.background_operator = None
        self.progress = None

        # initialize the GUI
        self.init_window()

    def init_window(self):
        # changing the title of our master widget
        self.root.title("Python Tk+PyPubSub Demo")

        # create the menu
        menu = Menu(self.root)
        self.root.config(menu=menu)
        file_menu = Menu(menu)
        file_menu.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file_menu)

        # put a paned window for the rest of the widgets
        panes = PanedWindow(self.root, sashrelief=GROOVE)
        panes.pack(fill=BOTH, expand=1)

        # create the left pane containing the controls
        pane_controls = Frame(panes)
        panes.add(pane_controls)
        self.run_button = Button(pane_controls, text="Run", command=self.client_run)
        self.stop_button = Button(pane_controls, text="Stop", command=self.client_stop)
        self.stop_button.configure(state='disabled')
        quit_button = Button(pane_controls, text="Quit", command=self.client_exit)

        # placing the button on my window
        self.run_button.pack(side=TOP, anchor=CENTER)
        self.stop_button.pack(side=TOP, anchor=CENTER)
        quit_button.pack(side=TOP, anchor=CENTER)

        # set up a scrolled listbox
        pane_tests = Frame(panes)
        scrollbar = Scrollbar(pane_tests)
        panes.add(pane_tests)
        my_list = Listbox(pane_tests, yscrollcommand=scrollbar.set)
        for line in range(100):
            my_list.insert(END, "This is line number " + str(line))
        my_list.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=my_list.yview)

        # status bar at the bottom
        frame_status = Frame(self.root)
        self.progress = ttk.Progressbar(frame_status)
        self.progress.grid(column=0, row=0, sticky=E+W)
        label = Label(frame_status, textvariable=self.label_string)
        self.label_string.set("Initialized")
        label.grid(column=1, row=0, sticky=E+W)
        frame_status.pack(fill=X)

        # wire up the background thread
        pub.subscribe(self.status_callback, PubSubMessageTypes.STATUS)
        pub.subscribe(self.finished_callback, PubSubMessageTypes.FINISHED)
        pub.subscribe(self.cancelled_callback, PubSubMessageTypes.CANCELLED)

    def run(self):
        self.root.mainloop()

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
        self.label_string.set("Properly cancelled!")
        self.client_done()
