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
    
    # Start in the main menu
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
                        current_state = GameState.PLAYING
                        game.reset()  # Start a new game
                    elif event.key == pygame.K_s: # 'S' for settings
                        current_state = GameState.COLOR_SETTINGS
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if menu_buttons['play'].collidepoint(mouse_pos):
                        current_state = GameState.PLAYING
                        game.reset()
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
            
            elif current_state == GameState.PLAYING:
                # Pass game-related inputs to the controller
                game.handle_input(event)
                # --- [NEW] Pause the game ---
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    current_state = GameState.PAUSED
            
            elif current_state == GameState.PAUSED:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                    current_state = GameState.PLAYING
            
            elif current_state == GameState.PLAYING:
                # Pass game-related inputs to the controller
                game.handle_input(event)
                # --- [TEMPLATE] FOR NEW GAME STATES ---
                # if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                #     current_state = GameState.PAUSED
            
            # elif current_state == GameState.PAUSED:
            #     if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            #         current_state = GameState.PLAYING
            
            elif current_state == GameState.GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    if event.key == pygame.K_r:
                        current_state = GameState.PLAYING
                        game.reset()  # Reset for a new game
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if game_over_buttons['restart'].collidepoint(mouse_pos):
                        settings.buttonClickSound.play()
                        current_state = GameState.PLAYING
                        game.reset()
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
            is_game_over = game.update()
            
            if is_game_over:
                settings.gameOverSound.play()
                game.save_score_if_high()
                current_state = GameState.GAME_OVER
            else:
                # Draw all the game elements
                game.draw(settings.window)

        elif current_state == GameState.PAUSED:
            # First, draw the underlying game screen so it's visible.
            game.draw(settings.window)
            # Then, draw the pause menu over it.
            ui.draw_pause_menu(settings.window)

        elif current_state == GameState.GAME_OVER:
            # Pass the final score and high score to the UI function
            game_over_buttons = ui.draw_game_over_screen(settings.window, game.score, game.high_score)

        # --- Finalize Frame ---
        # This is the crucial step that makes everything drawn in the loop
        # actually appear on the screen.
        pygame.display.update()
        # Use the game's current speed
        settings.clock.tick(game.speed)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()