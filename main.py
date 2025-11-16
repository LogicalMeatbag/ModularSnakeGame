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
# We check for a minimum version, not a specific one.
# 3.8 is a safe, modern minimum.
MIN_PYTHON_VERSION = (3, 8)

if sys.version_info < MIN_PYTHON_VERSION:
    current_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
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
import base64

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

def handle_main_menu_events(event, mouse_pos, menu_buttons, start_new_game_func, sequence):
    """Handles events for the MAIN_MENU state."""
    # This string is a Base64-encoded representation of the secret code.
    # It uses a custom format: steps are separated by ';', and alternate keys
    # for a step are separated by '|'. This is robust and supports keybinds.
    # Sequence: UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, B, A
    # NOTE: This string should be replaced with the one you manually encode.
    encoded_sequence = b'S19VUHxLX3c7S19VUHxLX3c7S19ET1dOfEtfcztLX0RPV058S19zO0tfTEVGVHxLX2E7S19SSUdIVHxLX2Q7S19MRUZUfEtfYTtLX1JJR0hUfEtfZDtLX2I7S19hCg=='

    # Decode the string and parse it into a list of lists of key codes.
    decoded_bytes = base64.b64decode(encoded_sequence)
    key_string = decoded_bytes.decode('utf-8')
    secret_code_steps = []
    for step_str in key_string.split(';'):
        # Use getattr to convert the string name (e.g., "K_UP") into the actual pygame constant.
        key_names = step_str.split('|')
        # Use .strip() on each name to remove any accidental whitespace or newlines.
        # This makes the parsing much more robust.
        keys_for_step = [getattr(pygame, name.strip()) for name in key_names]
        secret_code_steps.append(keys_for_step)

    if event.type == pygame.KEYDOWN:
        # --- Secret Code Logic ---
        # Keep track of the last N key presses, where N is the length of the code.
        sequence.append(event.key)
        if len(sequence) > len(secret_code_steps):
            sequence.pop(0)

        # If the sequence is the correct length, check it for a match.
        if len(sequence) == len(secret_code_steps):
            is_match = True
            # Iterate through the user's sequence and the valid steps.
            for i in range(len(secret_code_steps)):
                user_key = sequence[i]
                valid_keys_for_step = secret_code_steps[i]
                if user_key not in valid_keys_for_step:
                    is_match = False
                    break # Mismatch found, no need to check further.
            
            if is_match and not settings.rainbowModeUnlocked:
            # --- SUCCESS ---
                settings.rainbowModeUnlocked = True
                settings.userSettings["rainbowModeUnlocked"] = True # Save the unlock
                settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                settings.eatSound.play() # Play a confirmation sound

        if event.key == pygame.K_RETURN:
            return start_new_game_func()
        elif event.key == pygame.K_s:
            return GameState.COLOR_SETTINGS
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if menu_buttons['play'].collidepoint(mouse_pos):
            return start_new_game_func()
        elif menu_buttons['settings'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            return GameState.COLOR_SETTINGS
        elif menu_buttons['quit'].collidepoint(mouse_pos):
            return None # Signal to quit
    return GameState.MAIN_MENU # No state change

def handle_color_settings_events(event, mouse_pos, settings_buttons, color_names, current_color_index):
    """Handles events for the COLOR_SETTINGS state. Returns new state and color index."""
    new_state = GameState.COLOR_SETTINGS
    new_color_index = current_color_index

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RIGHT:
            new_color_index = (current_color_index + 1) % len(color_names)
        elif event.key == pygame.K_LEFT:
            new_color_index = (current_color_index - 1) % len(color_names)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            settings.userSettings["snakeColorName"] = color_names[current_color_index]
            settings_manager.save_settings(settings.settingsFile, settings.userSettings)
            new_state = GameState.MAIN_MENU
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if settings_buttons['left'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_color_index = (current_color_index - 1) % len(color_names)
        elif settings_buttons['right'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_color_index = (current_color_index + 1) % len(color_names)
        elif settings_buttons['keybinds'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.KEYBIND_SETTINGS
        elif settings_buttons['debug_toggle'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            settings.debugMode = not settings.debugMode
            settings.userSettings["debugMode"] = settings.debugMode
        elif settings_buttons['fps_toggle'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            settings.showFps = not settings.showFps
            settings.userSettings["showFps"] = settings.showFps
        elif settings_buttons['save'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            settings.userSettings["snakeColorName"] = color_names[current_color_index]
            settings_manager.save_settings(settings.settingsFile, settings.userSettings)
            new_state = GameState.MAIN_MENU
        # [REFACTOR] Check for a dedicated 'customize' button instead of clicking the text.
        elif settings_buttons.get('customize_button') and settings_buttons['customize_button'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.CUSTOM_COLOR_SETTINGS
        elif settings.debugMode and settings_buttons.get('debug_menu') and settings_buttons['debug_menu'].collidepoint(mouse_pos):
            settings.buttonClickSound.play()
            new_state = GameState.DEBUG_SETTINGS

    if new_color_index != current_color_index:
        update_snake_color_from_name(color_names[new_color_index])

    return new_state, new_color_index

def handle_keybind_settings_events(event, mouse_pos, keybind_buttons, temp_keybinds, selected_action):
    """Handles events for KEYBIND_SETTINGS. Returns new state and selected action."""
    new_state = GameState.KEYBIND_SETTINGS
    new_selected_action = selected_action

    if event.type == pygame.KEYDOWN:
        if selected_action:
            temp_keybinds[selected_action][0] = event.key
            new_selected_action = None
        elif event.key == pygame.K_ESCAPE:
            new_state = GameState.COLOR_SETTINGS
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
    return new_state, new_selected_action

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
                elif button.startswith('inc_'):
                    key = button[4:]
                    temp_debug_settings[key] += 1
                elif button.startswith('dec_'):
                    key = button[4:]
                    temp_debug_settings[key] = max(1, temp_debug_settings[key] - 1)
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

    # --- [NEW] State for custom color menu interactions ---
    heldButton = None
    heldButtonStartTime = 0

    # --- [NEW] State for the death animation ---
    deathAnimationStartTime = 0
    deathSoundHasPlayed = False
    deathStaggerDelay = 0 # Will be calculated dynamically
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
    menu_buttons = {}
    settings_buttons = {}
    keybind_buttons = {}
    custom_color_buttons = {}
    debug_settings_buttons = {}
    game_over_buttons = {}

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
                new_state = handle_main_menu_events(event, mouse_pos, menu_buttons, start_new_game, code_sequence)
                if new_state is None:
                    running = False
                else:
                    current_state = new_state

            elif current_state == GameState.COLOR_SETTINGS:
                current_state, current_color_index = handle_color_settings_events(event, mouse_pos, settings_buttons, color_names, current_color_index)
                if current_state == GameState.KEYBIND_SETTINGS:
                    selected_action_to_rebind = None # Reset on entering menu

            elif current_state == GameState.KEYBIND_SETTINGS:
                current_state, selected_action_to_rebind = handle_keybind_settings_events(event, mouse_pos, keybind_buttons, temp_keybinds, selected_action_to_rebind)

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
                    pause_start_time = pygame.time.get_ticks() # Record when pause starts
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
                    current_state = GameState.PLAYING
            
            elif current_state == GameState.GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    if event.key == pygame.K_r:
                        current_state = start_new_game()
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
            menu_buttons = ui.draw_main_menu(settings.window)
        
        elif current_state == GameState.COLOR_SETTINGS:
            settings_buttons = ui.draw_settings_menu(settings.window, color_names[current_color_index]) # Returns dict of buttons

        elif current_state == GameState.DEBUG_SETTINGS:
            debug_settings_buttons = ui.draw_debug_settings_menu(settings.window, temp_debug_settings)

        elif current_state == GameState.KEYBIND_SETTINGS:
            keybind_buttons = ui.draw_keybind_settings_menu(settings.window, temp_keybinds, selected_action_to_rebind)

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
                # --- [REFACTOR] Calculate stagger delay ONCE when animation starts ---
                soundDurationMs = settings.gameOverSound.get_length() * 1000
                # The time available for staggering is the total sound duration minus one segment's fade time.
                timeForStaggering = soundDurationMs - settings.DEATH_ANIMATION_SEGMENT_FADE_DURATION
                numSegments = len(game.snake.body)
                if numSegments > 1 and timeForStaggering > 0:
                    deathStaggerDelay = timeForStaggering / (numSegments - 1)
                else:
                    deathStaggerDelay = 0 # If snake is tiny or sound is short, they fade together.
            
            # Drawing is independent of logic updates and will run at the monitor's refresh rate.
            if current_state == GameState.PLAYING:
                game.draw(settings.window)
            
            # Draw revert countdown separately from the notification to ensure it lasts for the full event duration.
            if active_event in ["BEEEG Snake", "Small Snake", "Racecar Snake", "Slow Snake"]:
                time_left = (event_start_time + settings.EVENT_DURATION - current_time) / 1000
                if time_left > 0:
                    ui.draw_revert_countdown(settings.window, int(time_left) + 1)

        elif current_state == GameState.EVENT_COUNTDOWN:
            time_since_last_move, is_game_over = handle_game_update(time_since_last_move, delta_time, game, active_event)
            if is_game_over: # It's possible to die during the countdown
                game.save_score_if_high()
                current_state = GameState.DYING
                deathAnimationStartTime = pygame.time.get_ticks()
                deathSoundHasPlayed = False
                # --- [REFACTOR] Calculate stagger delay ONCE when animation starts ---
                soundDurationMs = settings.gameOverSound.get_length() * 1000
                timeForStaggering = soundDurationMs - settings.DEATH_ANIMATION_SEGMENT_FADE_DURATION
                numSegments = len(game.snake.body)
                if numSegments > 1 and timeForStaggering > 0:
                    deathStaggerDelay = timeForStaggering / (numSegments - 1)
                else:
                    deathStaggerDelay = 0
            
            # Drawing is independent
            game.draw(settings.window) # Keep drawing the game

            current_time = pygame.time.get_ticks()
            time_since_start = current_time - event_start_time
            
            if time_since_start >= settings.EVENT_COUNTDOWN_DURATION:
                # Countdown finished! Trigger the actual event.
                current_state = GameState.PLAYING
                
                # Create a list of possible events, excluding the last one.
                possible_events = [e for e in event_list if e != last_event]
                # If the list is somehow empty (e.g., only one event exists), fall back to the full list.
                if not possible_events:
                    possible_events = event_list

                active_event = random.choice(possible_events)
                game.start_event(active_event)
                event_start_time = pygame.time.get_ticks() # Reset timer for the event's duration
                notification_end_time = event_start_time + settings.EVENT_NOTIFICATION_DURATION
            else:
                # Draw the countdown UI
                seconds_left = (settings.EVENT_COUNTDOWN_DURATION - time_since_start) / 1000
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
            game.draw(settings.window, isDying=True, fadeProgress=fade_progress, staggerDelay=deathStaggerDelay)
            
            # Transition to the game over screen once the animation is complete.
            soundDurationMs = settings.gameOverSound.get_length() * 1000
            if fade_progress is not None and fade_progress >= soundDurationMs:
                current_state = GameState.GAME_OVER

        # --- Event Management (runs continuously during gameplay) ---
        if current_state in [GameState.PLAYING, GameState.EVENT_COUNTDOWN]:
            current_time = pygame.time.get_ticks()

            # 1. Check if an active event has expired.
            if active_event:
                is_food_event = game.is_food_event_active(active_event)
                if not is_food_event and current_time > event_start_time + settings.EVENT_DURATION:
                    game.stop_event(active_event)
                    last_event, active_event = active_event, None
                elif is_food_event and not game.food.items:
                    game.stop_event(active_event)
                    last_event, active_event = active_event, None

            # 2. If no event is active, count up the main event timer.
            if not active_event and current_state != GameState.EVENT_COUNTDOWN:
                if event_timer < settings.EVENT_TIMER_MAX:
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
                time_left = (event_start_time + settings.EVENT_DURATION - current_time) / 1000
                if time_left > 0: ui.draw_revert_countdown(settings.window, int(time_left) + 1)

        elif current_state == GameState.GAME_OVER:
            # Pass the final score and high score to the UI function
            game_over_buttons = ui.draw_game_over_screen(settings.window, game.score, game.high_score)

        if settings.debugMode:
            event_time_left = 0
            if active_event:
                event_time_left = (event_start_time + settings.EVENT_DURATION - pygame.time.get_ticks()) / 1000

            all_debug_info = {
                "State": (settings.debugSettings['showState'], current_state.name),
                "Snake Pos": (settings.debugSettings['showSnakePos'], str(game.snake.pos)),
                "Snake Len": (settings.debugSettings['showSnakeLen'], len(game.snake.body)),
                "Speed": (settings.debugSettings['showSpeed'], f"{game.speed:.1f}"),
                "Normal Speed": (settings.debugSettings['showNormalSpeed'], f"{game.normalSpeed:.1f}"),
                "Event Timer": (settings.debugSettings['showEventTimer'], f"{(settings.EVENT_TIMER_MAX - event_timer) / 1000:.1f}s"),
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
        # With vsync on, this loop will run at the monitor's refresh rate.
        delta_time = settings.clock.tick()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()