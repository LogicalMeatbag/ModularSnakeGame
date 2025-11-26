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
        """Handles all forms of input during the 'PLAYING' state using the settings bindings."""
        
        # --- Helper to convert a Pygame event into a consistent string format ---
        def get_input_string(e):
            if e.type == pygame.JOYBUTTONDOWN:
                return f"button_{e.button}"
            if e.type == pygame.JOYHATMOTION:
                # Hat motion is unique; we create separate strings for each direction
                if e.value[0] == 1: return f"hat_{e.hat}_x_1"
                if e.value[0] == -1: return f"hat_{e.hat}_x_-1"
                if e.value[1] == 1: return f"hat_{e.hat}_y_1"
                if e.value[1] == -1: return f"hat_{e.hat}_y_-1"
            if e.type == pygame.JOYAXISMOTION:
                # Axis motion is also unique; we create strings for positive/negative directions
                if e.value > settings.joystickDeadzone: return f"axis_{e.axis}_pos"
                if e.value < -settings.joystickDeadzone: return f"axis_{e.axis}_neg"
            return None

        input_str = get_input_string(event)
        binds = settings.userSettings['controllerBinds']

        # --- Check against all input types ---
        if event.type == pygame.KEYDOWN:
            self.snake.change_direction(event.key)
        elif input_str:
            # Check if the generated input string matches any of our bound actions
            if input_str == binds.get('UP'):
                self.snake.change_direction(settings.keybinds['UP'][0])
            elif input_str == binds.get('DOWN'):
                self.snake.change_direction(settings.keybinds['DOWN'][0])
            elif input_str == binds.get('LEFT'):
                self.snake.change_direction(settings.keybinds['LEFT'][0])
            elif input_str == binds.get('RIGHT'):
                self.snake.change_direction(settings.keybinds['RIGHT'][0])

    def update(self, active_event=None):
        """
        Updates the game state by one frame.
        Moves snake, checks for collisions, etc.
        Returns True if the game is over, False otherwise.
        """
        # --- [REFACTOR] Look Before You Leap ---
        # 1. Determine the next position of the snake's head.
        next_pos = list(self.snake.get_head_pos())
        self.snake.direction = self.snake.change_to # Lock in direction for this tick
        if self.snake.direction == 'UP':
            next_pos[1] -= 1
        elif self.snake.direction == 'DOWN':
            next_pos[1] += 1
        elif self.snake.direction == 'LEFT':
            next_pos[0] -= 1
        elif self.snake.direction == 'RIGHT':
            next_pos[0] += 1

        # 2. Check if this next position is a game-over collision.
        if self.snake.check_collision(next_pos) or self.snake.check_wall_collision(next_pos):
            return True # Game is over, snake does not move.

        # 3. If the move is safe, update the snake's position.
        self.snake.update_position(next_pos)

        # 4. Check for food collision at the new, safe position.
        eaten_food = self.food.check_collision(next_pos)
        
        if eaten_food:
            settings.eatSound.play()
            self.snake.grow()
            if eaten_food['type'] == 'normal':
                self.score += 1
            elif eaten_food['type'] == 'golden':
                self.score += settings.goldenFoodScore
            self.normalSpeed = settings.startSpeed + (self.score // 5) # e.g., speed increases every 5 points
            if eaten_food['type'] == 'normal':
                if not self.is_food_event_active(active_event):
                    chance = settings.debugSettings['goldenAppleChanceOverride'] if settings.debugMode else settings.goldenFoodChance
                    self.food.spawn_new_food(self.snake.get_body(), chance)

        # 5. Move the snake. The snake class itself now knows whether to pop its tail.
        self.snake.move()

        return False # Game continues
        
    def save_score_if_high(self):
        """Checks and saves the high score."""
        if self.score > self.high_score:
            self.high_score = self.score
            score_manager.save_high_score(settings.highScoreFile, self.high_score)

    def start_event(self, event_name):
        """Applies the effects of a random event."""
        # In strict mode, we access debugSettings directly, but only use the
        # values if debugMode is True. This ensures type safety.

        if event_name == "Apples Galore":
            count = settings.debugSettings['applesGaloreCountOverride'] if settings.debugMode else settings.APPLES_GALORE_COUNT
            self.food.spawn_galore('normal', count, self.snake.get_body())
        elif event_name == "Golden Apple Rain":
            count = settings.debugSettings['goldenAppleRainCountOverride'] if settings.debugMode else settings.GOLDEN_APPLE_RAIN_COUNT
            self.food.spawn_galore('golden', count, self.snake.get_body())
        elif event_name == "BEEEG Snake":
            self.snake.is_size_event_active = True
            self.snake.pre_event_length = len(self.snake.get_body())
            growth = settings.debugSettings['beegSnakeGrowthOverride'] if settings.debugMode else settings.BEEG_SNAKE_GROWTH
            self.snake.grow_by(growth)
        elif event_name == "Small Snake":
            self.snake.is_size_event_active = True
            self.snake.pre_event_length = len(self.snake.get_body())
            shrink = settings.debugSettings['smallSnakeShrinkOverride'] if settings.debugMode else settings.SMALL_SNAKE_SHRINK
            self.snake.shrink_by(shrink)
        elif event_name == "Racecar Snake":
            boost = settings.debugSettings['racecarSpeedBoostOverride'] if settings.debugMode else settings.RACECAR_SNAKE_SPEED_BOOST
            self.speed = self.normalSpeed + boost
        elif event_name == "Slow Snake":
            reduction = settings.debugSettings['slowSnakeSpeedReductionOverride'] if settings.debugMode else settings.SLOW_SNAKE_SPEED_REDUCTION
            self.speed = max(5, self.normalSpeed - reduction)
        
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
            self.snake.pre_event_length = 0 # Reset for the next event
            self.snake.growth_during_event = 0 # [FIX] This was the missing piece
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
            
    def draw(self, surface, isDying=False, fadeProgress=None):
        """Draws all active game elements."""
        self.snake.draw(surface, isDying, fadeProgress)
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