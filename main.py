#!/usr/bin/env python3

# main entry point into my_app, for either command line operation or gui operation
# if no command line args are given, it is gui operation
# but don't try to import any Tk/Gui stuff unless we are doing GUI operation

from sys import argv

if len(argv) == 1:  # GUI
    from my_app.gui import MyApp
    app = MyApp()
    app.run()
else:  # Non-GUI operation, execute some command
    ...
