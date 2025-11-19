"""
ui.py
- Contains all functions related to drawing to the screen.
- These functions are 'dumb' - they just draw what they are told,
  and don't contain any game logic.
"""
import pygame
import settings
import textwrap

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

def _draw_snake_preview(surface, x_pos, y_pos, color):
    """
    Internal helper to draw a right-facing 3-segment snake preview at a given center point.
    """
    preview_center_x = x_pos
    scale_factor = 2
    original_head = settings.snakeImages['head']
    original_body = settings.snakeImages['body']
    original_tail = settings.snakeImages['tail']
    
    scaled_size = (int(original_head.get_width() * scale_factor), int(original_head.get_height() * scale_factor))
    
    scaled_head = pygame.transform.scale(original_head, scaled_size)
    scaled_body = pygame.transform.scale(original_body, scaled_size)
    scaled_tail = pygame.transform.scale(original_tail, scaled_size)
    
    # Rotate the newly scaled sprites to face right
    head = pygame.transform.rotate(scaled_head, -90)
    body = pygame.transform.rotate(scaled_body, 90)
    tail = pygame.transform.rotate(scaled_tail, -90)
    
    # Tint the rotated sprites
    tinted_head = tint_surface(head, color)
    tinted_body = tint_surface(body, color)
    tinted_tail = tint_surface(tail, color)
    
    # The body is the center of the preview.
    surface.blit(tinted_body, tinted_body.get_rect(center=(preview_center_x, y_pos)))
    surface.blit(tinted_head, tinted_head.get_rect(center=(preview_center_x + body.get_width(), y_pos)))
    surface.blit(tinted_tail, tinted_tail.get_rect(center=(preview_center_x - body.get_width(), y_pos)))

def _draw_wrapped_text(surface, text, font, color, max_width, center_pos, right_align=False):
    """
    Internal helper to draw text that wraps if it exceeds max_width.
    Aligns the text block to the given center_pos.
    If right_align is True, it aligns the right edge of the text to center_pos.
    """
    if not text: return 0
    
    # Instead of estimating, we build lines word-by-word and measure their actual pixel width.
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        # Check if adding the new word exceeds the max width
        test_line = current_line + " " + word if current_line else word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            # The line is too long, so finalize the current line and start a new one
            lines.append(current_line)
            current_line = word
    lines.append(current_line) # Add the last line

    total_height = len(lines) * font.get_height()
    start_y = center_pos[1] - total_height // 2

    for i, line in enumerate(lines):
        line_surface = font.render(line, True, color)
        if right_align:
            line_rect = line_surface.get_rect(midright=(center_pos[0], start_y + i * font.get_height() + font.get_height() // 2))
        else:
            line_rect = line_surface.get_rect(center=(center_pos[0], start_y + i * font.get_height() + font.get_height() // 2))
        surface.blit(line_surface, line_rect)
    
    return total_height

def draw_score(surface, score, high_score):
    """Draws the current score and high score."""
    score_surface = settings.scoreFont.render(f'Score: {score}  High Score: {high_score}', True, settings.white)
    # Position relative to the game area, not the window
    surface.blit(score_surface, (settings.xOffset + 10, settings.yOffset + 10))

def draw_main_menu(surface, selected_index=None):
    """Draws the main menu screen and returns rects for buttons."""
    win_w, win_h = surface.get_size()
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}

    # Title
    title_surface = settings.titleFont.render(settings.gameTitle, True, settings.snakeColor)
    title_rect = title_surface.get_rect(center=(win_w / 2, win_h * 0.25))
    surface.blit(title_surface, title_rect)

    button_data = [('play', "Play", 0.5), ('settings', "Settings", 0.65), ('quit', "Quit", 0.8)]

    # Play Button
    for i, (key, text, y_factor) in enumerate(button_data):
        is_selected = (selected_index == i)
        
        text_surf = settings.scoreFont.render(text, True, settings.white)
        button_rect = pygame.Rect(0, 0, text_surf.get_width() + 40, 50)
        button_rect.center = (win_w / 2, win_h * y_factor)
        buttons[key] = button_rect

        is_hovered = button_rect.collidepoint(mouse_pos)
        
        # A selected button is always white, otherwise check for hover.
        color = settings.white if is_selected or is_hovered else settings.uiElementColor
        
        pygame.draw.rect(surface, color, button_rect, 2, 5)
        text_surf = settings.scoreFont.render(text, True, color) # Re-render with hover/select color
        surface.blit(text_surf, text_surf.get_rect(center=button_rect.center))

    return buttons

def draw_settings_menu(surface, current_color_name, current_sound_pack_name, selected_key=None):
    """Draws the settings menu screen and returns button rects."""
    win_w, win_h = surface.get_size()
    buttons = {} # Initialize the buttons dictionary
    mouse_pos = pygame.mouse.get_pos()

    # Title
    title_surface = settings.titleFont.render("Settings", True, settings.white)
    title_rect = title_surface.get_rect(center=(win_w / 2, win_h * 0.2))
    surface.blit(title_surface, title_rect)

    # --- Column Definitions ---
    col1_x = win_w * 0.22
    col2_x = win_w * 0.50
    col3_x = win_w * 0.78
    y_start = win_h * 0.30
    column_width = win_w * 0.24 # Approx width for each column

    # --- Column 1: Appearance ---
    title_height = _draw_wrapped_text(surface, "Appearance", settings.scoreFont, settings.white,
                       column_width, (col1_x, y_start))

    y_pos = y_start + title_height / 2 + 80 # Lower the preview slightly for better balance
    _draw_snake_preview(surface, col1_x, (y_pos + 45), settings.snakeColor)
    
    y_pos += 80 # Add a bit more space between the preview and the selector
    color_name_surface = settings.scoreFont.render(current_color_name, True, settings.snakeColor)
    surface.blit(color_name_surface, color_name_surface.get_rect(center=(col1_x, y_pos)))

    arrow_offset = 100
    left_arrow_rect = pygame.Rect(0, 0, 50, 50); left_arrow_rect.center = (col1_x - arrow_offset, y_pos - 30)
    left_arrow_color = settings.white if left_arrow_rect.collidepoint(mouse_pos) or selected_key == 'left' else settings.uiElementColor
    surface.blit(settings.scoreFont.render("<", True, left_arrow_color), settings.scoreFont.render("<", True, left_arrow_color).get_rect(center=left_arrow_rect.center))
    buttons['left'] = left_arrow_rect

    right_arrow_rect = pygame.Rect(0, 0, 50, 50); right_arrow_rect.center = (col1_x + arrow_offset, y_pos - 30)
    right_arrow_color = settings.white if right_arrow_rect.collidepoint(mouse_pos) or selected_key == 'right' else settings.uiElementColor
    surface.blit(settings.scoreFont.render(">", True, right_arrow_color), settings.scoreFont.render(">", True, right_arrow_color).get_rect(center=right_arrow_rect.center))
    buttons['right'] = right_arrow_rect

    y_pos += 80 # Match the spacing above
    if current_color_name == "Custom":
        customize_text = "Customize"
        customize_surf = settings.smallFont.render(customize_text, True, settings.white)
        customize_rect = pygame.Rect(0, 0, customize_surf.get_width() + 30, 40)
        customize_rect.center = (col1_x, y_pos)
        customize_color = settings.white if customize_rect.collidepoint(mouse_pos) or selected_key == 'customize_button' else settings.uiElementColor
        pygame.draw.rect(surface, customize_color, customize_rect, 2, 5)
        customize_surf = settings.smallFont.render(customize_text, True, customize_color)
        surface.blit(customize_surf, customize_surf.get_rect(center=customize_rect.center))
        buttons['customize_button'] = customize_rect

    # --- Column 2: Performance ---
    title_height = _draw_wrapped_text(surface, "Performance", settings.scoreFont, settings.white,
                       column_width, (col2_x, y_start))

    y_pos = y_start + title_height / 2 + 60 # Position content relative to the title's bottom edge
    label_height = _draw_wrapped_text(surface, "V-Sync:", settings.scoreFont, settings.white,
                       column_width / 2, (col2_x - 10, y_pos), right_align=True)

    vsync_box_rect = pygame.Rect(0, 0, 30, 30); vsync_box_rect.midleft = (col2_x + 10, y_pos)
    vsync_box_color = settings.white if vsync_box_rect.collidepoint(mouse_pos) or selected_key == 'vsync_toggle' else settings.uiElementColor
    pygame.draw.rect(surface, vsync_box_color, vsync_box_rect, 2, 3)
    if settings.vsync:
        pygame.draw.lines(surface, settings.snakeColor, False, [(vsync_box_rect.left + 5, vsync_box_rect.centery), (vsync_box_rect.centerx - 2, vsync_box_rect.bottom - 5), (vsync_box_rect.right - 5, vsync_box_rect.top + 5)], 3)
    buttons['vsync_toggle'] = vsync_box_rect

    y_pos += max(label_height, 30) + 30 # Increased spacing
    fps_limit_color = settings.white if not settings.vsync else settings.uiElementColor
    label_height = _draw_wrapped_text(surface, "Framerate Limit:", settings.scoreFont, fps_limit_color,
                       column_width / 2, (col2_x - 10, y_pos), right_align=True)

    dec_rect = pygame.Rect(0, 0, 40, 30); dec_rect.midleft = (col2_x + 10, y_pos)
    dec_color = settings.white if (dec_rect.collidepoint(mouse_pos) or selected_key == 'dec_fps') and not settings.vsync else settings.uiElementColor
    pygame.draw.rect(surface, dec_color, dec_rect, 2, 3)
    surface.blit(settings.smallFont.render("-", True, dec_color), settings.smallFont.render("-", True, dec_color).get_rect(center=dec_rect.center))
    buttons['dec_fps'] = dec_rect

    val_surf = settings.smallFont.render(str(settings.maxFps), True, fps_limit_color)
    surface.blit(val_surf, val_surf.get_rect(center=(dec_rect.right + 40, y_pos)))

    inc_rect = pygame.Rect(0, 0, 40, 30); inc_rect.midleft = (dec_rect.right + 80, y_pos)
    inc_color = settings.white if (inc_rect.collidepoint(mouse_pos) or selected_key == 'inc_fps') and not settings.vsync else settings.uiElementColor
    pygame.draw.rect(surface, inc_color, inc_rect, 2, 3)
    surface.blit(settings.smallFont.render("+", True, inc_color), settings.smallFont.render("+", True, inc_color).get_rect(center=inc_rect.center))
    buttons['inc_fps'] = inc_rect

    y_pos += max(label_height, 30) + 30 # Increased spacing
    label_height = _draw_wrapped_text(surface, "Show FPS:", settings.scoreFont, settings.white,
                       column_width / 2, (col2_x - 10, y_pos), right_align=True)

    fps_box_rect = pygame.Rect(0, 0, 30, 30); fps_box_rect.midleft = (col2_x + 10, y_pos)
    fps_box_color = settings.white if fps_box_rect.collidepoint(mouse_pos) or selected_key == 'fps_toggle' else settings.uiElementColor
    pygame.draw.rect(surface, fps_box_color, fps_box_rect, 2, 3)
    if settings.showFps:
        pygame.draw.lines(surface, settings.snakeColor, False, [(fps_box_rect.left + 5, fps_box_rect.centery), (fps_box_rect.centerx - 2, fps_box_rect.bottom - 5), (fps_box_rect.right - 5, fps_box_rect.top + 5)], 3)
    buttons['fps_toggle'] = fps_box_rect

    # --- Column 3: General ---
    title_height = _draw_wrapped_text(surface, "General", settings.scoreFont, settings.white,
                       column_width, (col3_x, y_start))

    y_pos = y_start + title_height / 2 + 60 # Position content relative to the title's bottom edge
    keybinds_text = "Configure Controls"
    
    button_width = column_width * 0.9
    char_width = settings.scoreFont.size('W')[0]
    wrap_at = max(1, int(button_width / char_width))
    wrapped_lines = textwrap.wrap(keybinds_text, width=wrap_at)
    button_height = len(wrapped_lines) * settings.scoreFont.get_height() + 20 # 10px padding top/bottom

    keybinds_rect = pygame.Rect(0, 0, button_width, button_height)
    keybinds_rect.center = (col3_x, y_pos)
    keybindsColor = settings.white if keybinds_rect.collidepoint(mouse_pos) or selected_key == 'keybinds' else settings.uiElementColor
    pygame.draw.rect(surface, keybindsColor, keybinds_rect, 2, 5)
    _draw_wrapped_text(surface, keybinds_text, settings.scoreFont, keybindsColor, button_width - 10, keybinds_rect.center)
    buttons['keybinds'] = keybinds_rect

    y_pos += button_height + 15 # Spacing
    controller_text = "Controller Settings"
    wrapped_lines_controller = textwrap.wrap(controller_text, width=wrap_at)
    button_height_controller = len(wrapped_lines_controller) * settings.scoreFont.get_height() + 20

    controller_rect = pygame.Rect(0, 0, button_width, button_height_controller)
    controller_rect.center = (col3_x, y_pos)
    controllerColor = settings.white if controller_rect.collidepoint(mouse_pos) or selected_key == 'controller_settings' else settings.uiElementColor
    pygame.draw.rect(surface, controllerColor, controller_rect, 2, 5)
    _draw_wrapped_text(surface, controller_text, settings.scoreFont, controllerColor, button_width - 10, controller_rect.center)
    buttons['controller_settings'] = controller_rect

    y_pos += button_height_controller + 15 # Spacing
    sound_pack_text = "Sound Pack"
    _draw_wrapped_text(surface, sound_pack_text, settings.scoreFont, settings.white, column_width, (col3_x, y_pos))
    
    y_pos += 40 # Space for the selector below the label
    sound_pack_name_surf = settings.smallFont.render(current_sound_pack_name, True, settings.white)
    surface.blit(sound_pack_name_surf, sound_pack_name_surf.get_rect(center=(col3_x, y_pos)))

    sound_arrow_offset = 80
    sound_left_rect = pygame.Rect(0,0,40,40); sound_left_rect.center = (col3_x - sound_arrow_offset, y_pos)
    sound_left_color = settings.white if sound_left_rect.collidepoint(mouse_pos) or selected_key == 'sound_left' else settings.uiElementColor
    surface.blit(settings.smallFont.render("<", True, sound_left_color), settings.smallFont.render("<", True, sound_left_color).get_rect(center=sound_left_rect.center))
    buttons['sound_left'] = sound_left_rect

    sound_right_rect = pygame.Rect(0,0,40,40); sound_right_rect.center = (col3_x + sound_arrow_offset, y_pos)
    sound_right_color = settings.white if sound_right_rect.collidepoint(mouse_pos) or selected_key == 'sound_right' else settings.uiElementColor
    surface.blit(settings.smallFont.render(">", True, sound_right_color), settings.smallFont.render(">", True, sound_right_color).get_rect(center=sound_right_rect.center))
    buttons['sound_right'] = sound_right_rect

    y_pos += 40 # Adjusted spacing
    label_height = _draw_wrapped_text(surface, "Debug Mode:", settings.scoreFont, settings.white,
                       column_width / 2, (col3_x - 10, y_pos), right_align=True)

    debug_box_rect = pygame.Rect(0, 0, 30, 30); debug_box_rect.midleft = (col3_x + 10, y_pos)
    debug_box_color = settings.white if debug_box_rect.collidepoint(mouse_pos) or selected_key == 'debug_toggle' else settings.uiElementColor
    pygame.draw.rect(surface, debug_box_color, debug_box_rect, 2, 3)
    if settings.debugMode:
        pygame.draw.lines(surface, settings.snakeColor, False, [(debug_box_rect.left + 5, debug_box_rect.centery), (debug_box_rect.centerx - 2, debug_box_rect.bottom - 5), (debug_box_rect.right - 5, debug_box_rect.top + 5)], 3)
    buttons['debug_toggle'] = debug_box_rect

    y_pos += max(label_height, 30) + 30 # Increased spacing
    if settings.debugMode:
        debug_text = "Debug Settings"
        debug_surf = settings.smallFont.render(debug_text, True, settings.white)
        debug_rect = pygame.Rect(0, 0, debug_surf.get_width() + 20, 40)
        debug_rect.center = (col3_x, y_pos)
        debug_color = settings.white if debug_rect.collidepoint(mouse_pos) or selected_key == 'debug_menu' else settings.uiElementColor
        pygame.draw.rect(surface, debug_color, debug_rect, 2, 5)
        debug_surf = settings.smallFont.render(debug_text, True, debug_color)
        surface.blit(debug_surf, debug_surf.get_rect(center=debug_rect.center))
        buttons['debug_menu'] = debug_rect
    else:
        buttons['debug_menu'] = pygame.Rect(0,0,0,0)

    # Save Button
    saveText = "Back to Menu"
    saveSurface = settings.scoreFont.render(saveText, True, settings.white)
    save_rect = pygame.Rect(0, 0, saveSurface.get_width() + 40, 50)
    save_rect.center = (win_w / 2, win_h * 0.92) # Positioned lower
    saveColor = settings.white if save_rect.collidepoint(mouse_pos) or selected_key == 'save' else settings.uiElementColor
    pygame.draw.rect(surface, saveColor, save_rect, 2, 5)
    saveSurface = settings.scoreFont.render(saveText, True, saveColor) # Re-render with hover color
    surface.blit(saveSurface, saveSurface.get_rect(center=save_rect.center))
    buttons['save'] = save_rect

    return buttons

def draw_controller_settings_menu(surface, current_binds, selected_action, selected_key=None):
    """Draws the controller binding configuration screen."""
    win_w, win_h = surface.get_size()
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}

    # Title
    title_surface = settings.titleFont.render("Controller Settings", True, settings.white)
    surface.blit(title_surface, title_surface.get_rect(center=(win_w / 2, win_h * 0.1)))

    # Define the actions to be displayed
    actions = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'CONFIRM', 'CANCEL', 'PAUSE', 'SETTINGS']
    
    y_pos = win_h * 0.25
    for action in actions:
        # Action Label (e.g., "UP")
        action_surface = settings.scoreFont.render(f"{action}:", True, settings.white)
        surface.blit(action_surface, action_surface.get_rect(midright=(win_w / 2 - 20, y_pos)))

        # Bound Input Name Button
        bound_input_name = current_binds.get(action, "Not Set").replace("_", " ").title()

        if selected_action == action:
            bound_input_name = "Press any button/axis..."
        
        key_surface_render = settings.smallFont.render(bound_input_name, True, settings.white)
        min_width = 350
        button_width = max(min_width, key_surface_render.get_width() + 40)
        key_rect = pygame.Rect(0, 0, button_width, 50)
        key_rect.midleft = (win_w / 2, y_pos)
        buttons[action] = key_rect

        is_hovered = key_rect.collidepoint(mouse_pos)
        is_selected = selected_action == action or selected_key == action
        key_color = settings.snakeColor if is_selected else (settings.white if is_hovered else settings.uiElementColor)
        pygame.draw.rect(surface, key_color, key_rect, 2, 5)
        key_surface_render = settings.smallFont.render(bound_input_name, True, key_color)
        surface.blit(key_surface_render, key_surface_render.get_rect(center=key_rect.center))
        y_pos += 65

    # Save & Back Button
    save_rect = pygame.Rect(0, 0, 200, 50)
    save_rect.center = (win_w / 2, win_h * 0.9) # Position it near the bottom
    save_color = settings.white if save_rect.collidepoint(mouse_pos) or selected_key == 'save' else settings.uiElementColor
    pygame.draw.rect(surface, save_color, save_rect, 2, 5)
    save_surface = settings.scoreFont.render("Save & Back", True, save_color)
    surface.blit(save_surface, save_surface.get_rect(center=save_rect.center))
    buttons['save'] = save_rect

    return buttons

def draw_keybind_settings_menu(surface, current_keybinds, selected_action, selected_key=None):
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
        
        key_surface_render = settings.smallFont.render(key_text, True, settings.white)
        # Ensure a minimum width for the "Press any key..." prompt
        min_width = 250
        button_width = max(min_width, key_surface_render.get_width() + 40)
        key_rect = pygame.Rect(0, 0, button_width, 50)
        key_rect.midleft = (win_w / 2, y_pos)
        buttons[action] = key_rect # Add rect to our buttons dict

        # Highlight if selected or hovered
        is_hovered = key_rect.collidepoint(mouse_pos)
        is_selected = selected_action == action or selected_key == action
        key_color = settings.snakeColor if is_selected else (settings.white if is_hovered else settings.uiElementColor)
        pygame.draw.rect(surface, key_color, key_rect, 2, 5)
        key_surface_render = settings.smallFont.render(key_text, True, key_color) # Re-render with color
        surface.blit(key_surface_render, key_surface_render.get_rect(center=key_rect.center))
        y_pos += 70 # Increment y-position for the next row

    # Save Button
    save_rect = pygame.Rect(0, 0, 200, 50) # This one can be fixed as it's just an icon/simple text
    save_rect.center = (win_w / 2, win_h * 0.85)
    save_color = settings.white if save_rect.collidepoint(mouse_pos) or selected_key == 'save' else settings.uiElementColor
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
    _draw_snake_preview(surface, win_w / 2, win_h * 0.3, temp_color)

    # RGB Sliders
    y_pos = win_h * 0.5
    for i, component in enumerate(['R', 'G', 'B']):
        # Label (R, G, or B)
        label_surface = settings.scoreFont.render(component, True, settings.white)
        surface.blit(label_surface, label_surface.get_rect(midright=(win_w / 2 - 170, y_pos)))

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
    back_text = "Back"
    back_surf = settings.scoreFont.render(back_text, True, settings.white)
    back_rect = pygame.Rect(0, 0, back_surf.get_width() + 40, 50)
    back_rect.center = (win_w / 2 - 100, win_h * 0.85)
    back_color = settings.white if back_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, back_color, back_rect, 2, 5)
    back_surf = settings.scoreFont.render(back_text, True, back_color) # Re-render
    surface.blit(back_surf, back_surf.get_rect(center=back_rect.center))
    buttons['back'] = back_rect

    # Apply Button
    apply_text = "Apply"
    apply_surf = settings.scoreFont.render(apply_text, True, settings.white)
    apply_rect = pygame.Rect(0, 0, apply_surf.get_width() + 40, 50)
    apply_rect.center = (win_w / 2 + 100, win_h * 0.85)
    apply_color = settings.white if apply_rect.collidepoint(mouse_pos) else settings.uiElementColor
    pygame.draw.rect(surface, apply_color, apply_rect, 2, 5)
    apply_surf = settings.scoreFont.render(apply_text, True, apply_color) # Re-render
    surface.blit(apply_surf, apply_surf.get_rect(center=apply_rect.center))
    buttons['apply'] = apply_rect

    return buttons

def draw_game_over_screen(surface, score, high_score, selected_index=None):
    """Draws the game over screen and returns button rects."""
    win_w, win_h = surface.get_size() # Use the full window for menu centering
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}

    # "Game Over!" text
    game_over_surface = settings.titleFont.render('Game Over!', True, settings.gameOverColor)
    game_over_rect = game_over_surface.get_rect(midtop=(win_w / 2, win_h / 4))

    # Final score
    final_score_surface = settings.scoreFont.render(f'Final Score: {score}', True, settings.white)
    final_score_rect = final_score_surface.get_rect(midtop=(win_w / 2, win_h / 2.5))
    
    surface.blit(game_over_surface, game_over_rect)
    surface.blit(final_score_surface, final_score_rect)

    button_data = [('restart', "Restart", 0.65), ('mainMenu', "Main Menu", 0.8)]

    for i, (key, text, y_factor) in enumerate(button_data):
        is_selected = (selected_index == i)
        text_surf = settings.scoreFont.render(text, True, settings.white)
        button_rect = pygame.Rect(0, 0, text_surf.get_width() + 40, 50)
        button_rect.center = (win_w / 2, win_h * y_factor)
        buttons[key] = button_rect
        is_hovered = button_rect.collidepoint(mouse_pos)
        color = settings.white if is_selected or is_hovered else settings.uiElementColor
        pygame.draw.rect(surface, color, button_rect, 2, 5)
        text_surf = settings.scoreFont.render(text, True, color)
        surface.blit(text_surf, text_surf.get_rect(center=button_rect.center))

    return buttons

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

def draw_fps_counter(surface, fps):
    """Draws a simple FPS counter in the top-right corner."""
    # Format the FPS to one decimal place
    fps_text = f"FPS: {fps:.1f}"
    fps_surface = settings.debugFont.render(fps_text, True, settings.white)
    
    # Position in the top-right corner with a small margin
    fps_rect = fps_surface.get_rect(topright=(surface.get_width() - 10, 10))
    surface.blit(fps_surface, fps_rect)

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

    # Title
    title_surface = settings.titleFont.render("Debug Settings", True, settings.gold)
    surface.blit(title_surface, title_surface.get_rect(center=(win_w / 2, win_h * 0.1)))

    # --- Column Layout ---
    col1_x = win_w * 0.20
    col2_x = win_w * 0.50
    col3_x = win_w * 0.80
    y_start = win_h * 0.2
    column_width = win_w * 0.28 # Define a width for wrapping

    # --- Helper function for drawing value editors ---
    def draw_value_editor(y, x, key, label, is_chance=False):
        label_surf = settings.debugMenuFont.render(label, True, settings.white)
        surface.blit(label_surf, label_surf.get_rect(midright=(x - 80, y)))

        dec_rect = pygame.Rect(0, 0, 30, 30); dec_rect.center = (x - 40, y)
        buttons[f'dec_{"chance_" if is_chance else ""}{key}'] = dec_rect # Fix button key
        dec_color = settings.white if dec_rect.collidepoint(mouse_pos) else settings.uiElementColor
        pygame.draw.rect(surface, dec_color, dec_rect, 2, 5)
        surface.blit(settings.debugMenuFont.render("-", True, dec_color), settings.debugMenuFont.render("-", True, dec_color).get_rect(center=dec_rect.center))
        
        value_to_draw = temp_debug_settings['eventChancesOverride'][key] if is_chance else temp_debug_settings[key]

        val_surf = settings.debugMenuFont.render(str(value_to_draw), True, settings.white)
        surface.blit(val_surf, val_surf.get_rect(center=(x + 20, y)))

        inc_rect = pygame.Rect(0, 0, 30, 30); inc_rect.center = (x + 80, y)
        buttons[f'inc_{"chance_" if is_chance else ""}{key}'] = inc_rect # Fix button key
        inc_color = settings.white if inc_rect.collidepoint(mouse_pos) else settings.uiElementColor
        pygame.draw.rect(surface, inc_color, inc_rect, 2, 5)
        surface.blit(settings.debugMenuFont.render("+", True, inc_color), settings.debugMenuFont.render("+", True, inc_color).get_rect(center=inc_rect.center))
        return y + 45

    # --- Column 1: General Overrides ---
    _draw_wrapped_text(surface, "General Overrides", settings.debugMenuFont, settings.white,
                       column_width, (col1_x, y_start))
    y_pos = y_start + 50

    y_pos = draw_value_editor(y_pos, col1_x, 'eventChanceOverride', "Event Chance %:")
    y_pos = draw_value_editor(y_pos, col1_x, 'goldenAppleChanceOverride', "Golden Apple 1-in-X:")
    y_pos = draw_value_editor(y_pos, col1_x, 'eventTimerMaxOverride', "Event Timer (s):")
    y_pos = draw_value_editor(y_pos, col1_x, 'eventDurationOverride', "Event Duration (s):")
    y_pos = draw_value_editor(y_pos, col1_x, 'eventCountdownDurationOverride', "Event Countdown (s):")
    y_pos += 15 # Add a small separator
    y_pos = draw_value_editor(y_pos, col1_x, 'applesGaloreCountOverride', "Apples Galore #:")
    y_pos = draw_value_editor(y_pos, col1_x, 'goldenAppleRainCountOverride', "Golden Rain #:")
    y_pos = draw_value_editor(y_pos, col1_x, 'beegSnakeGrowthOverride', "BEEG Growth:")
    y_pos = draw_value_editor(y_pos, col1_x, 'smallSnakeShrinkOverride', "Small Shrink:")
    y_pos = draw_value_editor(y_pos, col1_x, 'racecarSpeedBoostOverride', "Racecar Boost:")
    y_pos = draw_value_editor(y_pos, col1_x, 'slowSnakeSpeedReductionOverride', "Slow Reduction:")

    # --- Column 2: Event Chance Overrides ---
    _draw_wrapped_text(surface, "Event Chances", settings.debugMenuFont, settings.white,
                       column_width, (col2_x, y_start))
    y_pos = y_start + 50

    for event_name in sorted(temp_debug_settings['eventChancesOverride'].keys()):
        # Create a unique key for the button dictionary
        chance_key = f"chance_{event_name}"
        y_pos = draw_value_editor(y_pos, col2_x, event_name, f"{event_name}:", is_chance=True)

    # --- Column 3: Visibility Toggles ---
    _draw_wrapped_text(surface, "Overlay Visibility", settings.debugMenuFont, settings.white,
                       column_width, (col3_x, y_start))
    y_pos = y_start + 50

    for key in sorted([k for k in temp_debug_settings.keys() if k.startswith('show')]):
        label_surf = settings.debugMenuFont.render(key[4:] + ":", True, settings.white)
        surface.blit(label_surf, label_surf.get_rect(midright=(col3_x - 10, y_pos)))
        box_rect = pygame.Rect(0, 0, 25, 25); box_rect.midleft = (col3_x, y_pos)
        buttons[key] = box_rect
        box_color = settings.white if box_rect.collidepoint(mouse_pos) else settings.uiElementColor
        pygame.draw.rect(surface, box_color, box_rect, 2, 3)
        if temp_debug_settings[key]:
            pygame.draw.lines(surface, settings.snakeColor, False, [(box_rect.left + 5, box_rect.centery), (box_rect.centerx - 2, box_rect.bottom - 5), (box_rect.right - 5, box_rect.top + 5)], 3)
        y_pos += 35

    # Back Button
    back_rect = pygame.Rect(0, 0, 200, 50)
    back_rect.center = (win_w / 2, win_h * 0.9)
    buttons['back'] = back_rect
    pygame.draw.rect(surface, settings.white if back_rect.collidepoint(mouse_pos) else settings.uiElementColor, back_rect, 2, 5)
    surface.blit(settings.debugMenuFont.render("Back", True, settings.white), settings.debugMenuFont.render("Back", True, settings.white).get_rect(center=back_rect.center))

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