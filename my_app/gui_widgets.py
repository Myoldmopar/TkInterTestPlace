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
