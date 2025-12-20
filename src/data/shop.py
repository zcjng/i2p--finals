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
        

        self.mode = "buy"
        

        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0))
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        

        self.frame = Sprite("options/frame2.png", (1200, 700))
        self.title = Sprite("UI/raw/UI_Flat_Banner01a.png", (410, 110))
        
        self.close_button = Button(
            "options/exit.png", "options/exit2.png",
            px + 225, py + 215, 150, 70,
            lambda: self.close()
        )
        

        self.shop_items = [
            {"name": "Potion", "price": 200, "description": "Restores 20 HP", "sprite_path": "ingame_ui/potion.png", "category": "Medicine"},
            {"name": "Pokeball", "price": 200, "description": "Catch Pokemon", "sprite_path": "ingame_ui/ball.png", "category": "Poke Balls"},
            {"name": "Rare Candy", "price": 500, "description": "Level up Pokemon", "sprite_path": "ingame_ui/options2.png", "category": "Medicine"},
        ]
        
        self.selected_index = 0
        self.selector = pg.Surface((715, 80))
        self.selector.set_alpha(100)
        self.selector.fill((255, 255, 255))


        self.scroll_offset = 0
        self.max_visible_items = 5
        

        self.action_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_1.png",
            px - 100, py + 150, 200, 60,
            lambda: self.perform_action()
        )
        

        self.toggle_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_1.png",
            px + 120, py + 150, 200, 60,
            lambda: self.toggle_mode()
        )
        

        self.title_font = pg.font.Font("assets/fonts/Pokemon.ttf", 48)
        self.item_font = pg.font.Font("assets/fonts/Pokemon.ttf", 30)
        self.desc_font = pg.font.Font("assets/fonts/Pokemon.ttf", 24)
        self.small_font = pg.font.Font("assets/fonts/Pokemon.ttf", 18)
        
    def open(self):
        self.overlay = True
        self.mode = "buy"
        self.selected_index = 0
        self.game_manager.overlay = True
        
    def close(self):
        self.overlay = False
        self.game_manager.overlay = False
        
    def toggle_mode(self):
        """Toggle between buy and sell mode"""
        self.mode = "sell" if self.mode == "buy" else "buy"
        self.selected_index = 0
        self.scroll_offset = 0
        
    def get_current_items(self):
        """Get items based on current mode"""
        if self.mode == "buy":
            return self.shop_items
        else:

            sellable = []
            for item in self.game_manager.bag._items_data:
                if item.get("category") != "Key Items":
                    sellable.append(item)
            return sellable
        
    def handle_input(self):
        """Handle keyboard navigation"""
        items = self.get_current_items()
        
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            if self.selected_index > 0:
                self.selected_index -= 1

                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
            
        elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            if self.selected_index < len(items) - 1:
                self.selected_index += 1

                if self.selected_index >= self.scroll_offset + self.max_visible_items:
                    self.scroll_offset = self.selected_index - self.max_visible_items + 1
            
        elif input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e):
            self.perform_action()
            
        elif input_manager.key_pressed(pg.K_TAB):
            self.toggle_mode()
            
        elif input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
            self.close()
    
    def perform_action(self):
        """Perform buy or sell action based on mode"""
        if self.mode == "buy":
            self.buy_selected_item()
        else:
            self.sell_selected_item()
    
    def buy_selected_item(self):
        """Purchase the currently selected item"""
        items = self.get_current_items()
        if not items or self.selected_index >= len(items):
            return
        
        item = items[self.selected_index]
        
        if self.game_manager.bag.spend_money(item["price"]):

            self.game_manager.bag.add_item(
                item["name"], 
                item.get("sprite_path", "ingame_ui/default.png"),
                item.get("category", "Items")
            )
            from src.utils import Logger
            Logger.info(f"Purchased {item['name']} for ${item['price']}")
        else:
            from src.utils import Logger
            Logger.info("Not enough money!")
    
    def sell_selected_item(self):
        """Sell the currently selected item"""
        items = self.get_current_items()
        if not items or self.selected_index >= len(items):
            return
        
        item = items[self.selected_index]
        

        if item.get("category") == "Key Items":
            from src.utils import Logger
            Logger.info("Cannot sell Key Items!")
            return
        

        sell_price = self.get_sell_price(item["name"])
        

        for bag_item in self.game_manager.bag._items_data:
            if bag_item["name"] == item["name"]:
                bag_item["count"] -= 1
                

                self.game_manager.bag.add_money(sell_price)
                

                if bag_item["count"] <= 0:
                    self.game_manager.bag._items_data.remove(bag_item)

                    if self.selected_index >= len(self.get_current_items()):
                        self.selected_index = max(0, len(self.get_current_items()) - 1)
                
                from src.utils import Logger
                Logger.info(f"Sold {item['name']} for ${sell_price}")
                break
    
    def get_sell_price(self, item_name: str):
        """Calculate sell price for an item (half of buy price)"""

        for shop_item in self.shop_items:
            if shop_item["name"] == item_name:
                return shop_item["price"] // 2
        

        return 50
            
    def update(self, dt: float):
        if self.overlay:
            self.handle_input()
            self.close_button.update(dt)
            self.action_button.update(dt)
            self.toggle_button.update(dt)
            
    def draw(self, screen: pg.Surface):
        if not self.overlay:
            return
            

        screen.blit(self.dim_overlay, (0, 0))
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        

        screen.blit(self.frame.image, (px - 500, py - 300))

        

        mode_title = "BUY ITEMS" if self.mode == "buy" else "SELL ITEMS"
        title_text = self.title_font.render(mode_title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(px - 260, py - 252))
        screen.blit(title_text, title_rect)
        

        money_text = self.title_font.render(f"Money: ${self.game_manager.bag.money}", True, (255, 255, 255))
        screen.blit(money_text, (px + 150, py - 272))
        
        

        items = self.get_current_items()
        
        if not items:
            no_items_text = self.item_font.render("No items to sell!", True, (200, 200, 200))
            screen.blit(no_items_text, (px - 150, py - 50))
        else:

            start_y = py - 120
            visible_items = items[self.scroll_offset:self.scroll_offset + self.max_visible_items]
            
            for i, item in enumerate(visible_items):
                actual_index = self.scroll_offset + i
                y_pos = start_y + (i * 60) - 90
                

                if self.mode == "buy":
                    price = item.get('price', 0)
                    price_text = f"${price}"
                else:
                    sell_price = self.get_sell_price(item['name'])
                    count = item.get('count', 1)
                    price_text = f"${sell_price} (x{count})"
                

                item_text = self.title_font.render(f"{price_text}  {item['name']}", True, (255, 255, 255))
                screen.blit(item_text, (px  -330, y_pos))
                

                if actual_index == self.selected_index:
                    screen.blit(self.selector, (px - 350, y_pos - 15))
            

        

        self.close_button.draw(screen)

        
