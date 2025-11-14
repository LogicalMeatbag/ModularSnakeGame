"""
score_manager.py
- Handles all file I/O for reading and writing the high score.
- This keeps file operations separate from game logic.
- NEW: Encodes/decodes the score using Base64 to obfuscate it.
"""
import os
import settings
import base64
import error_handler
import binascii  # For error handling

# --- [NEW 3.14 FEATURE] Conditionally import the zstd module ---
# We try to import the new module. If it fails, we set a flag and move on.
# This allows the code to run on older Python versions without crashing.
try:
    import compression.zstd as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

def load_high_score(filepath):
    """
    Loads the high score from the specified file.
    NEW: Reads binary data and decodes from Base64.
    """
    if os.path.exists(filepath):
        try:
            # Open in 'rb' (read binary) mode
            with open(filepath, 'rb') as f:
                encoded_score = f.read()
                if not encoded_score:
                    return 0
                
                # --- [NEW 3.14 FEATURE] Try to decompress if zstd was used ---
                # The first byte tells us if it's compressed.
                if ZSTD_AVAILABLE and encoded_score[0] == 1:
                    decoded_score = zstd.decompress(encoded_score[1:])
                else:
                    # Fallback to simple Base64 decoding
                    decoded_score = base64.b64decode(encoded_score)
                str_score = decoded_score.decode('utf-8')
                return int(str_score)
        except (ValueError, binascii.Error, IOError, EOFError):
            # File is corrupt, empty, or unreadable.
            # We can overwrite it with 0.
            errorMessage = (
                "The high score file ('highscore.dat') was found to be corrupt or unreadable.\n\n"
                "Your high score has been reset to 0."
            )
            error_handler.show_error_message("File Warning", errorMessage)
            save_high_score(filepath, 0)
            return 0
    return 0

def save_high_score(filepath, new_high_score):
    """
    Saves the new high score to the specified file.
    NEW: Encodes to Base64 and writes as binary.
    """
    if settings.debugMode:
        print("Debug Mode is active. High score saving is disabled.")
        return # Do not save high scores in debug mode

    try:
        # Convert score to string, encode to utf-8 bytes
        str_score_bytes = str(new_high_score).encode('utf-8')
        
        # --- [NEW 3.14 FEATURE] Use zstd compression if available ---
        if ZSTD_AVAILABLE:
            # Compress the data and add a '1' byte at the start as a flag
            final_data = b'\x01' + zstd.compress(str_score_bytes)
        else:
            # On older Python, just use Base64
            final_data = base64.b64encode(str_score_bytes)
        
        # Open in 'wb' (write binary) mode
        with open(filepath, 'wb') as f:
            f.write(final_data)
    except IOError as e:
        errorMessage = (
            f"The high score could not be saved.\n\nDetails: {e}\n\n"
            "Please ensure the game has permission to write to its data folder."
        )
        error_handler.show_error_message("File Save Error", errorMessage)

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