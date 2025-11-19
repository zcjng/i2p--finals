from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger, Direction
from src.core import GameManager
import math
from typing import override


class Player(Entity):
    speed: float = 3.0 * GameSettings.TILE_SIZE
    game_manager: GameManager
    moving = False
    direction = Direction.DOWN
    teleporting = False
    teleport_cooldown = 0.2



    def __init__(self, x: float, y: float, game_manager: GameManager):
        super().__init__(x, y, game_manager)

    @override
    def update(self, dt: float):
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt
            
        if self.teleporting:
            if not self.game_manager._transitioning:
                self.teleporting = False
            else:
                return
            
        if not self.moving and self.teleport_cooldown <= 0:
            dx, dy = 0, 0
            
            if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a): 
                dx, dy = -1, 0
                self.direction = Direction.LEFT
            if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
                dx, dy = 1, 0
                self.direction = Direction.RIGHT
            if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
                dx, dy = 0, -1
                self.direction = Direction.UP
            if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
                dx, dy = 0, 1
                self.direction = Direction.DOWN
                
            if dx != 0 or dy != 0:
                
                next_pos = Position(
                    self.position.x + dx * GameSettings.TILE_SIZE,
                    self.position.y + dy * GameSettings.TILE_SIZE
                    
                )
                
                next_rect = self.animation.rect.move(dx * GameSettings.TILE_SIZE, dy * GameSettings.TILE_SIZE)
                
                tp = None
                
                if self.teleport_cooldown <= 0:
                    tp = self.game_manager.current_map.check_teleport(next_pos)
                    if tp:
                        Logger.debug("Teleport triggered before collision check")
                        self.game_manager.switch_map(tp.destination, self.direction)
                        self.teleport_cooldown = 0.2
                        self.teleporting = True
                        self.moving = False
                        return
                
                    
               
                if not self.game_manager.current_map.check_collision(next_rect) and not self.collides_with_entity(next_rect):
                    self.moving = True
                    self.move_start = Position(self.position.x, self.position.y)
                    self.move_target = next_pos
        
        if self.moving:
            
            delta = Position(
                self.move_target.x - self.position.x,
                self.move_target.y - self.position.y
            )
            
            dist = math.sqrt(delta.x ** 2 + delta.y ** 2)
            
            if dist > self.speed * dt:
                move = self.speed * dt / dist
                self.position.x += delta.x * move
                self.position.y += delta.y * move
            else:
                self.position.x = self.move_target.x
                self.position.y = self.move_target.y   
                self.moving = False

                    
        dir_map = {
            Direction.UP: "up",
            Direction.DOWN: "down",
            Direction.LEFT: "left",
            Direction.RIGHT: "right"
        }
        
        self.animation.switch(dir_map[self.direction])
        if self.moving:
            self.animation.update(dt)
        else:
            self.animation.accumulator = 0  
              
        
        super().update(dt)

    def collides_with_entity(self, next_rect):
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = enemy.animation.rect.copy()
            enemy_rect.topleft = (enemy.position.x, enemy.position.y)
            if next_rect.colliderect(enemy_rect):
                return True
        return False

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

