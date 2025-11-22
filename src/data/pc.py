import pygame as pg
from src.utils import GameSettings
from src.utils.definition import Monster
from src.interface.components import Button
from src.sprites import Sprite


class PCStorage:
    """
    Pokemon PC Storage System - stores overflow Pokemon when bag is full
    """
    _stored_monsters: list[Monster]
    MAX_BAG_SIZE = 6  # Maximum Pokemon in bag before overflow to PC
    
    def __init__(self, stored_monsters: list[Monster] | None = None):
        self._stored_monsters = stored_monsters if stored_monsters else []
        self.is_open = False
        
        # UI Setup
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(180)
        self.dim_overlay.fill((0, 0, 0))
        
        self.font = pg.font.Font('assets/fonts/Minecraft.ttf', 24)
        self.font_small = pg.font.Font('assets/fonts/Minecraft.ttf', 14)
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        
        # UI Components
        self.frame = Sprite("UI/raw/UI_Flat_Frame03a.png", (800, 600))
        
        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px + 300, py - 280, 60, 60,
            lambda: self.close()
        )
        
        self.withdraw_buttons = []
        self.deposit_buttons = []
        
        # Scroll state
        self.scroll_offset = 0
        self.max_visible = 5
        
    def open(self):
        """Open the PC storage interface"""
        self.is_open = True
        
    def close(self):
        """Close the PC storage interface"""
        self.is_open = False
        
    def deposit_pokemon(self, monster: Monster):
        """Move Pokemon from bag to PC storage"""
        self._stored_monsters.append(monster)
        
    def withdraw_pokemon(self, index: int) -> Monster | None:
        """Move Pokemon from PC storage to bag"""
        if 0 <= index < len(self._stored_monsters):
            return self._stored_monsters.pop(index)
        return None
    
    def is_bag_full(self, bag) -> bool:
        """Check if the bag has reached max capacity"""
        return len(bag._monsters_data) >= self.MAX_BAG_SIZE
    
    def auto_deposit(self, monster: Monster, bag):
        """Automatically deposit to PC if bag is full"""
        if self.is_bag_full(bag):
            self.deposit_pokemon(monster)
            return True
        return False
        
    def update(self, dt: float):
        if not self.is_open:
            return
            
        self.close_button.update(dt)
        
        # Handle scroll input
        from src.core.services import input_manager  # Import at top of file
    
        if input_manager.key_pressed(pg.K_UP) and self.scroll_offset > 0:
            self.scroll_offset -= 1
        
        if input_manager.key_pressed(pg.K_DOWN) and self.scroll_offset < max(0, len(self._stored_monsters) - self.max_visible):
            self.scroll_offset += 1
        
    def draw(self, screen: pg.Surface, bag=None):
        if not self.is_open:
            return
        
        # Draw dimmed background
        screen.blit(self.dim_overlay, (0, 0))
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        
        # Draw frame
        screen.blit(self.frame.image, (px - 400, py - 300))
        
        # Draw title
        title = self.font.render("PC Storage System", True, (255, 255, 255))
        screen.blit(title, (px - 120, py - 260))
        
        # Draw close button
        self.close_button.draw(screen)
        
        # Draw stored Pokemon
        if not self._stored_monsters:
            no_pokemon = self.font_small.render("No Pokemon stored in PC", True, (150, 150, 150))
            screen.blit(no_pokemon, (px - 150, py - 200))
        else:
            start_y = py - 220
            visible_monsters = self._stored_monsters[self.scroll_offset:self.scroll_offset + self.max_visible]
            
            for i, monster in enumerate(visible_monsters):
                y_pos = start_y + (i * 90)
                
                # Draw Pokemon sprite
                if 'sprite_path' in monster:
                    sprite = Sprite(monster['sprite_path'], (60, 60))
                    sprite.rect.topleft = (px - 350, y_pos)
                    sprite.draw(screen)
                
                # Draw Pokemon info
                name_text = self.font.render(monster['name'], True, (0, 0, 0))
                screen.blit(name_text, (px - 270, y_pos + 5))
                
                hp_text = self.font_small.render(f"HP: {monster.get('hp', 0)}/{monster.get('max_hp', 0)}", True, (0, 0, 0))
                screen.blit(hp_text, (px - 270, y_pos + 35))
                
                level_text = self.font_small.render(f"Level: {monster.get('level', 1)}", True, (0, 0, 0))
                screen.blit(level_text, (px - 150, y_pos + 35))
                
                # Withdraw button (if bag provided and not full)
                if bag and not self.is_bag_full(bag):
                    withdraw_text = self.font_small.render("[W] Withdraw", True, (0, 100, 0))
                    screen.blit(withdraw_text, (px + 150, y_pos + 20))
            
            # Scroll indicator
            if len(self._stored_monsters) > self.max_visible:
                scroll_text = self.font_small.render(
                    f"Showing {self.scroll_offset + 1}-{min(self.scroll_offset + self.max_visible, len(self._stored_monsters))} of {len(self._stored_monsters)}",
                    True, (100, 100, 100)
                )
                screen.blit(scroll_text, (px - 100, py + 240))
                
                controls = self.font_small.render("Use UP/DOWN arrows to scroll", True, (100, 100, 100))
                screen.blit(controls, (px - 120, py + 260))
        
        # Draw bag info if provided
        if bag:
            bag_info = self.font_small.render(
                f"Bag: {len(bag._monsters_data)}/{self.MAX_BAG_SIZE} Pokemon",
                True, (0, 0, 0)
            )
            screen.blit(bag_info, (px - 350, py + 240))
    
    def to_dict(self):
        return {
            "stored_monsters": list(self._stored_monsters)
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        stored = data.get("stored_monsters", [])
        return cls(stored)