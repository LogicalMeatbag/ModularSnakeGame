"""
error_handler.py
- A centralized utility for displaying error and warning messages.
- Uses a GUI popup (tkinter) when possible, with a fallback to the console.
"""
import sys
import traceback

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

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """
    A global exception hook to catch any unhandled exceptions.
    It formats the error and displays it using the GUI handler.
    This function's signature is required by sys.excepthook.
    """
    # Format the traceback into a string for the error message.
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    error_details = "".join(tb_lines)

    # Create a user-friendly message that includes the technical details.
    error_message = (
        "An unexpected error has occurred and the game must close.\n\n"
        "Please report this issue to the developer.\n\n"
        "--- Error Details ---\n"
        f"{error_details}"
    )

    # Use our existing GUI handler to show the fatal error.
    show_error_message("Unhandled Exception", error_message, isFatal=True)