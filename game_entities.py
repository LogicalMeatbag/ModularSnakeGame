"""
game_entities.py
- Defines the classes for the objects in our game (Snake, Food).
- This is an object-oriented approach.
"""
import pygame
import random
import settings
import ui # Import ui to access the new tint_surface utility

class Snake:
    def __init__(self):
        self.reset()
        self.scaled_images = {}
        self.last_block_size = -1 # Force a rescale on the first draw
        self.pre_event_length = 0
        self.is_size_event_active = False
        self.growth_during_event = 0


    def reset(self):
        """Resets the snake to its starting position and state."""
        start_x = settings.gridWidth // 2
        start_y = settings.gridHeight // 2
        self.pos = [start_x, start_y]
        self.direction = 'RIGHT'
        self.change_to = self.direction
        
        segment2_x = start_x - 1 # One block to the left
        
        self.body = [[start_x, start_y], [segment2_x, start_y]]
        # Reset event state
        self.pre_event_length = 0
        self.is_size_event_active = False
        self.growth_during_event = 0

    def change_direction(self, event_key):
        """Updates the snake's target direction based on key presses."""
        if event_key in settings.keybinds['UP'] and self.direction != 'DOWN':
            self.change_to = 'UP'
        if event_key in settings.keybinds['DOWN'] and self.direction != 'UP':
            self.change_to = 'DOWN'
        if event_key in settings.keybinds['LEFT'] and self.direction != 'RIGHT':
            self.change_to = 'LEFT'
        if event_key in settings.keybinds['RIGHT'] and self.direction != 'LEFT':
            self.change_to = 'RIGHT'

    def update_position(self):
        """Moves the snake by one block in its current direction."""
        # Validate the direction change
        self.direction = self.change_to
        
        if self.direction == 'UP':
            self.pos[1] -= 1
        elif self.direction == 'DOWN':
            self.pos[1] += 1
        elif self.direction == 'LEFT':
            self.pos[0] -= 1
        elif self.direction == 'RIGHT':
            self.pos[0] += 1

        # The snake's head always moves to the new position.
        self.body.insert(0, list(self.pos))

    def grow(self):
        """Grows the snake by not removing the tail segment. This is called when food is eaten."""
        if self.is_size_event_active:
            self.growth_during_event += 1
        pass

    def grow_by(self, amount):
        """Instantly grows the snake by a given amount for the 'BEEEG Snake' event."""
        if not self.body: return
        tail_segment = self.body[-1]
        for _ in range(amount):
            self.body.append(list(tail_segment)) # Add copies of the tail segment

    def shrink_by(self, amount):
        """
        Instantly shrinks the snake for the 'Small Snake' event, but not
        to a length less than 2.
        """
        min_length = 2
        current_length = len(self.body)
        
        # Calculate how many segments can be safely removed
        removable_segments = current_length - min_length
        segments_to_remove = min(amount, removable_segments)
        self.body = self.body[:-segments_to_remove]

    def revert_size(self):
        """Reverts the snake's size to its pre-event length."""
        # Calculate the final target length: the length before the event, plus any growth during it.
        target_length = self.pre_event_length + self.growth_during_event
        current_length = len(self.body)

        if current_length > target_length:
            # If we are longer than the target (e.g., BEEEG event), shrink to target.
            self.body = self.body[:target_length]
        elif current_length < target_length:
            # If we are shorter (e.g., Small event), grow to target.
            self.grow_by(target_length - current_length)
    
    def move(self):
        """Moves the snake by removing the tail segment (when no food is eaten)."""
        self.body.pop()

    def check_collision(self):
        """Checks for wall collisions or self-collisions."""
        # Self-collision
        for block in self.body[1:]:
            if self.pos[0] == block[0] and self.pos[1] == block[1]:
                return True
        return False
    
    def check_wall_collision(self):
        """Checks only for wall collisions. Separated for clarity."""
        # --- [REFACTOR] Check against grid dimensions ---
        if (self.pos[0] < 0 or self.pos[0] >= settings.gridWidth or
            self.pos[1] < 0 or self.pos[1] >= settings.gridHeight):
            return True

    def get_head_pos(self):
        """Returns the position of the snake's head."""
        return self.pos

    def get_body(self):
        """Returns the list of body segments."""
        return self.body

    def _update_scaled_images(self):
        """
        Re-scales the snake sprites only when the block size changes.
        This is far more efficient and prevents scaling-related alignment bugs.
        """
        if self.last_block_size != settings.blockSize:
            self.last_block_size = settings.blockSize
            size = (int(settings.blockSize), int(settings.blockSize))
            self.scaled_images = {
                key: pygame.transform.scale(img, size)
                for key, img in settings.snakeImages.items()
            }

    def _rotate_and_center(self, image, angle, cell_rect):
        """
        Rotates an image and correctly recalculates its center point
        to avoid all floating-point and rounding errors. This is the definitive
        solution to the 1-pixel misalignment bug.
        """
        # Rotate the image
        rotated_image = pygame.transform.rotate(image, angle)
        # Get the new rect and set its center to the integer-based center
        # of the grid cell. This prevents all rounding errors.
        new_rect = rotated_image.get_rect(center=cell_rect.center)
        return rotated_image, new_rect

    def draw(self, surface):
        """
        Draws the snake using sprites, determining the correct orientation for each segment.
        """
        self._update_scaled_images() # Efficiently rescale images if needed

        for index, segment in enumerate(self.body):
            # The segment's screen position
            rect = pygame.Rect(
                int(segment[0] * self.last_block_size + settings.xOffset), 
                int(segment[1] * self.last_block_size + settings.yOffset), 
                self.last_block_size, # Use the guaranteed integer size
                self.last_block_size
            )

            if index == 0:  # Head
                # Head orientation should be based on its current direction of travel
                image_to_rotate = self.scaled_images['head']
                if self.direction == 'UP':
                    angle = 0
                elif self.direction == 'DOWN':
                    angle = 180
                elif self.direction == 'LEFT':
                    angle = 90
                elif self.direction == 'RIGHT':
                    angle = -90
                final_image, final_rect = self._rotate_and_center(image_to_rotate, angle, rect)

            elif index == len(self.body) - 1:  # Tail
                image_to_rotate = self.scaled_images['tail']
                # Use vector subtraction to find the correct direction
                prev_segment = self.body[index - 1]
                vec_x = prev_segment[0] - segment[0]
                vec_y = prev_segment[1] - segment[1]

                if vec_y > 0: # Coming from below
                    angle = 180
                elif vec_y < 0: # Coming from above
                    angle = 0
                elif vec_x > 0: # Coming from the right
                    angle = -90
                elif vec_x < 0: # Coming from the left
                    angle = 90
                final_image, final_rect = self._rotate_and_center(image_to_rotate, angle, rect)

            else:  # Body segments
                prev_segment = self.body[index - 1]
                next_segment = self.body[index + 1]
                
                # Straight piece
                if prev_segment[0] == next_segment[0]:  # Vertical
                    image_to_rotate = self.scaled_images['body']
                    angle = 0
                elif prev_segment[1] == next_segment[1]:  # Horizontal
                    image_to_rotate = self.scaled_images['body']
                    angle = 90
                # Turn piece
                else:
                    image_to_rotate = self.scaled_images['turn']
                    # Use vector subtraction for reliable corner detection
                    prev_vec_x = prev_segment[0] - segment[0]
                    prev_vec_y = prev_segment[1] - segment[1]
                    next_vec_x = next_segment[0] - segment[0]
                    next_vec_y = next_segment[1] - segment[1]

                    # The base image is a top-right corner.
                    if (prev_vec_x > 0 and next_vec_y < 0) or (prev_vec_y < 0 and next_vec_x > 0): # Top-right corner
                        angle = 0
                    elif (prev_vec_x > 0 and next_vec_y > 0) or (prev_vec_y > 0 and next_vec_x > 0): # Bottom-right corner
                        angle = -90
                    elif (prev_vec_x < 0 and next_vec_y > 0) or (prev_vec_y > 0 and next_vec_x < 0): # Bottom-left corner
                        angle = 180
                    elif (prev_vec_x < 0 and next_vec_y < 0) or (prev_vec_y < 0 and next_vec_x < 0): # Top-left corner
                        angle = 90
                
                final_image, final_rect = self._rotate_and_center(image_to_rotate, angle, rect)

            # Color the final image and draw it
            # --- [EASTER EGG] Rainbow Snake Logic ---
            if settings.userSettings.get("snakeColorName") == "Rainbow":
                # Calculate a hue that shifts over time and with each segment
                hue = (pygame.time.get_ticks() / 20 + index * 15) % 360
                # Create a color object and set its hue
                rainbow_color = pygame.Color(0) # Start with black
                rainbow_color.hsva = (hue, 100, 100, 100) # Set Hue, Saturation, Value, Alpha
                
                colored_image = ui.tint_surface(final_image, rainbow_color)
                surface.blit(colored_image, final_rect)
            else:
                # Default behavior
                colored_image = ui.tint_surface(final_image, settings.snakeColor)
                surface.blit(colored_image, final_rect)


class Food:
    def __init__(self):
        """Manages a list of all food items on the screen."""
        self.scaled_images = {}
        self.last_block_size = -1 # Force a rescale on the first draw
        self.items = []
        self.reset([]) # Initial spawn


    def reset(self, snake_body):
        """Clears all food and spawns a single normal food item."""
        self.items.clear()
        self._spawn_item('normal', snake_body)

    def spawn_galore(self, food_type, count, snake_body):
        """Spawns a large number of a specific food type for an event."""
        self.items.clear() # Clear existing food
        for _ in range(count):
            self._spawn_item(food_type, snake_body)

    def _spawn_item(self, food_type, snake_body):
        """
        Internal helper to spawn a single food item of a given type.
        Ensures it doesn't spawn on the snake, other food, on the very edge of the screen,
        or too close to other food items.
        """
        occupied_positions = snake_body + [item['pos'] for item in self.items]
        MIN_FOOD_DISTANCE = 3 # Minimum grid spaces between two food items

        while True:
            pos = [
                random.randrange(1, settings.gridWidth - 1),
                random.randrange(1, settings.gridHeight - 1)
            ]

            is_too_close = False
            for item in self.items:
                dist = abs(pos[0] - item['pos'][0]) + abs(pos[1] - item['pos'][1])
                if dist < MIN_FOOD_DISTANCE:
                    is_too_close = True
                    break

            if pos not in snake_body and not is_too_close:
                if food_type == 'normal':
                    self.items.append({'pos': pos, 'type': 'normal', 'color': settings.foodColor})
                elif food_type == 'golden':
                    self.items.append({'pos': pos, 'type': 'golden', 'color': settings.gold})
                # elif food_type == 'speed':
                #     self.items.append({'pos': pos, 'type': 'speed', 'color': settings.blue})
                break

    def spawn_new_food(self, snake_body, golden_chance):
        """Public method called after food is eaten. Spawns a new normal food
        and has a chance to spawn a golden one."""
        # When spawning a new normal apple, first remove any other existing normal apples.
        self.items = [item for item in self.items if item['type'] != 'normal']

        self._spawn_item('normal', snake_body)
        
        if random.randint(1, golden_chance) == 1:
            self._spawn_item('golden', snake_body)

    def check_collision(self, snake_head_pos):
        """
        Checks if the snake head has collided with any food item.
        If so, removes the item and returns its dictionary. Otherwise, returns None.
        """
        for food_item in self.items:
            if snake_head_pos == food_item['pos']:
                self.items.remove(food_item)
                return food_item
        return None

    def _update_scaled_images(self):
        """
        Re-scales the food sprites only when the block size changes.
        """
        if self.last_block_size != settings.blockSize:
            self.last_block_size = settings.blockSize
            size = (int(settings.blockSize), int(settings.blockSize))
            self.scaled_images = {
                key: pygame.transform.scale(img, size)
                for key, img in settings.foodImages.items()
            }

    def draw(self, surface):
        """Draws all food items on the given surface using sprites."""
        self._update_scaled_images() # Ensure sprites are the correct size

        for item in self.items:
            rect = pygame.Rect(
                int(item['pos'][0] * self.last_block_size + settings.xOffset), 
                int(item['pos'][1] * self.last_block_size + settings.yOffset), 
                self.last_block_size, 
                self.last_block_size
            )
            apple_sprite = self.scaled_images['apple']
            colored_apple = ui.tint_surface(apple_sprite, item['color'])
            surface.blit(colored_apple, rect)

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