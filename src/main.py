#!/usr/bin/env python3
"""
Main script to run the Document Version Control System.
This connects all the component files and starts the application.
"""

import tkinter as tk
from gui_components import MainApplication

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()

if __name__ == "__main__":
    main()