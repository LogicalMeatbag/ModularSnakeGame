"""
error_handler.py
- A centralized utility for displaying error and warning messages.
- Uses a custom GUI popup (tkinter) to allow copying/saving error logs.
"""
import sys
import traceback
import datetime
import os

def show_error_message(title, message, isFatal=False):
    """
    Displays an error or warning message to the user using a custom window.

    Args:
        title (str): The title for the error window.
        message (str): The main error message content.
        isFatal (bool): If True, the program will exit after showing the message.
    """
    fullMessage = f"{message}"
    
    # Try to show a GUI error
    try:
        import tkinter as tk
        from tkinter import scrolledtext, filedialog
        
        class CustomErrorWindow:
            def __init__(self, title, message, isFatal):
                self.root = tk.Tk()
                self.root.title(title)
                self.root.geometry("600x450")
                self.message = message
                self.isFatal = isFatal
                
                # Make it modal-like if possible, though for a standalone error it matters less
                self.root.attributes("-topmost", True)

                # --- UI Layout ---
                
                # 1. Header Label
                header_frame = tk.Frame(self.root, pady=10)
                header_frame.pack(fill="x")
                
                icon_label = tk.Label(header_frame, text="⚠️" if not isFatal else "❌", font=("Segoe UI", 24))
                icon_label.pack(side="left", padx=20)
                
                title_label = tk.Label(header_frame, text=title, font=("Segoe UI", 14, "bold"), wraplength=500, justify="left")
                title_label.pack(side="left", fill="x", expand=True)

                # 2. Scrollable Text Area
                text_frame = tk.Frame(self.root, padx=10, pady=5)
                text_frame.pack(fill="both", expand=True)
                
                self.text_area = scrolledtext.ScrolledText(text_frame, wrap="word", font=("Consolas", 10))
                self.text_area.pack(fill="both", expand=True)
                self.text_area.insert("1.0", message)
                self.text_area.configure(state="disabled") # Read-only, but selectable

                # 3. Button Bar
                button_frame = tk.Frame(self.root, pady=10, padx=10)
                button_frame.pack(fill="x")

                # Left side buttons (Actions)
                tk.Button(button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(side="left", padx=5)
                tk.Button(button_frame, text="Save to File...", command=self.save_to_file).pack(side="left", padx=5)

                # Right side button (Close/Exit)
                close_text = "Exit Game" if isFatal else "Close"
                tk.Button(button_frame, text=close_text, command=self.close_window, width=15).pack(side="right", padx=5)

                # Handle window close button (X)
                self.root.protocol("WM_DELETE_WINDOW", self.close_window)

                self.root.mainloop()

            def copy_to_clipboard(self):
                self.root.clipboard_clear()
                self.root.clipboard_append(self.message)
                self.root.update() # Keep clipboard after window closes

            def save_to_file(self):
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                default_filename = f"error_log_{timestamp}.txt"
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                    initialfile=default_filename,
                    title="Save Error Log"
                )
                if filepath:
                    try:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(self.message)
                    except Exception as e:
                        # If saving fails, just append to the text area (meta-error!)
                        self.text_area.configure(state="normal")
                        self.text_area.insert("end", f"\n\n[Failed to save file: {e}]")
                        self.text_area.configure(state="disabled")

            def close_window(self):
                self.root.destroy()
                if self.isFatal:
                    sys.exit(1)

        # Instantiate and run the window
        CustomErrorWindow(title, fullMessage, isFatal)

    except ImportError:
        # Fallback to console if tkinter is not available
        print(f"--- {title} ---")
        print(fullMessage)
        if not isFatal:
            input("Press Enter to continue...")
        else:
            sys.exit(1)
    except Exception as e:
        # Fallback if the GUI itself crashes
        print(f"--- {title} ---")
        print(fullMessage)
        print(f"\n[Error displaying GUI: {e}]")
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