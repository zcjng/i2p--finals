import pygame as pg

from src.sprites import Sprite
from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button, Slider
from src.core.services import scene_manager, sound_manager, input_manager

from typing import override

class SettingScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    exit_button: Button
    
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)  # Set transparency level (0-255)
        self.dim_overlay.fill((0, 0, 0))  # Fill with black
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        
        self.exit_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            px + 300, py - 450, 90, 90,
            lambda: scene_manager.change_scene("menu")
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
        

        
    def on_volume_change(self, value: float):
        sound_manager.set_volume(value)
        self.update_volume_text(value)
        
    def update_volume_text(self, value: float):
        percentage = int(value * 100)
        self.volume_value = self.fontObj2.render(str(percentage), True, (0,0,0))
        
    @override
    def enter(self):
        
        pass

    @override
    def exit(self):
        pass

    @override
    def update(self, dt: float):
        if input_manager.key_pressed(pg.K_SPACE):
            scene_manager.change_scene("menu")
            return
        self.exit_button.update(dt)
        self.volume_slider.update(dt)
        
        if self.volume_slider.dragging:
            GameSettings.IS_MUTE = False
        if GameSettings.IS_MUTE:
            self.unmute_button.update(dt)
        else:
            self.mute_button.update(dt)
        

    @override
    def draw(self, screen: pg.Surface):

        self.background.draw(screen)
        screen.blit(self.dim_overlay, (0, 0))  # Draw the dim overlay
        screen.blit(self.frame.image, (GameSettings.SCREEN_WIDTH // 2 - 350, GameSettings.SCREEN_HEIGHT // 2 - 250))
        screen.blit(self.frameup.image, (GameSettings.SCREEN_WIDTH // 2 - 330, GameSettings.SCREEN_HEIGHT // 2 - 160))
        screen.blit(self.title.image, (GameSettings.SCREEN_WIDTH // 2 - 200, GameSettings.SCREEN_HEIGHT // 2 - 290))
        screen.blit(self.volume, (GameSettings.SCREEN_WIDTH // 2 - 315, GameSettings.SCREEN_HEIGHT // 2 - 147)) 
        screen.blit(self.volume_value, (GameSettings.SCREEN_WIDTH // 2 - 180, GameSettings.SCREEN_HEIGHT // 2 - 147)) 
        screen.blit(self.settings, (GameSettings.SCREEN_WIDTH // 2 - 80, GameSettings.SCREEN_HEIGHT // 2 - 245))
        

        screen.blit(self.framedown.image, (GameSettings.SCREEN_WIDTH // 2 - 330, GameSettings.SCREEN_HEIGHT // 2 - 40))
        screen.blit(self.mute, (GameSettings.SCREEN_WIDTH // 2 - 315, GameSettings.SCREEN_HEIGHT // 2 - 30)) 
        
        self.exit_button.draw(screen)
        self.volume_slider.draw(screen)
        
        if GameSettings.IS_MUTE:
            self.unmute_button.draw(screen)
        else:
            self.mute_button.draw(screen)