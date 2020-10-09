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

from my_app.gui_widgets import ScrollableFrame, IDFTestCaseRowFrame, ResultsTreeRoots
from my_app.structs import PubSubMessageTypes
from my_app.operator import BackgroundOperation


class MyApp(Frame):

    def __init__(self):
        self.root = Tk()
        Frame.__init__(self, self.root)

        # high level GUI configuration
        self.root.geometry('1200x500')
        self.root.resizable(width=1, height=1)
        self.root.option_add('*tearOff', False)  # keeps file menus from looking weird

        # members related to the background thread and operator instance
        self.long_thread = None
        self.background_operator = None

        # widgets that we might want to access later
        self.run_button = None
        self.stop_button = None
        self.label_string = StringVar()
        self.progress = None
        self.log_message_listbox = None
        self.results_tree = None

        # some data holders
        self.idf_test_cases = list()
        self.tree_folders = {}

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

        # now let's set up a list of checkboxes for selecting IDFs to run
        pane_idfs = ScrollableFrame(panes)
        for i in range(50):
            self.idf_test_cases.append(
                IDFTestCaseRowFrame(pane_idfs.scrollable_frame, f"File{i}", self.idf_selected_callback)
            )
            self.idf_test_cases[-1].pack()
        panes.add(pane_idfs)

        # the far right will be a notebook view with two panes: log messages and test results
        results_notebook = ttk.Notebook(panes)

        # set up a scrolled listbox for the log messages
        frame_log_messages = Frame(results_notebook)
        scrollbar = Scrollbar(frame_log_messages)
        self.log_message_listbox = Listbox(frame_log_messages, yscrollcommand=scrollbar.set)
        self.log_message_listbox.insert(END, "Program started...here are some fake messages")
        for line in range(25):
            self.log_message_listbox.insert(END, "This is line number " + str(line))
        self.log_message_listbox.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.log_message_listbox.yview)
        results_notebook.add(frame_log_messages, text="Log Messages")

        # set up a tree-view for the results
        frame_results = Frame(results_notebook)
        scrollbar = Scrollbar(frame_results)
        self.results_tree = ttk.Treeview(frame_results, columns=("Base File", "Mod File", "Diff File"))
        self.results_tree.heading("#0", text="Results", anchor=W)
        self.results_tree.heading("Base File", text="Base", anchor=W)
        self.results_tree.heading("Mod File", text="Mod", anchor=W)
        self.results_tree.heading("Diff File", text="Diff", anchor=W)
        self.rebuild_tree()
        self.results_tree.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.results_tree.yview)
        results_notebook.add(frame_results, text="Results")

        panes.add(results_notebook)

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

    def rebuild_tree(self, results=None):
        for root in ResultsTreeRoots.get_all():
            self.tree_folders[root] = self.results_tree.insert(
                parent="", index='end', text=root, values=("", "", "")
            )
            if results:
                self.results_tree.insert(
                    parent=self.tree_folders[root], index="end", text="Pretend",
                    values=("These", "Are", "Real")
                )
            else:
                self.results_tree.insert(
                    parent=self.tree_folders[root], index="end", text="Run test for results",
                    values=("", "", "")
                )

    def idf_selected_callback(self, test_case, checked):
        self.label_string.set(f"CHECKED: {test_case} ({checked.get()})")

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
        self.log_message_listbox.insert(END, "Attempting to cancel")
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

    def status_callback(self, status, object_completed, percent_complete):
        self.log_message_listbox.insert(END, object_completed)
        self.progress['value'] = percent_complete
        self.label_string.set(f"Hey, status update: {str(status)}")

    def finished_callback(self, results):
        self.log_message_listbox.insert(END, "All done, finished")
        self.label_string.set(f"Hey, all done! Results: {results['result_string']}")
        self.client_done()

    def cancelled_callback(self):
        self.log_message_listbox.insert(END, "Cancelled!")
        self.label_string.set("Properly cancelled!")
        self.client_done()
