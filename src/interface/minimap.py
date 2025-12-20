import pygame as pg
from src.utils import GameSettings, Position

class Minimap:
    def __init__(self, size: int = 150, padding: int = 10):
        """
        Initialize the minimap
        
        Args:
            size: Size of the minimap circle (diameter)
            padding: Distance from screen edge
        """
        self.size = size
        self.padding = padding
        self.radius = size // 2
        self.position = Position(padding + self.radius, padding + self.radius)  # Center point
        
        # Cached map surface (will be set when map changes)
        self.map_surface = None
        self.current_map_key = None
        
        # Zoom level - how much of the map to show (smaller = more zoomed in)
        self.zoom_factor = 0.50  # Shows 15% of the full map around player
        
        # Colors
        self.player_color = (255, 50, 50)  # Red dot for player
        self.border_color = (0, 0, 0)  # White border
        self.bg_color = (20, 20, 20)  # Dark background
        
        # Create border frame
        self.border_thickness = 3
        
        self.visible = False
        
        # Create circular mask for rendering
        self.circle_surface = pg.Surface((size, size), pg.SRCALPHA)
        pg.draw.circle(self.circle_surface, (255, 255, 255), (self.radius, self.radius), self.radius)
        
    def toggle(self):
        """Toggle minimap visibility"""
        self.visible = not self.visible
        
    def show(self):
        """Show the minimap"""
        self.visible = True
        
    def hide(self):
        """Hide the minimap"""
        self.visible = False
        
    def cache_map_surface(self, map_obj, map_key: str):
        """
        Cache the current map as a surface
        Only re-render when map changes
        """
        if self.current_map_key == map_key and self.map_surface is not None:
            return  # Already cached
        
        # Get the pre-rendered map surface
        self.map_surface = map_obj._surface.copy()
        self.current_map_key = map_key
        
        # Store map dimensions
        self.map_width = self.map_surface.get_width()
        self.map_height = self.map_surface.get_height()
        
    def draw(self, screen: pg.Surface, player_pos: Position, current_map, map_key: str):
        """
        Draw the minimap centered on player position with circular border
        
        Args:
            screen: Surface to draw on
            player_pos: Player's world position
            current_map: Current map object
            map_key: Current map identifier
        """
        if not self.visible:
            return
            
        self.cache_map_surface(current_map, map_key)
        
        if self.map_surface is None:
            return
        
        # Create a surface for the minimap content
        minimap_surface = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Calculate the visible area around the player (zoomed in)
        view_width = self.map_width * self.zoom_factor
        view_height = self.map_height * self.zoom_factor
        
        # Calculate the top-left corner of the visible area centered on player
        view_x = player_pos.x - view_width / 2
        view_y = player_pos.y - view_height / 2
        
        # Clamp to map boundaries
        view_x = max(0, min(view_x, self.map_width - view_width))
        view_y = max(0, min(view_y, self.map_height - view_height))
        
        # Create rect for the area to extract from the full map
        view_rect = pg.Rect(int(view_x), int(view_y), int(view_width), int(view_height))
        
        # Extract the visible portion of the map
        try:
            visible_map = self.map_surface.subsurface(view_rect).copy()
        except ValueError:
            # If subsurface fails, just use the whole map
            visible_map = self.map_surface.copy()
        
        # Scale the visible portion to fill the minimap
        scaled_map = pg.transform.scale(visible_map, (self.size, self.size))
        
        # Draw background
        pg.draw.circle(minimap_surface, self.bg_color, (self.radius, self.radius), self.radius)
        
        # Blit the scaled map onto the minimap surface
        minimap_surface.blit(scaled_map, (0, 0))
        
        # Apply circular mask
        minimap_surface.blit(self.circle_surface, (0, 0), special_flags=pg.BLEND_RGBA_MIN)
        
        # Calculate player position on minimap (should be center since we're centered on player)
        player_minimap_x = self.radius
        player_minimap_y = self.radius
        
        # But if player is near map edges, adjust position
        if view_x <= 0:
            player_minimap_x = int((player_pos.x / view_width) * self.size)
        elif view_x >= self.map_width - view_width:
            player_minimap_x = int(((player_pos.x - view_x) / view_width) * self.size)
            
        if view_y <= 0:
            player_minimap_y = int((player_pos.y / view_height) * self.size)
        elif view_y >= self.map_height - view_height:
            player_minimap_y = int(((player_pos.y - view_y) / view_height) * self.size)
        
        # Draw player dot
        pg.draw.circle(minimap_surface, self.player_color, 
                      (player_minimap_x, player_minimap_y), 
                      5)
        
        # Draw white border around player dot
        pg.draw.circle(minimap_surface, (255, 255, 255), 
                      (player_minimap_x, player_minimap_y), 
                      5, 2)
        
        # Draw the minimap to the screen
        screen.blit(minimap_surface, (self.padding, self.padding))
        
        # Draw circular border
        pg.draw.circle(screen, self.border_color, 
                      (int(self.position.x), int(self.position.y)), 
                      self.radius, self.border_thickness)
        
        # Optional: Draw title
        font = pg.font.Font(None, 18)
        title_text = font.render("MAP", True, (255, 255, 255))
        title_shadow = font.render("MAP", True, (0, 0, 0))
        
        title_x = self.padding + self.radius - title_text.get_width() // 2
        title_y = self.padding + 8
        
        screen.blit(title_shadow, (title_x + 1, title_y + 1))
        screen.blit(title_text, (title_x, title_y))