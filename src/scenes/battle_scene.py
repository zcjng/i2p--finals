import pygame as pg
import threading
import time
from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager


class BattleScene(Scene):
    background: BackgroundSprite
    def __init__(self, player_pokemon, enemy_pokemon):
        self.background = BackgroundSprite("backgrounds/background1.png")
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        self.p_pokemon = player_pokemon
        self.e_pokemon = enemy_pokemon
        
        self.p_name = self.p_pokemon['name']
        self.p_back_sprite = Sprite(self.p_pokemon['battle_sprite'], (500,500), 'right')
        self.p_back_sprite.update_pos(Position(px - 500, py - 350))
        
        self.e_front_sprite = Sprite(self.e_pokemon['battle_sprite'], (400, 400), 'left')
        self.e_front_sprite.update_pos(Position(px + 50, py - 380))
        
        
    @override
    def enter(self):
        if sound_manager.current_bgm:
            return
        
        sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
    def update(self, dt: float):
        pass
    
    def draw(self, screen: pg.Surface):
         self.background.draw(screen)
         self.p_back_sprite.draw(screen)
         self.e_front_sprite.draw(screen)
         