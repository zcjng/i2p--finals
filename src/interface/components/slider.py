from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger, Position
from typing import Callable, override
from .component import UIComponent

class Slider(UIComponent):
    hitbox: pg.Rect
    change: Callable[[float], None] | None
    is_pressed: bool = False

    def __init__(
        self,
        x: int, y: int, width: int, height: int,
        track_sprite_path: str, handle_sprite_path: str,
        initial_value: float, minimum: float, maximum: float,
        change: Callable[[float], None] | None = None,
    ):
        
        self.hitbox = pg.Rect(x, y, width, height)
        self.min_value = minimum
        self.max_value = maximum
        self.value = initial_value
        self.change = change
        self.dragging = False
        
        self.track_sprite = Sprite(track_sprite_path, (width, height))
        handle_size = height * 1.5
        self.handle_sprite = Sprite(handle_sprite_path, (handle_size, handle_size))
        self.handle_radius = handle_size // 1.7
        

    @override
    def update(self, dt: float):
        mouse_pos = input_manager.mouse_pos
        
        handle_x = self.normalize(self.value)
        handle_rect = pg.Rect(handle_x - self.handle_radius,
                              self.hitbox.centery - self.handle_radius,
                              self.handle_radius * 2,
                              self.handle_radius * 2)
        
        if input_manager.mouse_pressed(1):
            if handle_rect.collidepoint(mouse_pos) or self.hitbox.collidepoint(mouse_pos):
                self.dragging = True
                
        if not input_manager.mouse_down(1):
            self.dragging =False
            
        if self.dragging:
            
            relative_x = mouse_pos[0] - self.hitbox.x
            relative_x = max(0, min(relative_x, self.hitbox.width))
            new_value = self.min_value + (relative_x / self.hitbox.width) * (self.max_value - self.min_value)
            
            if new_value != self.value:
                self.value = new_value
                if self.change:
                    self.change(self.value)
    
    def normalize(self, value: float):
        normalize = (value - self.min_value) / (self.max_value - self.min_value)
        return int(self.hitbox.x + normalize * self.hitbox.width)
        
    
    def draw(self, screen: pg.Surface):
        screen.blit(self.track_sprite.image, self.hitbox)
        # Draw handle
        handle_x = self.normalize(self.value)
        handle_pos = Position(handle_x - self.handle_radius, self.hitbox.centery - self.handle_radius)
        self.handle_sprite.update_pos(handle_pos)
        self.handle_sprite.draw(screen)