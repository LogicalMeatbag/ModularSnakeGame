import pygame
import os
import sys
import error_handler
import settings_manager
import random
from typing import TypedDict, Any

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
# The window is initialized here, but will be re-initialized if vsync is toggled.
# We need to load the vsync setting before this call.
tempUserSettings = settings_manager.load_settings(settings_manager.get_settings_path(appDataFolder)) or {}
initialVsync = tempUserSettings.get("vsync", True)
window = pygame.display.set_mode((initialWidth, initialHeight), pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1 if initialVsync else 0)
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

colorOptions: dict[str, tuple[int, int, int]] = {
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

SPLASH_FADE_IN_DURATION = 1000  # 1 second to fade in
SPLASH_STAY_DURATION = 1500     # 1.5 seconds to stay on screen
SPLASH_FADE_OUT_DURATION = 500  # 0.5 seconds to fade out

DEATH_ANIMATION_INITIAL_PAUSE = 250 # A brief pause before the animation starts.
SNAKE_SIZE_ANIMATION_DURATION = 750 # How long the grow/shrink animation takes.
DEATH_FADE_OUT_DURATION = 1000 # How long the entire snake takes to fade out.

# Event-specific values
APPLES_GALORE_COUNT = 15
GOLDEN_APPLE_RAIN_COUNT = 10
BEEG_SNAKE_GROWTH = 10
SMALL_SNAKE_SHRINK = 5
RACECAR_SNAKE_SPEED_BOOST = 15
SLOW_SNAKE_SPEED_REDUCTION = 5

# Used for weighted random selection. Higher numbers are more likely.
DEFAULT_EVENT_WEIGHTS: dict[str, int] = {
    "Apples Galore": 10, "Golden Apple Rain": 5, "BEEEG Snake": 10, 
    "Small Snake": 10, "Racecar Snake": 8, "Slow Snake": 8
}

# --- [REFACTOR] Typed Dictionaries for Strict Type Safety ---
# These classes define the exact "shape" of our settings dictionaries,
# which resolves a host of strict-mode type errors.

class DebugSettingsDict(TypedDict):
    showState: bool
    showSnakePos: bool
    showSnakeLen: bool
    showSpeed: bool
    showNormalSpeed: bool
    showEventTimer: bool
    showActiveEvent: bool
    showEventTimeLeft: bool
    showSizeEventActive: bool
    showPreEventLen: bool
    eventChanceOverride: int
    goldenAppleChanceOverride: int
    eventTimerMaxOverride: int
    eventDurationOverride: int
    eventCountdownDurationOverride: int
    applesGaloreCountOverride: int
    goldenAppleRainCountOverride: int
    beegSnakeGrowthOverride: int
    smallSnakeShrinkOverride: int
    racecarSpeedBoostOverride: int
    slowSnakeSpeedReductionOverride: int
    eventChancesOverride: dict[str, int]

class UserSettingsDict(TypedDict):
    snakeColorName: str
    customColor: list[int]
    keybinds: dict[str, list[int]]
    debugMode: bool
    rainbowModeUnlocked: bool
    showFps: bool
    vsync: bool
    maxFps: int
    debugSettings: DebugSettingsDict

# --- DEFAULT SETTINGS DICTIONARY ---
defaultSettings: UserSettingsDict = {
    "snakeColorName": "Green",
    "customColor": list(colorOptions["Green"]),
    "keybinds": {
        'UP': [pygame.K_UP, pygame.K_w],
        'DOWN': [pygame.K_DOWN, pygame.K_s],
        'LEFT': [pygame.K_LEFT, pygame.K_a],
        'RIGHT': [pygame.K_RIGHT, pygame.K_d],
    },
    "debugMode": False,
    "rainbowModeUnlocked": False, # Easter Egg
    "showFps": False, # Moved from debugSettings
    "vsync": True,
    "maxFps": 144,
    "debugSettings": DebugSettingsDict({
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
        "goldenAppleChanceOverride": 15,
        "eventTimerMaxOverride": 15, # In seconds
        "eventDurationOverride": 10, # In seconds
        "eventCountdownDurationOverride": 5, # In seconds
        "applesGaloreCountOverride": 15,
        "goldenAppleRainCountOverride": 10,
        "beegSnakeGrowthOverride": 10,
        "smallSnakeShrinkOverride": 5,
        "racecarSpeedBoostOverride": 15, # The comma was missing on the line above this one
        "slowSnakeSpeedReductionOverride": 5,
        "eventChancesOverride": DEFAULT_EVENT_WEIGHTS.copy()
    })
}

# --- LOAD SAVED SETTINGS ---
settingsFile = settings_manager.get_settings_path(appDataFolder)

def merge_settings(defaults, saved):
    """
    Recursively merges saved settings into the defaults. This ensures that
    new settings keys (including nested ones) are always present.
    """
    merged = defaults.copy()
    for key, value in saved.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged

# Load saved settings, or use an empty dict as a fallback.
savedUserSettings = settings_manager.load_settings(settingsFile) or {}

# Merge the loaded settings into the defaults to create the final, complete settings object.
# This ensures that any new settings added to defaultSettings are present.
userSettings: UserSettingsDict = merge_settings(defaultSettings, savedUserSettings)
debugSettings: DebugSettingsDict = userSettings["debugSettings"]

# --- APPLY LOADED/DEFAULT SETTINGS ---
savedColorName = userSettings["snakeColorName"]

if savedColorName == "Custom":
    snakeColor = tuple(userSettings["customColor"])
else:
    snakeColor = colorOptions.get(savedColorName, colorOptions["Green"])

# Directly access the validated settings from the userSettings dictionary.
keybinds, debugMode, rainbowModeUnlocked, showFps, vsync, maxFps = (
    userSettings["keybinds"], userSettings["debugMode"], userSettings["rainbowModeUnlocked"],
    userSettings["showFps"], userSettings["vsync"], userSettings["maxFps"]
)

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
debugFontFile = os.path.join(base_path, 'assets', 'fonts', 'consola.ttf') # Path for the new debug font

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
debugMenuFont = None

LoadingMessagesSounds = [
    "Calibrating audio synthesizers...", "Composing 8-bit symphonies...",
    "Teaching snakes to hiss...", "Polishing the 'nom nom' sound..."
]
LoadingMessagesSnake = [
    "Stitching pixels together...", "Herding digital serpents...",
    "Untangling Python code...", "Applying googly eyes...",
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
    global eatSound, gameOverSound, buttonClickSound, snakeImages, splashLogoImage, foodImages, debugMenuFont
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
        debugFont = pygame.font.Font(debugFontFile, 18) # Use Consolas for the overlay
        debugMenuFont = pygame.font.Font(debugFontFile, 24) # Use a larger Consolas for the menu
    except Exception as e:
        error_handler.show_error_message("Font Warning", f"Custom font could not be loaded.\n\nDetails: {e}", isFatal=False)
        scoreFont = pygame.font.Font(None, 35)
        titleFont = pygame.font.Font(None, 60)
        smallFont = pygame.font.Font(None, 30)
        debugFont = pygame.font.Font(None, 18)
        debugMenuFont = pygame.font.Font(None, 24)
    
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