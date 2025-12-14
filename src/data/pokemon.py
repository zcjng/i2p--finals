import pygame as pg
import json
import math
import random
from src.utils import GameSettings, Position
from src.utils.definition import Monster
from src.interface.components import Button
from src.core.services import scene_manager, input_manager
from src.sprites import Sprite, Animation


class Pokemon:
    _monsters_data: list[Monster]
    
    def __init__(self, monsters_data: list[Monster] | None = None, game_manager = None):
        self._monsters_data = monsters_data if monsters_data else []
        self.overlay = False
        self.max_party_size = 6
        
        self.dim_overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.dim_overlay.set_alpha(150)
        self.dim_overlay.fill((0, 0, 0, 175))
          
        self.font = pg.font.Font('assets/fonts/Minecraft.ttf', 20)
        self.font_small = pg.font.Font('assets/fonts/Minecraft.ttf', 12)
        self.font_large = pg.font.Font('assets/fonts/Pokemon.ttf', 50)
        
        self.pokemon_start_x = GameSettings.SCREEN_WIDTH // 2 - 450
        self.pokemon_start_y = GameSettings.SCREEN_HEIGHT // 2 - 270
        self.pokemon_spacing = 70
        
        # Selection system
        self.selected_pokemon_index = 0
        self.selected_pokemon_sprite = None
        
        self.bounce_time = 0  # Timer for bounce animation
        self.random_phase = [random.random() * 10 for _ in self._monsters_data]
        # Load initial sprites
        self.update_sprites()
        
        self.quit_overlay = pg.Surface((265, 80))  # <-- size you want
        self.quit_overlay.fill((255, 255, 255))
        self.quit_overlay.set_alpha(int(255 * 0.2))
        
        self.opened_from_menu = False
        self.game_manager = game_manager
        
    def update_sprites(self):
        """Update the background and UI sprites"""
        self.background = Sprite(f"Bag/bg_1.png", (GameSettings.SCREEN_WIDTH - 250, GameSettings.SCREEN_HEIGHT))
        self.pokemon_icon = Sprite(f"Bag/bag_1.PNG", (300, 300))  # You can create a pokeball icon
        self.bag_bar = Sprite(f"Bag/bag_bar.png", (GameSettings.SCREEN_WIDTH, 200))
        self.cursor = Sprite(f"Bag/cursor.png", (570, 110))
        self.category_bar = Sprite(f"Bag/category_bar.png", (350, 90))
        self.party_box = Sprite(f"pokemon/partybox.png", (320, 700))
        self.pokemon_data = Sprite(f"pokemon/pokemon_data.png", (800, 400))
        
    def add_pokemon(self, name: str, hp: int, max_hp: int, level: int, sprite_path: str, battle_sprite: str):
        """Add a pokemon to the party"""
        if len(self._monsters_data) >= self.max_party_size:
            return False  # Party is full
        
        self._monsters_data.append({
            "name": name,
            "hp": hp,
            "max_hp": max_hp,
            "level": level,
            "sprite_path": sprite_path,
            "battle_sprite": battle_sprite
        })
        
        self.random_phase.append(random.random() * 10)
        return True
    
    def remove_pokemon(self, index: int):
        """Remove a pokemon from the party by index"""
        if 0 <= index < len(self._monsters_data):
            self._monsters_data.pop(index)
            self.random_phase.pop(index)
            if self.selected_pokemon_index >= len(self._monsters_data) and self.selected_pokemon_index > 0:
                self.selected_pokemon_index -= 1
            self.update_selected_pokemon_sprite()
    
    def get_lead_pokemon(self):
        """Get the first pokemon with HP > 0"""
        for pokemon in self._monsters_data:
            if pokemon.get('hp', 0) > 0:
                return pokemon
        return None
    
    def get_alive_pokemon_count(self):
        """Count how many pokemon have HP > 0"""
        return sum(1 for p in self._monsters_data if p.get('hp', 0) > 0)
    
    def has_alive_pokemon(self):
        """Check if player has any pokemon with HP > 0"""
        return self.get_alive_pokemon_count() > 0
    
    def update_selected_pokemon_sprite(self):
        """Update the sprite of the currently selected pokemon"""
        if self.selected_pokemon_index < len(self._monsters_data):
            # A pokemon is selected
            selected_pokemon = self._monsters_data[self.selected_pokemon_index]
            sprite_path = selected_pokemon.get('idle')
            if sprite_path:
                self.selected_pokemon_sprite = Animation(
                                                sprite_path,
                                                rows=["idle"],  # If you have multiple animation states, add them here
                                                n_keyframes=4,   # Number of frames in the animation (adjust based on your sprite)
                                                size=(200, 200),   # Size of the selector
                                                loop=1,           # Animation loop time in seconds
                                                vertical=False
                                            )
            
        else:
            # # Quit selected → keep the last pokemon sprite
            if self._monsters_data:
                last_pokemon = self._monsters_data[-1]
            sprite_path = last_pokemon.get('idle', last_pokemon.get('sprite_path'))
            if sprite_path:
                self.selected_pokemon_sprite = Animation(
                    sprite_path,
                    rows=["idle"],
                    n_keyframes=4,
                    size=(200, 200),
                    loop=1,
                    vertical=False
                )
    
    def handle_input(self):
        """Handle keyboard input for pokemon selection"""
        max_index = len(self._monsters_data)  # CLOSE is at index = len(monsters_data)
        
        # Navigate up
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            if self.selected_pokemon_index > 0:
                self.selected_pokemon_index -= 1
                self.update_selected_pokemon_sprite()
        
        # Navigate down
        if input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            if self.selected_pokemon_index < max_index:
                self.selected_pokemon_index += 1
                self.update_selected_pokemon_sprite()
        
        # Select pokemon (Enter or E)
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e):
            if self.selected_pokemon_index == max_index:
                # Selected CLOSE
                self.close()
            else:
                # Selected a pokemon - you can add interaction logic here
                pass
        
        # Close with ESC
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.close()
            
    def get_quit_position(self):
        return (
        self.pokemon_start_x - 120,
        self.pokemon_start_y + 437
    )
    
    def update(self, dt: float):
        if self.overlay:
            self.handle_input()
            self.bounce_time += dt
            if self.selected_pokemon_sprite:
                self.selected_pokemon_sprite.update(dt)
    def draw(self, screen: pg.Surface):
        # Draw background
        screen.blit(self.party_box.image, (GameSettings.SCREEN_WIDTH // 2 - 600, GameSettings.SCREEN_HEIGHT // 2 - 300))
        screen.blit(self.pokemon_data.image, (GameSettings.SCREEN_WIDTH // 2 - 200 , GameSettings.SCREEN_HEIGHT // 2 - 200))
        #
        # Draw pokemon list
        pokemon_y = self.pokemon_start_y
        pokemon_index = 0
        pokemons = 0
        
        for pokemon in self._monsters_data:
            name = pokemon["name"]
            hp = pokemon["hp"]
            max_hp = pokemon["max_hp"]
            level = pokemon["level"]
            sprite = pokemon['sprite_path']
            
            
            if pokemon_index == self.selected_pokemon_index:
                # Selected: faster, higher bounce
                frame_duration = 0.10  # 80ms per frame = choppier
                frame = int(self.bounce_time / frame_duration) % 2
                bounce_table = [-5, 5]  # discrete bounce steps
                bounce_offset = bounce_table[frame]
            else:
                # Unselected: slower, subtle bounce
                frame_duration = 0.10
    
                # add random phase shift per index
                t = self.bounce_time + self.random_phase[min(pokemon_index, len(self.random_phase)-1)]
                
                frame = int(t / frame_duration) % 2
                bounce_offset = [-1, 1][frame]
                            
            pokemons += 1
            # Draw cursor if this pokemon is selected
            
            
            # Draw pokemon name

            
            
            sprite = Sprite(sprite, (80,80))
            if pokemons % 2 == 0:
                screen.blit(sprite.image, (self.pokemon_start_x + 45, pokemon_y + bounce_offset))
                self.pokemon_spacing = 90
            else:
                screen.blit(sprite.image, (self.pokemon_start_x - 100, pokemon_y + bounce_offset))
                self.pokemon_spacing = 35

            
            
            pokemon_y += self.pokemon_spacing
            pokemon_index += 1
        

        
        
        
        # Draw selected pokemon sprite (display area on the left side)
        if self.selected_pokemon_sprite:
            selected_pokemon = (self._monsters_data[self.selected_pokemon_index]
                    if self.selected_pokemon_index < len(self._monsters_data)
                    else self._monsters_data[self.selected_pokemon_index - 1])
            sprite_x = GameSettings.SCREEN_WIDTH // 2 - 80
            sprite_y = GameSettings.SCREEN_HEIGHT // 2 - 100
            
            # Draw the animated sprite
            self.selected_pokemon_sprite.update_pos(Position(sprite_x, sprite_y))
            self.selected_pokemon_sprite.draw(screen)
            
            # Draw Pokemon name
            name_text = self.font_large.render(selected_pokemon["name"], True, (255, 255, 255))
            name_shadow = self.font_large.render(selected_pokemon["name"], True, (0, 0, 0))
            screen.blit(name_shadow, (GameSettings.SCREEN_WIDTH // 2 + 162, GameSettings.SCREEN_HEIGHT // 2 - 123))
            screen.blit(name_text, (GameSettings.SCREEN_WIDTH // 2 + 160, GameSettings.SCREEN_HEIGHT // 2 - 125))
            
            # Draw Level
            level_text = self.font_large.render(f"Lv.{selected_pokemon['level']}", True, (255, 255, 255))
            level_shadow = self.font_large.render(f"Lv.{selected_pokemon['level']}", True, (0, 0, 0))
            screen.blit(level_shadow, (GameSettings.SCREEN_WIDTH // 2 + 372, GameSettings.SCREEN_HEIGHT // 2 - 123))
            screen.blit(level_text, (GameSettings.SCREEN_WIDTH // 2 + 370, GameSettings.SCREEN_HEIGHT // 2 - 125))
            
            # Draw HP text
            hp = selected_pokemon["hp"]
            max_hp = selected_pokemon["max_hp"]
            
            hp_text_shadow = self.font_large.render(f"HP: {int(hp)}/{int(max_hp)}", True, (0, 0, 0))
            screen.blit(hp_text_shadow, (GameSettings.SCREEN_WIDTH // 2 + 162, GameSettings.SCREEN_HEIGHT // 2 - 31 ))
            hp_text = self.font_large.render(f"HP: {int(hp)}/{int(max_hp)}", True, (255, 255, 255))
            screen.blit(hp_text, (GameSettings.SCREEN_WIDTH // 2 + 160, GameSettings.SCREEN_HEIGHT // 2 - 33))
            
            # Draw HP bar
            bar_x = GameSettings.SCREEN_WIDTH // 2 + 155
            bar_y = GameSettings.SCREEN_HEIGHT // 2 - 75
            bar_width = 300
            bar_height = 40
            
            # Background bar (dark gray)
            pg.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
            
            # HP fill with color based on percentage
            hp_percentage = hp / max_hp if max_hp > 0 else 0
            current_bar_width = int(bar_width * hp_percentage)
            
            if hp_percentage > 0.5:
                bar_color = (50, 200, 50)  # Green
            elif hp_percentage > 0.2:
                bar_color = (200, 200, 50)  # Yellow
            else:
                bar_color = (200, 50, 50)  # Red
            
            if current_bar_width > 0:
                pg.draw.rect(screen, bar_color, (bar_x, bar_y, current_bar_width, bar_height))
            
            # Border
            pg.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 2)
                    

            
            
        # Draw party count
        party_text = self.font_small.render(f"Party: {len(self._monsters_data)}/{self.max_party_size}", True, (70, 70, 70))
        screen.blit(party_text, (GameSettings.SCREEN_WIDTH // 2 - 500, GameSettings.SCREEN_HEIGHT // 2 + 300))

        quit_index = len(self._monsters_data)

        if self.selected_pokemon_index == quit_index:
            quit_x, quit_y = self.get_quit_position()
            screen.blit(self.quit_overlay, (quit_x, quit_y))

    def open(self):
        self.overlay = True
        self.update_selected_pokemon_sprite()

    def close(self):
        self.overlay = False
        self.selected_pokemon_index = 0 
        if self.opened_from_menu:
            self.opened_from_menu = False
            
            self.game_manager.menu.open()

    def to_dict(self):
        return {
            "monsters": list(self._monsters_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Pokemon":
        monsters = data.get("monsters") or []
        return cls(monsters)