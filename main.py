#!/usr/bin/env python3

# main entry point into my_app, for either command line operation or gui operation
# if no command line args are given, it is gui operation
# but don't try to import any Tk/Gui stuff unless we are doing GUI operation

from sys import argv

if len(argv) == 1:  # GUI
    from tkinter import Tk
    from my_app.gui import Window
    root = Tk()
    root.geometry("400x300")
    root.option_add('*tearOff', False)  # keeps file menus from looking weird
    app = Window(root)
    root.mainloop()
else:  # Non-GUI operation, execute some command
    ...
