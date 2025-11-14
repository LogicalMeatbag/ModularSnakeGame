"""
settings_manager.py
- Handles all file I/O for reading and writing the user's custom settings.
- This keeps settings file operations separate from game logic.
- Uses the JSON format for easy reading and writing of structured data.
"""
import os
import json
import error_handler

def get_settings_path(game_data_folder):
    """Constructs the path for the settings.dat file."""
    return os.path.join(game_data_folder, "settings.dat")

def save_settings(filepath, settings_data):
    """
    Saves the user's settings dictionary to the specified file as JSON.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(settings_data, f, indent=4)
    except IOError as e:
        errorMessage = (
            f"Your settings could not be saved.\n\nDetails: {e}\n\n"
            "Please ensure the game has permission to write to its data folder."
        )
        error_handler.show_error_message("File Save Error", errorMessage)

def load_settings(filepath):
    """
    Loads the user's settings from the specified JSON file.
    Returns the settings dictionary if successful, otherwise returns None.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                # Handle case where file is empty
                content = f.read()
                if not content:
                    return None
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            errorMessage = (
                "The settings file ('settings.dat') was found to be corrupt or unreadable.\n\n"
                f"Details: {e}\n\nYour settings have been reset to default."
            )
            error_handler.show_error_message("File Warning", errorMessage)
            # We return None and let the game create a new default file.
            return None
    return None

if __name__ == "__main__":
    import os
    import sys
    import subprocess
    
    # This block runs only when the script is executed directly.
    # It finds and executes the main.py file.
    print("This is a module file. Attempting to run the main game...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py_path = os.path.join(script_dir, 'main.py')
    
    # Run main.py using the same python interpreter, with the correct working directory
    subprocess.Popen([sys.executable, main_py_path], cwd=script_dir)