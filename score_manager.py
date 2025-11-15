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

# Conditionally import the zstd module. If it fails, set a flag and move on.
# This allows the code to run on older Python versions without crashing.
try:
    import compression.zstd as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

# A secret key for our simple XOR cipher. This makes it harder for users
# to manually edit the high score file.
SECRET_KEY = b"ANAHKEN_SNAKE_GAME_KEY"

def _xor_cipher(data, key):
    """
    A simple XOR cipher function. Applying it once encrypts the data,
    and applying it a second time decrypts it.
    """
    # Use itertools.cycle to repeat the key if it's shorter than the data
    from itertools import cycle
    
    # The core of the XOR cipher: byte-by-byte XOR operation
    # between the data and the repeating key.
    return bytes([b ^ k for b, k in zip(data, cycle(key))])

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
                
                # Try to decompress if zstd was used (the first byte is a flag).
                if ZSTD_AVAILABLE and encoded_score[0] == 1:
                    processed_data = zstd.decompress(encoded_score[1:])
                else:
                    # Fallback to simple Base64 decoding
                    processed_data = base64.b64decode(encoded_score)
                
                # Decrypt the data using the XOR cipher
                decrypted_data = _xor_cipher(processed_data, SECRET_KEY)
                
                return int(decrypted_data.decode('utf-8'))
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

        # Encrypt the score data first using our custom cipher
        encrypted_data = _xor_cipher(str_score_bytes, SECRET_KEY)
        
        if ZSTD_AVAILABLE:
            # Compress the data and add a '1' byte at the start as a compression flag
            final_data = b'\x01' + zstd.compress(encrypted_data)
        else:
            # On older Python, just use Base64
            final_data = base64.b64encode(encrypted_data)

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