# src/interface/menu.py
import pygame as pg
from src.utils import GameSettings, Position
from src.interface.components import Button
from src.sprites import Sprite, Animation
from src.core.services import input_manager

class Menu:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.overlay = False
        
        # Dim overlay
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0))
        
        # Menu positioning
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        
        # Menu buttons (vertical layout)
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
        
        # Selector sprite
        self.selector = Animation(
            "UI/Flecha.png",
            rows=["idle"],  # If you have multiple animation states, add them here
            n_keyframes=8,   # Number of frames in the animation (adjust based on your sprite)
            size=(60, 40),   # Size of the selector
            loop=1.5,           # Animation loop time in seconds
            vertical=True
        )
        
        # Menu navigation
        self.buttons = [
            self.pokemon_button,
            self.bag_button,
            self.save_button,
            self.load_button,
            self.options_button
        ]
        self.button_positions = [
            (button_x, button_y_start),
            (button_x, button_y_start + button_spacing),
            (button_x, button_y_start + button_spacing * 2),
            (button_x, button_y_start + button_spacing * 3),
            (button_x, button_y_start + button_spacing * 4)
        ]
        self.selected_index = 0
        
        # Brightness overlay for selected button
        self.brightness_overlay = pg.Surface((300, 80))
        self.brightness_overlay.fill((255, 255, 255))
        self.brightness_overlay.set_alpha(int(255 * 0.15))  # 15% brightness increase
        
        # Callbacks
        self._save_callback = None
        self._load_callback = None
    
    def set_save_callback(self, callback):
        self._save_callback = callback
    
    def set_load_callback(self, callback):
        self._load_callback = callback
    
    def open(self):
        self.overlay = True
        self.selected_index = 0  # Reset to first option
    
    def close(self):
        self.overlay = False
    
    def toggle(self):
        if self.overlay:
            self.close()
        else:
            self.open()
    
    def open_pokemon(self):
        # TODO: Open Pokemon party screen
        self.close()
        self.game_manager.pokemon.open()
        
    
    def open_bag(self):
        self.close()
        self.game_manager.bag.open()
    
    def open_options(self):
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
        # Navigate up
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.buttons)
        
        # Navigate down
        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.buttons)
        
        # Select/activate button
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e) or input_manager.key_pressed(pg.K_SPACE):
            self.buttons[self.selected_index].on_click()
    
    def update(self, dt: float):
        if self.overlay:
            self.handle_input()
            
            self.selector.update(dt)
            
            # Still allow mouse clicks on buttons
            self.pokemon_button.update(dt)
            self.bag_button.update(dt)
            self.save_button.update(dt)
            self.load_button.update(dt)
            self.options_button.update(dt)
    
    def draw(self, screen: pg.Surface):
        if self.overlay:
            # Draw dim overlay
            screen.blit(self.dim_overlay, (0, 0))
            
            # Draw buttons
            self.pokemon_button.draw(screen)
            self.bag_button.draw(screen)
            self.save_button.draw(screen)
            self.load_button.draw(screen)
            self.options_button.draw(screen)
            
            # Draw brightness overlay on selected button
            button_x, button_y = self.button_positions[self.selected_index]
            screen.blit(self.brightness_overlay, (button_x, button_y))
            
            # Draw selector next to selected button
            selector_x = button_x - 70  # Position to the left of button
            selector_y = button_y + (90 // 2) - (self.selector.rect.height // 2)  # Center vertically (80 is button height)
            self.selector.update_pos(Position(selector_x, selector_y))
            self.selector.draw(screen)