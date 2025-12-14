import pygame as pg
from src.utils import GameSettings, Position

class Minimap:
    def __init__(self, size: int = 150, padding: int = 10):
        """
        Initialize the minimap
        
        Args:
            size: Size of the minimap square (width and height)
            padding: Distance from screen edge
        """
        self.size = size
        self.padding = padding
        self.position = Position(padding, padding)  # Top-left corner
        
        # Cached map surface (will be set when map changes)
        self.map_surface = None
        self.current_map_key = None
        
        # Colors
        self.player_color = (255, 50, 50)  # Red dot for player
        self.border_color = (255, 255, 255)  # White border
        self.bg_color = (0, 0, 0, 180)  # Semi-transparent black background
        
        # Create border frame
        self.border_thickness = 3
        
    def cache_map_surface(self, map_obj, map_key: str):
        """
        Cache the current map as a scaled-down surface
        Only re-render when map changes
        """
        if self.current_map_key == map_key and self.map_surface is not None:
            return  # Already cached
        
        # Get the pre-rendered map surface
        full_map = map_obj._surface
        
        # Calculate scale to fit minimap
        map_width = full_map.get_width()
        map_height = full_map.get_height()
        
        # Scale to fit minimap size while maintaining aspect ratio
        scale_x = self.size / map_width
        scale_y = self.size / map_height
        scale = min(scale_x, scale_y)
        
        scaled_width = int(map_width * scale)
        scaled_height = int(map_height * scale)
        
        # Scale down the map
        self.map_surface = pg.transform.scale(full_map, (scaled_width, scaled_height))
        self.current_map_key = map_key
        self.scale = scale
        
    def draw(self, screen: pg.Surface, player_pos: Position, current_map, map_key: str):
        """
        Draw the minimap with player position
        
        Args:
            screen: Surface to draw on
            player_pos: Player's world position
            current_map: Current map object
            map_key: Current map identifier
        """
        # Cache map surface if needed
        self.cache_map_surface(current_map, map_key)
        
        if self.map_surface is None:
            return
        
        # Create background with semi-transparency
        bg_surface = pg.Surface((self.size, self.size))
        bg_surface.fill((20, 20, 20))
        bg_surface.set_alpha(180)
        
        # Draw background
        screen.blit(bg_surface, (self.position.x, self.position.y))
        
        # Center the map on the minimap background
        map_x = self.position.x + (self.size - self.map_surface.get_width()) // 2
        map_y = self.position.y + (self.size - self.map_surface.get_height()) // 2
        
        # Draw the scaled map
        screen.blit(self.map_surface, (map_x, map_y))
        
        # Calculate player position on minimap
        player_minimap_x = map_x + (player_pos.x * self.scale)
        player_minimap_y = map_y + (player_pos.y * self.scale)
        
        # Draw player dot
        pg.draw.circle(screen, self.player_color, 
                      (int(player_minimap_x), int(player_minimap_y)), 
                      4)
        
        # Draw white border around player dot
        pg.draw.circle(screen, (255, 255, 255), 
                      (int(player_minimap_x), int(player_minimap_y)), 
                      4, 1)
        
        # Draw border around minimap
        border_rect = pg.Rect(self.position.x, self.position.y, self.size, self.size)
        pg.draw.rect(screen, self.border_color, border_rect, self.border_thickness)
        
        # Optional: Draw title
        font = pg.font.Font(None, 20)
        title_text = font.render("MAP", True, (255, 255, 255))
        screen.blit(title_text, (self.position.x + 5, self.position.y + 5))