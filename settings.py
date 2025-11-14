import pygame
import os
import sys
import settings_manager

# --- PYINSTALLER PATH FIX ---
# This is the 'sys._MEIPASS' logic, which finds our assets (sounds, fonts)
# whether we are running as a .py script or a bundled .exe
if getattr(sys, 'frozen', False):
    # Running as a bundled .exe
    base_path = sys._MEIPASS # For assets inside the .exe
else:
    # Running as a .py script
    base_path = os.path.dirname(os.path.abspath(__file__)) # For assets next to the .py

# --- [NEW] APP DATA PATH FOR HIGH SCORE ---
# This is the professional way to store user-specific game data.
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

# --- [MODIFIED] WINDOW & GAME CONSTANTS ---
# Set a default starting size for the window.
# The user can resize it.
initialWidth = 1280
initialHeight = 720

# --- [NEW] DYNAMIC SCALING CONSTANTS ---
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

# --- [MODIFIED] CREATE THE RESIZABLE WINDOW ---
# We create the window here so all other modules can draw on it
# pygame.RESIZABLE allows the user to change the window size.
# pygame.DOUBLEBUF is recommended for smoother rendering.
gameTitle = "ANAHKEN's Modular Snake Game"
window = pygame.display.set_mode((initialWidth, initialHeight), pygame.RESIZABLE | pygame.DOUBLEBUF)
pygame.display.set_caption(gameTitle)
clock = pygame.time.Clock()

# --- COLORS ---
white = (255, 255, 255) # General UI text
backgroundColor = (0, 0, 0) # The play area background
borderColor = (40, 40, 40) # The color of the letterbox border
uiElementColor = (100, 100, 100)  # For UI elements like inactive buttons

# --- [NEW] PRE-DEFINED COLOR OPTIONS FOR SETTINGS MENU ---
colorOptions = {
# These are RGB color values for snake colors. 
    "Green": (0, 255, 0),
    "Blue": (0, 100, 255),
    "Purple": (148, 0, 211),
    "Orange": (255, 165, 0),
    "Pink": (255, 105, 180),
    "Cyan": (0, 255, 255), 
}

# --- [NEW] Special Food Settings ---
# --- [NEW] CUSTOMIZABLE COLORS ---
foodColor = (255, 0, 0) # A pure, bright red for maximum vibrancy
gameOverColor = (255, 0, 0) # A bright, classic red for game over

# --- Special Food Settings ---
gold = (255, 215, 0)  # Color for the special food
goldenFoodScore = 5
goldenFoodChance = 15 # Represents a 1 in 15 chance

# --- [TEMPLATE] FOR NEW FOOD ---
# To add a new food type, first define its properties here.
# BLUE = (0, 100, 255) # 1. Add a new color for it.
# speedFoodScore = 2 # 2. Define its score value.
# speedFoodChance = 10 # 3. Define its spawn chance (e.g., 1 in 10).

# --- [TEMPLATE] FOR NEW ENTITY COLORS ---
# obstacleColor = (128, 128, 128)

# --- DEFAULT SETTINGS DICTIONARY ---
# --- [MODIFIED] Add keybinds to the default settings ---
defaultSettings = {
    "snakeColorName": "Green",
    "keybinds": {
        'UP': [pygame.K_UP, pygame.K_w],
        'DOWN': [pygame.K_DOWN, pygame.K_s],
        'LEFT': [pygame.K_LEFT, pygame.K_a],
        'RIGHT': [pygame.K_RIGHT, pygame.K_d],
    }
}

# --- LOAD SAVED SETTINGS ---
settingsFile = settings_manager.get_settings_path(appDataFolder)
userSettings = settings_manager.load_settings(settingsFile)

if userSettings is None: userSettings = {} # Ensure userSettings is a dict

# --- APPLY LOADED/DEFAULT SETTINGS ---
snakeColor = colorOptions.get(userSettings.get("snakeColorName", defaultSettings["snakeColorName"]), colorOptions["Green"])
keybinds = userSettings.get("keybinds", defaultSettings["keybinds"])


# --- FILE PATHS ---
eatSoundFile = os.path.join(base_path, 'assets', 'sounds', 'eat.wav')
gameOverSoundFile = os.path.join(base_path, 'assets', 'sounds', 'game_over.wav')

# --- LOAD ASSETS (FONTS & SOUNDS) ---
# --- [TEMPLATE] FOR NEW SOUNDS ---
# To add a new sound, first define its file path.
# obstacleHitSoundFile = os.path.join(base_path, 'assets', 'sounds', 'obstacle_hit.wav')

# --- [TEMPLATE] FOR IMAGES ---
# To add an image (like a game icon), first define its file path.
snakeHeadFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_head.png')
snakeBodyFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_body_straight.png')
snakeTailFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_body_end.png')
snakeTurnFile = os.path.join(base_path, 'assets', 'images', 'snake', 'snake_body_corner.png')
appleFile = os.path.join(base_path, 'assets', 'images', 'food', 'apple.png') # Assumed path for the apple

try:
    eatSound = pygame.mixer.Sound(eatSoundFile)
    gameOverSound = pygame.mixer.Sound(gameOverSoundFile)
    # --- [TEMPLATE] FOR LOADING NEW SOUNDS ---
    # obstacleHitSound = pygame.mixer.Sound(obstacleHitSoundFile)
except pygame.error as e:
    print(f"Warning: Could not load sound files: {e}")
    # Create "dummy" sound objects
    eatSound = pygame.mixer.Sound(buffer=b'') 
    gameOverSound = pygame.mixer.Sound(buffer=b'')
    # obstacleHitSound = pygame.mixer.Sound(buffer=b'')

# --- [NEW] Load Snake Sprites in a separate block for better error handling ---
try:
    snakeImages = {
        'head': pygame.image.load(snakeHeadFile).convert_alpha(),
        'body': pygame.image.load(snakeBodyFile).convert_alpha(),
        'tail': pygame.image.load(snakeTailFile).convert_alpha(),
        'turn': pygame.image.load(snakeTurnFile).convert_alpha(),
    }
except pygame.error as e:
    print(f"FATAL: Could not load snake image files: {e}")
    print("Please ensure the 'assets/images/snake/' folder and its contents are correct.")
    snakeImages = {} # Set to empty dict so the game doesn't crash immediately

# --- [NEW] Load Food Sprites ---
try:
    foodImages = {
        'apple': pygame.image.load(appleFile).convert_alpha(),
    }
except pygame.error as e:
    print(f"FATAL: Could not load food image files: {e}")
    foodImages = {}

try:
    scoreFont = pygame.font.SysFont('timesnewroman', 35)
    titleFont = pygame.font.SysFont('timesnewroman', 60)
    smallFont = pygame.font.SysFont('timesnewroman', 30)
except Exception as e:
    print(f"Warning: Could not load fonts. Using default. Error: {e}")
    scoreFont = pygame.font.Font(None, 35)
    titleFont = pygame.font.Font(None, 60)
    smallFont = pygame.font.Font(None, 30)

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

# --- [NEW] DYNAMIC FONT SIZES ---
# Store the base sizes to be used for scaling
baseScoreFontSize = 35
baseTitleFontSize = 60
baseSmallFontSize = 30