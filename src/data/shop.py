import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item
from src.interface.components import Button
from src.core.services import scene_manager, input_manager
from src.sprites import Sprite

class Shop:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.overlay = False
        
        # UI elements
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0))
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        # Shop UI sprites, buttons, etc.
        self.frame = Sprite("UI/raw/UI_Flat_Frame03a.png", (700, 500))
        self.title = Sprite("UI/raw/UI_Flat_Banner01a.png", (410, 110))
        # ... more UI elements
        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px + 250, py - 200, 80, 80,
            lambda: self.close()
        )
        
        self.items = [
            {"name": "Potion", "price": 200, "description": "Restores 20 HP"},
            {"name": "Pokeball", "price": 200, "description": "Catch Pokemon"},

        ]
        
        self.selected_index = 0
        self.selector = Sprite("UI/raw/UI_Selector.png", (25, 25))
        
        self.buy_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_1.png",
            px - 100, py + 150, 200, 60,
            lambda: self.buy_selected_item()
        )
        
        # Fonts
        self.title_font = pg.font.Font("assets/fonts/Minecraft.ttf", 48)
        self.item_font = pg.font.Font("assets/fonts/Minecraft.ttf", 30)
        self.desc_font = pg.font.Font("assets/fonts/Minecraft.ttf", 24)
        
    def open(self):
        self.overlay = True
        self.selected_index = 0
        self.game_manager.overlay = True
        
    def close(self):
        self.overlay = False
        self.game_manager.overlay = False
        
    def handle_input(self):
        """Handle keyboard navigation"""
        if input_manager.key_pressed(pg.K_UP):
            self.selected_index = max(0, self.selected_index - 1)
            
        elif input_manager.key_pressed(pg.K_DOWN):
            self.selected_index = min(len(self.items) - 1, self.selected_index + 1)
            
        elif input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_z):
            self.buy_selected_item()
            
        elif input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
            self.close()
            
    
    def buy_selected_item(self):
        """Purchase the currently selected item"""
        if not self.items:
            return
        
        item = self.items[self.selected_index]
        
        if self.game_manager.bag.spend_money(item["price"]):
            # Successfully purchased
            self.game_manager.bag.add_item(
                item["name"], 
                item.get("sprite_path", "ingame_ui/default.png")
            )
            print(f"Purchased {item['name']} for ${item['price']}")
        else:
            print("Not enough money!")
            
    def update(self, dt: float):
        if self.overlay:
            # Handle shop interactions
            self.handle_input()
            self.close_button.update(dt)
            self.buy_button.update(dt)
            
    def draw(self, screen: pg.Surface):
        if not self.overlay:
            return
            
        # Draw dim overlay
        screen.blit(self.dim_overlay, (0, 0))
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        
        # Draw frame and title
        screen.blit(self.frame.image, (px - 350, py - 250))
        screen.blit(self.title.image, (px - 200, py - 290))
        
        # Draw title text
        title_text = self.title_font.render("Poke Mart", True, (0, 0, 0))
        screen.blit(title_text, (px - 80, py - 245))
        
        # Draw player money
        money_text = self.item_font.render(f"Money: ${self.game_manager.bag.money}", True, (255, 215, 0))
        screen.blit(money_text, (px - 300, py - 180))
        
        # Draw items
        start_y = py - 120
        for i, item in enumerate(self.items):
            y_pos = start_y + (i * 60)
            
            # Item name and price
            item_text = self.item_font.render(f"{item['name']} - ${item['price']}", True, (255, 255, 255))
            screen.blit(item_text, (px - 250, y_pos))
            
            # Draw selector next to selected item
            if i == self.selected_index:
                screen.blit(self.selector.image, (px - 290, y_pos + 5))
        
        # Draw selected item description
        if self.items:
            selected_item = self.items[self.selected_index]
            desc_text = self.desc_font.render(selected_item['description'], True, (200, 200, 200))
            screen.blit(desc_text, (px - 300, py + 80))
        
        # Draw buttons
        self.close_button.draw(screen)
        self.buy_button.draw(screen)
        
        # Draw "BUY" text on button
        buy_text = self.item_font.render("BUY", True, (0, 0, 0))
        screen.blit(buy_text, (px - 30, py + 160))