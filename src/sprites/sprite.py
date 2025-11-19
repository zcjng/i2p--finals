import pygame as pg
from src.core.services import resource_manager
from src.utils import Position, PositionCamera
from typing import Optional

class Sprite:
    image: pg.Surface
    rect: pg.Rect
    
    def __init__(self, img_path: str, size: tuple[int, int] | None = None, half: str | None = None):
        
        
        full_image = resource_manager.get_image(img_path)
        
        if half == 'left':
            width = full_image.get_width() // 2
            self.image = full_image.subsurface((0, 0, width, full_image.get_height()))
        elif half == 'right':
            width = full_image.get_width() // 2
            self.image = full_image.subsurface((width, 0, width, full_image.get_height()))
        else:
            self.image = full_image
            
        if half is not None:
            self.image = self.image.copy()
            
        if size is not None:
            self.image = pg.transform.scale(self.image, size)
        self.rect = self.image.get_rect()
        
    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        if camera is not None:
            screen.blit(self.image, camera.transform_rect(self.rect))
        else:
            screen.blit(self.image, self.rect)
        
    def draw_hitbox(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        if camera is not None:
            pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(self.rect), 1)
        else:
            pg.draw.rect(screen, (255, 0, 0), self.rect, 1)
        
    def update_pos(self, pos: Position):
        self.rect.topleft = (round(pos.x), round(pos.y))