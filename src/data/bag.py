import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item
from src.interface.components import Button
from src.core.services import scene_manager
from src.sprites import Sprite


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]
    
    
    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        
        self.overlay = False
        
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT)) # Set transparency level (0-255)
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0, 175))  # Fill with black
          
        self.font = pg.font.Font('assets/fonts/Minecraft.ttf', 20)
        self.font_small = pg.font.Font('assets/fonts/Minecraft.ttf', 12)
        self.animal_start_x = GameSettings.SCREEN_WIDTH // 2 - 300
        self.animal_start_y = GameSettings.SCREEN_HEIGHT // 2 - 200
        self.item_start_x = GameSettings.SCREEN_WIDTH // 2 - 50
        self.item_start_y = GameSettings.SCREEN_HEIGHT // 2 - 200
        self.animal_spacing = 70
        self.item_spacing = 40
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        
        self.bag_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            px - 500, py - 520, 100, 100,
            lambda: self.open(),
        )

        self.close_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            px - 400, py - 400, 80, 80,
            lambda: self.close()
        )
        
        self.frame = Sprite("UI/raw/UI_Flat_Frame03a.png", (700, 500))
        
    def update(self, dt: float):
        
        if self.overlay:
            self.close_button.update(dt)
        else:
            self.bag_button.update(dt)
        

    def draw(self, screen: pg.Surface):
        self.bag_button.draw(screen)
        screen.blit(self.frame.image, (GameSettings.SCREEN_WIDTH // 2 - 350, GameSettings.SCREEN_HEIGHT // 2 - 250))
  
        animal_y = self.animal_start_y
        item_y = self.item_start_y
        for monster in self._monsters_data:
            text = monster['name']
            hp = monster['hp']
            level = monster["level"]
            sprite = Sprite(monster['sprite_path'], (70, 70))
            
            sprite.rect.topleft = (self.animal_start_x, animal_y - 20)
            sprite.draw(screen)
            text_render = self.font.render(text, True, (0,0,0))
            screen.blit(text_render, (self.animal_start_x + 80, animal_y))
            
            hp_text = self.font_small.render('HP:', True, (0,0,0))
            hp_render = self.font_small.render(str(hp), True, (0,0,0))
            screen.blit(hp_render, (self.animal_start_x + 100, animal_y + 30))
            screen.blit(hp_text, (self.animal_start_x + 80, animal_y + 30))
            
            level_text = self.font_small.render('Level:', True, (0,0,0))
            level_render = self.font_small.render(str(level), True, (0,0,0))
            screen.blit(level_render , (self.animal_start_x + 160, animal_y + 30))
            screen.blit(level_text, (self.animal_start_x + 120, animal_y + 30))
            
            animal_y += self.animal_spacing
            
        for items in self._items_data:
            name = items["name"]
            value = items["count"]
            
            sprite = Sprite(items["sprite_path"], (40, 40))
            name_text = self.font.render(str(name), True, (0,0,0))
            value_text = self.font.render(str(value), True, (0,0,0))
            
            sprite.rect.topleft = (self.item_start_x + 100, item_y - 20)
            sprite.draw(screen)
            
            screen.blit(name_text, (self.item_start_x + 170, item_y - 20))
            screen.blit(value_text, (self.item_start_x + 170, item_y + 5))
            item_y += self.item_spacing + 10
        
    def open(self):
        self.overlay = True
        self.bag_button.is_pressed = True
    def close(self):
        self.overlay = False
        self.bag_button.is_pressed = False

    def to_dict(self):
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag