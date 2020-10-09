from threading import Thread
from tkinter import (
    Tk, ttk,  # Core pieces
    Button, Canvas, Checkbutton, Frame, Label, Listbox, Menu, PanedWindow, Scrollbar,  # Widgets
    BooleanVar, StringVar,  # Special Types
    messagebox,  # Dialog boxes
    E, W,  # Cardinal directions N, S,
    X, Y, BOTH,  # Orthogonal directions (for fill)
    END, TOP, LEFT, CENTER,  # relative directions (RIGHT)
    GROOVE,  # relief type (for panedwindow sash)
)

from pubsub import pub

from my_app.structs import PubSubMessageTypes
from my_app.operator import BackgroundOperation


class ScrollableFrame(ttk.Frame):

    def __init__(self, container):
        super().__init__(container)
        canvas = Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class IDFTestCaseRowFrame(ttk.Frame):

    def __init__(self, container, idf_file_path_from_repo_root, cb):
        super().__init__(container)
        self.idf_path = idf_file_path_from_repo_root
        self.checked = BooleanVar()
        self.checkbox = Checkbutton(container, text=idf_file_path_from_repo_root, variable=self.checked, command=cb)
        self.checkbox.pack(fill=X)

    def set_enabled_status(self, enabled: bool):
        self.checkbox.configure(state='normal' if enabled else 'disable')


class MyApp(Frame):

    def __init__(self):
        self.root = Tk()
        Frame.__init__(self, self.root)

        self.root.geometry('800x500')
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
        self.idf_test_cases = None

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

        # now let's set up a tableview with checkboxes for selecting IDFs to run
        pane_idfs = ScrollableFrame(panes)
        self.idf_test_cases = list()
        for i in range(50):
            self.idf_test_cases.append(
                IDFTestCaseRowFrame(pane_idfs.scrollable_frame, f"File{i}", self.idf_selected_callback)
            )
            self.idf_test_cases[-1].pack()
        panes.add(pane_idfs)

        # set up a scrolled listbox
        pane_tests = Frame(panes)
        scrollbar = Scrollbar(pane_tests)
        my_list = Listbox(pane_tests, yscrollcommand=scrollbar.set)
        for line in range(100):
            my_list.insert(END, "This is line number " + str(line))
        my_list.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=my_list.yview)
        panes.add(pane_tests)

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

    def idf_selected_callback(self, check):
        self.label_string.set("CHECKED")

    def set_gui_status_for_run(self, is_running: bool):
        if is_running:
            self.run_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            for idf in self.idf_test_cases:
                idf.set_enabled_status(False)
        else:
            self.run_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
            for idf in self.idf_test_cases:
                idf.set_enabled_status(True)

    def client_run(self):
        if self.long_thread:
            messagebox.showerror("Cannot run another thread, wait for the current to finish -- how'd you get here?!?")
            return
        self.background_operator = BackgroundOperation()
        self.background_operator.get_ready_to_go()
        self.set_gui_status_for_run(True)
        number_of_iterations = 5
        self.long_thread = Thread(target=self.background_operator.run, args=(number_of_iterations,))
        self.long_thread.start()

    def client_stop(self):
        self.label_string.set("Attempting to cancel...")
        self.background_operator.please_stop()

    def client_exit(self):
        if self.long_thread:
            messagebox.showerror("Uh oh!", "Cannot exit program while operations are running; abort them then exit")
            return
        exit()

    def client_done(self):
        self.set_gui_status_for_run(False)
        self.long_thread = None

    def status_callback(self, status, percent_complete):
        self.progress['value'] = percent_complete
        self.label_string.set(f"Hey, status update: {str(status)}")

    def finished_callback(self, results):
        self.label_string.set(f"Hey, all done! Results: {results['result_string']}")
        self.client_done()

    def cancelled_callback(self):
        self.label_string.set("Properly cancelled!")
        self.client_done()
