"""
splash_screen.py
- Contains the logic to display a timed splash screen on game startup.
- This runs once before the main menu is displayed.
"""
import pygame
import settings
import time

# --- [NEW] PyInstaller Splash Screen Integration ---
# This special module only exists when running from a PyInstaller bundle.
# We use a try-except block to handle both bundled and script-based execution.
try:
    import pyi_splash  # type: ignore
except ImportError:
    pyi_splash = None # Define it as None so we can check for it later

def show():
    """
    Displays the splash screen with a fade-in and fade-out effect.
    Handles its own simple event loop.
    """

    # --- [NEW] Close the native PyInstaller splash screen ---
    if pyi_splash:
        pyi_splash.close()

    # --- [NEW] Pre-load the splash logo itself ---
    # This must be done before other assets so it can be displayed.
    try:
        settings.splashLogoImage = pygame.image.load(settings.splashLogoFile).convert_alpha()
    except pygame.error:
        settings.splashLogoImage = None # Handle case where logo is missing

    # --- [FIX] Pre-load the font needed for the splash screen UI ---
    # This ensures we can always draw the loading text, independent of the main asset loader.
    try:
        loading_font = pygame.font.Font(settings.fontFile, 30)
    except Exception:
        # Fallback to a default system font if the custom one fails
        loading_font = pygame.font.Font(None, 30)

    start_time = pygame.time.get_ticks()
    win_w, win_h = settings.window.get_size()
    scaled_logo = None
    logo_rect = None

    # --- [FIX] Only process the logo if it was loaded successfully ---
    if settings.splashLogoImage:
        # Get a scaled version of the logo to fit the window nicely
        logo_w, logo_h = settings.splashLogoImage.get_size()
        
        # --- [REFACTOR] Fit logo to window ---
        # Calculate the scale ratio based on both width and height.
        ratio_w = win_w / logo_w
        ratio_h = win_h / logo_h
        # Choose the smaller ratio to ensure the entire image fits on screen.
        # We multiply by 0.8 to add a 10% margin on all sides for a cleaner look.
        scale_ratio = min(ratio_w, ratio_h) * 0.8

        scaled_w = int(logo_w * scale_ratio)
        scaled_h = int(logo_h * scale_ratio)
        scaled_logo = pygame.transform.smoothscale(settings.splashLogoImage, (scaled_w, scaled_h))
        logo_rect = scaled_logo.get_rect(center=(win_w / 2, win_h / 2))

    # --- [NEW] Dynamic Loading Logic ---
    asset_loader = settings.load_assets()
    loading_text = "Initializing..."
    loading_percent = 0.0
    loading_finished_time = -1
    is_loading_done = False

    # Main loop for the splash screen
    while True:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time

        # Check for quit events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            # Allow skipping with a key press or mouse click
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return

        # --- Process one loading step per frame ---
        if not is_loading_done:
            try:
                current_step, total_steps, message = next(asset_loader)
                loading_text = message
                loading_percent = current_step / total_steps
            except StopIteration:
                is_loading_done = True
                loading_finished_time = current_time
                loading_text = "Ready!"
                loading_percent = 1.0

        # --- Animation Logic ---
        alpha = 0
        if loading_finished_time != -1:
            # If loading is done, start the fade-out sequence.
            time_since_finish = current_time - loading_finished_time
            if time_since_finish < settings.SPLASH_FADE_OUT_DURATION:
                alpha = int(255 * (1 - (time_since_finish / settings.SPLASH_FADE_OUT_DURATION)))
            else:
                break # Fade out complete, exit splash screen
        elif elapsed_time < settings.SPLASH_FADE_IN_DURATION:
            # Fading in while loading
            alpha = int(255 * (elapsed_time / settings.SPLASH_FADE_IN_DURATION))
        else:
            # Fully visible while loading
            alpha = 255

        # --- Drawing ---
        settings.window.fill(settings.backgroundColor)
        
        # Draw Logo (only if it exists)
        if scaled_logo and logo_rect:
            scaled_logo.set_alpha(alpha)
            settings.window.blit(scaled_logo, logo_rect)

        # Draw Loading Text and Percentage
        text_alpha = min(alpha, 200) # Make text slightly less bright than logo
        text_surf = loading_font.render(loading_text, True, (*settings.white, text_alpha))
        percent_surf = loading_font.render(f"{int(loading_percent * 100)}%", True, (*settings.white, text_alpha))
        
        settings.window.blit(text_surf, text_surf.get_rect(center=(win_w / 2, win_h * 0.8)))
        settings.window.blit(percent_surf, percent_surf.get_rect(center=(win_w / 2, win_h * 0.85)))

        pygame.display.update()
        settings.clock.tick(60) # Run at a steady 60 FPS