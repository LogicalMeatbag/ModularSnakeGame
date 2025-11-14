# ANAHKEN's Modular Snake Game

A classic implementation of the Snake game, built with Python and Pygame, featuring a clean, modular, and easily customizable code structure.

![A player playing ANAHKEN's Modular Snake Game.](https://github.com/user-attachments/assets/0a8ca9b5-dd17-482f-8d38-268852190e6d)

## Features

*   **Classic Snake Gameplay**: Eat food to grow longer and increase your score.
*   **Dynamic Random Events**: Keep on your toes! The game can randomly trigger events like "Apples Galore", "Golden Apple Rain", "BEEEG Snake", and more to change up the gameplay.
*   **Advanced In-Game Settings Menu**:
    *   **Color Customization**: Choose from presets or create your own unique snake color with RGB sliders and direct value input.
    *   **Keybinding Configuration**: Remap your controls for up, down, left, and right movements.
*   **Modern & Resizable Window**: Start at any size and resize the window on the fly. The game grid adapts automatically.
*   **Persistent High Score**: Your best score is automatically saved (and compressed!) in your user profile's AppData folder.
*   **Polished UI/UX**: Enjoy sprite-based graphics, intelligent food spawning, a pause menu, and satisfying audio feedback.
*   **Clean, Modular Code**: The project is split into logical modules, making it easy to understand and extend.
*   **Robust Error Handling**: Clear, visual error messages guide the user if assets are missing or the environment is set up incorrectly.
*   **Developer-Friendly Features**:
    *   **Comprehensive Debug Mode**: Toggle a real-time overlay showing game state variables, and access a special menu to override event chances for easy testing.
    *   **High-Refresh-Rate Ready**: Uses a V-Sync'd, delta-time-based game loop for perfectly smooth rendering on any monitor (60Hz, 144Hz, etc.).
*   **Ready for Distribution**: Contains logic to correctly find assets when bundled into a single executable with tools like PyInstaller.

## Requirements

To run the game from the source code, you will need:

*   **Python 3.8+**
*   **Pygame 2.0+**

## How to Run

There are two ways to play the game.

### From an Executable (Easiest)

If you have a `.exe` version of the game:
1.  Double-click the `.exe` file.
2.  Your high score will be saved automatically in `%APPDATA%\ANAHKENsSnake\`.

### From the Source Code

1.  **Clone or download the repository:**
    ```sh
    git clone https://github.com/LogicalMeatbag/ModularSnakeGame.git
    cd ModularSnakeGame
    ```

2.  **Install Pygame:**
    Open your terminal or command prompt and run:
    ```sh
    pip install pygame
    ```

3.  **Run the game:**
    Execute the `main.py` script:
    ```sh
    python main.py
    ```
    *(Note: Thanks to a robust launcher script, you can actually run any of the project's `.py` files to start the game.)*

## Customization

The game now offers two levels of customization:

### In-Game Settings
From the main menu, you can enter the **Settings** screen to:
*   Change the **Snake Color**.
*   **Configure Controls** for up, down, left, and right movements.
*   Enable **Debug Mode** and access its own configuration menu.

These settings are saved automatically in a `settings.dat` file in your AppData folder.

### Code-Level Settings (`settings.py`)
For more advanced changes, you can edit the `settings.py` file to modify:
*   **Game Speed**: Change `startSpeed` to make the game begin faster or slower.
*   **Grid Layout**: Change `gridWidth` and `gridHeight` to alter the number of blocks in the play area.
*   **Food Properties**: Adjust colors, scores, and spawn chances for different food types.
*   **Default Fonts and Colors**: Change the look and feel of the UI.

## File Structure

*   `main.py`: The main entry point of the application. It contains the main game loop and manages the overall game state (Main Menu, Playing, Game Over).
*   `settings.py`: A central configuration file. Contains all constants like colors, window dimensions, file paths, fonts, and loaded assets.
*   `game_controller.py`: Manages a single game session. It holds the snake and food objects, tracks the score, and handles the core update logic (movement, eating, collisions).
*   `game_entities.py`: Defines the classes for the objects in the game: `Snake` and `Food`. These classes manage their own state and drawing logic.
*   `ui.py`: Contains simple functions for drawing UI elements to the screen, such as the main menu, game over screen, and score display.
*   `score_manager.py`: A utility module for loading and saving the obfuscated and compressed high score file (`highscore.dat`).
*   `settings_manager.py`: A utility module for loading and saving the user's custom settings (`settings.dat`).
*   `assets/`: A folder containing subdirectories for all game assets.
    *   `assets/images`: Contains all the images for the game.
    *   `assets/sounds`: Contains all the sounds for the game.

## Building from Source

This project is set up to be easily bundled into a single executable using **PyInstaller**.

1.  **Install PyInstaller:**
    ```sh
    pip install pyinstaller
    ```

2.  **Run the PyInstaller command:**
    Open a terminal in the project directory and run the following command. The `--add-data` flags are crucial for including the sound files.
    The simplest way is to copy the entire `assets` folder.
    ```sh
    pyinstaller --onefile --windowed --name "SnakeGame" --icon="assets/images/icon.png" --add-data "assets;assets" main.py
    ```

3.  **Find your executable:**
    PyInstaller will create a `dist` folder containing `SnakeGame.exe`. This file can be shared and run on other Windows machines without needing Python or Pygame installed.

## License

This project is open source and available under the MIT License.
