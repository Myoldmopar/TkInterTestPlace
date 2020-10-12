from threading import Thread
from tkinter import (
    Tk, ttk,  # Core pieces
    Button, Frame, Label, Listbox, Menu, Scrollbar,  # Widgets
    StringVar,  # Special Types
    messagebox,  # Dialog boxes
    E, W,  # Cardinal directions N, S,
    X, Y, BOTH,  # Orthogonal directions (for fill)
    END, TOP, LEFT, CENTER,  # relative directions (RIGHT)
    filedialog,  # system dialogs
)

from pubsub import pub

from my_app.background_operation import BackgroundOperation


from tkinter import (
    BooleanVar,
    Canvas,
    Checkbutton,
    ttk
)


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
        self.checkbox = Checkbutton(
            container,
            text=idf_file_path_from_repo_root,
            variable=self.checked,
            command=lambda i=idf_file_path_from_repo_root, c=self.checked: cb(i, c)
        )
        self.checkbox.pack()

    def set_enabled_status(self, enabled: bool):
        self.checkbox.configure(state='normal' if enabled else 'disable')


class ResultsTreeRoots:
    AllFiles = "All Files Run"
    Case1Success = "Case 1 Successful Runs"
    Case1Fail = "Case 1 Failed Runs"
    Case2Success = "Case 2 Successful Runs"
    Case2Fail = "Case 2 Failed Runs"
    AllCompared = "All Files Compared"
    BigMathDiff = "Big Math Diffs"
    SmallMathDiff = "Small Math Diffs"
    BigTableDiff = "Big Table Diffs"
    SmallTableDiff = "Small Table Diffs"
    TextDiff = "Text Diffs"

    @staticmethod
    def get_all():
        return [
            ResultsTreeRoots.AllFiles,
            ResultsTreeRoots.Case1Success,
            ResultsTreeRoots.Case1Fail,
            ResultsTreeRoots.Case2Success,
            ResultsTreeRoots.Case2Fail,
            ResultsTreeRoots.AllCompared,
            ResultsTreeRoots.BigMathDiff,
            ResultsTreeRoots.SmallMathDiff,
            ResultsTreeRoots.BigTableDiff,
            ResultsTreeRoots.SmallTableDiff,
            ResultsTreeRoots.TextDiff,
        ]


class PubSubMessageTypes:
    STATUS = '10'
    FINISHED = '20'
    CANCELLED = '30'


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
        self.build_dir_1_button = None
        self.build_dir_2_button = None
        self.run_button = None
        self.stop_button = None
        self.quit_button = None
        self.label_string = StringVar()
        self.build_dir_1_var = StringVar()
        self.build_dir_1_var.set("Select build dir 1")
        self.build_dir_2_var = StringVar()
        self.build_dir_2_var.set("Select build dir 2")
        self.progress = None
        self.log_message_listbox = None
        self.results_tree = None

        # some data holders
        self.idf_test_cases = list()
        self.tree_folders = {}
        self.build_dir_1 = None
        self.build_dir_2 = None

        # initialize the GUI
        self.init_window()

    def init_window(self):
        # changing the title of our master widget
        self.root.title("EnergyPlus Regression Tool 2")

        # create the menu
        menu = Menu(self.root)
        self.root.config(menu=menu)
        file_menu = Menu(menu)
        file_menu.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label="File", menu=file_menu)

        # main notebook holding everything
        main_notebook = ttk.Notebook(self.root)

        # run configuration
        pane_run = Frame(main_notebook)
        self.build_dir_1_button = Button(pane_run, textvariable=self.build_dir_1_var, command=self.client_build_dir_1)
        self.build_dir_1_button.pack(side=TOP, anchor=CENTER)
        self.build_dir_2_button = Button(pane_run, textvariable=self.build_dir_2_var, command=self.client_build_dir_2)
        self.build_dir_2_button.pack(side=TOP, anchor=CENTER)
        self.run_button = Button(pane_run, text="Run", command=self.client_run)
        self.run_button.pack(side=TOP, anchor=CENTER)
        self.stop_button = Button(pane_run, text="Stop", command=self.client_stop, state='disabled')
        self.stop_button.pack(side=TOP, anchor=CENTER)
        self.quit_button = Button(pane_run, text="Quit", command=self.client_exit)
        self.quit_button.pack(side=TOP, anchor=CENTER)
        main_notebook.add(pane_run, text='Run Configuration')

        # now let's set up a list of checkboxes for selecting IDFs to run
        pane_idfs = ScrollableFrame(main_notebook)
        for i in range(50):
            self.idf_test_cases.append(
                IDFTestCaseRowFrame(pane_idfs.scrollable_frame, f"File{i}", self.idf_selected_callback)
            )
            self.idf_test_cases[-1].pack()
        main_notebook.add(pane_idfs, text="IDF Selection")

        # set up a scrolled listbox for the log messages
        frame_log_messages = Frame(main_notebook)
        scrollbar = Scrollbar(frame_log_messages)
        self.log_message_listbox = Listbox(frame_log_messages, yscrollcommand=scrollbar.set)
        self.log_message_listbox.insert(END, "Program started...here are some fake messages")
        for line in range(25):
            self.log_message_listbox.insert(END, "This is line number " + str(line))
        self.log_message_listbox.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.log_message_listbox.yview)
        main_notebook.add(frame_log_messages, text="Log Messages")

        # set up a tree-view for the results
        frame_results = Frame(main_notebook)
        scrollbar = Scrollbar(frame_results)
        self.results_tree = ttk.Treeview(frame_results, columns=("Base File", "Mod File", "Diff File"))
        self.results_tree.heading("#0", text="Results", anchor=W)
        self.results_tree.heading("Base File", text="Base", anchor=W)
        self.results_tree.heading("Mod File", text="Mod", anchor=W)
        self.results_tree.heading("Diff File", text="Diff", anchor=W)
        self.build_results_tree()
        self.results_tree.pack(fill=BOTH, side=LEFT, expand=True)
        scrollbar.pack(fill=Y, side=LEFT)
        scrollbar.config(command=self.results_tree.yview)
        main_notebook.add(frame_results, text="Results")

        # pack the main notebook on the window
        main_notebook.pack(fill=BOTH, expand=1)

        # status bar at the bottom
        frame_status = Frame(self.root)
        self.progress = ttk.Progressbar(frame_status)
        self.progress.grid(column=0, row=0, sticky=E+W)
        label = Label(frame_status, textvariable=self.label_string)
        self.label_string.set("Initialized")
        label.grid(column=1, row=0, sticky=E+W)
        frame_status.pack(fill=X)

        # wire up the background thread
        pub.subscribe(self.status_handler, PubSubMessageTypes.STATUS)
        pub.subscribe(self.finished_handler, PubSubMessageTypes.FINISHED)
        pub.subscribe(self.cancelled_handler, PubSubMessageTypes.CANCELLED)

    def run(self):
        self.root.mainloop()

    def build_results_tree(self, results=None):
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

    def build_idf_list(self):
        pass

    def idf_selected_callback(self, test_case, checked):
        total = 0
        total_checked = 0
        for i in self.idf_test_cases:
            total += 1
            if i.checked.get():
                total_checked += 1
        chk_string = "Checked" if checked else "Unchecked"
        if checked:
            self.label_string.set(f"{chk_string} {test_case} ({total_checked}/{total} selected)")

    def set_gui_status_for_run(self, is_running: bool):
        if is_running:
            self.build_dir_1_button.configure(state='disabled')
            self.build_dir_2_button.configure(state='disabled')
            self.run_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            self.quit_button.configure(state='disabled')
            for idf in self.idf_test_cases:
                idf.set_enabled_status(False)
        else:
            self.build_dir_1_button.configure(state='normal')
            self.build_dir_2_button.configure(state='normal')
            self.run_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
            self.quit_button.configure(state='normal')
            for idf in self.idf_test_cases:
                idf.set_enabled_status(True)

    # -- Handling UI actions like button presses

    def client_build_dir_1(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.build_dir_1 = selected_dir
            self.build_dir_1_var.set(selected_dir)
        self.build_idf_list()

    def client_build_dir_2(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.build_dir_2 = selected_dir
            self.build_dir_2_var.set(selected_dir)
        self.build_idf_list()

    def client_run(self):
        if self.long_thread:
            messagebox.showerror("Cannot run another thread, wait for the current to finish -- how'd you get here?!?")
            return
        self.background_operator = BackgroundOperation()
        self.background_operator.get_ready_to_go(
            MyApp.status_listener, MyApp.finished_listener, MyApp.cancelled_listener
        )
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

    # -- Callbacks from the background thread coming via PyPubSub

    @staticmethod
    def status_listener(status, object_completed, percent_complete):
        """Operates on background thread, just issues a pubsub message"""
        pub.sendMessage(
            PubSubMessageTypes.STATUS, status=status,
            object_completed=object_completed, percent_complete=percent_complete)

    def status_handler(self, status, object_completed, percent_complete):
        self.log_message_listbox.insert(END, object_completed)
        self.progress['value'] = percent_complete
        self.label_string.set(f"Hey, status update: {str(status)}")

    @staticmethod
    def finished_listener(results_dict):
        """Operates on background thread, just issues a pubsub message"""
        pub.sendMessage(PubSubMessageTypes.FINISHED, results=results_dict)

    def finished_handler(self, results):
        self.log_message_listbox.insert(END, "All done, finished")
        self.label_string.set(f"Hey, all done! Results: {results['result_string']}")
        self.client_done()

    @staticmethod
    def cancelled_listener():
        """Operates on background thread, just issues a pubsub message"""
        pub.sendMessage(PubSubMessageTypes.CANCELLED)

    def cancelled_handler(self):
        self.log_message_listbox.insert(END, "Cancelled!")
        self.label_string.set("Properly cancelled!")
        self.client_done()
