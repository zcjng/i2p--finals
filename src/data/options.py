import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item
from src.interface.components import Button, Slider
from src.core.services import scene_manager, sound_manager
from src.sprites import Sprite

class Options:
    
    def __init__(self, game_manager =None):
        
        
        self.overlay = False
        self.opened_from_menu = False
        self.game_manager = game_manager

        
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0, 175))
          
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        

        self.close_button = Button(
            "options/exit.png", "options/exit2.png",
            px - 100, py + 100, 200, 80,
            lambda: self.close()
        )
        
        self.mute_button = Button(
            "options/blank.png", "options/blank2.png",
            GameSettings.SCREEN_WIDTH // 2 + 240, GameSettings.SCREEN_HEIGHT // 2 - 147, 60, 60,
            lambda: sound_manager.set_mute(True)
        )
        
        self.unmute_button = Button(
            "options/x.png", "options/x2.png",
            GameSettings.SCREEN_WIDTH // 2 + 240, GameSettings.SCREEN_HEIGHT // 2 - 147, 60, 60,
            lambda: sound_manager.set_mute(False)
        )
        
        
        
        self.volume_slider = Slider(
            x=GameSettings.SCREEN_WIDTH // 2 - 295, y=GameSettings.SCREEN_HEIGHT // 2 - 197, width=593, height=48,
            track_sprite_path='UI/raw/UI_Flat_BarFill01f.png', handle_sprite_path='UI/raw/UI_Flat_Button01a_1.png',
            initial_value=0.1, minimum=0.0, maximum=1.0, change=lambda value: self.on_volume_change(value)
            )
        
        self.title = Sprite("options/banner.png", (410, 110))
        self.frame = Sprite("options/frame.png", (1000, 800))
    
        
        
        
        self.fontObj2 = pg.font.Font("assets/fonts/Pokemon.ttf", 50)
        self.volume = self.fontObj2.render("VOLUME :", True, (255, 255, 255))
        self.mute = self.fontObj2.render("MUTE :", True, (255, 255, 255))
        self.update_volume_text(GameSettings.AUDIO_VOLUME)
    
    

        

            
    def on_volume_change(self, value: float):
        sound_manager.set_volume(value)
        self.update_volume_text(value)
        
    def update_volume_text(self, value: float):
        percentage = int(value * 100)
        self.volume_value = self.fontObj2.render(str(percentage), True, (255,255,255))
        
    
    def update(self, dt: float):
        
        
        if self.overlay:
            self.close_button.update(dt)
            self.volume_slider.update(dt)
            if self.volume_slider.dragging:
                GameSettings.IS_MUTE = False
                
            if GameSettings.IS_MUTE:
                self.unmute_button.update(dt)
            else:
                self.mute_button.update(dt)

        

    def draw(self, screen: pg.Surface):

        screen.blit(self.frame.image, (GameSettings.SCREEN_WIDTH // 2 - 420, GameSettings.SCREEN_HEIGHT // 2 - 350))
        
        screen.blit(self.title.image, (GameSettings.SCREEN_WIDTH // 2 - 145, GameSettings.SCREEN_HEIGHT // 2 - 360))
        screen.blit(self.volume, (GameSettings.SCREEN_WIDTH // 2 - 290, GameSettings.SCREEN_HEIGHT // 2 - 250)) 
        screen.blit(self.volume_value, (GameSettings.SCREEN_WIDTH // 2 + 260, GameSettings.SCREEN_HEIGHT // 2 - 250)) 
        

        
        screen.blit(self.mute, (GameSettings.SCREEN_WIDTH // 2 - 290, GameSettings.SCREEN_HEIGHT // 2 - 140)) 
        
        self.volume_slider.draw(screen)

        
        if GameSettings.IS_MUTE:
            self.unmute_button.draw(screen)
        else:
            self.mute_button.draw(screen)
    def open(self):
        self.overlay = True
        
    def close(self):
        self.overlay = False
        if self.opened_from_menu:
            self.opened_from_menu = False
            
            self.game_manager.menu.open()