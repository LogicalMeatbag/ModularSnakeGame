"""
error_handler.py
- A centralized utility for displaying error and warning messages.
- Uses a GUI popup (tkinter) when possible, with a fallback to the console.
"""
import sys

def show_error_message(title, message, isFatal=False):
    """
    Displays an error or warning message to the user.

    Args:
        title (str): The title for the error window.
        message (str): The main error message content.
        isFatal (bool): If True, the program will exit after showing the message.
    """
    fullMessage = f"{message}"
    
    # Try to show a GUI error
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw() # Hide the main tkinter window
        messagebox.showerror(title, fullMessage)
    except ImportError:
        # Fallback to console if tkinter is not available
        print(f"--- {title} ---")
        print(fullMessage)
        if not isFatal:
            input("Press Enter to continue...")

    if isFatal:
        sys.exit(1)