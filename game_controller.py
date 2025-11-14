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
from game_entities import Snake, Food

class GameController:
    def __init__(self):
        """Initializes the game state."""
        self.snake = Snake()
        self.food = Food()
        # --- [TEMPLATE] FOR NEW ENTITIES ---
        # self.obstacles = Obstacle() 
        self.score = 0
        # --- [NEW] Separate speed from normal speed for events ---
        self.normalSpeed = settings.startSpeed
        self.speed = settings.startSpeed
        self.high_score = score_manager.load_high_score(settings.highScoreFile)
        
    def reset(self):
        """Resets the game to its starting state."""
        self.snake.reset()
        self.food.reset(self.snake.get_body())
        # --- [TEMPLATE] FOR NEW ENTITIES ---
        # self.obstacles.reset()
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

        # --- [MODIFIED] Check for food collision ---
        eaten_food = self.food.check_collision(self.snake.get_head_pos())
        
        if eaten_food:
            settings.eatSound.play()
            self.snake.grow() # Grow the snake
            
            # Apply effects based on food type
            if eaten_food['type'] == 'normal':
                self.score += 1
                self.normalSpeed += 1 # Increase the base speed
            elif eaten_food['type'] == 'golden':
                self.score += settings.goldenFoodScore
            # --- [TEMPLATE] FOR NEW FOOD ---
            # 6. Add the effect of eating the new food type.
            # elif eaten_food['type'] == 'speed':
            #     self.score += settings.speedFoodScore
            #     self.speed += 5 # e.g., temporary speed boost
            
            # --- [FIX] Only spawn new food if a food event is not active ---
            if not self.is_food_event_active(active_event):
                # --- [NEW] Use debug override if active ---
                chance = settings.debugSettings['goldenAppleChanceOverride'] if settings.debugMode else settings.goldenFoodChance
                self.food.spawn_new_food(self.snake.get_body(), chance)
        else:
            # --- [NEW] Only adjust speed if no event is active ---
            # This prevents speed from resetting mid-event
            if not self.is_speed_event_active():
                self.speed = self.normalSpeed
            self.snake.move() # No food, so just move

        # Check for game-over collisions
        if self.snake.check_wall_collision() or self.snake.check_collision():
            return True  # Game is over
        
        # --- [TEMPLATE] FOR NEW ENTITY COLLISIONS ---
        # for obstacle in self.obstacles.items:
        #     if self.snake.get_head_pos() == obstacle['pos']:
        #         settings.obstacleHitSound.play()
        #     return True  # Game is over

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

    def is_food_event_active(self, active_event):
        """Helper to check if a food-spawning event is active."""
        if not active_event: return False
        return active_event in ["Apples Galore", "Golden Apple Rain"]

    def is_speed_event_active(self):
        """
        Helper to check if a speed-modifying event is active.
        This is a bit of a hack; a more robust system would use an event state object.
        For now, we can infer it by comparing current speed to normal speed.
        """
        return self.speed != self.normalSpeed
            
    def draw(self, surface):
        """Draws all active game elements."""
        self.snake.draw(surface)
        self.food.draw(surface)
        # --- [TEMPLATE] FOR NEW ENTITIES ---
        # self.obstacles.draw(surface)
        # We draw the score here because it's part of the 'playing' screen
        ui.draw_score(surface, self.score, self.high_score)

# Need to import ui after the class is defined to avoid circular import
import ui

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