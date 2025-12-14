import pygame as pg
import json
from src.utils import GameSettings, Position
from src.utils.definition import Item
from src.interface.components import Button
from src.core.services import scene_manager, input_manager
from src.sprites import Sprite, Animation


class Bag:
    _items_data: list[Item]
    
    def __init__(self, items_data: list[Item] | None = None, money: int = 0, game_manager = None):
        self._items_data = items_data if items_data else []
        self.money = money  
        self.overlay = False
        self.item_used = None
        self.opened_from_menu = False
        self.game_manager = game_manager
        # Category system
        self.categories = [
            {"name": "Items", "bag_icon": "bag_1", "bg": "bg_1"},
            {"name": "Key Items", "bag_icon": "bag_2", "bg": "bg_2"},
            {"name": "Berries", "bag_icon": "bag_3", "bg": "bg_3"},
            {"name": "TMs", "bag_icon": "bag_4", "bg": "bg_4"},
            {"name": "Medicine", "bag_icon": "bag_5", "bg": "bg_5"},
            {"name": "Poke Balls", "bag_icon": "bag_6", "bg": "bg_6"},
            {"name": "Battle Items", "bag_icon": "bag_7", "bg": "bg_7"},
            {"name": "Misc", "bag_icon": "bag_8", "bg": "bg_8"}
        ]
        self.current_category_index = 0
        
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0, 175))
          
        self.font = pg.font.Font('assets/fonts/Minecraft.ttf', 20)
        self.font_small = pg.font.Font('assets/fonts/Minecraft.ttf', 12)
        self.font_category = pg.font.Font('assets/fonts/Pokemon.ttf', 70)
        
        self.item_start_x = GameSettings.SCREEN_WIDTH // 2 - 200
        self.item_start_y = GameSettings.SCREEN_HEIGHT // 2 - 320
        self.item_spacing = 60
        
        # Item selection
        self.selected_item_index = 0
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        
        self.selected_item_index = 0
        self.selected_item_sprite = None
        
        # Load initial sprites
        self.update_sprites()
        
    def update_sprites(self):
        """Update the background and bag icon based on current category"""
        current_cat = self.categories[self.current_category_index]
        
        # Load background
        self.background = Sprite(f"Bag/bg_1.png", (GameSettings.SCREEN_WIDTH - 250, GameSettings.SCREEN_HEIGHT))
        
        # Load bag icon (optional, if you want to display it)
        self.bag_icon = Sprite(f"Bag/{current_cat['bag_icon']}.PNG", (300, 300))
        self.bag_bar = Sprite(f"Bag/bar_bar_cool.png", (GameSettings.SCREEN_WIDTH, 200))
        
        # Load cursor selector
        self.cursor = Sprite(f"Bag/cursor.png", (570, 110))
        self.category_bar = Sprite(f"Bag/category_bar_cool.png", (350, 90))
        
        self.left_arrow = Animation(
            "Bag/leftarrow.png",
            rows=["idle"],  # If you have multiple animation states, add them here
            n_keyframes=8,   # Number of frames in the animation (adjust based on your sprite)
            size=(100, 70),   # Size of the selector
            loop=1,           # Animation loop time in seconds
            vertical=True
        )
        
        self.right_arrow = Animation(
            "Bag/rightarrow.png",
            rows=["idle"],  # If you have multiple animation states, add them here
            n_keyframes=8,   # Number of frames in the animation (adjust based on your sprite)
            size=(100, 70),   # Size of the selector
            loop=1,           # Animation loop time in seconds
            vertical=True
        )
        
    def switch_category(self, direction: int):
        """Switch to next or previous category
        direction: 1 for right, -1 for left
        """
        self.current_category_index = (self.current_category_index + direction) % len(self.categories)
        self.selected_item_index = 0  # Reset selection when switching categories
        self.update_sprites()
        
    def get_current_category_items(self):
        """Get items that belong to the current category"""
        current_category = self.categories[self.current_category_index]["name"]
        
        # Filter items by category
        filtered_items = []
        for item in self._items_data:
            item_category = item.get("category", "Items")  # Default to "Items" if no category
            if item_category == current_category:
                filtered_items.append(item)
        
        return filtered_items
    
    def update_selected_item_sprite(self):
        """Update the sprite of the currently selected item"""
        current_items = self.get_current_category_items()
        
        if self.selected_item_index < len(current_items):
            # An item is selected
            selected_item = current_items[self.selected_item_index]
            sprite_path = selected_item.get("sprite_path")
            if sprite_path:
                self.selected_item_sprite = Sprite(sprite_path, (60, 60))  # <- Creates sprite
            else:
                self.selected_item_sprite = None
        else:
            # CLOSE BAG is selected
            self.selected_item_sprite = None
    def add_money(self, amount: int):
        self.money += amount
        
    def spend_money(self, amount: int):
        if self.money >= amount:
            self.money -= amount
            return True
        return False
    
    def add_item(self, item_name: str, sprite_path: str, category: str = None, count: int = 1):
        """Add an item to the bag or increase its count
        
        Args:
            item_name: Name of the item
            sprite_path: Path to the item sprite
            category: Category the item belongs to (Items, Key Items, Berries, etc.)
            count: Number to add
        """
        # Auto-assign categories based on item name if no category provided
        if category is None:
            if item_name == "Potion":
                category = "Medicine"
            elif item_name == "Pokeball":
                category = "Poke Balls"
            else:
                category = "Items"  # Default category
        
        # Check if item already exists
        for item in self._items_data:
            if item["name"] == item_name:
                item["count"] += count
                # Update category for existing item too
                item["category"] = category
                return
        
        # If not, add new item
        self._items_data.append({
            "name": item_name,
            "count": count,
            "sprite_path": sprite_path,
            "category": category
        })
    
    def fix_item_categories(self):
        """Fix categories for existing items in the bag"""
        for item in self._items_data:
            if item["name"] == "Potion":
                item["category"] = "Medicine"
            elif item["name"] == "Pokeball":
                item["category"] = "Poke Balls"
    
    def handle_input(self):
        """Handle keyboard input for category switching and item selection"""
        current_items = self.get_current_category_items()
        max_index = len(current_items)  # CLOSE BAG is at index = len(current_items)
        
        # Switch left (previous category)
        if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
            self.switch_category(-1)
            self.update_selected_item_sprite()
        
        # Switch right (next category)
        if input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
            self.switch_category(1)
            self.update_selected_item_sprite()
        
        # Navigate up
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            if self.selected_item_index > 0:
                self.selected_item_index -= 1
                self.update_selected_item_sprite()
        
        # Navigate down
        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            if self.selected_item_index < max_index:
                self.selected_item_index += 1
                self.update_selected_item_sprite()
        
        # Select item (Enter or E)
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e):
            if self.selected_item_index == max_index:
                # Selected CLOSE BAG
                self.close(reopen_menu=True)
            else:
            # An item was selected
                selected_item = current_items[self.selected_item_index]
                
                # Town Map can only be used from menu
                if selected_item["name"] == "Town Map":
                    if self.opened_from_menu:
                        self.game_manager.townmap.opened_from_menu = False
                        self.close(reopen_menu=False)
                        self.game_manager.townmap.open()
                    # If not from menu (in battle), do nothing
                
                # Other items can only be used in battle
                elif not self.opened_from_menu:
                    self.item_used = True  # Signal BattleScene
                    self.close()

        
        
        # Close bag with ESC
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.close()
        
    def update(self, dt: float):
        if self.overlay:
            self.handle_input()
            
        self.right_arrow.update(dt)
        self.left_arrow.update(dt)


    def draw(self, screen: pg.Surface):
        # Draw background
        screen.blit(self.background.image, (GameSettings.SCREEN_WIDTH // 2 - 520, GameSettings.SCREEN_HEIGHT // 2 - 360))
        
        # Draw bag icon in top left corner
        screen.blit(self.bag_icon.image, (GameSettings.SCREEN_WIDTH // 2 - 540, GameSettings.SCREEN_HEIGHT // 2 - 200))
        screen.blit(self.category_bar.image, (GameSettings.SCREEN_WIDTH // 2 - 560, GameSettings.SCREEN_HEIGHT // 2 - 300))
        
        selector_x = GameSettings.SCREEN_WIDTH // 2 - 540  # Position to the left of button
        selector_y = GameSettings.SCREEN_HEIGHT // 2 - 50- (self.left_arrow.rect.height // 2)  # Center vertically (80 is button height)
        self.left_arrow.update_pos(Position(selector_x - 70, selector_y))
        self.left_arrow.draw(screen)
        
        self.right_arrow.update_pos(Position(selector_x + 270, selector_y))
        self.right_arrow.draw(screen)
        
        
        
        
        # Draw category name
        current_category = self.categories[self.current_category_index]["name"]
        category_text = self.font_category.render(current_category, True, (255,255,255))
        category_shadow = self.font_category.render(current_category, True, (0, 0, 0))
        text_width = category_text.get_width()
        center_x = GameSettings.SCREEN_WIDTH // 2 - 385 - text_width // 2

        screen.blit(category_shadow, (center_x + 2, GameSettings.SCREEN_HEIGHT // 2 - 288))
        screen.blit(category_text, (center_x, GameSettings.SCREEN_HEIGHT // 2 - 290))
        
        # Draw money
        
        
        
        # Draw navigation hints

        
        # Draw items in current category
        item_y = self.item_start_y
        current_items = self.get_current_category_items()
        
        screen.blit(self.bag_bar.image, (GameSettings.SCREEN_WIDTH // 2 - 640, GameSettings.SCREEN_HEIGHT // 2 + 170))
        
        # Draw all items
        item_index = 0
        for item in current_items:
            name = item["name"]
            count = item["count"]
            
            # Draw cursor if this item is selected
            if item_index == self.selected_item_index:
                self.cursor.rect.topleft = (self.item_start_x + 50, item_y - 18)
                self.cursor.draw(screen)
            
            # Draw item sprite
            '''
            sprite = Sprite(item["sprite_path"], (40, 40))
            sprite.rect.topleft = (self.item_start_x, item_y)
            sprite.draw(screen)
            '''
            
            # Draw item name and count
            name_text = self.font_category.render(str(name), True, (70, 70, 70))
            count_text = self.font_category.render(f"x {count}", True, (70, 70, 70))
            
            name_text_shadow = self.font_category.render(str(name), True, (160, 160, 160))
            count_text_shadow = self.font_category.render(f"x {count}", True, (160, 160, 160))
            
            screen.blit(name_text_shadow, (self.item_start_x + 93, item_y + 3))
            screen.blit(count_text_shadow, (self.item_start_x + 523, item_y +3))
            
            screen.blit(name_text, (self.item_start_x + 90, item_y))
            screen.blit(count_text, (self.item_start_x + 520, item_y))
            
            item_y += self.item_spacing
            item_index += 1
        
        # Draw cursor if CLOSE BAG is selected
        if self.selected_item_index == len(current_items):
            self.cursor.rect.topleft = (self.item_start_x + 50, item_y - 18)
            self.cursor.draw(screen)
        
        # Draw CLOSE BAG option at the end
        close_text = self.font_category.render("CLOSE BAG", True, (200, 70, 70))
        close_text_shadow = self.font_category.render("CLOSE BAG", True, (160, 160, 160))
        
        screen.blit(close_text_shadow, (self.item_start_x + 93, item_y + 3))
        screen.blit(close_text, (self.item_start_x + 90, item_y))
        
        # Draw selected item sprite (display area on the left side)
        if self.selected_item_sprite:
            sprite_x = GameSettings.SCREEN_WIDTH // 2 - 440  # <- Position X
            sprite_y = GameSettings.SCREEN_HEIGHT // 2 + 280  # <- Position Y
            self.selected_item_sprite.rect.center = (sprite_x, sprite_y)
            self.selected_item_sprite.draw(screen)
    def open(self):
        self.overlay = True
        self.update_selected_item_sprite()
        self.item_used = None

    def close(self, reopen_menu):
        self.overlay = False
        if self.opened_from_menu and reopen_menu:
            self.opened_from_menu = False
            self.game_manager.menu.open()
        elif self.opened_from_menu:
            self.opened_from_menu = False

    def to_dict(self):
        return {
            "items": list(self._items_data),
            "money": self.money
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        items = data.get("items") or []
        money = data.get("money", 0)
        bag = cls(items, money)
        bag.fix_item_categories()  # Automatically fix categories when loading
        return bag