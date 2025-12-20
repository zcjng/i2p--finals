from __future__ import annotations
import pygame as pg
from heapq import heappush, heappop
from typing import Optional
from src.utils import Position, GameSettings
from src.core.services import input_manager

TILE = GameSettings.TILE_SIZE


class TownMap:
    def __init__(self, game_manager):
        self.game_manager = game_manager

        self.destination_tile: Optional[tuple[int, int]] = None
        self.current_path_tiles: list[tuple[int, int]] = []

        self.recalc_cooldown = 0
        self.recalc_delay = 0.25  # seconds
        self.overlay = False
        self.opened_from_menu = False  # Track if opened from menu like Bag does
        
        # Navigation arrow properties
        self.arrow_distance = TILE * 3  # How far ahead to show arrow
        self.arrow_size = 32
        self.arrow_bounce_offset = 0
        self.arrow_bounce_speed = 2.0
        self.arrow_bounce_amount = 8
        
        # Progress tracking
        self.last_player_tile: Optional[tuple[int, int]] = None
        self.path_progress = 0  # How far along the path (0.0 to 1.0)
        
        # Overlay UI
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.fill((0, 0, 0))
        self.dim_overlay.set_alpha(180)
        
        # UI elements
        try:
            self.font = pg.font.Font('assets/fonts/Pokemon.ttf', 36)
            self.font_small = pg.font.Font('assets/fonts/Pokemon.ttf', 24)
        except:
            self.font = pg.font.Font(None, 36)
            self.font_small = pg.font.Font(None, 24)
        
        self.selected_place_index = 0
        
        # Create arrow surface (simple triangle)
        self.arrow_surface = self._create_arrow_surface()

    def _create_arrow_surface(self) -> pg.Surface:
        """Create a simple arrow pointing up"""
        surface = pg.Surface((self.arrow_size, self.arrow_size), pg.SRCALPHA)
        # Draw a triangle
        points = [
            (self.arrow_size // 2, 0),  # Top
            (0, self.arrow_size),  # Bottom left
            (self.arrow_size, self.arrow_size)  # Bottom right
        ]
        pg.draw.polygon(surface, (255, 255, 0), points)
        pg.draw.polygon(surface, (200, 200, 0), points, 3)  # Border
        return surface

    def open(self):
        """Open the townmap overlay"""
        self.overlay = True
        self.selected_place_index = 0

    def close(self, reopen_menu=True):
        """Close the townmap overlay"""
        self.overlay = False
        if self.opened_from_menu and reopen_menu:
            self.opened_from_menu = False
            if self.game_manager and hasattr(self.game_manager, 'menu'):
                self.game_manager.menu.open()
        elif self.opened_from_menu:
            self.opened_from_menu = False

    def toggle(self):
        """Toggle the townmap overlay"""
        if self.overlay:
            self.close(reopen_menu=False)
        else:
            self.open()

    # --------------------------------------------------
    # Tile helpers
    # --------------------------------------------------
    def world_to_tile(self, pos: Position) -> tuple[int, int]:
        return int(pos.x // TILE), int(pos.y // TILE)

    def tile_to_world_center(self, tile: tuple[int, int]) -> Position:
        x, y = tile
        return Position(
            x * TILE + TILE // 2,
            y * TILE + TILE // 2
        )

    # --------------------------------------------------
    # Places
    # --------------------------------------------------
    def get_places_in_current_map(self):
        """
        Get places from the current map's TMX object layers.
        Looks for objects in layers named 'places' or 'locations'
        """
        current_key = self.game_manager.current_map_key
        current_map = self.game_manager.maps[current_key]
        
        places = []
        
        # If map already has places attribute, use it
        if hasattr(current_map, "places") and current_map.places:
            return current_map.places
        
        # Otherwise, try to extract from TMX data
        if hasattr(current_map, "tmxdata"):
            for layer in current_map.tmxdata.layers:
                # Look for object layers with place names
                if hasattr(layer, 'name') and ('place' in layer.name.lower() or 'location' in layer.name.lower()):
                    if hasattr(layer, '__iter__'):  # Check if it's an object layer
                        for obj in layer:
                            if hasattr(obj, 'name') and hasattr(obj, 'x') and hasattr(obj, 'y'):
                                places.append({
                                    "name": obj.name,
                                    "position": Position(obj.x, obj.y)
                                })
        
        # For testing: Add some default places if none found
        if not places:
            # Add teleporter destinations as places
            if hasattr(current_map, 'teleporters') and current_map.teleporters:
                for i, tp in enumerate(current_map.teleporters):
                    places.append({
                        "name": f"Exit to {tp.destination.replace('.tmx', '').title()}",
                        "position": tp.pos
                    })
        
        return places

    # --------------------------------------------------
    # A* Pathfinding
    # --------------------------------------------------
    def heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def a_star(self, start: tuple[int, int], goal: tuple[int, int]):
        open_set = []
        heappush(open_set, (0, start))

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score = {start: 0}

        width = self.game_manager.current_map.width
        height = self.game_manager.current_map.height

        while open_set:
            _, current = heappop(open_set)

            if current == goal:
                return self.reconstruct_path(came_from, current)

            cx, cy = current
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy

                if not (0 <= nx < width and 0 <= ny < height):
                    continue

                rect = pg.Rect(
                    nx * TILE,
                    ny * TILE,
                    TILE,
                    TILE
                )

                # ✅ IMPORTANT FIX:
                # Only map collision, NOT NPCs / trainers
                if self.game_manager.current_map.check_collision(rect):
                    continue

                neighbor = (nx, ny)
                tentative_g = g_score[current] + 1

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self.heuristic(neighbor, goal)
                    heappush(open_set, (f, neighbor))

        return []

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------
    def navigate_to_place(self, place):
        player = self.game_manager.player
        if not player:
            return

        start = self.world_to_tile(player.position)
        goal = self.world_to_tile(place["position"])

        if self.destination_tile == goal:
            return

        self.destination_tile = goal
        self.current_path_tiles = self.a_star(start, goal)
        self.path_progress = 0

    def cancel_navigation(self):
        """Cancel current navigation"""
        self.destination_tile = None
        self.current_path_tiles = []
        self.path_progress = 0

    def get_next_direction(self) -> Optional[str]:
        """Get the direction the player should move next"""
        if not self.current_path_tiles or len(self.current_path_tiles) < 2:
            return None
        
        player = self.game_manager.player
        if not player:
            return None
            
        current_tile = self.world_to_tile(player.position)
        
        # Find current position in path
        if current_tile in self.current_path_tiles:
            idx = self.current_path_tiles.index(current_tile)
            if idx + 1 < len(self.current_path_tiles):
                next_tile = self.current_path_tiles[idx + 1]
                dx = next_tile[0] - current_tile[0]
                dy = next_tile[1] - current_tile[1]
                
                if dx > 0:
                    return "right"
                elif dx < 0:
                    return "left"
                elif dy > 0:
                    return "down"
                elif dy < 0:
                    return "up"
        
        return None

    # --------------------------------------------------
    # Input handling
    # --------------------------------------------------
    def handle_input(self):
        """Handle input when overlay is open"""
        if not self.overlay:
            return
        
        places = self.get_places_in_current_map()
        
        if not places:
            # No places available, just allow closing
            if input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
                self.close()
            return
        
        # Navigate up
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            if self.selected_place_index > 0:
                self.selected_place_index -= 1
        
        # Navigate down
        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            if self.selected_place_index < len(places):  # +1 for CANCEL option
                self.selected_place_index += 1
        
        # Select place (Enter or E)
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e):
            if self.selected_place_index < len(places):
                # Navigate to selected place
                self.navigate_to_place(places[self.selected_place_index])
                self.close(reopen_menu=self.opened_from_menu)
            else:
                # Cancel/Close selected
                self.close(reopen_menu=self.opened_from_menu)
        
        # Close with ESC or X
        if input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
            self.close()

    # --------------------------------------------------
    # Update loop
    # --------------------------------------------------
    def update(self, dt: float):
        self.recalc_cooldown -= dt
        self.arrow_bounce_offset += self.arrow_bounce_speed * dt
        
        if self.overlay:
            self.handle_input()
        
        self.update_path()

    def update_path(self):
        player = self.game_manager.player
        if not player or not self.current_path_tiles:
            return

        player_tile = self.world_to_tile(player.position)

        if player_tile in self.current_path_tiles:
            idx = self.current_path_tiles.index(player_tile)
            self.current_path_tiles = self.current_path_tiles[idx:]
            
            # Update progress
            if len(self.current_path_tiles) > 1:
                total_tiles = len(self.current_path_tiles)
                self.path_progress = 1.0 - (total_tiles / max(total_tiles, 1))
            
            # Check if reached destination
            if len(self.current_path_tiles) <= 1:
                self.cancel_navigation()
                
        elif self.recalc_cooldown <= 0:
            # Player off path, recalculate
            if self.destination_tile:
                self.current_path_tiles = self.a_star(
                    player_tile,
                    self.destination_tile
                )
                self.recalc_cooldown = self.recalc_delay

    def update_path_progress(self, player_position: Position, dt: float):
        """Update path progress tracking - called from GameScene"""
        if not self.current_path_tiles:
            return
        
        player_tile = self.world_to_tile(player_position)
        
        # Track if player moved to a new tile
        if self.last_player_tile != player_tile:
            self.last_player_tile = player_tile
            self.update_path()

    # --------------------------------------------------
    # Drawing
    # --------------------------------------------------
    def draw_navigation_arrows(self, screen: pg.Surface, camera):
        """Draw navigation arrows showing the path direction"""
        if not self.current_path_tiles or len(self.current_path_tiles) < 2:
            return
        
        player = self.game_manager.player
        if not player:
            return
        
        # Get next tile in path
        current_tile = self.world_to_tile(player.position)
        if current_tile not in self.current_path_tiles:
            return
        
        idx = self.current_path_tiles.index(current_tile)
        if idx + 1 >= len(self.current_path_tiles):
            return
        
        next_tile = self.current_path_tiles[idx + 1]
        next_pos = self.tile_to_world_center(next_tile)
        
        # Calculate arrow position
        arrow_x = next_pos.x - camera.x - self.arrow_size // 2
        arrow_y = next_pos.y - camera.y - self.arrow_size // 2
        
        # Add bounce effect
        bounce = abs((self.arrow_bounce_offset % 1.0) - 0.5) * 2 * self.arrow_bounce_amount
        arrow_y -= bounce
        
        # Determine rotation based on direction
        dx = next_tile[0] - current_tile[0]
        dy = next_tile[1] - current_tile[1]
        
        angle = 0
        if dx > 0:  # Right
            angle = -90
        elif dx < 0:  # Left
            angle = 90
        elif dy > 0:  # Down
            angle = 180
        # dy < 0 means up, which is 0 degrees (default)
        
        # Rotate and draw arrow
        rotated_arrow = pg.transform.rotate(self.arrow_surface, angle)
        arrow_rect = rotated_arrow.get_rect(center=(arrow_x + self.arrow_size // 2, 
                                                     arrow_y + self.arrow_size // 2))
        screen.blit(rotated_arrow, arrow_rect)
        
        # Optional: Draw path tiles for debugging
        if hasattr(GameSettings, 'DEBUG') and GameSettings.DEBUG:
            for tile in self.current_path_tiles:
                tile_pos = self.tile_to_world_center(tile)
                screen_x = tile_pos.x - camera.x
                screen_y = tile_pos.y - camera.y
                pg.draw.circle(screen, (0, 255, 0), (int(screen_x), int(screen_y)), 5)

    def draw(self, screen: pg.Surface):
        """Draw the townmap overlay UI"""
        if not self.overlay:
            return
        
        places = self.get_places_in_current_map()
        
        # Title
        title = self.font.render("Town Map", True, (255, 255, 255))
        title_rect = title.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 80))
        screen.blit(title, title_rect)
        
        # Instructions
        instructions = [
            "Select a destination to navigate",
            "Use UP/DOWN or W/S to select",
            "Press ENTER or E to confirm",
            "Press ESC or X to close"
        ]
        
        y_offset = 140
        for instruction in instructions:
            text = self.font_small.render(instruction, True, (200, 200, 200))
            text_rect = text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 30
        
        # List places
        if places:
            y_offset += 30
            places_title = self.font.render("Locations:", True, (255, 255, 255))
            places_rect = places_title.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, y_offset))
            screen.blit(places_title, places_rect)
            y_offset += 50
            
            for i, place in enumerate(places):
                place_name = place.get("name", f"Location {i+1}")
                
                # Highlight selected place
                if i == self.selected_place_index:
                    color = (255, 255, 0)  # Yellow
                    # Draw selection box
                    box_rect = pg.Rect(
                        GameSettings.SCREEN_WIDTH // 2 - 200,
                        y_offset - 5,
                        400,
                        35
                    )
                    pg.draw.rect(screen, (100, 100, 0), box_rect, 2)
                else:
                    color = (200, 200, 200)
                
                place_text = self.font_small.render(f"• {place_name}", True, color)
                place_rect = place_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, y_offset))
                screen.blit(place_text, place_rect)
                y_offset += 40
            
            # Draw CANCEL option
            y_offset += 10
            if self.selected_place_index == len(places):
                color = (255, 100, 100)  # Red
                box_rect = pg.Rect(
                    GameSettings.SCREEN_WIDTH // 2 - 200,
                    y_offset - 5,
                    400,
                    35
                )
                pg.draw.rect(screen, (100, 50, 50), box_rect, 2)
            else:
                color = (200, 150, 150)
            
            cancel_text = self.font_small.render("CANCEL", True, color)
            cancel_rect = cancel_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, y_offset))
            screen.blit(cancel_text, cancel_rect)
        else:
            # No places available
            y_offset += 30
            no_places = self.font.render("No locations available", True, (200, 200, 200))
            no_places_rect = no_places.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, y_offset))
            screen.blit(no_places, no_places_rect)