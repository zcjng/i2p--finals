import pygame as pg
from src.utils import GameSettings, Position
from src.sprites import Sprite
from src.core.services import input_manager
from collections import deque

class TownMap:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.overlay = False
        self.opened_from_menu = False
        
        # Define navigable places (add your actual map data here)
        self.places = [
            {"name": "Starting Area", "map": "map3.tmx", "position": Position(10 * GameSettings.TILE_SIZE, 10 * GameSettings.TILE_SIZE)},
            {"name": "Gym", "map": "gym.tmx", "position": Position(15 * GameSettings.TILE_SIZE, 20 * GameSettings.TILE_SIZE)},
            {"name": "House", "map": "house.tmx", "position": Position(8 * GameSettings.TILE_SIZE, 5 * GameSettings.TILE_SIZE)},
        ]
        
        # UI setup
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0))
        
        self.selected_index = 0
        self.font_title = pg.font.Font('assets/fonts/Pokemon.ttf', 80)
        self.font_place = pg.font.Font('assets/fonts/Pokemon.ttf', 60)
        self.font_small = pg.font.Font('assets/fonts/Pokemon.ttf', 40)
        
        # Navigation path
        self.current_path = []
        self.path_arrows = []
        
        # Cursor selector
        try:
            self.cursor = Sprite("UI/raw/UI_Selector.png", (25, 25))
        except:
            self.cursor = None
    
    def get_places_in_current_map(self):
        """Get only places that are in the current map"""
        current_map = self.game_manager.current_map_key
        return [p for p in self.places if p["map"] == current_map]
    
    def bfs_pathfind(self, start_pos: Position, end_pos: Position):
        """
        Use BFS to find shortest path from start to end, avoiding collision tiles.
        Returns list of positions representing the path.
        """
        # Convert world positions to tile coordinates
        start_tile = (int(start_pos.x // GameSettings.TILE_SIZE), int(start_pos.y // GameSettings.TILE_SIZE))
        end_tile = (int(end_pos.x // GameSettings.TILE_SIZE), int(end_pos.y // GameSettings.TILE_SIZE))
        
        # BFS setup
        queue = deque([(start_tile, [start_tile])])
        visited = {start_tile}
        
        # Directions: up, down, left, right
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        while queue:
            (current_x, current_y), path = queue.popleft()
            
            # Check if we reached the destination
            if (current_x, current_y) == end_tile:
                # Convert tile path back to world positions
                world_path = []
                for tile_x, tile_y in path:
                    world_x = tile_x * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
                    world_y = tile_y * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
                    world_path.append(Position(world_x, world_y))
                return world_path
            
            # Explore neighbors
            for dx, dy in directions:
                next_x, next_y = current_x + dx, current_y + dy
                
                # Check bounds
                if (next_x < 0 or next_y < 0 or 
                    next_x >= self.game_manager.current_map.width or 
                    next_y >= self.game_manager.current_map.height):
                    continue
                
                # Check if already visited
                if (next_x, next_y) in visited:
                    continue
                
                # Check collision
                test_rect = pg.Rect(
                    next_x * GameSettings.TILE_SIZE,
                    next_y * GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE
                )
                
                if self.game_manager.check_collision(test_rect):
                    continue
                
                # Add to queue
                visited.add((next_x, next_y))
                new_path = path + [(next_x, next_y)]
                queue.append(((next_x, next_y), new_path))
        
        # No path found
        return []
    
    def create_arrow_path(self, path):
        """Create arrow sprites along the path"""
        self.path_arrows = []
        
        for i in range(len(path) - 1):
            current = path[i]
            next_pos = path[i + 1]
            
            # Determine direction
            dx = next_pos.x - current.x
            dy = next_pos.y - current.y
            
            # Create arrow (you can replace this with actual arrow sprites)
            arrow_info = {
                "position": current,
                "direction": self.get_direction(dx, dy)
            }
            self.path_arrows.append(arrow_info)
    
    def get_direction(self, dx, dy):
        """Get direction name from delta x and delta y"""
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"
    
    def navigate_to_place(self, place):
        """Set navigation to selected place"""
        player_pos = self.game_manager.player.position
        destination = place["position"]
        
        # Find path using BFS
        path = self.bfs_pathfind(player_pos, destination)
        
        if path:
            self.current_path = path
            self.create_arrow_path(path)
            self.close()
        else:
            # No path found - could show error message
            pass
    
    def clear_navigation(self):
        """Clear current navigation path"""
        self.current_path = []
        self.path_arrows = []
    
    def handle_input(self):
        """Handle keyboard input"""
        places = self.get_places_in_current_map()
        
        if not places:
            return
        
        max_index = len(places)
        
        # Navigate up
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            self.selected_index = (self.selected_index - 1) % max_index
        
        # Navigate down
        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            self.selected_index = (self.selected_index + 1) % max_index
        
        # Select destination
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e):
            selected_place = places[self.selected_index]
            self.navigate_to_place(selected_place)
        
        # Close map
        if input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
            self.close()
    
    def update_path_progress(self, player_pos: Position):
        """Remove arrows that the player has passed and recalculate if off-path"""
        # Early exit if no navigation active
        if not self.current_path or not self.path_arrows:
            return
        
        # Check if player is close to the next waypoint
        threshold = GameSettings.TILE_SIZE * 0.6  # 60% of a tile
        off_path_threshold = GameSettings.TILE_SIZE * 2.5  # How far off path before recalculating
        
        # Check if player has strayed too far from the path
        if len(self.current_path) > 0:
            # Find closest waypoint in the path
            min_distance = float('inf')
            closest_index = 0
            
            for i, waypoint in enumerate(self.current_path):
                distance_squared = ((player_pos.x - waypoint.x) ** 2 + 
                                   (player_pos.y - waypoint.y) ** 2)
                distance = distance_squared ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    closest_index = i
            
            # If player is too far from any waypoint, recalculate path
            if min_distance > off_path_threshold:
                # Get the original destination (last waypoint)
                destination = self.current_path[-1]
                
                # Recalculate path from current position
                new_path = self.bfs_pathfind(player_pos, destination)
                
                if new_path:
                    self.current_path = new_path
                    self.create_arrow_path(new_path)
                else:
                    # Can't find path anymore, clear navigation
                    self.clear_navigation()
                return
        
        # Normal path following - remove waypoints as player reaches them
        while self.current_path and len(self.current_path) > 1:
            next_waypoint = self.current_path[0]
            
            distance_squared = ((player_pos.x - next_waypoint.x) ** 2 + 
                               (player_pos.y - next_waypoint.y) ** 2)
            threshold_squared = threshold ** 2
            
            if distance_squared < threshold_squared:
                # Player reached this waypoint, remove it
                self.current_path.pop(0)
                if self.path_arrows:
                    self.path_arrows.pop(0)
            else:
                break
        
        # Check if reached destination
        if len(self.current_path) == 1:
            destination = self.current_path[0]
            distance_squared = ((player_pos.x - destination.x) ** 2 + 
                               (player_pos.y - destination.y) ** 2)
            threshold_squared = threshold ** 2
            
            if distance_squared < threshold_squared:
                # Reached destination!
                self.clear_navigation()
            
    def update(self, dt: float):
        if self.overlay:
            self.handle_input()
    
    def draw(self, screen: pg.Surface):
        """Draw the town map UI"""
        if not self.overlay:
            return
        
        # Draw dim overlay
        screen.blit(self.dim_overlay, (0, 0))
        
        px = GameSettings.SCREEN_WIDTH // 2
        py = GameSettings.SCREEN_HEIGHT // 2
        
        # Draw title
        title = self.font_title.render("TOWN MAP", True, (255, 255, 255))
        title_rect = title.get_rect(center=(px, py - 300))
        screen.blit(title, title_rect)
        
        # Get places in current map
        places = self.get_places_in_current_map()
        
        if not places:
            no_places = self.font_place.render("No locations in this area", True, (200, 200, 200))
            no_places_rect = no_places.get_rect(center=(px, py))
            screen.blit(no_places, no_places_rect)
            return
        
        # Draw place list
        start_y = py - 150
        for i, place in enumerate(places):
            y_pos = start_y + (i * 80)
            color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)
            
            # Draw cursor for selected item
            if i == self.selected_index and self.cursor:
                self.cursor.rect.center = (px - 250, y_pos)
                self.cursor.draw(screen)
            
            # Draw place name
            place_text = self.font_place.render(place["name"], True, color)
            place_rect = place_text.get_rect(center=(px, y_pos))
            screen.blit(place_text, place_rect)
        
        # Draw instructions
        instructions = self.font_small.render("Press ENTER to navigate | ESC to close", True, (150, 150, 150))
        instructions_rect = instructions.get_rect(center=(px, py + 250))
        screen.blit(instructions, instructions_rect)
    
    def draw_navigation_arrows(self, screen: pg.Surface, camera):
        """Draw arrows on the game world to show the path"""
        if not self.path_arrows:
            return
        
        arrow_colors = {
            "up": (0, 255, 0),
            "down": (0, 255, 0),
            "left": (0, 255, 0),
            "right": (0, 255, 0)
        }
        
        for arrow in self.path_arrows:
            pos = arrow["position"]
            direction = arrow["direction"]
            
            # Transform position to screen coordinates
            screen_x = pos.x - camera.x
            screen_y = pos.y - camera.y
            
            # Draw arrow (simple triangle)
            color = arrow_colors[direction]
            size = 15
            
            if direction == "up":
                points = [
                    (screen_x, screen_y - size),
                    (screen_x - size//2, screen_y + size//2),
                    (screen_x + size//2, screen_y + size//2)
                ]
            elif direction == "down":
                points = [
                    (screen_x, screen_y + size),
                    (screen_x - size//2, screen_y - size//2),
                    (screen_x + size//2, screen_y - size//2)
                ]
            elif direction == "left":
                points = [
                    (screen_x - size, screen_y),
                    (screen_x + size//2, screen_y - size//2),
                    (screen_x + size//2, screen_y + size//2)
                ]
            else:  # right
                points = [
                    (screen_x + size, screen_y),
                    (screen_x - size//2, screen_y - size//2),
                    (screen_x - size//2, screen_y + size//2)
                ]
            
            pg.draw.polygon(screen, color, points)
            pg.draw.polygon(screen, (255, 255, 255), points, 2)  # White outline
    
    def open(self):
        self.overlay = True
        self.selected_index = 0
    
    def close(self):
        self.overlay = False
        if self.opened_from_menu:
            self.opened_from_menu = False
            self.game_manager.menu.open()