
import pygame as pg
from src.utils import GameSettings, Position
from src.interface.components import Button
from src.sprites import Sprite, Animation
from src.core.services import input_manager

class Menu:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.overlay = False
        

        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0))
        

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        

        button_x = px + 300
        button_y_start = py - 300
        button_spacing = 130
        
        
        self.pokemon_button = Button(
            "UI/Pokemon.png", "UI/Pokemon.png",
            button_x, button_y_start, 300, 80,
            lambda: self.open_pokemon()
        )
        
        self.bag_button = Button(
            "UI/Bag.png", "UI/Bag.png",
            button_x, button_y_start + button_spacing, 300, 80,
            lambda: self.open_bag()
        )
        
        self.save_button = Button(
            "UI/Save.png", "UI/Save.png",
            button_x, button_y_start + button_spacing * 2, 300, 80,
            lambda: self.save_game()
        )
        
        self.load_button = Button(
            "UI/Load.png", "UI/Load.png",
            button_x, button_y_start + button_spacing * 3, 300, 80,
            lambda: self.load_game()
        )
        
        self.options_button = Button(
            "UI/Options.png", "UI/Options.png",
            button_x, button_y_start + button_spacing * 4, 300, 80,
            lambda: self.open_options()
        )
        
        self.close_button = Button(
            "UI/Close.png", "UI/Close.png",
            button_x - 900, button_y_start - 20, 300, 150,
            lambda: self.close()
        )
        

        self.selector = Animation(
            "UI/Flecha.png",
            rows=["idle"],
            n_keyframes=8,
            size=(60, 40),
            loop=1.5,
            vertical=True
        )
        

        self.buttons = [
            self.pokemon_button,
            self.bag_button,
            self.save_button,
            self.load_button,
            self.options_button,
            self.close_button
        ]
        self.button_positions = [
            (button_x, button_y_start),
            (button_x, button_y_start + button_spacing),
            (button_x, button_y_start + button_spacing * 2),
            (button_x, button_y_start + button_spacing * 3),
            (button_x, button_y_start + button_spacing * 4),
            (button_x - 900, button_y_start - 20)
        ]
        self.selected_index = 0
        self.saved_index = 0

        self.brightness_overlay = pg.Surface((300, 80))
        self.brightness_overlay.fill((255, 255, 255))
        self.brightness_overlay.set_alpha(int(255 * 0.15))
        

        self._save_callback = None
        self._load_callback = None
    
    def set_save_callback(self, callback):
        self._save_callback = callback
    
    def set_load_callback(self, callback):
        self._load_callback = callback
    
    def open(self):
        self.overlay = True
        self.selected_index = 0
    
    def close(self):
        self.overlay = False
    
    def toggle(self):
        if self.overlay:
            self.close()
        else:
            self.open()
    
    def open_pokemon(self):

        self.game_manager.pokemon.opened_from_menu = True
        self.close()
        self.game_manager.pokemon.open()
        
    
    def open_bag(self):
        self.game_manager.bag.opened_from_menu = True
        self.close()
        self.game_manager.bag.open()
    
    def open_options(self):
        self.game_manager.options.opened_from_menu = True
        self.close()
        self.game_manager.options.open()
    
    def save_game(self):
        if self._save_callback:
            self._save_callback()
    
    def load_game(self):
        if self._load_callback:
            self._load_callback()
    
    def handle_input(self):
        """Handle keyboard navigation"""

        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.buttons)
        

        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.buttons)
            
        if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
            self.saved_index = self.selected_index
            index = (self.selected_index + 5)
            print(index)
            if index >= 5:
                index = 5
                self.selected_index = index
                
        if input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
            self.selected_index = self.saved_index

        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e) or input_manager.key_pressed(pg.K_SPACE):
            self.buttons[self.selected_index].on_click()
    
    def update(self, dt: float):
        if self.overlay:
            self.handle_input()
            
            self.selector.update(dt)
            

            self.pokemon_button.update(dt)
            self.bag_button.update(dt)
            self.save_button.update(dt)
            self.load_button.update(dt)
            self.options_button.update(dt)
            self.close_button.update(dt)
    
    def draw(self, screen: pg.Surface):
        if self.overlay:

            screen.blit(self.dim_overlay, (0, 0))
            

            self.pokemon_button.draw(screen)
            self.bag_button.draw(screen)
            self.save_button.draw(screen)
            self.load_button.draw(screen)
            self.options_button.draw(screen)
            self.close_button.draw(screen)
            

            button_x, button_y = self.button_positions[self.selected_index]
            
            if self.selected_index == 5:
                self.brightness_overlay = pg.Surface((75, 75))
                self.brightness_overlay.fill((255, 255, 255))
                self.brightness_overlay.set_alpha(int(255 * 0.15))
                screen.blit(self.brightness_overlay, (button_x, button_y))
            else:
                self.brightness_overlay = pg.Surface((300, 80))
                self.brightness_overlay.fill((255, 255, 255))
                self.brightness_overlay.set_alpha(int(255 * 0.15))
                screen.blit(self.brightness_overlay, (button_x, button_y))
            

            selector_x = button_x - 70
            selector_y = button_y + (90 // 2) - (self.selector.rect.height // 2)
            self.selector.update_pos(Position(selector_x, selector_y))
            self.selector.draw(screen)