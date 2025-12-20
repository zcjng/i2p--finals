import pygame as pg
from src.utils import GameSettings, Position, Logger
from src.sprites import Sprite, Animation
from src.core.services import input_manager
from collections import deque

class TownMap:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.overlay = False
        self.opened_from_menu = False
        

        self.map_connections = {
            "map3.tmx": [
                {
                    "name": "Gym", 
                    "destination_map": "gym.tmx",
                    "teleporter_pos": Position(24 * GameSettings.TILE_SIZE, 23 * GameSettings.TILE_SIZE)
                },
                {
                    "name": "House", 
                    "destination_map": "house.tmx",
                    "teleporter_pos": Position(16 * GameSettings.TILE_SIZE, 28 * GameSettings.TILE_SIZE)
                }
            ],
            "gym.tmx": [
                {
                "name": "Back to Town", 
                    "destination_map": "map3.tmx",
                    "teleporter_pos": Position(12 * GameSettings.TILE_SIZE, 14 * GameSettings.TILE_SIZE)
                }
            ],
            "house.tmx": [
                {
                    "name": "Back to Town", 
                    "destination_map": "map3.tmx",
                    "teleporter_pos": Position(12 * GameSettings.TILE_SIZE, 14 * GameSettings.TILE_SIZE)
                }
            ]
        }
        

        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0))
        
        self.selected_index = 0
        self.font_title = pg.font.Font('assets/fonts/Pokemon.ttf', 80)
        self.font_place = pg.font.Font('assets/fonts/Pokemon.ttf', 60)
        self.font_small = pg.font.Font('assets/fonts/Pokemon.ttf', 40)
        

        self.current_path = []
        self.path_arrows = []
        self.auto_walking = False
        self.current_destination = None
        

        try:
            self.cursor = Animation(
                "UI/Flecha.png",
                rows=["idle"],
                n_keyframes=8,
                size=(60, 40),
                loop=1.5,
                vertical=True
            )
        except:
            self.cursor = None
    
    def get_available_destinations(self):
        """Get available destinations from current map"""
        current_map = self.game_manager.current_map_key
        destinations = self.map_connections.get(current_map, [])
        return destinations
    
    def bfs_pathfind(self, start_pos: Position, end_pos: Position):
        """Use BFS to find shortest path from start to end, avoiding collision tiles."""
        start_tile = (int(start_pos.x // GameSettings.TILE_SIZE), int(start_pos.y // GameSettings.TILE_SIZE))
        end_tile = (int(end_pos.x // GameSettings.TILE_SIZE), int(end_pos.y // GameSettings.TILE_SIZE))
        
        queue = deque([(start_tile, [start_tile])])
        visited = {start_tile}
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        while queue:
            (current_x, current_y), path = queue.popleft()
            
            if (current_x, current_y) == end_tile:
                world_path = []
                for tile_x, tile_y in path:
                    world_x = tile_x * GameSettings.TILE_SIZE
                    world_y = tile_y * GameSettings.TILE_SIZE
                    world_path.append(Position(world_x, world_y))
                return world_path
            
            for dx, dy in directions:
                next_x, next_y = current_x + dx, current_y + dy
                
                if (next_x < 0 or next_y < 0 or 
                    next_x >= self.game_manager.current_map.width or 
                    next_y >= self.game_manager.current_map.height):
                    continue
                
                if (next_x, next_y) in visited:
                    continue
                
                test_rect = pg.Rect(
                    next_x * GameSettings.TILE_SIZE,
                    next_y * GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE
                )
                

                if self.game_manager.current_map.check_collision(test_rect):
                    continue
                
                visited.add((next_x, next_y))
                new_path = path + [(next_x, next_y)]
                queue.append(((next_x, next_y), new_path))
        
        return []
    
    def create_arrow_path(self, path):
        """Create arrow sprites along the path"""
        self.path_arrows = []
        for i in range(len(path) - 1):
            current = path[i]
            next_pos = path[i + 1]
            dx = next_pos.x - current.x
            dy = next_pos.y - current.y
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
    
    def navigate_to_destination(self, destination_info):
        """Set navigation to selected destination"""
        if not self.game_manager.player:
            return
            
        player_pos = self.game_manager.player.position
        teleporter_pos = destination_info["teleporter_pos"]
        
        path = self.bfs_pathfind(player_pos, teleporter_pos)
        
        if path:
            self.current_path = path
            self.create_arrow_path(path)
            self.auto_walking = True
            self.current_destination = destination_info
            Logger.info(f"Navigation path found with {len(path)} waypoints")
            self.close()
        else:
            Logger.warning("Cannot find path to destination!")
    
    def clear_navigation(self):
        """Clear current navigation path"""
        self.current_path = []
        self.path_arrows = []
        self.auto_walking = False
        self.current_destination = None
        
    def check_cancel_input(self):
        """Check if player wants to cancel auto-walking"""

        if input_manager.key_pressed(pg.K_x) or input_manager.key_pressed(pg.K_ESCAPE):
            Logger.info("Navigation cancelled by player")
            self.clear_navigation()
            return True
        

        if (input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w) or
            input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s) or
            input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a) or
            input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d)):
            Logger.info("Navigation cancelled by player input")
            self.clear_navigation()
            return True
        
        return False
    
    def auto_walk_update(self, dt: float):
        """Handle automatic walking along the path"""
        if not self.auto_walking or not self.current_path or not self.game_manager.player:
            return
        
        if self.check_cancel_input():
            return
        
        player = self.game_manager.player
        if player.moving:
            return
        
        if len(self.current_path) > 0:
            next_waypoint = self.current_path[0]
            player_tile_x = int(player.position.x // GameSettings.TILE_SIZE)
            player_tile_y = int(player.position.y // GameSettings.TILE_SIZE)
            waypoint_tile_x = int(next_waypoint.x // GameSettings.TILE_SIZE)
            waypoint_tile_y = int(next_waypoint.y // GameSettings.TILE_SIZE)
            
            if player_tile_x == waypoint_tile_x and player_tile_y == waypoint_tile_y:
                self.current_path.pop(0)
                if self.path_arrows:
                    self.path_arrows.pop(0)
                if len(self.current_path) == 0:
                    self.clear_navigation()
                return
            
            dx = waypoint_tile_x - player_tile_x
            dy = waypoint_tile_y - player_tile_y
            
            from src.utils import Direction
            if abs(dx) > abs(dy):
                if dx > 0:
                    player.move(Direction.RIGHT)
                else:
                    player.move(Direction.LEFT)
            else:
                if dy > 0:
                    player.move(Direction.DOWN)
                else:
                    player.move(Direction.UP)
    
    def handle_input(self):
        """Handle keyboard input"""
        destinations = self.get_available_destinations()
        
        if not destinations:
            if input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
                self.close()
            return
        
        max_index = len(destinations)
        
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            self.selected_index = (self.selected_index - 1) % max_index
        
        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            self.selected_index = (self.selected_index + 1) % max_index
        
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e):
            selected_destination = destinations[self.selected_index]
            self.navigate_to_destination(selected_destination)
            if self.game_manager.menu.overlay:
                self.game_manager.menu.close()
        if input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
            self.close()
    
    def update_path_progress(self, player_pos: Position):
        """Remove arrows that the player has passed"""
        if not self.current_path or not self.path_arrows:
            return
        
        threshold = GameSettings.TILE_SIZE * 0.8
        
        while self.current_path and len(self.current_path) > 1:
            next_waypoint = self.current_path[0]
            distance_squared = ((player_pos.x - next_waypoint.x) ** 2 + 
                               (player_pos.y - next_waypoint.y) ** 2)
            threshold_squared = threshold ** 2
            
            if distance_squared < threshold_squared:
                self.current_path.pop(0)
                if self.path_arrows:
                    self.path_arrows.pop(0)
            else:
                break
        
        if len(self.current_path) == 1:
            destination = self.current_path[0]
            distance_squared = ((player_pos.x - destination.x) ** 2 + 
                               (player_pos.y - destination.y) ** 2)
            threshold_squared = threshold ** 2
            
            if distance_squared < threshold_squared:
                self.clear_navigation()
    
    def update(self, dt: float):
        if self.overlay:
            self.handle_input()
            self.cursor.update(dt)
        else:
            self.auto_walk_update(dt)
    
    def draw(self, screen: pg.Surface):
        """Draw the town map UI"""
        if not self.overlay:
            return
        
        screen.blit(self.dim_overlay, (0, 0))
        
        px = GameSettings.SCREEN_WIDTH // 2
        py = GameSettings.SCREEN_HEIGHT // 2
        
        title = self.font_title.render("TOWN MAP", True, (255, 255, 255))
        title_rect = title.get_rect(center=(px, py - 300))
        screen.blit(title, title_rect)
        
        destinations = self.get_available_destinations()
        
        if not destinations:
            no_places = self.font_place.render("No destinations available", True, (200, 200, 200))
            no_places_rect = no_places.get_rect(center=(px, py))
            screen.blit(no_places, no_places_rect)
            
            instructions = self.font_small.render("Press ESC to close", True, (150, 150, 150))
            instructions_rect = instructions.get_rect(center=(px, py + 250))
            screen.blit(instructions, instructions_rect)
            return
        
        start_y = py - 150
        for i, destination in enumerate(destinations):
            y_pos = start_y + (i * 80)
            color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)
            
            if i == self.selected_index and self.cursor:
                self.cursor.rect.center = (px - 200, y_pos + 10)
                self.cursor.draw(screen)
            
            dest_text = self.font_place.render(destination["name"], True, color)
            dest_rect = dest_text.get_rect(center=(px, y_pos))
            screen.blit(dest_text, dest_rect)
        
    
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
            
            screen_x = pos.x - camera.x + GameSettings.TILE_SIZE // 2
            screen_y = pos.y - camera.y + GameSettings.TILE_SIZE // 2
            
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
            else:
                points = [
                    (screen_x + size, screen_y),
                    (screen_x - size//2, screen_y - size//2),
                    (screen_x - size//2, screen_y + size//2)
                ]
            
            pg.draw.polygon(screen, color, points)
            pg.draw.polygon(screen, (255, 255, 255), points, 2)
    
    def open(self):
        Logger.info("Town Map overlay opened!")
        current_map = self.game_manager.current_map_key
        destinations = self.map_connections.get(current_map, [])
        Logger.info(f"Opening with map: {current_map}, {len(destinations)} destinations available")
        self.overlay = True
        self.selected_index = 0
    
    def close(self):
        self.overlay = False
        if self.opened_from_menu:
            self.opened_from_menu = False
            self.game_manager.menu.open()