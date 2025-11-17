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
        self.just_grew = False # Flag to prevent tail from being popped right after growing.
        self.animating_segments = [] # For grow/shrink animations


    def reset(self):
        """Resets the snake to its starting position and state."""
        start_x = settings.gridWidth // 2
        start_y = settings.gridHeight // 2
        self.pos = [start_x, start_y]
        self.direction = 'RIGHT'
        self.change_to = self.direction
        
        segment2_x = start_x - 1 # One block to the left
        
        self.body = [[start_x, start_y], [segment2_x, start_y]]
        self.initial_body = list(self.body) # Store the body at the moment of death
        # Reset event state
        self.pre_event_length = 0
        self.is_size_event_active = False
        self.growth_during_event = 0
        self.just_grew = False
        self.animating_segments = []

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

    def update_position(self, next_pos):
        """
        Moves the snake's head to the pre-validated next position.
        """
        self.pos = next_pos
        # The snake's head always moves to the new position.
        self.initial_body = list(self.body) # Store the body state before the move
        self.body.insert(0, list(self.pos))

    def grow(self):
        """Grows the snake by not removing the tail segment. This is called when food is eaten."""
        if self.is_size_event_active:
            self.growth_during_event += 1
        self.just_grew = True # Set the flag

    def grow_by(self, amount):
        """Instantly grows the snake by a given amount for the 'BEEEG Snake' event."""
        if not self.body or amount <= 0: return
        tail_segment = self.body[-1]
        start_time = pygame.time.get_ticks()
        for i in range(amount):
            new_segment = list(tail_segment)
            self.body.append(new_segment)
            # Add to animation list to be faded in
            self.animating_segments.append({'segment': new_segment, 'type': 'in', 'start_time': start_time})

    def shrink_by(self, amount):
        """
        Instantly shrinks the snake for the 'Small Snake' event, but not
        to a length less than 2.
        """
        min_length = 2
        # Only consider non-animating segments for the current length
        stable_length = len([s for s in self.body if s not in [a['segment'] for a in self.animating_segments]])
        
        # Calculate how many segments can be safely removed
        removable_segments = stable_length - min_length
        segments_to_remove_count = min(amount, removable_segments)
        if segments_to_remove_count <= 0: return

        segments_to_animate = self.body[-segments_to_remove_count:]
        start_time = pygame.time.get_ticks()

        for i in range(len(self.body) - segments_to_remove_count, len(self.body)):
            segment = self.body[i]
            image_key = 'body' # Default to body
            angle = 0

            if i == len(self.body) - 1: # This is the tail
                image_key = 'tail'
                prev_segment = self.body[i - 1]
                vec_x, vec_y = prev_segment[0] - segment[0], prev_segment[1] - segment[1]
                if vec_y > 0: angle = 180
                elif vec_y < 0: angle = 0
                elif vec_x > 0: angle = -90
                elif vec_x < 0: angle = 90
            else: # This is a body segment
                prev_segment = self.body[i - 1]
                next_segment = self.body[i + 1]
                if prev_segment[0] == next_segment[0] or prev_segment[1] == next_segment[1]:
                    image_key = 'body'
                    angle = 90 if prev_segment[1] == next_segment[1] else 0
                else:
                    image_key = 'turn'
                    prev_vec_x, prev_vec_y = prev_segment[0] - segment[0], prev_segment[1] - segment[1]
                    next_vec_x, next_vec_y = next_segment[0] - segment[0], next_segment[1] - segment[1]
                    if (prev_vec_x > 0 and next_vec_y < 0) or (prev_vec_y < 0 and next_vec_x > 0): angle = 0
                    elif (prev_vec_x > 0 and next_vec_y > 0) or (prev_vec_y > 0 and next_vec_x > 0): angle = -90
                    elif (prev_vec_x < 0 and next_vec_y > 0) or (prev_vec_y > 0 and next_vec_x < 0): angle = 180
                    elif (prev_vec_x < 0 and next_vec_y < 0) or (prev_vec_y < 0 and next_vec_x < 0): angle = 90
            
            # Store all necessary info for drawing later
            self.animating_segments.append({
                'segment': segment, 'type': 'out', 'start_time': start_time,
                'image_key': image_key, 'angle': angle
            })

        # Now, logically remove the segments from the snake's body
        self.body = self.body[:-segments_to_remove_count]

    def revert_size(self):
        """Reverts the snake's size to its pre-event length."""
        # Calculate the final target length: the length before the event, plus any growth during it.
        target_length = self.pre_event_length + self.growth_during_event
        current_length = len(self.body)

        if current_length > target_length:
            # If we are longer than the target (e.g., BEEEG event), shrink to target.
            self.shrink_by(current_length - target_length)
        elif current_length < target_length:
            # If we are shorter (e.g., Small event), grow to target.
            self.grow_by(target_length - current_length) # This will now animate
    
    def move(self):
        """Moves the snake by removing the tail segment (when no food is eaten)."""
        if self.just_grew:
            self.just_grew = False # Reset the flag for the next frame
        else:
            self.body.pop()

    def check_collision(self, next_pos):
        """Checks for wall collisions or self-collisions."""
        # Self-collision
        for block in self.body[1:]:
            if next_pos[0] == block[0] and next_pos[1] == block[1]:
                return True
        return False
    
    def check_wall_collision(self, next_pos):
        """Checks only for wall collisions. Separated for clarity."""
        # --- [REFACTOR] Check against grid dimensions ---
        if (next_pos[0] < 0 or next_pos[0] >= settings.gridWidth or
            next_pos[1] < 0 or next_pos[1] >= settings.gridHeight):
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

    def draw(self, surface, isDying=False, fadeProgress=None):
        """
        Draws the snake using sprites, determining the correct orientation for each segment.
        """
        self._update_scaled_images() # Efficiently rescale images if needed

        current_time = pygame.time.get_ticks()
        # Iterate over a copy of the list to allow removing items
        for anim in self.animating_segments[:]:
            elapsed = current_time - anim['start_time']
            if elapsed >= settings.SNAKE_SIZE_ANIMATION_DURATION:
                # Animation is finished
                if anim['type'] == 'out':
                    # For a fade-out, the segment is already logically removed from the body.
                    # We just need to stop drawing it.
                    pass
                # Remove from the animation list so it's no longer processed or drawn.
                self.animating_segments.remove(anim)

        # Create a quick lookup for animating segments and their state
        animating_lookup = {id(a['segment']): a for a in self.animating_segments}

        for original_index, segment in enumerate(self.body):
            # The segment's screen position
            rect = pygame.Rect(
                int(segment[0] * self.last_block_size + settings.xOffset), 
                int(segment[1] * self.last_block_size + settings.yOffset), 
                self.last_block_size, # Use the guaranteed integer size
                self.last_block_size
            )

            segment_id = id(segment)

            if original_index == 0:  # Head
                # Use the 'head_lose' sprite if dying, otherwise use the normal head.
                image_to_rotate = self.scaled_images['head_lose'] if isDying else self.scaled_images['head']
                if self.direction == 'UP':
                    angle = 0
                elif self.direction == 'DOWN':
                    angle = 180
                elif self.direction == 'LEFT':
                    angle = 90
                elif self.direction == 'RIGHT':
                    angle = -90
                final_image, final_rect = self._rotate_and_center(image_to_rotate, angle, rect)

            elif original_index == len(self.body) - 1:  # Tail
                image_to_rotate = self.scaled_images['tail']
                # Use vector subtraction to find the correct direction
                prev_segment = self.body[original_index - 1]
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
                prev_segment = self.body[original_index - 1]
                next_segment = self.body[original_index + 1]
                
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

            # --- Tint the image first ---
            # --- [EASTER EGG] Rainbow Snake Logic ---
            if settings.userSettings.get("snakeColorName") == "Rainbow":
                hue = (pygame.time.get_ticks() / 20) % 360
                rainbow_color = pygame.Color(0)
                rainbow_color.hsva = (hue, 100, 100, 100)
                colored_image = ui.tint_surface(final_image, rainbow_color)
            else:
                # Default behavior
                colored_image = ui.tint_surface(final_image, settings.snakeColor)
            
            # --- Then, apply alpha fades for animations ---
            if fadeProgress is not None:
                # Death animation (fades out the whole snake)
                # Calculate a single, uniform fade progress for all segments.
                progress = fadeProgress / settings.DEATH_FADE_OUT_DURATION
                progress = max(0.0, min(1.0, progress)) # Clamp value between 0 and 1
                colored_image.set_alpha(int(255 * (1.0 - progress))) # Apply alpha
            elif segment_id in animating_lookup:
                # Grow/Shrink animation (fades individual segments)
                anim = animating_lookup[segment_id]
                elapsed = current_time - anim['start_time']
                progress = min(1.0, elapsed / settings.SNAKE_SIZE_ANIMATION_DURATION)

                if anim['type'] == 'in':
                    # Fading in: alpha goes from 0 to 255
                    colored_image.set_alpha(int(255 * progress))
                elif anim['type'] == 'out':
                    # Fading out: alpha goes from 255 to 0
                    colored_image.set_alpha(int(255 * (1.0 - progress)))

            # --- Finally, draw the fully prepared image to the screen once ---
            surface.blit(colored_image, final_rect)
            
        # This block handles segments that are no longer in self.body but are still fading.
        for anim in self.animating_segments:
            if anim['type'] == 'out':
                segment = anim['segment']

                rect = pygame.Rect(
                    int(segment[0] * self.last_block_size + settings.xOffset), 
                    int(segment[1] * self.last_block_size + settings.yOffset), 
                    self.last_block_size,
                    self.last_block_size
                )
                
                image_to_rotate = self.scaled_images[anim['image_key']]
                angle = anim['angle']

                final_image, final_rect = self._rotate_and_center(image_to_rotate, angle, rect)
                
                # Tint the image
                colored_image = ui.tint_surface(final_image, settings.snakeColor)

                # Apply the fade-out animation
                elapsed = current_time - anim['start_time']
                progress = min(1.0, elapsed / settings.SNAKE_SIZE_ANIMATION_DURATION)
                colored_image.set_alpha(int(255 * (1.0 - progress)))

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