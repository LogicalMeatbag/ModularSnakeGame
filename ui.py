"""
ui.py
- Contains all functions related to drawing to the screen.
- These functions are 'dumb' - they just draw what they are told,
  and don't contain any game logic.
"""
import pygame
import settings

def tint_surface(surface, color):
    """
    Utility function to color a white/grayscale surface, preserving transparency.
    """
    # This is the correct and final method for tinting a grayscale sprite.
    # 1. Create a new surface filled with the tint color.
    colored_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    colored_surface.fill(color)
    # 2. Use the grayscale sprite as a mask to multiply the tint.
    colored_surface.blit(surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return colored_surface

def _draw_snake_preview(surface, y_pos, color):
    """
    Internal helper to draw a centered, right-facing 3-segment snake preview.
    """
    win_w, _ = surface.get_size()
    preview_center_x = win_w / 2

    # --- [FIX] Rotate sprites to face right ---
    head = pygame.transform.rotate(settings.snakeImages['head'], -90)
    body = pygame.transform.rotate(settings.snakeImages['body'], 90)
    tail = pygame.transform.rotate(settings.snakeImages['tail'], -90)

    # Tint the rotated sprites
    tinted_head = tint_surface(head, color)
    tinted_body = tint_surface(body, color)
    tinted_tail = tint_surface(tail, color)

    # --- [FIX] Center the entire snake, not just one part ---
    # The body is the center of the preview.
    surface.blit(tinted_body, tinted_body.get_rect(center=(preview_center_x, y_pos)))
    surface.blit(tinted_head, tinted_head.get_rect(center=(preview_center_x + body.get_width(), y_pos)))
    surface.blit(tinted_tail, tinted_tail.get_rect(center=(preview_center_x - body.get_width(), y_pos)))

def draw_score(surface, score, high_score):
    """Draws the current score and high score."""
    score_surface = settings.scoreFont.render(f'Score: {score}  High Score: {high_score}', True, settings.white)
    # Position relative to the game area, not the window
    surface.blit(score_surface, (settings.xOffset + 10, settings.yOffset + 10))

def draw_main_menu(surface):
    """Draws the main menu screen and returns rects for buttons."""
    win_w, win_h = surface.get_size()
    mouse_pos = pygame.mouse.get_pos()

    # Title
    title_surface = settings.titleFont.render(settings.gameTitle, True, settings.snakeColor)
    title_rect = title_surface.get_rect(center=(win_w / 2, win_h * 0.25))
    surface.blit(title_surface, title_rect)

    # Play Button
    play_rect = pygame.Rect(0, 0, 200, 50)
    play_rect.center = (win_w / 2, win_h * 0.5)
    play_color = settings.white if play_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, play_color, play_rect, 2, 5)
    play_surface = settings.scoreFont.render("Play", True, play_color)
    surface.blit(play_surface, play_surface.get_rect(center=play_rect.center))

    # Settings Button
    settings_rect = pygame.Rect(0, 0, 200, 50)
    settings_rect.center = (win_w / 2, win_h * 0.65)
    settings_color = settings.white if settings_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, settings_color, settings_rect, 2, 5)
    settings_surface = settings.scoreFont.render("Settings", True, settings_color)
    surface.blit(settings_surface, settings_surface.get_rect(center=settings_rect.center))

    # Quit Button
    quit_rect = pygame.Rect(0, 0, 200, 50)
    quit_rect.center = (win_w / 2, win_h * 0.8)
    quit_color = settings.white if quit_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, quit_color, quit_rect, 2, 5)
    quit_surface = settings.scoreFont.render("Quit", True, quit_color)
    surface.blit(quit_surface, quit_surface.get_rect(center=quit_rect.center))

    return {'play': play_rect, 'settings': settings_rect, 'quit': quit_rect}

def draw_settings_menu(surface, current_color_name):
    """Draws the settings menu screen and returns button rects."""
    win_w, win_h = surface.get_size()
    mouse_pos = pygame.mouse.get_pos()

    # Title
    title_surface = settings.titleFont.render("Settings", True, settings.white)
    title_rect = title_surface.get_rect(center=(win_w / 2, win_h * 0.2))
    surface.blit(title_surface, title_rect)

    # Color option label
    color_label_surface = settings.scoreFont.render("Snake Color", True, settings.white)
    color_label_rect = color_label_surface.get_rect(center=(win_w / 2, win_h * 0.4))
    surface.blit(color_label_surface, color_label_rect)

    # --- [NEW] Snake Preview ---
    # Use the new helper function to draw the preview
    _draw_snake_preview(surface, win_h * 0.5, settings.snakeColor)

    # --- Color Selector ---
    # Left Arrow
    # --- [FIX] Position arrows relative to the snake preview width ---
    arrow_offset = settings.snakeImages['head'].get_width() * 1.5 + 40 # 1.5 blocks for half the snake, plus 40px padding
    left_arrow_rect = pygame.Rect(0, 0, 50, 50)
    left_arrow_rect.center = (win_w / 2 - arrow_offset, win_h * 0.5)
    left_arrow_color = settings.white if left_arrow_rect.collidepoint(mouse_pos) else settings.uiElementColor
    left_arrow_surf = settings.scoreFont.render("<", True, left_arrow_color)
    surface.blit(left_arrow_surf, left_arrow_surf.get_rect(center=left_arrow_rect.center))

    # Right Arrow
    right_arrow_rect = pygame.Rect(0, 0, 50, 50)
    right_arrow_rect.center = (win_w / 2 + arrow_offset, win_h * 0.5)
    right_arrow_color = settings.white if right_arrow_rect.collidepoint(mouse_pos) else settings.uiElementColor
    right_arrow_surf = settings.scoreFont.render(">", True, right_arrow_color)
    surface.blit(right_arrow_surf, right_arrow_surf.get_rect(center=right_arrow_rect.center))

    # --- [NEW] Debug Settings Button (only shows if debug mode is on) ---
    if settings.debugMode:
        debugMenuText = "Debug Settings"
        debugMenuSurface = settings.smallFont.render(debugMenuText, True, settings.white)
        debug_menu_rect = pygame.Rect(0, 0, debugMenuSurface.get_width() + 20, 40)
        debug_menu_rect.center = (win_w / 2, win_h * 0.6)
        debugMenuColor = settings.white if debug_menu_rect.collidepoint(mouse_pos) else settings.uiElementColor
        pygame.draw.rect(surface, debugMenuColor, debug_menu_rect, 2, 5)
        debugMenuSurface = settings.smallFont.render(debugMenuText, True, debugMenuColor)
        surface.blit(debugMenuSurface, debugMenuSurface.get_rect(center=debug_menu_rect.center))

    # Keybinds Button
    # --- [FIX] Dynamically size the button based on the text width ---
    keybindsText = "Configure Controls"
    keybindsSurface = settings.scoreFont.render(keybindsText, True, settings.white) # Render once to get size
    keybinds_rect = pygame.Rect(0, 0, keybindsSurface.get_width() + 40, 50) # Add 20px padding on each side
    keybinds_rect.center = (win_w / 2, win_h * 0.7)
    keybindsColor = settings.white if keybinds_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, keybindsColor, keybinds_rect, 2, 5)
    keybindsSurface = settings.scoreFont.render(keybindsText, True, keybindsColor) # Re-render with hover color
    surface.blit(keybindsSurface, keybindsSurface.get_rect(center=keybinds_rect.center))

    # --- [NEW] Debug Mode Toggle ---
    debug_toggle_y = win_h * 0.78
    debug_label_surface = settings.scoreFont.render("Debug Mode:", True, settings.white)
    debug_label_rect = debug_label_surface.get_rect(midright=(win_w / 2, debug_toggle_y))
    surface.blit(debug_label_surface, debug_label_rect)

    debug_box_rect = pygame.Rect(0, 0, 30, 30)
    debug_box_rect.midleft = (win_w / 2 + 10, debug_toggle_y)
    debug_box_color = settings.white if debug_box_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, debug_box_color, debug_box_rect, 2, 3)

    if settings.debugMode:
        # Draw a checkmark if debug mode is enabled
        checkmark_points = [
            (debug_box_rect.left + 5, debug_box_rect.centery),
            (debug_box_rect.centerx - 2, debug_box_rect.bottom - 5),
            (debug_box_rect.right - 5, debug_box_rect.top + 5)
        ]
        pygame.draw.lines(surface, settings.snakeColor, False, checkmark_points, 3)

    # Save Button
    saveText = "Back to Menu"
    saveSurface = settings.scoreFont.render(saveText, True, settings.white)
    save_rect = pygame.Rect(0, 0, saveSurface.get_width() + 40, 50)
    save_rect.center = (win_w / 2, win_h * 0.88) # Moved down slightly
    saveColor = settings.white if save_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, saveColor, save_rect, 2, 5)
    saveSurface = settings.scoreFont.render(saveText, True, saveColor) # Re-render with hover color
    surface.blit(saveSurface, saveSurface.get_rect(center=save_rect.center))

    # --- [MODIFIED] Return the rect for the color name text, which is now below the preview ---
    # --- [FIX] Add padding to prevent text from overlapping with the snake preview ---
    spriteHeight = settings.snakeImages['head'].get_height()
    text_y_pos = win_h * 0.5 + (spriteHeight / 2) + 20 # Half sprite height + 20px padding
    color_name_surface = settings.scoreFont.render(current_color_name, True, settings.snakeColor)
    color_name_rect = color_name_surface.get_rect(center=(win_w / 2, text_y_pos))
    surface.blit(color_name_surface, color_name_rect)

    return {
        'left': left_arrow_rect, 
        'right': right_arrow_rect, 
        'keybinds': keybinds_rect, 
        'save': save_rect, 
        'color_name_display': color_name_rect,
        'debug_toggle': debug_box_rect,
        'debug_menu': debug_menu_rect if settings.debugMode else None
    }

def draw_keybind_settings_menu(surface, current_keybinds, selected_action):
    """Draws the keybinding configuration screen."""
    win_w, win_h = surface.get_size()
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}

    # Title
    title_surface = settings.titleFont.render("Configure Controls", True, settings.white)
    title_rect = title_surface.get_rect(center=(win_w / 2, win_h * 0.15))
    surface.blit(title_surface, title_rect)

    # Draw each keybind option
    y_pos = win_h * 0.3
    for action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
        # Action Label (e.g., "UP")
        action_surface = settings.scoreFont.render(f"{action}:", True, settings.white)
        action_rect = action_surface.get_rect(midright=(win_w / 2 - 20, y_pos))
        surface.blit(action_surface, action_rect)

        # Key Name Button
        key_names = [pygame.key.name(k) for k in current_keybinds[action]]
        key_text = " + ".join(key_names).upper()

        # If this action is selected for rebinding, show prompt
        if selected_action == action:
            key_text = "Press any key..."
        
        key_rect = pygame.Rect(0, 0, 300, 50)
        key_rect.midleft = (win_w / 2, y_pos)
        buttons[action] = key_rect # Add rect to our buttons dict

        # Highlight if selected or hovered
        is_hovered = key_rect.collidepoint(mouse_pos)
        is_selected = selected_action == action
        key_color = settings.snakeColor if is_selected else (settings.white if is_hovered else settings.uiElementColor)
        
        pygame.draw.rect(surface, key_color, key_rect, 2, 5)
        key_surface = settings.smallFont.render(key_text, True, key_color)
        surface.blit(key_surface, key_surface.get_rect(center=key_rect.center))

        y_pos += 70 # Increment y-position for the next row

    # Save Button
    save_rect = pygame.Rect(0, 0, 250, 50)
    save_rect.center = (win_w / 2, win_h * 0.85)
    save_color = settings.white if save_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, save_color, save_rect, 2, 5)
    save_surface = settings.scoreFont.render("Save & Back", True, save_color)
    surface.blit(save_surface, save_surface.get_rect(center=save_rect.center))
    buttons['save'] = save_rect

    return buttons

def draw_custom_color_menu(surface, temp_color, editing_component=None, input_string=""):
    """Draws the UI for creating a custom RGB color."""
    win_w, win_h = surface.get_size()
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}

    # Title
    title_surface = settings.titleFont.render("Custom Color", True, settings.white)
    title_rect = title_surface.get_rect(center=(win_w / 2, win_h * 0.15))
    surface.blit(title_surface, title_rect)

    # Color Preview
    _draw_snake_preview(surface, win_h * 0.3, temp_color)

    # RGB Sliders
    y_pos = win_h * 0.5
    for i, component in enumerate(['R', 'G', 'B']):
        # Label (R, G, or B)
        label_surface = settings.scoreFont.render(component, True, settings.white)
        surface.blit(label_surface, label_surface.get_rect(midright=(win_w / 2 - 170, y_pos)))

        # --- [NEW] Value display / text input box ---
        value_rect = pygame.Rect(0, 0, 100, 40)
        value_rect.center = (win_w / 2, y_pos)
        buttons[f'edit_{component}'] = value_rect # Add rect for click detection

        if editing_component == component:
            # Draw an active input box with a blinking cursor
            pygame.draw.rect(surface, settings.white, value_rect, 2, 5)
            # Blinking cursor: visible for 500ms, invisible for 500ms
            cursor_visible = (pygame.time.get_ticks() // 500) % 2 == 0
            text_to_draw = input_string + ('|' if cursor_visible else '')
            value_surface = settings.scoreFont.render(text_to_draw, True, settings.white)
        else:
            # Draw an inactive value display
            pygame.draw.rect(surface, settings.uiElementColor, value_rect, 2, 5)
            value_surface = settings.scoreFont.render(str(temp_color[i]), True, settings.white)
        
        surface.blit(value_surface, value_surface.get_rect(center=value_rect.center))

        # Decrement Button
        dec_rect = pygame.Rect(0, 0, 50, 40)
        dec_rect.center = (win_w / 2 - 100, y_pos)
        dec_color = settings.white if dec_rect.collidepoint(mouse_pos) else settings.uiElementColor
        pygame.draw.rect(surface, dec_color, dec_rect, 2, 5)
        dec_surf = settings.scoreFont.render("-", True, dec_color)
        surface.blit(dec_surf, dec_surf.get_rect(center=dec_rect.center))
        buttons[f'dec_{component}'] = dec_rect

        # Increment Button
        inc_rect = pygame.Rect(0, 0, 50, 40)
        inc_rect.center = (win_w / 2 + 100, y_pos)
        inc_color = settings.white if inc_rect.collidepoint(mouse_pos) else settings.uiElementColor
        pygame.draw.rect(surface, inc_color, inc_rect, 2, 5)
        inc_surf = settings.scoreFont.render("+", True, inc_color)
        surface.blit(inc_surf, inc_surf.get_rect(center=inc_rect.center))
        buttons[f'inc_{component}'] = inc_rect

        y_pos += 70

    # Back Button
    back_rect = pygame.Rect(0, 0, 150, 50)
    back_rect.center = (win_w / 2 - 100, win_h * 0.85)
    back_color = settings.white if back_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, back_color, back_rect, 2, 5)
    back_surf = settings.scoreFont.render("Back", True, back_color)
    surface.blit(back_surf, back_surf.get_rect(center=back_rect.center))
    buttons['back'] = back_rect

    # Apply Button
    apply_rect = pygame.Rect(0, 0, 150, 50)
    apply_rect.center = (win_w / 2 + 100, win_h * 0.85)
    apply_color = settings.white if apply_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, apply_color, apply_rect, 2, 5)
    apply_surf = settings.scoreFont.render("Apply", True, apply_color)
    surface.blit(apply_surf, apply_surf.get_rect(center=apply_rect.center))
    buttons['apply'] = apply_rect

    return buttons

def draw_game_over_screen(surface, score, high_score):
    """Draws the game over screen and returns button rects."""
    win_w, win_h = surface.get_size() # Use the full window for menu centering
    mouse_pos = pygame.mouse.get_pos()

    # "Game Over!" text
    game_over_surface = settings.titleFont.render('Game Over!', True, settings.gameOverColor)
    game_over_rect = game_over_surface.get_rect()
    game_over_rect.midtop = (win_w / 2, win_h / 4)

    # Final score
    final_score_surface = settings.scoreFont.render(f'Final Score: {score}', True, settings.white)
    final_score_rect = final_score_surface.get_rect()
    final_score_rect.midtop = (win_w / 2, win_h / 2.5)
    
    surface.blit(game_over_surface, game_over_rect)
    surface.blit(final_score_surface, final_score_rect)

    # Restart Button
    restart_rect = pygame.Rect(0, 0, 200, 50)
    restart_rect.center = (win_w / 2, win_h * 0.65)
    restart_color = settings.white if restart_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, restart_color, restart_rect, 2, 5)
    restart_surface = settings.scoreFont.render("Restart", True, restart_color)
    surface.blit(restart_surface, restart_surface.get_rect(center=restart_rect.center))

    # --- [MODIFIED] Main Menu Button ---
    mainMenuRect = pygame.Rect(0, 0, 200, 50)
    mainMenuRect.center = (win_w / 2, win_h * 0.8)
    mainMenuColor = settings.white if mainMenuRect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, mainMenuColor, mainMenuRect, 2, 5)
    mainMenuSurface = settings.scoreFont.render("Main Menu", True, mainMenuColor)
    surface.blit(mainMenuSurface, mainMenuSurface.get_rect(center=mainMenuRect.center))

    return {'restart': restart_rect, 'mainMenu': mainMenuRect}

def draw_event_notification(surface, event_name):
    """Draws a large notification for a random event."""
    win_w, win_h = surface.get_size()
    
    # Use a slightly smaller font than the main title for the event name
    event_font = pygame.font.SysFont(None, 50)
    event_surface = event_font.render(f"{event_name}!", True, settings.gold)
    event_rect = event_surface.get_rect(center=(win_w / 2, win_h * 0.2))
    surface.blit(event_surface, event_rect)

def draw_event_countdown(surface, seconds_left):
    """Draws a countdown notification before a random event triggers."""
    win_w, win_h = surface.get_size()
    
    # Use a smaller font for the countdown to differentiate it from the event name
    countdown_font = pygame.font.SysFont(None, 40)
    countdown_text = f"Event happening in {seconds_left}..."
    countdown_surface = countdown_font.render(countdown_text, True, settings.white)
    countdown_rect = countdown_surface.get_rect(center=(win_w / 2, win_h * 0.2))
    surface.blit(countdown_surface, countdown_rect)

def draw_revert_countdown(surface, seconds_left):
    """Draws a countdown for when a temporary effect will revert."""
    win_w, win_h = surface.get_size()
    
    # Use the same smaller font as the event countdown
    revert_font = pygame.font.SysFont(None, 40)
    revert_text = f"You will be reverted back in {seconds_left}..."
    revert_surface = revert_font.render(revert_text, True, settings.white)
    revert_rect = revert_surface.get_rect(center=(win_w / 2, win_h * 0.25)) # Slightly lower
    surface.blit(revert_surface, revert_rect)

def draw_debug_overlay(surface, debug_info):
    """Draws a debug overlay with game state information."""
    x_pos = 10
    y_pos = 10
    
    # Create a semi-transparent background for readability
    max_width = 0
    for key, value in debug_info.items():
        text = f"{key}: {value}"
        max_width = max(max_width, settings.debugFont.size(text)[0])
    
    bg_height = len(debug_info) * 20 + 10
    bg_rect = pygame.Rect(x_pos - 5, y_pos - 5, max_width + 10, bg_height)
    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, 150))
    surface.blit(bg_surface, (bg_rect.x, bg_rect.y))

    # Draw the "Debug Mode" title
    title_surf = settings.debugFont.render("--- DEBUG MODE ---", True, settings.gold)
    surface.blit(title_surf, (x_pos, y_pos))
    y_pos += 20

    for key, value in debug_info.items():
        text_surface = settings.debugFont.render(f"{key}: {value}", True, settings.white)
        surface.blit(text_surface, (x_pos, y_pos))
        y_pos += 20

def draw_debug_settings_menu(surface, temp_debug_settings):
    """Draws the menu for configuring debug variables."""
    win_w, win_h = surface.get_size()
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}
    y_pos = win_h * 0.1

    # Title
    title_surface = settings.titleFont.render("Debug Settings", True, settings.gold)
    surface.blit(title_surface, title_surface.get_rect(center=(win_w / 2, y_pos)))
    y_pos += 80

    # --- Visibility Toggles ---
    vis_title_surf = settings.scoreFont.render("Overlay Visibility", True, settings.white)
    surface.blit(vis_title_surf, vis_title_surf.get_rect(center=(win_w / 4, y_pos)))

    # --- Value Overrides ---
    val_title_surf = settings.scoreFont.render("Value Overrides", True, settings.white)
    surface.blit(val_title_surf, val_title_surf.get_rect(center=(win_w * 0.75, y_pos)))
    y_pos += 50

    # Draw visibility toggles on the left
    vis_y = y_pos
    for key in [k for k in temp_debug_settings.keys() if k.startswith('show')]:
        label_surf = settings.smallFont.render(key[4:] + ":", True, settings.white) # "showState" -> "State:"
        surface.blit(label_surf, label_surf.get_rect(midright=(win_w / 4 - 10, vis_y)))

        box_rect = pygame.Rect(0, 0, 25, 25)
        box_rect.midleft = (win_w / 4, vis_y)
        buttons[key] = box_rect

        box_color = settings.white if box_rect.collidepoint(mouse_pos) else settings.uiElementColor
        pygame.draw.rect(surface, box_color, box_rect, 2, 3)
        if temp_debug_settings[key]:
            pygame.draw.line(surface, settings.snakeColor, (box_rect.left + 5, box_rect.top + 5), (box_rect.right - 5, box_rect.bottom - 5), 3)
            pygame.draw.line(surface, settings.snakeColor, (box_rect.left + 5, box_rect.bottom - 5), (box_rect.right - 5, box_rect.top + 5), 3)
        vis_y += 35

    # Draw value editors on the right
    val_y = y_pos
    for key in ['eventChanceOverride', 'goldenAppleChanceOverride']:
        label_text = key.replace('Override', '')
        label_surf = settings.smallFont.render(label_text + ":", True, settings.white)
        surface.blit(label_surf, label_surf.get_rect(midright=(win_w * 0.75 - 80, val_y)))

        # Decrement button
        dec_rect = pygame.Rect(0, 0, 40, 40)
        dec_rect.center = (win_w * 0.75 - 40, val_y)
        buttons[f'dec_{key}'] = dec_rect
        pygame.draw.rect(surface, settings.uiElementColor, dec_rect, 2, 5)
        surface.blit(settings.scoreFont.render("-", True, settings.white), settings.scoreFont.render("-", True, settings.white).get_rect(center=dec_rect.center))

        # Value display
        val_surf = settings.scoreFont.render(str(temp_debug_settings[key]), True, settings.white)
        surface.blit(val_surf, val_surf.get_rect(center=(win_w * 0.75 + 20, val_y)))

        # Increment button
        inc_rect = pygame.Rect(0, 0, 40, 40)
        inc_rect.center = (win_w * 0.75 + 80, val_y)
        buttons[f'inc_{key}'] = inc_rect
        pygame.draw.rect(surface, settings.uiElementColor, inc_rect, 2, 5)
        surface.blit(settings.scoreFont.render("+", True, settings.white), settings.scoreFont.render("+", True, settings.white).get_rect(center=inc_rect.center))
        val_y += 60

    # Back Button
    back_rect = pygame.Rect(0, 0, 200, 50)
    back_rect.center = (win_w / 2, win_h * 0.9)
    buttons['back'] = back_rect
    pygame.draw.rect(surface, settings.white if back_rect.collidepoint(mouse_pos) else settings.uiElementColor, back_rect, 2, 5)
    surface.blit(settings.scoreFont.render("Back", True, settings.white), settings.scoreFont.render("Back", True, settings.white).get_rect(center=back_rect.center))

    return buttons

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