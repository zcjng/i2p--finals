import pygame as pg
from src.utils import GameSettings
from src.utils.definition import Monster
from src.interface.components import Button
from src.sprites import Sprite


class PCStorage:
    """
    Pokemon PC Storage System - stores overflow Pokemon when party is full
    """
    _stored_monsters: list[Monster]
    MAX_PARTY_SIZE = 6
    
    def __init__(self, stored_monsters: list[Monster] | None = None):
        self._stored_monsters = stored_monsters if stored_monsters else []
        self.is_open = False
        

        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(180)
        self.dim_overlay.fill((0, 0, 0))
        
        self.font = pg.font.Font('assets/fonts/Minecraft.ttf', 24)
        self.font_small = pg.font.Font('assets/fonts/Minecraft.ttf', 14)
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        

        self.frame = Sprite("options/frame2.png", (1200, 700))
        
        self.close_button = Button(
            "options/exit.png", "options/exit2.png",
            px + 240, py - 300, 150, 70,
            lambda: self.close()
        )
        

        self.scroll_offset = 0
        self.max_visible = 5
        self.selected_index = 0
        
    def open(self):
        """Open the PC storage interface"""
        self.is_open = True
        self.selected_index = 0
        
    def close(self):
        """Close the PC storage interface"""
        self.is_open = False
        
    def deposit_pokemon(self, monster: Monster):
        """Move Pokemon from party to PC storage"""
        self._stored_monsters.append(monster)
        
    def withdraw_pokemon(self, index: int) -> Monster | None:
        """Move Pokemon from PC storage to party"""
        if 0 <= index < len(self._stored_monsters):
            return self._stored_monsters.pop(index)
        return None
    
    def is_party_full(self, pokemon_party):
        """Check if the party has reached max capacity"""
        return len(pokemon_party._monsters_data) >= self.MAX_PARTY_SIZE
    
    def auto_deposit(self, monster: Monster, pokemon_party):
        """Automatically deposit to PC if party is full"""
        if self.is_party_full(pokemon_party):
            self.deposit_pokemon(monster)
            return True
        return False
        
    def update(self, dt: float, pokemon_party=None):
        if not self.is_open:
            return
            
        self.close_button.update(dt)
        

        from src.core.services import input_manager
        
        max_index = len(self._stored_monsters) - 1
        

        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            if self.selected_index > 0:
                self.selected_index -= 1

                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
        
        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            if self.selected_index < max_index:
                self.selected_index += 1

                if self.selected_index >= self.scroll_offset + self.max_visible:
                    self.scroll_offset = self.selected_index - self.max_visible + 1
        

        if input_manager.key_pressed(pg.K_e) or input_manager.key_pressed(pg.K_RETURN):
            from src.utils import Logger
            Logger.info(f"Withdraw key pressed! Selected index: {self.selected_index}, Total monsters: {len(self._stored_monsters)}")
            
            if pokemon_party:
                Logger.info(f"Party size: {len(pokemon_party._monsters_data)}/{self.MAX_PARTY_SIZE}")
                
                if not self.is_party_full(pokemon_party):
                    Logger.info("Party not full, attempting withdraw...")
                    
                    if 0 <= self.selected_index < len(self._stored_monsters):
                        Logger.info(f"Valid index, withdrawing pokemon at index {self.selected_index}")
                        withdrawn = self.withdraw_pokemon(self.selected_index)
                        
                        if withdrawn:
                            Logger.info(f"Successfully withdrew {withdrawn['name']}")

                            success = pokemon_party.add_pokemon(
                                withdrawn['name'],
                                withdrawn['hp'],
                                withdrawn['max_hp'],
                                withdrawn['level'],
                                withdrawn['sprite_path'],
                                withdrawn['battle_sprite']
                            )
                            
                            Logger.info(f"Add to party result: {success}")
                            

                            if success and 'idle' in withdrawn:
                                pokemon_party._monsters_data[-1]['idle'] = withdrawn['idle']
                            

                            if success and 'element' in withdrawn:
                                pokemon_party._monsters_data[-1]['element'] = withdrawn['element']
                            

                            if self.selected_index >= len(self._stored_monsters) and self.selected_index > 0:
                                self.selected_index -= 1
                        else:
                            Logger.error("Failed to withdraw pokemon")
                    else:
                        Logger.error(f"Invalid index: {self.selected_index}")
                else:
                    Logger.info("Party is full!")
            else:
                Logger.error("No pokemon_party provided to update()")
        

        if input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
            self.close()
        
    def draw(self, screen: pg.Surface, pokemon_party=None):
        if not self.is_open:
            return
        

        screen.blit(self.dim_overlay, (0, 0))
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        

        screen.blit(self.frame.image, (px - 520, py - 300))
        

        title = self.font.render("PC Storage System", True, (255, 255, 255))
        screen.blit(title, (px - 120, py - 260))
        

        self.close_button.draw(screen)
        

        if not self._stored_monsters:
            no_pokemon = self.font_small.render("No Pokemon stored in PC", True, (150, 150, 150))
            screen.blit(no_pokemon, (px - 150, py - 200))
        else:
            start_y = py - 220
            visible_monsters = self._stored_monsters[self.scroll_offset:self.scroll_offset + self.max_visible]
            
            for i, monster in enumerate(visible_monsters):
                actual_index = self.scroll_offset + i
                y_pos = start_y + (i * 90)
                

                if actual_index == self.selected_index:
                    highlight = pg.Surface((700, 80))
                    highlight.set_alpha(100)
                    highlight.fill((100, 150, 255))
                    screen.blit(highlight, (px - 360, y_pos - 5))
                

                if 'sprite_path' in monster:
                    sprite = Sprite(monster['sprite_path'], (60, 60))
                    sprite.rect.topleft = (px - 350, y_pos)
                    sprite.draw(screen)
                

                name_text = self.font.render(monster['name'], True, (255, 255, 255))
                screen.blit(name_text, (px - 270, y_pos + 5))
                
                hp_text = self.font_small.render(
                    f"HP: {monster.get('hp', 0)}/{monster.get('max_hp', 0)}", 
                    True, 
                    (255, 255, 255)
                )
                screen.blit(hp_text, (px - 270, y_pos + 35))
                
                level_text = self.font_small.render(
                    f"Level: {monster.get('level', 1)}", 
                    True, 
                    (255, 255, 255)
                )
                screen.blit(level_text, (px - 150, y_pos + 35))
                

                if 'element' in monster:
                    element_text = self.font_small.render(
                        monster['element'], 
                        True, 
                        (150, 255, 150)
                    )
                    screen.blit(element_text, (px - 30, y_pos + 35))
                

                if pokemon_party and not self.is_party_full(pokemon_party):
                    if actual_index == self.selected_index:
                        withdraw_text = self.font_small.render(
                            "[E] Withdraw", 
                            True, 
                            (100, 255, 100)
                        )
                        screen.blit(withdraw_text, (px + 150, y_pos + 20))
                else:

                    if actual_index == self.selected_index:
                        full_text = self.font_small.render(
                            "Party Full!", 
                            True, 
                            (255, 100, 100)
                        )
                        screen.blit(full_text, (px + 150, y_pos + 20))
        

        if pokemon_party:
            party_info = self.font_small.render(
                f"Party: {len(pokemon_party._monsters_data)}/{self.MAX_PARTY_SIZE} Pokemon",
                True, (255, 255, 255)
            )
            screen.blit(party_info, (px - 350, py + 240))
    
    def to_dict(self):
        return {
            "stored_monsters": list(self._stored_monsters)
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        stored = data.get("stored_monsters", [])
        return cls(stored)