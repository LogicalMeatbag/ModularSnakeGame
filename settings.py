import pygame
import os
import sys
import error_handler
import settings_manager
import random

# --- PYINSTALLER PATH FIX ---
# This is the 'sys._MEIPASS' logic, which finds our assets (sounds, fonts)
# whether we are running as a .py script or a bundled .exe
if getattr(sys, 'frozen', False):
    # Running as a bundled .exe
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))) # For assets inside the .exe
else:
    # Running as a .py script
    base_path = os.path.dirname(os.path.abspath(__file__)) # For assets next to the .py

def get_app_data_folder():
    app_data_path = os.getenv('APPDATA')
    if app_data_path:
        # Create a dedicated folder for our game inside AppData
        game_data_folder = os.path.join(app_data_path, "ANAHKENsSnake")
        os.makedirs(game_data_folder, exist_ok=True)
        return game_data_folder
    else:
        # Fallback for rare cases where APPDATA is not set
        # Just save it next to the script or .exe
        return os.path.dirname(os.path.abspath(__file__))

appDataFolder = get_app_data_folder()
highScoreFile = os.path.join(appDataFolder, "highscore.dat")
# --- PYGAME & SOUND INIT ---
pygame.init()
pygame.mixer.init()

# Set a default starting size for the window.
# The user can resize it.
initialWidth = 1280
initialHeight = 720

# The grid dimensions are now fixed. The block size will change.
gridWidth = 64  # Number of blocks horizontally
gridHeight = 36 # Number of blocks vertically

# These will be calculated dynamically
blockSize = 20 
width = gridWidth * blockSize
height = gridHeight * blockSize
xOffset = 0
yOffset = 0

startSpeed = 15

# pygame.RESIZABLE allows the user to change the window size.
# pygame.DOUBLEBUF is recommended for smoother rendering.
gameTitle = "ANAHKEN's Modular Snake Game"
window = pygame.display.set_mode((initialWidth, initialHeight), pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1)
pygame.display.set_caption(gameTitle)

# --- SET WINDOW ICON ---
iconFile = os.path.join(base_path, 'assets', 'images', 'icon.png')
try:
    gameIcon = pygame.image.load(iconFile).convert_alpha()
    pygame.display.set_icon(gameIcon)
except (pygame.error, FileNotFoundError) as e:
    # This is not a fatal error, the game can run without an icon.
    errorMessage = (
        f"The game icon could not be loaded.\n\nDetails: {e}\n\n"
        "Please ensure 'assets/images/icon.png' exists."
        "The game will continue without a custom window icon."
    )
    error_handler.show_error_message("Asset Warning", errorMessage)
clock = pygame.time.Clock()

# --- COLORS ---
white = (255, 255, 255) # General UI text
backgroundColor = (0, 0, 0) # The play area background
borderColor = (40, 40, 40) # The color of the letterbox border
uiElementColor = (100, 100, 100)  # For UI elements like inactive buttons

colorOptions = {
# These are RGB color values for snake colors. 
    "Green": (0, 255, 0),
    "Blue": (0, 100, 255),
    "Purple": (148, 0, 211),
    "Orange": (255, 165, 0),
    "Pink": (255, 105, 180),
    "Cyan": (0, 255, 255), 
}

foodColor = (255, 0, 0) # A pure, bright red for maximum vibrancy
gameOverColor = (255, 0, 0) # A bright, classic red for game over

# --- Special Food Settings ---
gold = (255, 215, 0)  # Color for the special food
goldenFoodScore = 5
goldenFoodChance = 15 # Represents a 1 in 15 chance

# --- Random Event Settings ---
EVENT_TIMER_MAX = 15 * 1000 # An event can trigger every 15 seconds (in milliseconds)
EVENT_CHANCE = 25 # 25% chance to trigger an event when the timer is up
EVENT_DURATION = 10 * 1000 # Most events last for 10 seconds
EVENT_NOTIFICATION_DURATION = 3 * 1000 # "Apples Galore!" message shows for 3 seconds
EVENT_COUNTDOWN_DURATION = 5 * 1000 # Start countdown 5 seconds before event can trigger

# --- [NEW] Splash Screen Settings ---
SPLASH_FADE_IN_DURATION = 1000  # 1 second to fade in
SPLASH_STAY_DURATION = 1500     # 1.5 seconds to stay on screen
SPLASH_FADE_OUT_DURATION = 500  # 0.5 seconds to fade out

# --- [NEW] Death Animation Settings ---
DEATH_ANIMATION_INITIAL_PAUSE = 250 # A brief pause before the animation starts.
DEATH_ANIMATION_SEGMENT_FADE_DURATION = 500 # How long each individual segment takes to fade.

# Event-specific values
APPLES_GALORE_COUNT = 15
GOLDEN_APPLE_RAIN_COUNT = 10
BEEG_SNAKE_GROWTH = 10
SMALL_SNAKE_SHRINK = 5
RACECAR_SNAKE_SPEED_BOOST = 15
SLOW_SNAKE_SPEED_REDUCTION = 5

# --- DEFAULT SETTINGS DICTIONARY ---
defaultSettings = {
    "snakeColorName": "Green",
    "keybinds": {
        'UP': [pygame.K_UP, pygame.K_w],
        'DOWN': [pygame.K_DOWN, pygame.K_s],
        'LEFT': [pygame.K_LEFT, pygame.K_a],
        'RIGHT': [pygame.K_RIGHT, pygame.K_d],
    },
    "debugMode": False,
    "rainbowModeUnlocked": False, # Easter Egg
    "showFps": False, # Moved from debugSettings
    "debugSettings": {
        "showState": True,
        "showSnakePos": True,
        "showSnakeLen": True,
        "showSpeed": True,
        "showNormalSpeed": True,
        "showEventTimer": True,
        "showActiveEvent": True,
        "showEventTimeLeft": True,
        "showSizeEventActive": True,
        "showPreEventLen": True,
        "eventChanceOverride": 25,
        "goldenAppleChanceOverride": 15
    }
}

# --- LOAD SAVED SETTINGS ---
settingsFile = settings_manager.get_settings_path(appDataFolder)
userSettings = settings_manager.load_settings(settingsFile)

if userSettings is None: userSettings = {} # Ensure userSettings is a dict

# --- APPLY LOADED/DEFAULT SETTINGS ---
savedColorName = userSettings.get("snakeColorName", defaultSettings["snakeColorName"])

if savedColorName == "Custom":
    # If the saved name is "Custom", load the specific RGB value.
    # Fallback to Green if the customColor value is somehow missing.
    snakeColor = tuple(userSettings.get("customColor", colorOptions["Green"]))
else:
    # Otherwise, load the color from the presets dictionary.
    snakeColor = colorOptions.get(savedColorName, colorOptions["Green"])

keybinds = userSettings.get("keybinds", defaultSettings["keybinds"])
debugMode = userSettings.get("debugMode", defaultSettings["debugMode"])
rainbowModeUnlocked = userSettings.get("rainbowModeUnlocked", defaultSettings["rainbowModeUnlocked"])
showFps = userSettings.get("showFps", defaultSettings["showFps"])
debugSettings = userSettings.get("debugSettings", defaultSettings["debugSettings"])


# --- FILE PATHS ---
eatSoundFile = os.path.join(base_path, 'assets', 'sounds', 'eat.wav')
gameOverSoundFile = os.path.join(base_path, 'assets', 'sounds', 'game_over.wav')
buttonClickSoundFile = os.path.join(base_path, 'assets', 'sounds', 'click.wav')


snakeHeadFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_head.png')
snakeBodyFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_body_straight.png')
snakeTailFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_body_end.png')
snakeTurnFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_body_corner.png')
snakeHeadLoseFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_head_lose.png')

appleFile = os.path.join(base_path, 'assets', 'images', 'food', 'apple.png') # Assumed path for the apple
splashLogoFile = os.path.join(base_path, 'assets', 'images', 'splash_screen.png') # Path for the new splash logo
fontFile = os.path.join(base_path, 'assets', 'fonts', 'PixelifySans-Regular.ttf') # Path for the new pixel font

# --- DYNAMICALLY LOADED ASSETS ---
# These are initialized to None and will be loaded by the load_assets function.
eatSound = None
gameOverSound = None
buttonClickSound = None
snakeImages = {}
splashLogoImage = None
foodImages = {}
scoreFont = None
titleFont = None
smallFont = None
debugFont = None

# --- [NEW] Easter Egg Loading Messages ---
LoadingMessagesSounds = [
    "Calibrating audio synthesizers...", "Composing 8-bit symphonies...",
    "Teaching snakes to hiss...", "Polishing the 'nom nom' sound..."
]
LoadingMessagesSnake = [
    "Stitching pixels together...", "Herding digital serpents...",
    "Untangling Python code...", "Applying googly eyes..."
    "Painting the snakes..."
]
LoadingMessagesFood = [
    "Polishing the apples...", "Checking for worms...",
    "Debating apple nutritional value...", "Hiding golden apples...",
    "Buying apples...", "Crafting golden apples..."
]
LoadingMessagesFonts = [
    "Perfecting pixel typography...", "Choosing the right font weight...",
    "Making sure the 'S' is snake-like...", "Kerning the characters...",
    "Writing the text...", "Participating in spelling bees..."
]
LoadingMessagesDone = ["Ready to slither!", "Let the feast begin!", "Game loaded. Good luck!"]

# --- ASSET LOADING FUNCTION ---
def load_assets():
    """
    Loads all game assets in steps, yielding progress. This is a generator.
    Each yield returns: (current_step, total_steps, message)
    """
    global eatSound, gameOverSound, buttonClickSound, snakeImages, splashLogoImage, foodImages
    global scoreFont, titleFont, smallFont, debugFont
    total_steps = 4
    import time # Import the time module for adding delays

    # Step 1: Load Sounds
    yield (0, total_steps, random.choice(LoadingMessagesSounds))
    try:
        eatSound = pygame.mixer.Sound(eatSoundFile)
        gameOverSound = pygame.mixer.Sound(gameOverSoundFile)
        buttonClickSound = pygame.mixer.Sound(buttonClickSoundFile)
        buttonClickSound.set_volume(0.5)
    except pygame.error as e:
        error_handler.show_error_message("Asset Warning", f"Could not load a sound file.\n\nDetails: {e}", isFatal=False)
        eatSound, gameOverSound, buttonClickSound = pygame.mixer.Sound(buffer=b''), pygame.mixer.Sound(buffer=b''), pygame.mixer.Sound(buffer=b'')

    # Step 2: Load Snake Images
    yield (1, total_steps, random.choice(LoadingMessagesSnake))
    # time.sleep(5)

    try:
        snakeImages = {
            'head': pygame.image.load(snakeHeadFile).convert_alpha(),
            'body': pygame.image.load(snakeBodyFile).convert_alpha(),
            'tail': pygame.image.load(snakeTailFile).convert_alpha(),
            'turn': pygame.image.load(snakeTurnFile).convert_alpha(),
            'head_lose': pygame.image.load(snakeHeadLoseFile).convert_alpha(),
        }
    except pygame.error as e:
        error_handler.show_error_message("Fatal Asset Error", f"A critical snake image could not be loaded.\n\nDetails: {e}", isFatal=True)

    # Step 3: Load Food Images
    yield (2, total_steps, random.choice(LoadingMessagesFood))
    # time.sleep(0.3)

    try:
        foodImages = {'apple': pygame.image.load(appleFile).convert_alpha()}
    except pygame.error as e:
        error_handler.show_error_message("Fatal Asset Error", f"The food image could not be loaded.\n\nDetails: {e}", isFatal=True)

    # Step 4: Load Fonts
    yield (3, total_steps, random.choice(LoadingMessagesFonts))
    # time.sleep(0.3)

    try:
        scoreFont = pygame.font.Font(fontFile, 35)
        titleFont = pygame.font.Font(fontFile, 60)
        smallFont = pygame.font.Font(fontFile, 30)
        debugFont = pygame.font.Font(fontFile, 18)
    except Exception as e:
        error_handler.show_error_message("Font Warning", f"Custom font could not be loaded.\n\nDetails: {e}", isFatal=False)
        scoreFont = pygame.font.Font(None, 35)
        titleFont = pygame.font.Font(None, 60)
        smallFont = pygame.font.Font(None, 30)
        debugFont = pygame.font.Font(None, 18)
    
    yield (4, total_steps, random.choice(LoadingMessagesDone))


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