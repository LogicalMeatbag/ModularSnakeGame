"""
main.py
- This is the main entry point for the game.
- It performs environment checks (Python version, pygame install) first.
- It initializes the game and contains the main game loop.
- It manages the overall game state (MainMenu, Playing, GameOver).
"""
import sys
import os
import error_handler

# This will catch any error that isn't explicitly handled elsewhere
# and display it in a user-friendly GUI window before the program
# terminates. This is our safety net for all unanticipated errors.
sys.excepthook = error_handler.handle_uncaught_exception

# --- 1. Python Version Check ---
MIN_PYTHON_VERSION = (3, 8)

if sys.version_info < MIN_PYTHON_VERSION:
    current_ver = f"{sys.version_info.major}.{sys.version_info.minor}" # "3.7" # (Uncomment this to test error message)
    required_ver = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"
    
    error_message = (
        f"Python Version Error!\n\n"
        f"This game requires Python {required_ver} or newer to run.\n\n"
        f"You are currently using Python {current_ver}.\n\n"
        f"Please upgrade your Python installation to run this game."
    )
    
    error_handler.show_error_message("Python Version Error", error_message, isFatal=True)

# --- 2. Pygame Import Check ---

try:
    import pygame
    from enum import Enum
except ImportError:
    error_message = (
        "Missing Library Error!\n\n"
        "The 'pygame' library was not found on your system.\n\n"
        "To install it, open your terminal (Command Prompt) and run:\n\n"
        "pip install pygame\n\n"
        "If you have multiple Python versions, you may need to use:\n"
        "python -m pip install pygame"
    )
    
    error_handler.show_error_message("Missing Library Error", error_message, isFatal=True)
# --- If we get here, all checks passed! ---
# Now we can safely import the rest of our game modules.

import settings
import random
import settings_manager
import ui
from game_controller import GameController
import splash_screen # Import the new splash screen module
import base64
import binascii

class GameState(Enum):
    MAIN_MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    COLOR_SETTINGS = 4
    KEYBIND_SETTINGS = 5
    PAUSED = 6
    CUSTOM_COLOR_SETTINGS = 7
    EVENT_COUNTDOWN = 8
    DEBUG_SETTINGS = 9
    DYING = 10
    CONTROLLER_SETTINGS = 11
    
def update_dynamic_dimensions(window_surface):
    """
    Calculates the new BLOCK_SIZE and game area dimensions based on the
    current window size to maintain a constant grid aspect ratio.
    """
    win_w, win_h = window_surface.get_size()

    # Calculate block size based on width and height, choosing the smaller of the two
    # to ensure the whole grid fits on screen (letterboxing).
    block_w = win_w // settings.gridWidth
    block_h = win_h // settings.gridHeight
    settings.blockSize = min(block_w, block_h)

    # If block size is 0, it means the window is too small. Default to 1 to avoid errors.
    if settings.blockSize == 0:
        settings.blockSize = 1

    # Recalculate the actual game area dimensions
    settings.width = settings.gridWidth * settings.blockSize
    settings.height = settings.gridHeight * settings.blockSize

    # Calculate offsets to center the game area in the window
    settings.xOffset = (win_w - settings.width) // 2
    settings.yOffset = (win_h - settings.height) // 2

def update_snake_color_from_name(selected_color_name):
    """
    A reusable helper function to update the global snakeColor based on a name.
    Handles the logic for "Custom" vs. preset colors.
    """
    if selected_color_name == "Custom":
        # Use the saved custom color, or default to Green if none is saved
        settings.snakeColor = tuple(settings.userSettings.get("customColor", settings.colorOptions["Green"]))
    elif selected_color_name == "Rainbow":
        # For "Rainbow", we don't need to set a static color. The drawing logic
        # in game_entities.py handles this case dynamically. We can set a
        # placeholder color, but the important part is preventing the KeyError.
        settings.snakeColor = (0, 0, 0) # This color won't be used.
    else:
        settings.snakeColor = settings.colorOptions[selected_color_name]

def handle_game_update(time_since_last_move, delta_time, game_instance, active_event):
    """
    A reusable helper to handle the time-based game logic update.
    This is called from both PLAYING and EVENT_COUNTDOWN states.
    Returns the new time_since_last_move and a game_over flag.
    """
    time_since_last_move += delta_time
    move_interval = 1000 / game_instance.speed # in milliseconds
    game_over = False

    # It's possible for multiple updates to happen in a single frame on a slow machine,
    # so we use a while loop.
    while time_since_last_move >= move_interval:
        time_since_last_move -= move_interval
        if game_instance.update(active_event):
            game_over = True
            # If game is over, stop processing more moves in this frame
            break 
    
    return time_since_last_move, game_over

def check_secret_code(sequence: list[int]) -> bool:
    """
    Checks if the provided key sequence matches the secret code.
    Returns True if the code is successfully entered, False otherwise.
    """
    # This string is a Base64-encoded representation of the secret code.
    # Sequence: UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, B, A
    encoded_sequence = b'S19VUHxLX3c7S19VUHxLX3c7S19ET1dOfEtfcztLX0RPV058S19zO0tfTEVGVHxLX2E7S19SSUdIVHxLX2Q7S1fTEUZUfEtfYTtLX1JJR0hUfEtfZDtLX2I7S19hCg=='

    try:
        decoded_bytes = base64.b64decode(encoded_sequence)
        key_string = decoded_bytes.decode('utf-8')
        secret_code_steps = []
        for step_str in key_string.split(';'):
            key_names = step_str.split('|')
            keys_for_step = [getattr(pygame, name.strip()) for name in key_names]
            secret_code_steps.append(keys_for_step)
    except (binascii.Error, AttributeError, UnicodeDecodeError):
        # If the encoded string is corrupt, the code can't be entered.
        return False

    # The sequence must be the exact length of the code.
    if len(sequence) != len(secret_code_steps):
        return False

    # Iterate through the user's sequence and the valid steps.
    for i, user_key in enumerate(sequence):
        valid_keys_for_step = secret_code_steps[i]
        if user_key not in valid_keys_for_step:
            return False # Mismatch found.

    # If we get here, it's a match.
    return True

def get_controller_input_string(event):
    """Helper to convert a Pygame controller event into a consistent string format."""
    if event.type == pygame.JOYBUTTONDOWN:
        return f"button_{event.button}"
    if event.type == pygame.JOYHATMOTION:
        if event.value[0] == 1: return f"hat_{event.hat}_x_1"
        if event.value[0] == -1: return f"hat_{event.hat}_x_-1"
        if event.value[1] == 1: return f"hat_{event.hat}_y_1"
        if event.value[1] == -1: return f"hat_{event.hat}_y_-1"
    if event.type == pygame.JOYAXISMOTION:
        if event.value > settings.JOYSTICK_DEADZONE: return f"axis_{event.axis}_pos"
        if event.value < -settings.JOYSTICK_DEADZONE: return f"axis_{event.axis}_neg"
        return None
    return None

def handle_main_menu_events(event, mouse_pos, menu_buttons, start_new_game_func, sequence, selected_index):
    """Handles events for the MAIN_MENU state."""
    # This string is a Base64-encoded representation of the secret code.
    # It uses a custom format: steps are separated by ';', and alternate keys
    # for a step are separated by '|'. This is robust and supports keybinds.
    # Sequence: UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, B, A
    # NOTE: This string should be replaced with the one you manually encode.

    new_state = GameState.MAIN_MENU
    new_selected_index = selected_index
    input_str = get_controller_input_string(event)

    if event.type == pygame.KEYDOWN:
        # --- Secret Code Input ---
        # Append the new key and keep the sequence at a manageable length.
        sequence.append(event.key)
        if len(sequence) > 10: # Length of the secret code
            sequence.pop(0)

        # Check the sequence if rainbow mode isn't already unlocked.
        if not settings.rainbowModeUnlocked and check_secret_code(sequence):
            # --- SUCCESS ---
                settings.rainbowModeUnlocked = True
                settings.userSettings["rainbowModeUnlocked"] = True # Save the unlock
                settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                settings.eatSound.play() # Play a confirmation sound

        if event.key in [pygame.K_UP, pygame.K_w]:
            new_selected_index = (selected_index - 1) % 3
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            new_selected_index = (selected_index + 1) % 3
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            # Simulate a click on the selected button
            if selected_index == 0: new_state = start_new_game_func()
            elif selected_index == 1: new_state = GameState.COLOR_SETTINGS
            elif selected_index == 2: return None, -1 # Quit

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if menu_buttons['play'].collidepoint(mouse_pos):
            new_state = start_new_game_func()
        elif menu_buttons['settings'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.COLOR_SETTINGS
        elif menu_buttons['quit'].collidepoint(mouse_pos):
            return None, -1 # Signal to quit
    elif input_str:
        binds = settings.userSettings['controllerBinds']
        if input_str == binds.get('CONFIRM'):
            if new_selected_index == 0: new_state = start_new_game_func()
            elif new_selected_index == 1: new_state = GameState.COLOR_SETTINGS
            elif new_selected_index == 2: return None, -1 # Quit
        elif input_str == binds.get('UP'):
            new_selected_index = (selected_index - 1) % 3
        elif input_str == binds.get('DOWN'):
            new_selected_index = (selected_index + 1) % 3
    return new_state, new_selected_index

def handle_color_settings_events(event, mouse_pos, settings_buttons, color_names, current_color_index, selected_key):
    """Handles events for the COLOR_SETTINGS state. Returns new state and color index."""
    new_state = GameState.COLOR_SETTINGS
    new_color_index = current_color_index
    input_str = get_controller_input_string(event)
    new_selected_key = selected_key
    sound_pack_names = list(settings.soundPacks.keys())
    current_sound_pack_index = sound_pack_names.index(settings.userSettings['soundPack'])
    nav_grid = [
        ['left',              'right', 'vsync_toggle', None,      'keybinds',            None],
        ['customize_button',  None,    'dec_fps',      'inc_fps', 'controller_settings', None,],
        [None,                None,    'fps_toggle',   None,      'sound_left',          'sound_right'],
        [None,                None,    None,           None,      'debug_toggle',        None],
        [None,                None,    None,           None,      'debug_menu',          None],
        [None,                None,    'save',         'save',    None,                  None]
    ]
 
    # --- [FIX] Initialize grid position before any event handling ---
    # This ensures `current_pos` is never None when `move_in_grid` is called.
    # --- [REFACTOR] Grid-based Navigation ---
    # This 2D list represents the visual layout of the settings menu.
    # `None` is used as a placeholder for empty spots.
    # Find current position in the grid
    current_pos = None
    for r, row in enumerate(nav_grid):
        for c, item in enumerate(row):
            if item == new_selected_key:
                current_pos = [r, c]
                break
        if current_pos:
            break
    if not current_pos:
        current_pos = [0, 0] # Default to top-left if not found

    def move_in_grid(pos, dr, dc):
        """Helper to find the next valid button in the grid."""
        r, c = pos
        rows = len(nav_grid)
        cols = len(nav_grid[0])

        # If moving down from any row before the last one, and there's nothing directly below,
        # snap to the 'save' button in the middle of the last row.
        if dr == 1 and r < rows - 1:
            next_r = r + 1
            # Check if the spot directly below is empty
            if nav_grid[next_r][c] is None:
                # Find the first available 'save' button in the last row
                for save_c, item in enumerate(nav_grid[-1]):
                    if item == 'save':
                        return nav_grid[-1][save_c]

        # Original logic for all other directions
        start_c, start_r = c, r
        c, r = (c + dc) % cols, (r + dr) % rows
        while nav_grid[r][c] is None and (r, c) != (start_r, start_c):
            c, r = (c + dc) % cols, (r + dr) % rows
        return nav_grid[r][c]
        
        return new_selected_key # Fallback if something goes wrong

    def perform_action(action_key):
        nonlocal new_state, new_color_index, current_sound_pack_index
        if action_key == 'left': new_color_index = (current_color_index - 1) % len(color_names)
        elif action_key == 'right': new_color_index = (current_color_index + 1) % len(color_names)
        elif action_key == 'customize_button': new_state = GameState.CUSTOM_COLOR_SETTINGS
        elif action_key == 'vsync_toggle':
            settings.vsync = not settings.vsync
            settings.window = pygame.display.set_mode(settings.window.get_size(), pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1 if settings.vsync else 0)
        elif action_key == 'dec_fps' and not settings.vsync: settings.maxFps = max(30, settings.maxFps - 12)
        elif action_key == 'inc_fps' and not settings.vsync: settings.maxFps = min(360, settings.maxFps + 12)
        elif action_key == 'fps_toggle': settings.showFps = not settings.showFps
        elif action_key == 'keybinds': new_state = GameState.KEYBIND_SETTINGS
        elif action_key == 'controller_settings': new_state = GameState.CONTROLLER_SETTINGS
        elif action_key == 'debug_toggle': settings.debugMode = not settings.debugMode
        elif action_key == 'debug_menu': new_state = GameState.DEBUG_SETTINGS
        elif action_key == 'sound_left':
            current_sound_pack_index = (current_sound_pack_index - 1) % len(sound_pack_names)
            settings.userSettings['soundPack'] = sound_pack_names[current_sound_pack_index]
            settings.set_sound_paths(settings.userSettings['soundPack'])
            pygame.mixer.quit()
            pygame.mixer.init()
            settings.reload_sounds()
        elif action_key == 'sound_right':
            current_sound_pack_index = (current_sound_pack_index + 1) % len(sound_pack_names)
            settings.userSettings['soundPack'] = sound_pack_names[current_sound_pack_index]
            settings.set_sound_paths(settings.userSettings['soundPack'])
            pygame.mixer.quit()
            pygame.mixer.init()
            settings.reload_sounds()
        elif action_key == 'save': new_state = GameState.MAIN_MENU
        settings.buttonClickSound.play()

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RIGHT:
            new_color_index = (current_color_index + 1) % len(color_names)
        elif event.key == pygame.K_LEFT:
            new_color_index = (current_color_index - 1) % len(color_names)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            settings.userSettings["snakeColorName"] = color_names[current_color_index]
            settings_manager.save_settings(settings.settingsFile, settings.userSettings)
            perform_action('save')
    elif input_str:
        binds = settings.userSettings['controllerBinds']
        if input_str == binds.get('UP'): new_selected_key = move_in_grid(current_pos, -1, 0)
        elif input_str == binds.get('DOWN'): new_selected_key = move_in_grid(current_pos, 1, 0)
        elif input_str == binds.get('LEFT'):
            new_selected_key = move_in_grid(current_pos, 0, -1)
        elif input_str == binds.get('RIGHT'):
            new_selected_key = move_in_grid(current_pos, 0, 1)

        if input_str == binds.get('CONFIRM'):
            if new_selected_key:
                perform_action(new_selected_key)
        elif input_str == binds.get('CANCEL'):
            perform_action('save') # Treat cancel as saving and going back

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if settings_buttons['left'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_color_index = (current_color_index - 1) % len(color_names)
        elif settings_buttons['right'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_color_index = (current_color_index + 1) % len(color_names)
        elif settings_buttons.get('sound_left') and settings_buttons['sound_left'].collidepoint(mouse_pos):
            perform_action('sound_left')
        elif settings_buttons.get('sound_right') and settings_buttons['sound_right'].collidepoint(mouse_pos):
            perform_action('sound_right')
        elif settings_buttons['keybinds'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.KEYBIND_SETTINGS
        elif settings_buttons.get('controller_settings') and settings_buttons['controller_settings'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.CONTROLLER_SETTINGS
        elif settings_buttons['debug_toggle'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            settings.debugMode = not settings.debugMode
            settings.userSettings["debugMode"] = settings.debugMode
            # No need to save here, it's saved on exit.
        elif settings_buttons['fps_toggle'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            settings.showFps = not settings.showFps
        elif settings_buttons.get('vsync_toggle') and settings_buttons['vsync_toggle'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            settings.vsync = not settings.vsync
            # This setting requires re-initializing the display mode to take effect.
            current_size = settings.window.get_size()
            settings.window = pygame.display.set_mode(current_size, pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1 if settings.vsync else 0)
        elif settings_buttons['save'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            # Save all settings when leaving the menu
            settings.userSettings["snakeColorName"] = color_names[current_color_index]
            settings.userSettings["showFps"] = settings.showFps
            settings.userSettings["vsync"] = settings.vsync
            settings.userSettings["maxFps"] = settings.maxFps
            settings_manager.save_settings(settings.settingsFile, settings.userSettings)
            new_state = GameState.MAIN_MENU
        elif settings_buttons.get('customize_button') and settings_buttons['customize_button'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.CUSTOM_COLOR_SETTINGS
        # Only allow changing framerate limit if V-Sync is off
        elif not settings.vsync and settings_buttons.get('inc_fps') and settings_buttons['inc_fps'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            # Increase in steps of 12, common for refresh rates (60, 72, 120, 144, 240)
            settings.maxFps = min(360, settings.maxFps + 12)
        elif not settings.vsync and settings_buttons.get('dec_fps') and settings_buttons['dec_fps'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            settings.maxFps = max(30, settings.maxFps - 12)
        elif settings.debugMode and settings_buttons.get('debug_menu') and settings_buttons['debug_menu'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.DEBUG_SETTINGS

    if new_color_index != current_color_index:
        update_snake_color_from_name(color_names[new_color_index])

    if new_state == GameState.MAIN_MENU: # If we are exiting, save everything
        settings.userSettings["snakeColorName"] = color_names[current_color_index]
        settings.userSettings["showFps"] = settings.showFps
        settings.userSettings["vsync"] = settings.vsync
        settings.userSettings["maxFps"] = settings.maxFps
        settings.userSettings["debugMode"] = settings.debugMode
        settings.userSettings["soundPack"] = sound_pack_names[current_sound_pack_index]
        settings_manager.save_settings(settings.settingsFile, settings.userSettings)

    return new_state, new_color_index, new_selected_key

def handle_keybind_settings_events(event, mouse_pos, keybind_buttons, temp_keybinds, selected_action, selected_key):
    """Handles events for KEYBIND_SETTINGS. Returns new state and selected action."""
    new_state = GameState.KEYBIND_SETTINGS
    new_selected_action = selected_action
    new_selected_key = selected_key
    sound_pack_names = list(settings.soundPacks.keys())
    current_sound_pack_index = sound_pack_names.index(settings.userSettings['soundPack'])

    # --- Grid-based Navigation ---
    nav_grid = [
        ['UP', 'DOWN'],
        ['LEFT', 'RIGHT'],
        ['save', 'save']
    ]
    current_pos = None
    for r, row in enumerate(nav_grid):
        for c, item in enumerate(row):
            if item == selected_key:
                current_pos = [r, c]; break
        if current_pos: break
    if not current_pos: current_pos = [0, 0]

    def move_in_grid(pos, dr, dc):
        new_r, new_c = (pos[0] + dr) % len(nav_grid), (pos[1] + dc) % len(nav_grid[0])
        return nav_grid[new_r][new_c]

    input_str = get_controller_input_string(event)

    if event.type == pygame.KEYDOWN:
        if selected_action:
            temp_keybinds[selected_action][0] = event.key
            new_selected_action = None
        elif event.key == pygame.K_ESCAPE:
            new_state = GameState.COLOR_SETTINGS # Exit on escape
    elif input_str:
        binds = settings.userSettings['controllerBinds']
        if not selected_action:
            if input_str == binds.get('UP'): new_selected_key = move_in_grid(current_pos, -1, 0)
            elif input_str == binds.get('DOWN'): new_selected_key = move_in_grid(current_pos, 1, 0)
            elif input_str == binds.get('LEFT'): new_selected_key = move_in_grid(current_pos, 0, -1)
            elif input_str == binds.get('RIGHT'): new_selected_key = move_in_grid(current_pos, 0, 1)
            elif input_str == binds.get('CONFIRM'):
                if new_selected_key == 'save':
                    new_state = GameState.COLOR_SETTINGS
                else:
                    new_selected_action = new_selected_key
            elif input_str == binds.get('CANCEL'):
                new_state = GameState.COLOR_SETTINGS
        else: # An action is selected for rebinding
            if input_str == binds.get('CANCEL'):
                new_selected_action = None # Cancel rebinding
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if selected_action:
            new_selected_action = None
        else:
            for action, rect in keybind_buttons.items():
                if rect.collidepoint(mouse_pos):
                    if action == 'save':
                        settings.buttonClickSound.play()
                        settings.keybinds = temp_keybinds
                        settings.userSettings["keybinds"] = temp_keybinds
                        settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                        new_state = GameState.COLOR_SETTINGS
                    else:
                        settings.buttonClickSound.play()
                        new_selected_action = action
                    break
    
    if new_state != GameState.KEYBIND_SETTINGS: # If exiting
        settings.keybinds = temp_keybinds
        settings.userSettings["keybinds"] = temp_keybinds
        settings_manager.save_settings(settings.settingsFile, settings.userSettings)

    return new_state, new_selected_action, new_selected_key

def handle_controller_settings_events(event, mouse_pos, buttons, temp_binds, selected_action, selected_key):
    """Handles events for CONTROLLER_SETTINGS. Returns new state and selected action."""
    new_state = GameState.CONTROLLER_SETTINGS
    new_selected_action = selected_action
    input_str = get_controller_input_string(event)
    new_selected_key = selected_key
    sound_pack_names = list(settings.soundPacks.keys())
    current_sound_pack_index = sound_pack_names.index(settings.userSettings['soundPack'])

    # --- Grid-based Navigation ---
    nav_grid = [
        ['UP', 'CONFIRM'],
        ['DOWN', 'CANCEL'],
        ['LEFT', 'PAUSE'],
        ['RIGHT', 'SETTINGS'],
        ['save', 'save']
    ]
    current_pos = None
    for r, row in enumerate(nav_grid):
        for c, item in enumerate(row):
            if item == selected_key:
                current_pos = [r, c]; break
        if current_pos: break
    if not current_pos: current_pos = [0, 0]

    def move_in_grid(pos, dr, dc):
        new_r, new_c = (pos[0] + dr) % len(nav_grid), (pos[1] + dc) % len(nav_grid[0])
        return nav_grid[new_r][new_c]
    def save_and_exit():
        nonlocal new_state
        settings.userSettings['controllerBinds'] = temp_binds
        settings_manager.save_settings(settings.settingsFile, settings.userSettings)
        new_state = GameState.COLOR_SETTINGS
        settings.buttonClickSound.play()


    if selected_action:
        if input_str:
            temp_binds[selected_action] = input_str
            new_selected_action = None
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            new_selected_action = None # Cancel rebinding
    else:
        binds = settings.userSettings['controllerBinds']
        if input_str:
            if input_str == binds.get('UP'): new_selected_key = move_in_grid(current_pos, -1, 0)
            elif input_str == binds.get('DOWN'): new_selected_key = move_in_grid(current_pos, 1, 0)
            elif input_str == binds.get('LEFT'): new_selected_key = move_in_grid(current_pos, 0, -1)
            elif input_str == binds.get('RIGHT'): new_selected_key = move_in_grid(current_pos, 0, 1)
            elif input_str == binds.get('CONFIRM'):
                if new_selected_key == 'save': save_and_exit()
                else: new_selected_action = new_selected_key
            elif input_str == binds.get('CANCEL'):
                save_and_exit()

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            save_and_exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for action, rect in buttons.items():
                if rect.collidepoint(mouse_pos):
                    if action == 'save':
                        # This is the save button, not a rebindable action.
                        settings.buttonClickSound.play()
                        settings.userSettings['controllerBinds'] = temp_binds
                        save_and_exit()
                    else:
                        settings.buttonClickSound.play()
                        new_selected_action = action
                    break
    return new_state, new_selected_action, new_selected_key

def handle_custom_color_settings_events(event, mouse_pos, custom_color_buttons, temp_custom_color, editing_comp, input_str):
    """Handles events for CUSTOM_COLOR_SETTINGS. Returns state, editing component, and input string."""
    new_state = GameState.CUSTOM_COLOR_SETTINGS
    new_editing_comp = editing_comp
    new_input_str = input_str
    held_button_action = None

    if editing_comp:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                try:
                    value = int(input_str)
                    component_index = ['R', 'G', 'B'].index(editing_comp)
                    temp_custom_color[component_index] = max(0, min(255, value))
                except ValueError: pass
                new_editing_comp = None
            elif event.key == pygame.K_ESCAPE:
                new_editing_comp = None
            elif event.key == pygame.K_BACKSPACE:
                new_input_str = input_str[:-1]
            elif event.unicode.isdigit():
                new_input_str += event.unicode
    else:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_on_button = False
            for button, rect in custom_color_buttons.items():
                if rect.collidepoint(mouse_pos):
                    clicked_on_button = True
                    settings.buttonClickSound.play()
                    if button.startswith('inc_') or button.startswith('dec_'):
                        held_button_action = button
                    elif button.startswith('edit_'):
                        new_editing_comp = button.split('_')[1]
                        component_index = ['R', 'G', 'B'].index(new_editing_comp)
                        new_input_str = str(temp_custom_color[component_index])
                    elif button == 'apply':
                        settings.userSettings["customColor"] = temp_custom_color
                        settings.userSettings["snakeColorName"] = "Custom"
                        settings.snakeColor = tuple(temp_custom_color)
                        settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                        new_state = GameState.COLOR_SETTINGS
                    elif button == 'back':
                        new_state = GameState.COLOR_SETTINGS
                    break
            if not clicked_on_button:
                new_editing_comp = None
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            new_state = GameState.COLOR_SETTINGS

    return new_state, new_editing_comp, new_input_str, held_button_action

def handle_debug_settings_events(event, mouse_pos, debug_buttons, temp_debug_settings):
    """Handles events for the DEBUG_SETTINGS state."""
    new_state = GameState.DEBUG_SETTINGS
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for button, rect in debug_buttons.items():
            if rect.collidepoint(mouse_pos):
                settings.buttonClickSound.play()
                if button.startswith('show'):
                    temp_debug_settings[button] = not temp_debug_settings[button]
                elif button.startswith('inc_chance_'):
                    temp_debug_settings['eventChancesOverride'][button.replace('inc_chance_', '')] += 1
                elif button.startswith('dec_chance_'):
                    temp_debug_settings['eventChancesOverride'][button.replace('dec_chance_', '')] = max(0, temp_debug_settings['eventChancesOverride'][button.replace('dec_chance_', '')] - 1)
                elif button.startswith('inc_'): # General increment
                    key = button.replace('inc_', '')
                    # Use a larger step for timer values for convenience
                    step = 5 if 'Timer' in key or 'Duration' in key else 1
                    temp_debug_settings[key] += step
                elif button.startswith('dec_'): # General decrement
                    key = button.replace('dec_', '')
                    step = 5 if 'Timer' in key or 'Duration' in key else 1
                    temp_debug_settings[key] = max(1, temp_debug_settings[key] - step)
                elif button == 'back':
                    new_state = GameState.COLOR_SETTINGS
                break
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        new_state = GameState.COLOR_SETTINGS
    
    if new_state != GameState.DEBUG_SETTINGS:
        settings.debugSettings = temp_debug_settings.copy()
        settings.userSettings["debugSettings"] = settings.debugSettings
        settings_manager.save_settings(settings.settingsFile, settings.userSettings)
        
    return new_state

def main():
    # The game controller manages the actual game session
    game = GameController()

    def start_new_game():
        """Resets all game-specific state to start a fresh game."""
        nonlocal active_event, last_event, event_timer, notification_end_time, countdown_seconds_left, time_since_last_move
        
        # Reset the core game controller (snake, food, score, speed)
        game.reset()
        
        # Reset all event-related variables to their initial states
        active_event = None
        last_event = None
        event_timer = 0
        notification_end_time = 0
        countdown_seconds_left = 0

        time_since_last_move = 0
        
        # Set the game state to playing
        return GameState.PLAYING
    
    # --- Game State & Loop Variables ---
    current_state = GameState.MAIN_MENU
    running = True

    # --- Controller Initialization ---
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

    # --- Easter Egg State ---
    code_sequence = []

    color_names = list(settings.colorOptions.keys()) + ["Custom"]
    if settings.rainbowModeUnlocked:
        color_names.append("Rainbow")
        
    current_color_index = color_names.index(settings.userSettings.get("snakeColorName", settings.defaultSettings["snakeColorName"]))

    # Start with the saved custom color or the default snake color
    initial_custom_color = settings.userSettings.get("customColor", list(settings.snakeColor))
    temp_custom_color = list(initial_custom_color) # Work on a copy

    # Work on a temporary copy
    temp_debug_settings = settings.debugSettings.copy()


    # Work on a temporary copy of the keybinds
    temp_keybinds = {k: list(v) for k, v in settings.keybinds.items()}
    selected_action_to_rebind = None # e.g., 'UP', 'DOWN', None

    heldButton = None
    heldButtonStartTime = 0

    deathAnimationStartTime = 0
    deathSoundHasPlayed = False
    heldButtonLastTick = 0
    INITIAL_HOLD_DELAY = 400
    REPEATED_HOLD_DELAY = 40

    editingColorComponent = None # 'R', 'G', 'B', or None
    rgbInputString = ""

    event_list = [
        "Apples Galore", "Golden Apple Rain", "BEEEG Snake", 
        "Small Snake", "Racecar Snake", "Slow Snake"
    ]
    active_event = None
    last_event = None # Store the previously completed event
    event_start_time = 0
    event_timer = 0 # Counts up to trigger a new event
    notification_end_time = 0 # For showing the event name text
    countdown_seconds_left = 0 # For showing the pre-event countdown
    
    time_since_last_move = 0
    delta_time = 0

    pause_start_time = 0 # To track duration of pause
    update_dynamic_dimensions(settings.window)

    # --- UI Button State ---
    # Initialize all button dictionaries to empty dicts before the loop.
    # This prevents an UnboundLocalError on the first frame.
    selected_main_menu_index = 0
    menu_buttons = {}
    selected_settings_key = 'left' # Default selection for settings menu
    # --- [NEW] State for timed joystick menu navigation ---
    joystick_axis_states = {} # Tracks timers for each axis
    JOYSTICK_INITIAL_DELAY = 300 # ms before repeat starts
    JOYSTICK_REPEAT_DELAY = 150  # ms between repeats

    joystickAxisActiveY = False # State tracker for analog stick menu navigation
    settings_buttons = {}
    splash_screen.show()

    keybind_buttons = {}
    controller_settings_buttons = {}
    custom_color_buttons = {}
    debug_settings_buttons = {}
    game_over_buttons = {}
    selected_game_over_index = 0

    while running:

        # --- Event Handler ---
        # Handle events based on the current game state
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                heldButton = None # Stop holding on any mouse up event

            if event.type == pygame.VIDEORESIZE:
                # Recreate the window surface with the new size
                settings.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                # Recalculate all dynamic sizes and offsets
                update_dynamic_dimensions(settings.window)
                # Force entities to update their internal scaling on the next frame.
                game.snake.last_block_size = -1
                game.food.last_block_size = -1

            # --- Get mouse position once per frame ---
            mouse_pos = pygame.mouse.get_pos()

            # --- State-based Event Handling ---
            if current_state == GameState.MAIN_MENU:
                new_state, selected_main_menu_index = handle_main_menu_events(event, mouse_pos, menu_buttons, start_new_game, code_sequence, selected_main_menu_index)
                if new_state is None:
                    running = False
                else:
                    current_state = new_state                    

            elif current_state == GameState.COLOR_SETTINGS:
                current_state, current_color_index, selected_settings_key = handle_color_settings_events(event, mouse_pos, settings_buttons, color_names, current_color_index, selected_settings_key)
                if current_state == GameState.KEYBIND_SETTINGS:
                    selected_action_to_rebind = None # Reset on entering menu

            elif current_state == GameState.KEYBIND_SETTINGS:
                current_state, selected_action_to_rebind, selected_settings_key = handle_keybind_settings_events(event, mouse_pos, keybind_buttons, temp_keybinds, selected_action_to_rebind, selected_settings_key)

            elif current_state == GameState.CONTROLLER_SETTINGS:
                current_state, selected_action_to_rebind, selected_settings_key = handle_controller_settings_events(event, mouse_pos, controller_settings_buttons, settings.userSettings['controllerBinds'], selected_action_to_rebind, selected_settings_key)
                if current_state != GameState.CONTROLLER_SETTINGS:
                    selected_action_to_rebind = None # Reset on exit

            elif current_state == GameState.CUSTOM_COLOR_SETTINGS:
                new_state, new_edit_comp, new_input_str, held_action = handle_custom_color_settings_events(event, mouse_pos, custom_color_buttons, temp_custom_color, editingColorComponent, rgbInputString)
                current_state, editingColorComponent, rgbInputString = new_state, new_edit_comp, new_input_str
                if held_action:
                    heldButton = held_action
                    heldButtonStartTime = pygame.time.get_ticks()
                    heldButtonLastTick = heldButtonStartTime
                    # Perform initial click action
                    component = heldButton.split('_')[1]
                    component_index = ['R', 'G', 'B'].index(component)
                    amount = 5 if heldButton.startswith('inc_') else -5
                    temp_custom_color[component_index] = max(0, min(255, temp_custom_color[component_index] + amount))
                if current_state == GameState.COLOR_SETTINGS: # If we are leaving the menu
                    temp_custom_color = list(settings.userSettings.get("customColor", list(settings.snakeColor))) # Reset temp color

            elif current_state == GameState.DEBUG_SETTINGS:
                current_state = handle_debug_settings_events(event, mouse_pos, debug_settings_buttons, temp_debug_settings)
            
            elif current_state == GameState.PLAYING:
                # Pass game-related inputs to the controller
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    pause_start_time = pygame.time.get_ticks()
                    current_state = GameState.PAUSED
                elif get_controller_input_string(event) == settings.userSettings['controllerBinds'].get('PAUSE'):
                    pause_start_time = pygame.time.get_ticks()
                    current_state = GameState.PAUSED

            elif current_state == GameState.EVENT_COUNTDOWN: # Also allow pausing during countdown
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    current_state = GameState.PAUSED
                elif event.type == pygame.JOYBUTTONDOWN and event.button == 7: # 'Start' button
                    current_state = GameState.PAUSED
            
            elif current_state == GameState.EVENT_COUNTDOWN: # Also allow pausing during countdown
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    current_state = GameState.PAUSED            
            elif current_state == GameState.PAUSED:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    pause_duration = pygame.time.get_ticks() - pause_start_time
                    if active_event:
                        event_start_time += pause_duration
                        notification_end_time += pause_duration
                    current_state = GameState.PLAYING if not active_event else GameState.EVENT_COUNTDOWN
                elif get_controller_input_string(event) == settings.userSettings['controllerBinds'].get('PAUSE'):
                    # Same logic as keyboard unpause
                    current_state = GameState.PLAYING
            
            elif current_state == GameState.GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        selected_game_over_index = (selected_game_over_index - 1) % 2
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        selected_game_over_index = (selected_game_over_index + 1) % 2
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if selected_game_over_index == 0: current_state = start_new_game()
                        elif selected_game_over_index == 1: current_state = GameState.MAIN_MENU
                elif get_controller_input_string(event):
                    input_str = get_controller_input_string(event)
                    binds = settings.userSettings['controllerBinds']
                    if input_str == binds.get('CONFIRM'):
                        if selected_game_over_index == 0: current_state = start_new_game()
                        elif selected_game_over_index == 1: current_state = GameState.MAIN_MENU
                    elif input_str == binds.get('UP'):
                        selected_game_over_index = (selected_game_over_index - 1) % 2
                    elif input_str == binds.get('DOWN'):
                        selected_game_over_index = (selected_game_over_index + 1) % 2
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if game_over_buttons['restart'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_state = start_new_game()
                    elif game_over_buttons['mainMenu'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_state = GameState.MAIN_MENU

        # --- Game Logic & Drawing ---
        
        # Clear the screen
        settings.window.fill(settings.borderColor)
        # Draw the game area background on top, creating the letterbox effect.
        # This guarantees the background aligns perfectly with the grid.
        game_area_rect = pygame.Rect(
            int(settings.xOffset), int(settings.yOffset), int(settings.width), int(settings.height)
        )
        pygame.draw.rect(settings.window, settings.backgroundColor, game_area_rect)

        # Rebuild the list of color names every frame to immediately reflect unlocks.
        color_names = list(settings.colorOptions.keys()) + ["Custom"]
        if settings.rainbowModeUnlocked:
            color_names.append("Rainbow")

        # --- Handle Dynamic Colors ---
        # If Rainbow is selected, we need to update the global snakeColor on every
        # frame to create the cycling effect for all UI elements.
        if color_names[current_color_index] == "Rainbow":
            hue = (pygame.time.get_ticks() / 20) % 360
            rainbow_color = pygame.Color(0)
            rainbow_color.hsva = (hue, 100, 100, 100)
            settings.snakeColor = rainbow_color

        if current_state == GameState.MAIN_MENU:
            menu_buttons = ui.draw_main_menu(settings.window, selected_main_menu_index)
        
        elif current_state == GameState.COLOR_SETTINGS:
            sound_pack_names = list(settings.soundPacks.keys())
            current_sound_pack_name = sound_pack_names[sound_pack_names.index(settings.userSettings['soundPack'])]
            settings_buttons = ui.draw_settings_menu(settings.window, color_names[current_color_index], current_sound_pack_name, selected_settings_key)

        elif current_state == GameState.DEBUG_SETTINGS:
            debug_settings_buttons = ui.draw_debug_settings_menu(settings.window, temp_debug_settings)

        elif current_state == GameState.KEYBIND_SETTINGS:
            keybind_buttons = ui.draw_keybind_settings_menu(settings.window, temp_keybinds, selected_action_to_rebind, selected_settings_key)

        elif current_state == GameState.CONTROLLER_SETTINGS:
            controller_settings_buttons = ui.draw_controller_settings_menu(settings.window, settings.userSettings['controllerBinds'], selected_action_to_rebind, selected_key=selected_settings_key)

        elif current_state == GameState.CUSTOM_COLOR_SETTINGS:
            if heldButton:
                currentTime = pygame.time.get_ticks()
                if currentTime - heldButtonStartTime > INITIAL_HOLD_DELAY:
                    if currentTime - heldButtonLastTick > REPEATED_HOLD_DELAY:
                        heldButtonLastTick = currentTime
                        component = heldButton.split('_')[1]
                        component_index = ['R', 'G', 'B'].index(component)
                        amount = 5 if heldButton.startswith('inc_') else -5
                        temp_custom_color[component_index] = max(0, min(255, temp_custom_color[component_index] + amount))

            custom_color_buttons = ui.draw_custom_color_menu(
                settings.window, 
                temp_custom_color, 
                editing_component=editingColorComponent, 
                input_string=rgbInputString
            )

        elif current_state == GameState.PLAYING:
            # The game.update() method now handles all game logic
            time_since_last_move, is_game_over = handle_game_update(time_since_last_move, delta_time, game, active_event)
            if is_game_over:
                game.save_score_if_high()
                # Instead of ending instantly, start the death animation.
                current_state = GameState.DYING
                deathAnimationStartTime = pygame.time.get_ticks()
                deathSoundHasPlayed = False
            
            # Drawing is independent of logic updates and will run at the monitor's refresh rate.
            if current_state == GameState.PLAYING:
                game.draw(settings.window)
            
            # Draw revert countdown separately from the notification to ensure it lasts for the full event duration.
            if active_event in ["BEEEG Snake", "Small Snake", "Racecar Snake", "Slow Snake"]:
                duration = (settings.debugSettings['eventDurationOverride'] * 1000) if settings.debugMode else settings.EVENT_DURATION
                time_left = (event_start_time + duration - pygame.time.get_ticks()) / 1000
                if time_left > 0:
                    ui.draw_revert_countdown(settings.window, int(time_left) + 1)

        elif current_state == GameState.EVENT_COUNTDOWN:
            time_since_last_move, is_game_over = handle_game_update(time_since_last_move, delta_time, game, active_event)
            if is_game_over: # It's possible to die during the countdown
                game.save_score_if_high()
                current_state = GameState.DYING
                deathAnimationStartTime = pygame.time.get_ticks()
                deathSoundHasPlayed = False
            
            # Drawing is independent
            game.draw(settings.window) # Keep drawing the game

            current_time = pygame.time.get_ticks()
            time_since_start = current_time - event_start_time
            
            countdown_duration = (settings.debugSettings['eventCountdownDurationOverride'] * 1000) if settings.debugMode else settings.EVENT_COUNTDOWN_DURATION
            if time_since_start >= countdown_duration:
                # Countdown finished! Trigger the actual event.
                current_state = GameState.PLAYING
                
                weights_source = settings.debugSettings['eventChancesOverride'] if settings.debugMode else settings.DEFAULT_EVENT_WEIGHTS

                # Filter out the last event to prevent repeats
                possible_events = []
                weights = []
                for event, weight in weights_source.items():
                    if event != last_event:
                        possible_events.append(event)
                        weights.append(weight)

                # random.choices returns a list, so we take the first element.
                # It can handle an empty list, in which case it returns an empty list.
                chosen_event = random.choices(possible_events, weights=weights, k=1)
                active_event = chosen_event[0] if chosen_event else None
                game.start_event(active_event)
                event_start_time = pygame.time.get_ticks() # Reset timer for the event's duration
                notification_end_time = event_start_time + settings.EVENT_NOTIFICATION_DURATION
            else:
                # Draw the countdown UI
                seconds_left = (countdown_duration - time_since_start) / 1000
                ui.draw_event_countdown(settings.window, int(seconds_left) + 1)

        elif current_state == GameState.PAUSED:
            # First, draw the underlying game screen so it's visible.
            game.draw(settings.window)
            pause_font = pygame.font.SysFont(None, 80)
            if active_event:
                event_start_time += pygame.time.get_ticks() - pause_start_time
            pause_surface = pause_font.render("PAUSED", True, settings.white)
            pause_rect = pause_surface.get_rect(center=(settings.window.get_width() / 2, settings.window.get_height() / 2))
            settings.window.blit(pause_surface, pause_rect)

        elif current_state == GameState.DYING:
            timeSinceDeath = pygame.time.get_ticks() - deathAnimationStartTime
            fade_progress = None

            # After the initial pause, start the sound and the fade-out animation.
            if timeSinceDeath > settings.DEATH_ANIMATION_INITIAL_PAUSE:
                if not deathSoundHasPlayed:
                    settings.gameOverSound.play()
                    deathSoundHasPlayed = True
                
                # The fade_progress is now just the time since the animation began.
                fade_progress = timeSinceDeath - settings.DEATH_ANIMATION_INITIAL_PAUSE

            # Draw the snake, passing the fade progress to it.
            game.draw(settings.window, isDying=True, fadeProgress=fade_progress)
            
            # Transition to the game over screen once the animation is complete.
            # The animation is complete when the fade duration has passed.
            if fade_progress is not None and fade_progress >= settings.DEATH_FADE_OUT_DURATION:
                current_state = GameState.GAME_OVER

        # --- Event Management (runs continuously during gameplay) ---
        if current_state in [GameState.PLAYING, GameState.EVENT_COUNTDOWN]:
            current_time = pygame.time.get_ticks()

            # 1. Check if an active event has expired.
            if active_event:
                duration = (settings.debugSettings['eventDurationOverride'] * 1000) if settings.debugMode else settings.EVENT_DURATION
                is_food_event = game.is_food_event_active(active_event)
                if not is_food_event and current_time > event_start_time + duration:
                    game.stop_event(active_event)
                    last_event, active_event = active_event, None
                elif is_food_event and not game.food.items:
                    game.stop_event(active_event)
                    last_event, active_event = active_event, None

            # 2. If no event is active, count up the main event timer.
            if not active_event and current_state != GameState.EVENT_COUNTDOWN:
                timer_max = (settings.debugSettings['eventTimerMaxOverride'] * 1000) if settings.debugMode else settings.EVENT_TIMER_MAX
                if event_timer < timer_max:
                    event_timer += delta_time
                else:
                    event_timer = 0
                    chance = settings.debugSettings['eventChanceOverride'] if settings.debugMode else settings.EVENT_CHANCE
                    if random.randint(1, 100) <= chance:
                        current_state = GameState.EVENT_COUNTDOWN
                        event_start_time = current_time

            # 3. Handle drawing UI notifications.
            if current_time < notification_end_time:
                if active_event:
                    ui.draw_event_notification(settings.window, active_event)
            
            if active_event in ["BEEEG Snake", "Small Snake", "Racecar Snake", "Slow Snake"]:
                duration = (settings.debugSettings['eventDurationOverride'] * 1000) if settings.debugMode else settings.EVENT_DURATION
                time_left = (event_start_time + duration - current_time) / 1000
                if time_left > 0: ui.draw_revert_countdown(settings.window, int(time_left) + 1)

        elif current_state == GameState.GAME_OVER:
            # Pass the final score and high score to the UI function
            game_over_buttons = ui.draw_game_over_screen(settings.window, game.score, game.high_score, selected_game_over_index)

        if settings.debugMode and current_state != GameState.DEBUG_SETTINGS:
            event_time_left = 0
            if active_event:
                duration = (settings.debugSettings['eventDurationOverride'] * 1000) if settings.debugMode else settings.EVENT_DURATION
                event_time_left = (event_start_time + duration - pygame.time.get_ticks()) / 1000

            all_debug_info = {
                "State": (settings.debugSettings['showState'], current_state.name),
                "Snake Pos": (settings.debugSettings['showSnakePos'], str(game.snake.pos)),
                "Snake Len": (settings.debugSettings['showSnakeLen'], len(game.snake.body)),
                "Speed": (settings.debugSettings['showSpeed'], f"{game.speed:.1f}"),
                "Normal Speed": (settings.debugSettings['showNormalSpeed'], f"{game.normalSpeed:.1f}"),"Event Timer": (settings.debugSettings['showEventTimer'], 
                f"{((settings.debugSettings['eventTimerMaxOverride'] * 1000 if settings.debugMode else settings.EVENT_TIMER_MAX) - event_timer) / 1000:.1f}s"),
                "Active Event": (settings.debugSettings['showActiveEvent'], active_event),
                "Event Time Left": (settings.debugSettings['showEventTimeLeft'], f"{event_time_left:.1f}s"),
                "Size Event Active": (settings.debugSettings['showSizeEventActive'], game.snake.is_size_event_active),
                "Pre-Event Len": (settings.debugSettings['showPreEventLen'], game.snake.pre_event_length),
            }

            visible_debug_info = {}
            visible_debug_info["High Score Saving"] = "DISABLED"
            for key, (is_visible, value) in all_debug_info.items():
                if is_visible:
                    visible_debug_info[key] = value
            ui.draw_debug_overlay(settings.window, visible_debug_info)

        # The FPS counter is now completely independent of the debug overlay.
        # It is drawn after all other UI so it appears on top.
        if settings.showFps:
            ui.draw_fps_counter(settings.window, settings.clock.get_fps())

        # --- Finalize Frame ---
        # This is the crucial step that makes everything drawn in the loop
        # actually appear on the screen.
        pygame.display.update()
        # clock.tick() returns milliseconds since the last frame.
        # We pass maxFps to cap the framerate if vsync is not honored by the driver.
        delta_time = settings.clock.tick(settings.maxFps)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()