"""
score_manager.py
- Handles all file I/O for reading and writing the high score.
- This keeps file operations separate from game logic.
- NEW: Encodes/decodes the score using Base64 to obfuscate it.
"""
import os
import base64
import binascii  # For error handling

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
                
                # Decode the Base64 data
                str_score = base64.b64decode(encoded_score).decode('utf-8')
                return int(str_score)
        except (ValueError, binascii.Error, IOError, EOFError):
            # File is corrupt, empty, or unreadable.
            # We can overwrite it with 0.
            save_high_score(filepath, 0)
            return 0
    return 0

def save_high_score(filepath, new_high_score):
    """
    Saves the new high score to the specified file.
    NEW: Encodes to Base64 and writes as binary.
    """
    try:
        # Convert score to string, encode to utf-8 bytes
        str_score_bytes = str(new_high_score).encode('utf-8')
        
        # Encode those bytes into Base64
        encoded_score = base64.b64encode(str_score_bytes)
        
        # Open in 'wb' (write binary) mode
        with open(filepath, 'wb') as f:
            f.write(encoded_score)
    except IOError as e:
        print(f"Warning: Unable to save high score file. Error: {e}")

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