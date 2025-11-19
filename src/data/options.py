import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item
from src.interface.components import Button, Slider
from src.core.services import scene_manager, sound_manager
from src.sprites import Sprite

class Options:
    
    def __init__(self):
        
        self._save_callback = None
        self._load_callback = None
        
        self.overlay = False
        

        
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)  # Set transparency level (0-255)
        self.dim_overlay.fill((0, 0, 0, 175))  # Fill with black
          
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        
        self.options_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            px - 620, py - 520, 100, 100,
            lambda: self.open(),
        )

        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px - 400, py - 400, 80, 80,
            lambda: self.close()
        )
        
        self.mute_button = Button(
            "UI/raw/UI_Flat_ToggleOff03a.png", "UI/raw/UI_Flat_ToggleOff03a.png",
            px - 210, py - 210, 50, 30,
            lambda: sound_manager.set_mute(True)
        )
        
        self.unmute_button = Button(
            "UI/raw/UI_Flat_ToggleOn03a.png", "UI/raw/UI_Flat_ToggleOn03a.png",
            px - 210, py - 210, 50, 30,
            lambda: sound_manager.set_mute(False)
        )
        
        self.load_button = Button(
            "UI/button_load.png", "UI/button_load_hover.png",
            px - 300, py - 150, 100, 100,
            lambda: self._on_load()
        )
        
        self.save_button = Button(
            "UI/button_save.png", "UI/button_save_hover.png",
            px - 150, py - 150, 100, 100,
            lambda: self._on_save()
        )
        
        
        self.volume_slider = Slider(
            x=330, y=270, width=600, height=30,
            track_sprite_path='UI/raw/UI_Flat_BarFill01f.png', handle_sprite_path='UI/raw/UI_Flat_Button01a_1.png',
            initial_value=0.1, minimum=0.0, maximum=1.0, change=lambda value: self.on_volume_change(value)
            )
        
        self.title = Sprite("UI/raw/UI_Flat_Banner01a.png", (410, 110))
        self.frame = Sprite("UI/raw/UI_Flat_Frame03a.png", (700, 500))
        self.frameup = Sprite("UI/raw/UI_Flat_Bar01a.png", (200, 50))
        
        self.framedown = Sprite("UI/raw/UI_Flat_Bar01a.png", (200, 50))
        
        fontObj = pg.font.Font("assets/fonts/Minecraft.ttf", 48)
        self.settings = fontObj.render("Settings", True, (0, 0, 0))
        
        self.fontObj2 = pg.font.Font("assets/fonts/Minecraft.ttf", 30)
        self.volume = self.fontObj2.render("Volume :", True, (0, 0, 0))
        self.mute = self.fontObj2.render("Mute :", True, (0, 0, 0))
        self.update_volume_text(GameSettings.AUDIO_VOLUME)
    
    
    def set_save_callback(self, callback):
        self._save_callback = callback

    def set_load_callback(self, callback):
        self._load_callback = callback
        
    def _on_save(self):
        if self._save_callback:
            self._save_callback()
            
    def _on_load(self):
        if self._load_callback:
            self._load_callback()
            
    def on_volume_change(self, value: float):
        sound_manager.set_volume(value)
        self.update_volume_text(value)
        
    def update_volume_text(self, value: float):
        percentage = int(value * 100)
        self.volume_value = self.fontObj2.render(str(percentage), True, (0,0,0))
        
    
    def update(self, dt: float):
        
        
        if self.overlay:
            self.close_button.update(dt)
            self.volume_slider.update(dt)
            self.load_button.update(dt)
            self.save_button.update(dt)
            if self.volume_slider.dragging:
                GameSettings.IS_MUTE = False
                
            if GameSettings.IS_MUTE:
                self.unmute_button.update(dt)
            else:
                self.mute_button.update(dt)
        else:
            self.options_button.update(dt)
        

    def draw(self, screen: pg.Surface):
        self.options_button.draw(screen) 
        # Draw the dim overlay
        screen.blit(self.frame.image, (GameSettings.SCREEN_WIDTH // 2 - 350, GameSettings.SCREEN_HEIGHT // 2 - 250))
        screen.blit(self.frameup.image, (GameSettings.SCREEN_WIDTH // 2 - 330, GameSettings.SCREEN_HEIGHT // 2 - 160))
        screen.blit(self.title.image, (GameSettings.SCREEN_WIDTH // 2 - 200, GameSettings.SCREEN_HEIGHT // 2 - 290))
        screen.blit(self.volume, (GameSettings.SCREEN_WIDTH // 2 - 315, GameSettings.SCREEN_HEIGHT // 2 - 147)) 
        screen.blit(self.volume_value, (GameSettings.SCREEN_WIDTH // 2 - 180, GameSettings.SCREEN_HEIGHT // 2 - 147)) 
        screen.blit(self.settings, (GameSettings.SCREEN_WIDTH // 2 - 80, GameSettings.SCREEN_HEIGHT // 2 - 245))
        

        screen.blit(self.framedown.image, (GameSettings.SCREEN_WIDTH // 2 - 330, GameSettings.SCREEN_HEIGHT // 2 - 40))
        screen.blit(self.mute, (GameSettings.SCREEN_WIDTH // 2 - 315, GameSettings.SCREEN_HEIGHT // 2 - 30)) 
        
        self.volume_slider.draw(screen)
        self.load_button.draw(screen)
        self.save_button.draw(screen)
        
        if GameSettings.IS_MUTE:
            self.unmute_button.draw(screen)
        else:
            self.mute_button.draw(screen)
    def open(self):
        self.overlay = True
        self.options_button.is_pressed = True
        
    def close(self):
        self.overlay = False
        self.options_button.is_pressed = False