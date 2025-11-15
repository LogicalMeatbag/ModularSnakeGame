"""
game_controller.py
- Defines the GameController class.
- This class manages the state of a single game session:
  - Holds the snake, food, score, and speed.
  - Handles the update logic (moving, collisions, eating).
  - Handles user input during play.
  - Knows how to save the high score.
"""
import pygame
import settings
import score_manager
import ui
from game_entities import Snake, Food

class GameController:
    def __init__(self):
        """Initializes the game state."""
        self.snake = Snake()
        self.food = Food()
        # self.obstacles = Obstacle() # Example for new entities
        self.score = 0
        self.normalSpeed = settings.startSpeed
        self.speed = settings.startSpeed
        self.high_score = score_manager.load_high_score(settings.highScoreFile)
        
    def reset(self):
        """Resets the game to its starting state."""
        self.snake.reset()
        self.food.reset(self.snake.get_body())
        # self.obstacles.reset() # Example for new entities
        self.score = 0
        self.normalSpeed = settings.startSpeed
        self.speed = self.normalSpeed
        # High score persists, so we reload it
        self.high_score = score_manager.load_high_score(settings.highScoreFile)

    def handle_input(self, event):
        """Handles key presses during the 'PLAYING' state."""
        if event.type == pygame.KEYDOWN:
            self.snake.change_direction(event.key)

    def update(self, active_event=None):
        """
        Updates the game state by one frame.
        Moves snake, checks for collisions, etc.
        Returns True if the game is over, False otherwise.
        """
        self.snake.update_position()

        eaten_food = self.food.check_collision(self.snake.get_head_pos())
        
        if eaten_food:
            settings.eatSound.play()
            self.snake.grow() # Grow the snake
            
            # Apply effects based on food type
            if eaten_food['type'] == 'normal':
                self.score += 1
            elif eaten_food['type'] == 'golden':
                self.score += settings.goldenFoodScore
            # elif eaten_food['type'] == 'speed':
            #     self.score += settings.speedFoodScore
            #     self.speed += 5 # e.g., temporary speed boost
            
            # Speed now increases based on score, which is a more balanced progression.
            self.normalSpeed = settings.startSpeed + (self.score // 5) # e.g., speed increases every 5 points

            # Only spawn a new normal apple when a normal apple is eaten.
            # This prevents the normal apple from respawning when a golden one is eaten, for instance.
            if eaten_food['type'] == 'normal':
                if not self.is_food_event_active(active_event):
                    chance = settings.debugSettings['goldenAppleChanceOverride'] if settings.debugMode else settings.goldenFoodChance
                    self.food.spawn_new_food(self.snake.get_body(), chance)
        else:
            # If no food was eaten, and no speed event is active, ensure speed matches normalSpeed.
            if not self.is_speed_event_active(active_event):
                self.speed = self.normalSpeed # This is the default behavior
            self.snake.move() # No food, so just move

        # Check for game-over collisions
        if self.snake.check_wall_collision() or self.snake.check_collision():
            return True  # Game is over
        
        # for obstacle in self.obstacles.items:
        #     if self.snake.get_head_pos() == obstacle['pos']:
        #         settings.obstacleHitSound.play()
        
        # --- [TEMPLATE] How to add ongoing event logic ---
        # if active_event == "My New Event":
        #     # This code will run every game tick while the event is active.
        #     # For example, you could slowly drain the player's score.
        #     self.score = max(0, self.score - 0.01)

        return False # Game continues
        
    def save_score_if_high(self):
        """Checks and saves the high score."""
        if self.score > self.high_score:
            self.high_score = self.score
            score_manager.save_high_score(settings.highScoreFile, self.high_score)

    def start_event(self, event_name):
        """Applies the effects of a random event."""
        if event_name == "Apples Galore":
            self.food.spawn_galore('normal', settings.APPLES_GALORE_COUNT, self.snake.get_body())
        elif event_name == "Golden Apple Rain":
            self.food.spawn_galore('golden', settings.GOLDEN_APPLE_RAIN_COUNT, self.snake.get_body())
        elif event_name == "BEEEG Snake":
            self.snake.is_size_event_active = True
            self.snake.pre_event_length = len(self.snake.get_body())
            self.snake.grow_by(settings.BEEG_SNAKE_GROWTH)
        elif event_name == "Small Snake":
            self.snake.is_size_event_active = True
            self.snake.pre_event_length = len(self.snake.get_body())
            self.snake.shrink_by(settings.SMALL_SNAKE_SHRINK)
        elif event_name == "Racecar Snake":
            self.speed = self.normalSpeed + settings.RACECAR_SNAKE_SPEED_BOOST
        elif event_name == "Slow Snake":
            self.speed = max(5, self.normalSpeed - settings.SLOW_SNAKE_SPEED_REDUCTION)
        
        # --- [TEMPLATE] How to add a new event ---
        # 1. Add the name to `event_list` in main.py.
        # 2. Add constants to `settings.py` (e.g., MY_NEW_EVENT_VALUE = 5).
        # 3. Add the logic here.
        # elif event_name == "My New Event":
        #     self.score += settings.MY_NEW_EVENT_VALUE

    def stop_event(self, event_name):
        """Resets the effects of a timed event."""
        # Handle different event types
        if event_name in ["Racecar Snake", "Slow Snake"]:
            self.speed = self.normalSpeed
        elif event_name in ["BEEEG Snake", "Small Snake"]:
            self.snake.revert_size()
            self.snake.is_size_event_active = False
            self.snake.pre_event_length = 0
        # For food events, clear all food and spawn one new normal apple.
        elif event_name in ["Apples Galore", "Golden Apple Rain"]:
            self.food.reset(self.snake.get_body())
        
        # --- [TEMPLATE] How to revert a temporary event ---
        # 1. Add the event name to the `if` check in main.py to show the revert countdown.
        # 2. Add the cleanup logic here.
        # elif event_name == "My New Temporary Event":
        #     # Revert any changes made when the event started.

    def is_food_event_active(self, active_event):
        """Helper to check if a food-spawning event is active."""
        if not active_event: return False
        return active_event in ["Apples Galore", "Golden Apple Rain"]

    def is_speed_event_active(self, active_event):
        """
        Helper to check if a speed-modifying event is active.
        This is now done by explicitly checking the active event name.
        """
        return active_event in ["Racecar Snake", "Slow Snake"]
            
    def draw(self, surface):
        """Draws all active game elements."""
        self.snake.draw(surface)
        self.food.draw(surface)
        # self.obstacles.draw(surface) # Example for new entities
        # We draw the score here because it's part of the 'playing' screen
        ui.draw_score(surface, self.score, self.high_score) # This function is now available

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