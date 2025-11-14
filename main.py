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
from settings import gameTitle # so we can print it before running the main.py code

print(f'Starting {gameTitle}... (Python {sys.version_info.major}.{sys.version_info.minor})')
# --- [NEW] Set up global exception handler ---
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

# --- [TESTING] How to test this block without uninstalling pygame ---
# To test the error message, temporarily uncomment the two lines below.
# They "hide" the pygame module, forcing the ImportError to trigger.
# sys.modules['pygame'] = None

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

def main():
    # The game controller manages the actual game session
    game = GameController()

    # --- [FIX] Define start_new_game inside main() to give it access to the correct scope ---
    def start_new_game():
        """Resets all game-specific state to start a fresh game."""
        nonlocal active_event, event_timer, notification_end_time, countdown_seconds_left, time_since_last_move
        
        # Reset the core game controller (snake, food, score, speed)
        game.reset()
        
        # Reset all event-related variables to their initial states
        active_event = None
        event_timer = 0
        notification_end_time = 0
        countdown_seconds_left = 0

        # --- [NEW] Reset the game logic timer ---
        time_since_last_move = 0
        
        # Set the game state to playing
        return GameState.PLAYING
    
    # --- Game State & Loop Variables ---
    current_state = GameState.MAIN_MENU
    running = True

    # --- [NEW] State for settings menu ---
    # --- [MODIFIED] Add a "Custom" option to the color list ---
    color_names = list(settings.colorOptions.keys()) + ["Custom"]
    current_color_index = color_names.index(settings.userSettings.get("snakeColorName", settings.defaultSettings["snakeColorName"]))

    # --- [NEW] State for custom color menu ---
    # Start with the saved custom color or the default snake color
    initial_custom_color = settings.userSettings.get("customColor", list(settings.snakeColor))
    temp_custom_color = list(initial_custom_color) # Work on a copy

    # --- [NEW] State for debug settings menu ---
    # Work on a temporary copy
    temp_debug_settings = settings.debugSettings.copy()

    # --- [NEW] State for keybind menu ---
    # Work on a temporary copy of the keybinds
    temp_keybinds = {k: list(v) for k, v in settings.keybinds.items()}
    selected_action_to_rebind = None # e.g., 'UP', 'DOWN', None

    # --- [NEW] State for custom color menu interactions ---
    heldButton = None
    heldButtonStartTime = 0
    heldButtonLastTick = 0
    INITIAL_HOLD_DELAY = 400 # ms
    REPEATED_HOLD_DELAY = 40 # ms

    editingColorComponent = None # 'R', 'G', 'B', or None
    rgbInputString = ""

    # --- [NEW] State for random events ---
    event_list = [
        "Apples Galore", "Golden Apple Rain", "BEEEG Snake", 
        "Small Snake", "Racecar Snake", "Slow Snake"
    ]
    active_event = None
    event_start_time = 0
    event_timer = 0 # Counts up to trigger a new event
    notification_end_time = 0 # For showing the event name text
    countdown_seconds_left = 0 # For showing the pre-event countdown
    
    # --- [NEW] Timer for time-based game logic updates ---
    time_since_last_move = 0
    delta_time = 0

    pause_start_time = 0 # To track duration of pause
    # --- [NEW] Initial dimension calculation ---
    update_dynamic_dimensions(settings.window)

    while running:
        # --- Event Handler ---
        # Handle events based on the current game state
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                heldButton = None # Stop holding on any mouse up event

            # --- [NEW] Handle window resizing ---
            if event.type == pygame.VIDEORESIZE:
                # Recreate the window surface with the new size
                settings.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                # Recalculate all dynamic sizes and offsets
                update_dynamic_dimensions(settings.window)
                # --- [FIX] Force entities to update their internal scaling ---
                # This tells the snake and food to rescale their sprites on the next frame.
                game.snake.last_block_size = -1
                game.food.last_block_size = -1

            # --- Get mouse position once per frame ---
            mouse_pos = pygame.mouse.get_pos()

            if current_state == GameState.MAIN_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        current_state = start_new_game()
                    elif event.key == pygame.K_s: # 'S' for settings
                        current_state = GameState.COLOR_SETTINGS
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if menu_buttons['play'].collidepoint(mouse_pos):
                        current_state = start_new_game()
                    elif menu_buttons['settings'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_state = GameState.COLOR_SETTINGS
                    elif menu_buttons['quit'].collidepoint(mouse_pos):
                        running = False
            
            elif current_state == GameState.COLOR_SETTINGS:
                # This state handles changing the snake's color
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        current_color_index = (current_color_index + 1) % len(color_names)
                        # --- [FIX] Update color immediately for visual feedback ---
                        selected_color_name = color_names[current_color_index]
                        if selected_color_name == "Custom":
                            settings.snakeColor = tuple(settings.userSettings.get("customColor", settings.colorOptions["Green"]))
                        else:
                            settings.snakeColor = settings.colorOptions[selected_color_name]
                    elif event.key == pygame.K_LEFT:
                        current_color_index = (current_color_index - 1) % len(color_names)
                        # --- [FIX] Update color immediately for visual feedback ---
                        selected_color_name = color_names[current_color_index]
                        if selected_color_name == "Custom":
                            settings.snakeColor = tuple(settings.userSettings.get("customColor", settings.colorOptions["Green"]))
                        else:
                            settings.snakeColor = settings.colorOptions[selected_color_name]
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        # Save current selection and go back
                        settings.userSettings["snakeColorName"] = color_names[current_color_index]
                        settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                        current_state = GameState.MAIN_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if settings_buttons['left'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_color_index = (current_color_index - 1) % len(color_names)
                    elif settings_buttons['right'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_color_index = (current_color_index + 1) % len(color_names)

                    # --- [FIX] Update color immediately after any change ---
                    selected_color_name = color_names[current_color_index]
                    if selected_color_name == "Custom":
                        # Use the saved custom color, or default to Green if none is saved
                        settings.snakeColor = tuple(settings.userSettings.get("customColor", settings.colorOptions["Green"]))
                    else:
                        settings.snakeColor = settings.colorOptions[selected_color_name]

                    if settings_buttons['keybinds'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_state = GameState.KEYBIND_SETTINGS
                        # Reset rebinding state when entering the menu
                        selected_action_to_rebind = None
                    elif settings_buttons['debug_toggle'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        settings.debugMode = not settings.debugMode # Toggle the flag
                        settings.userSettings["debugMode"] = settings.debugMode # Update for saving
                    elif settings_buttons['save'].collidepoint(mouse_pos):
                        # Save the current color selection and go back
                        settings.buttonClickSound.play()
                        settings.userSettings["snakeColorName"] = selected_color_name
                        # Keybinds are saved in their own menu, so we only need to save color settings here.
                        settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                        current_state = GameState.MAIN_MENU
                    
                    # --- [FIX] Check if user clicked on the "Custom" color name to open custom editor ---
                    if color_names[current_color_index] == "Custom" and settings_buttons['color_name_display'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_state = GameState.CUSTOM_COLOR_SETTINGS

                    # --- [NEW] Check for debug settings button click ---
                    if settings_buttons.get('debug_menu') and settings_buttons['debug_menu'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_state = GameState.DEBUG_SETTINGS

            elif current_state == GameState.KEYBIND_SETTINGS:
                if event.type == pygame.KEYDOWN:
                    if selected_action_to_rebind:
                        # We are waiting for a key press to assign it
                        # For simplicity, we'll assign to the primary key slot
                        temp_keybinds[selected_action_to_rebind][0] = event.key
                        selected_action_to_rebind = None # Stop waiting
                    elif event.key == pygame.K_ESCAPE:
                        # Discard changes and go back
                        current_state = GameState.COLOR_SETTINGS

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if selected_action_to_rebind:
                        # If waiting for input, a click will cancel the rebind
                        selected_action_to_rebind = None
                    else:
                        # Check if a keybind button was clicked
                        for action, rect in keybind_buttons.items():
                            if rect.collidepoint(mouse_pos):
                                if action == 'save':
                                    settings.buttonClickSound.play()
                                    # Save changes and go back
                                    settings.keybinds = temp_keybinds
                                    settings.userSettings["keybinds"] = temp_keybinds
                                    settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                                    current_state = GameState.COLOR_SETTINGS
                                else:
                                    # Set this action to be rebound
                                    settings.buttonClickSound.play()
                                    selected_action_to_rebind = action
                                break # Stop checking after a click

            elif current_state == GameState.CUSTOM_COLOR_SETTINGS:
                if editingColorComponent:
                    # --- Handle Text Input ---
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            # Apply the typed value
                            try:
                                value = int(rgbInputString)
                                component_index = ['R', 'G', 'B'].index(editingColorComponent)
                                temp_custom_color[component_index] = max(0, min(255, value))
                            except ValueError:
                                pass # Ignore invalid input
                            editingColorComponent = None
                        elif event.key == pygame.K_ESCAPE:
                            editingColorComponent = None # Cancel editing
                        elif event.key == pygame.K_BACKSPACE:
                            rgbInputString = rgbInputString[:-1]
                        elif event.unicode.isdigit():
                            rgbInputString += event.unicode
                else:
                    # --- Handle Button Clicks ---
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        clicked_on_button = False
                        for button, rect in custom_color_buttons.items():
                            if rect.collidepoint(mouse_pos):
                                clicked_on_button = True
                                settings.buttonClickSound.play()
                                if button.startswith('inc_') or button.startswith('dec_'):
                                    # Start holding the button
                                    heldButton = button
                                    heldButtonStartTime = pygame.time.get_ticks()
                                    heldButtonLastTick = heldButtonStartTime
                                    # Perform initial click action
                                    component = button.split('_')[1]
                                    component_index = ['R', 'G', 'B'].index(component)
                                    amount = 5 if button.startswith('inc_') else -5
                                    temp_custom_color[component_index] = max(0, min(255, temp_custom_color[component_index] + amount))
                                elif button.startswith('edit_'):
                                    # Start editing a text value
                                    editingColorComponent = button.split('_')[1]
                                    component_index = ['R', 'G', 'B'].index(editingColorComponent)
                                    rgbInputString = str(temp_custom_color[component_index])
                                elif button == 'apply':
                                    # Save the custom color and apply it
                                    settings.userSettings["customColor"] = temp_custom_color
                                    settings.userSettings["snakeColorName"] = "Custom"
                                    settings.snakeColor = tuple(temp_custom_color)
                                    settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                                    current_state = GameState.COLOR_SETTINGS
                                elif button == 'back':
                                    # Discard changes and go back
                                    temp_custom_color = list(settings.userSettings.get("customColor", list(settings.snakeColor)))
                                    current_state = GameState.COLOR_SETTINGS
                                break
                        if not clicked_on_button:
                            editingColorComponent = None # Stop editing if clicking elsewhere

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Discard changes and go back
                            temp_custom_color = list(settings.userSettings.get("customColor", list(settings.snakeColor)))
                            current_state = GameState.COLOR_SETTINGS

            elif current_state == GameState.DEBUG_SETTINGS:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for button, rect in debug_settings_buttons.items():
                        if rect.collidepoint(mouse_pos):
                            settings.buttonClickSound.play()
                            if button.startswith('show'):
                                # Toggle visibility
                                temp_debug_settings[button] = not temp_debug_settings[button]
                            elif button.startswith('inc_'):
                                key = button[4:]
                                temp_debug_settings[key] += 1
                            elif button.startswith('dec_'):
                                key = button[4:]
                                temp_debug_settings[key] = max(1, temp_debug_settings[key] - 1) # Prevent going below 1
                            elif button == 'back':
                                # Save changes and go back
                                settings.debugSettings = temp_debug_settings.copy()
                                settings.userSettings["debugSettings"] = settings.debugSettings
                                settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                                current_state = GameState.COLOR_SETTINGS
                            break # Stop checking after a click
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Save and go back on escape as well
                    settings.debugSettings = temp_debug_settings.copy()
                    settings.userSettings["debugSettings"] = settings.debugSettings
                    settings_manager.save_settings(settings.settingsFile, settings.userSettings)
                    current_state = GameState.COLOR_SETTINGS
            
            elif current_state == GameState.PLAYING:
                # Pass game-related inputs to the controller
                game.handle_input(event)
                # --- [NEW] Pause the game ---
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    pause_start_time = pygame.time.get_ticks() # Record when pause starts
                    current_state = GameState.PAUSED
            
            elif current_state == GameState.EVENT_COUNTDOWN:
                # --- [FIX] Also handle player input during the event countdown ---
                game.handle_input(event)
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    # It should also be possible to pause during the countdown
                    pause_start_time = pygame.time.get_ticks()
                    current_state = GameState.PAUSED
            
            elif current_state == GameState.PAUSED:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    # --- [NEW] Adjust event timers when unpausing ---
                    # This prevents events from ending while paused.
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
        # --- [NEW] Draw border and background ---
        # 1. Fill the entire window with the border color.
        settings.window.fill(settings.borderColor)
        # 2. Draw the game area background on top, creating the letterbox effect. 
        # --- [FIX] Ensure all rect dimensions are integers to prevent rounding errors ---
        # This guarantees the background aligns perfectly with the grid.
        game_area_rect = pygame.Rect(
            int(settings.xOffset), int(settings.yOffset), int(settings.width), int(settings.height)
        )
        pygame.draw.rect(settings.window, settings.backgroundColor, game_area_rect)

        if current_state == GameState.MAIN_MENU:
            menu_buttons = ui.draw_main_menu(settings.window)
        
        elif current_state == GameState.COLOR_SETTINGS:
            settings_buttons = ui.draw_settings_menu(settings.window, color_names[current_color_index]) # Returns dict of buttons

        elif current_state == GameState.DEBUG_SETTINGS:
            debug_settings_buttons = ui.draw_debug_settings_menu(settings.window, temp_debug_settings)

        elif current_state == GameState.KEYBIND_SETTINGS:
            keybind_buttons = ui.draw_keybind_settings_menu(settings.window, temp_keybinds, selected_action_to_rebind)

        elif current_state == GameState.CUSTOM_COLOR_SETTINGS:
            # --- [NEW] Handle held button logic ---
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
            # and returns True if the game is over.
            # --- [NEW] Time-based logic update ---
            time_since_last_move += delta_time
            # Calculate the required time between moves based on speed
            move_interval = 1000 / game.speed # in milliseconds

            if time_since_last_move >= move_interval:
                time_since_last_move -= move_interval # Decrement, don't reset, to carry over excess time
                is_game_over = game.update(active_event)
                
                if is_game_over:
                    settings.gameOverSound.play()
                    game.save_score_if_high()
                    current_state = GameState.GAME_OVER
            
            # --- [NEW] Drawing is now independent of logic updates ---
            # It will always run at the monitor's refresh rate.
            if current_state == GameState.PLAYING:
                game.draw(settings.window)

            # --- [NEW] Handle event logic inside the PLAYING state ---
            current_time = pygame.time.get_ticks()

            # 1. Check if an active event has expired
            if active_event and current_time > event_start_time + settings.EVENT_DURATION:
                game.stop_event(active_event)
                active_event = None

            # 2. If no event is active, count up the main event timer.
            if not active_event and current_state != GameState.EVENT_COUNTDOWN:
                if event_timer < settings.EVENT_TIMER_MAX:
                    event_timer += delta_time # Use our delta_time variable
                else:
                    # Timer is up. Roll the dice to see if we start a countdown.
                    event_timer = 0 # Reset timer for the next cycle
                    chance = settings.debugSettings['eventChanceOverride'] if settings.debugMode else settings.EVENT_CHANCE
                    if random.randint(1, 100) <= chance:
                        # Success! Start the pre-event countdown.
                        current_state = GameState.EVENT_COUNTDOWN
                        event_start_time = current_time # Use this to time the countdown

            # 3. Handle drawing UI notifications
            if current_time < notification_end_time:
                if active_event: # Ensure there's an event to announce
                    ui.draw_event_notification(settings.window, active_event)
                    # --- [NEW] If it's a size event, show the revert countdown ---
            
            # --- [FIX] Draw revert countdown separately from the notification ---
            # This ensures it lasts for the full event duration.
            if active_event in ["BEEEG Snake", "Small Snake"]:
                time_left = (event_start_time + settings.EVENT_DURATION - current_time) / 1000
                if time_left > 0:
                    ui.draw_revert_countdown(settings.window, int(time_left) + 1)

        elif current_state == GameState.EVENT_COUNTDOWN:
            # We are in the pre-event countdown.
            # --- [FIX] Update the game state so it doesn't pause during the countdown. ---
            # --- [NEW] Also use time-based updates here ---
            time_since_last_move += delta_time
            move_interval = 1000 / game.speed

            if time_since_last_move >= move_interval:
                time_since_last_move -= move_interval
                is_game_over = game.update(active_event)
                if is_game_over: # It's possible to die during the countdown
                    settings.gameOverSound.play()
                    game.save_score_if_high()
                    current_state = GameState.GAME_OVER
            
            # Drawing is independent
            game.draw(settings.window) # Keep drawing the game

            current_time = pygame.time.get_ticks()
            time_since_start = current_time - event_start_time
            
            if time_since_start >= settings.EVENT_COUNTDOWN_DURATION:
                # Countdown finished! Trigger the actual event.
                current_state = GameState.PLAYING
                active_event = random.choice(event_list)
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
            # Then, draw the pause menu over it.
            # --- [FIX] The pause menu doesn't exist yet, so we'll just draw text ---
            pause_font = pygame.font.SysFont(None, 80)
            # --- [FIX] Adjust pause timers when unpausing ---
            # This prevents events from ending while paused.
            if active_event:
                event_start_time += pygame.time.get_ticks() - pause_start_time
            pause_surface = pause_font.render("PAUSED", True, settings.white)
            pause_rect = pause_surface.get_rect(center=(settings.window.get_width() / 2, settings.window.get_height() / 2))
            settings.window.blit(pause_surface, pause_rect)

        elif current_state == GameState.GAME_OVER:
            # Pass the final score and high score to the UI function
            game_over_buttons = ui.draw_game_over_screen(settings.window, game.score, game.high_score)

        # --- [NEW] Draw Debug Overlay if enabled ---
        if settings.debugMode:
            event_time_left = 0
            if active_event:
                event_time_left = (event_start_time + settings.EVENT_DURATION - pygame.time.get_ticks()) / 1000

            # --- [NEW] Build debug info based on visibility settings ---
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

            visible_debug_info = {"High Score Saving": "DISABLED"}
            for key, (is_visible, value) in all_debug_info.items():
                if is_visible:
                    visible_debug_info[key] = value
            ui.draw_debug_overlay(settings.window, visible_debug_info)

        # --- Finalize Frame ---
        # This is the crucial step that makes everything drawn in the loop
        # actually appear on the screen.
        pygame.display.update()
        # --- [NEW] Uncap framerate and get delta time ---
        # clock.tick() returns milliseconds since the last frame.
        # With vsync on, this loop will run at the monitor's refresh rate.
        delta_time = settings.clock.tick()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()