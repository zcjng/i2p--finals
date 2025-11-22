import pygame as pg
import threading
import time
from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager

class Character:
    def __init__(self, pokemon_data):
        self.name = pokemon_data['name']
        self.max_hp = float(pokemon_data.get('max_hp', pokemon_data.get('hp', 20)))
        self.hp = float(pokemon_data.get('hp', self.max_hp))
        self.attack = float(pokemon_data.get('attack', 40))
        self.defense = float(pokemon_data.get('defense', 5))
        self.battle_sprite = pokemon_data['battle_sprite']
        self.level = pokemon_data.get('level', 1)
  
    def is_alive(self):
        return self.hp > 0
  
    def take_damage(self, amount):
        self.hp -= float(amount)
  
    def attack_target(self, other):
        damage = max(1.0, self.attack - other.defense)
        other.take_damage(damage)
        return damage
        
    
class BattleScene(Scene):
    background: BackgroundSprite
    def __init__(self, player_pokemon, enemy_pokemon, game_manager):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.game_manager = game_manager
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        self.player = Character(player_pokemon)
        self.enemy = Character(enemy_pokemon)
        
        self.p_back_sprite = Sprite(self.player.battle_sprite, (500,500), 'right')
        self.p_back_sprite.update_pos(Position(px - 500, py - 350))
        
        self.e_front_sprite = Sprite(self.enemy.battle_sprite, (400, 400), 'left')
        self.e_front_sprite.update_pos(Position(px + 50, py - 380))
        
        self.message_box = Sprite("UI/raw/UI_Battle_Frame.png", (1280, 212))
        self.menu = Sprite("UI/raw/UI_Battle_Menu.png", (580, 212))
        
        self.player_menu = Sprite("UI/raw/UI_Player_Menu.png", (580, 200))
        self.player_hp = Sprite("UI/raw/UI_Player_HP.png", (370, 35))
        
        self.enemy_menu = Sprite("UI/raw/UI_Enemy_Menu.png", (580, 150))
        
        self.selector = Sprite("UI/raw/UI_Selector.png", (25, 25))
        
        # Battle state
        self.message = f"A wild {self.enemy.name} appeared!"
        self.displayed_message = ''
        self.message_index = 0
        self.message_speed = 0.05
        self.message_timer = 0
        
        self.waiting_input = False
        self.player_turn = True
        self.battle_over = False
        
        self.player_hp_display = self.player.hp
        self.enemy_hp_display = self.enemy.hp
        
        self.enemy_attack_timer = 0
        self.intro_timer = 0
        self.needs_enemy_attack = False
        self.needs_show_menu = False
        self.battle_end_timer = 0
        
        self.menu_index = 0  # 0=FIGHT, 1=BAG, 2=CATCH, 3=RUN
        self.menu_actions = [
            lambda: self.player_attack(),
            lambda: None,  # BAG - not implemented
            lambda: self.catch_pokemon(enemy_pokemon),
            lambda: self.run_from_battle()
        ]
                
        self.fight_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 150, py + 150, 200, 90,
            lambda: self.player_attack()
        )
        
        self.bag_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 390, py + 150, 200, 90
        )
        
        self.pokemon_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 150, py + 260, 200, 90,
            lambda: self.catch_pokemon(enemy_pokemon)
        )
        
        self.run_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 390, py + 260, 200, 90,
            lambda: self.run_from_battle()
        )
        
    def run_from_battle(self):
        """Exit battle and return to game"""
        self.sync_pokemon_to_bag()
        self.game_manager.in_battle = False
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        scene_manager.change_scene('game')
            
    def sync_pokemon_to_bag(self):
        """Sync the battle pokemon's HP back to the bag"""
        if not self.game_manager.bag._monsters_data:
            return
        
        # Find and update the player's pokemon in the bag
        for monster in self.game_manager.bag._monsters_data:
            if monster.get('name') == self.player.name:
                monster['hp'] = max(0, self.player.hp)  # Ensure HP doesn't go negative
                Logger.info(f"Updated {self.player.name} HP to {self.player.hp}")
                break
            
    def player_attack(self):
        if not self.waiting_input or not self.player_turn or self.battle_over:
            return
        
        self.waiting_input = False
        damage = self.player.attack_target(self.enemy)
        self.set_message(f"{self.player.name} attacked! {self.enemy.name} took {int(damage)}!")
        
        if not self.enemy.is_alive():
            self.battle_over = True
            self.set_message(f"{self.enemy.name} has fainted! You win!")
            self.battle_end_timer = 2.0
            
            return
        
        self.player_turn = False
        self.enemy_attack_timer = 1.5  # 1.5 seconds
        self.needs_enemy_attack = True
        
    def enemy_attack(self):

        damage = self.enemy.attack_target(self.player)
        self.set_message(f"{self.enemy.name} attacked! {self.player.name} took {int(damage)}!")
        
        if not self.player.is_alive():
            self.battle_over = True
            self.set_message(f"{self.player.name} has fainted! You lost!")
            self.battle_end_timer = 2.0
            
            return
        
        self.player_turn = True
        self.waiting_input = True
        
    def catch_pokemon(self, enemy_pokemon):
        
        caught_pokemon = enemy_pokemon.copy()
        caught_pokemon['hp'] = max(0, self.enemy.hp)
        
        if self.game_manager.pc_storage.is_bag_full(self.game_manager.bag):
            
            self.game_manager.pc_storage.deposit_pokemon(caught_pokemon)
            self.set_message(f"Caught {self.enemy.name}! Sent to PC (Bag full)")
        else:

            self.game_manager.bag._monsters_data.append(caught_pokemon)
            self.set_message(f"You just caught {self.enemy.name}!")
            
        self.battle_over = True
        self.battle_end_timer = 2.0
        
    def set_message(self, message: str):
        """Set a new message and reset the typewriter effect"""
        self.message = message
        self.displayed_message = ""
        self.message_index = 0
        self.message_timer = 0
        
    @override
    def enter(self):
        if not sound_manager.current_bgm:
            sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
        
        self.waiting_input = False
        self.intro_timer = 2.0  # 2 seconds
        self.needs_show_menu = True
        
    def get_hp_color(self, hp_ratio: float):
        """Get HP bar color based on HP percentage (green -> yellow -> red)"""
        if hp_ratio > 0.5:
            # Green to Yellow (100% -> 50%)
            t = (hp_ratio - 0.5) / 0.5  # 1.0 at 100%, 0.0 at 50%
            r = int(255 * (1 - t))
            g = 200
            b = 50
        else:
            # Yellow to Red (50% -> 0%)
            t = hp_ratio / 0.5  # 1.0 at 50%, 0.0 at 0%
            r = 255
            g = int(200 * t)
            b = 50
        return (r, g, b)

    def draw_hp_bar(self, screen: pg.Surface, x: int, y: int, 
                    current_hp: float, max_hp: float, width: int = 200, height: int = 16):
        """Draw a dynamic HP bar with color gradient based on HP"""
        hp_ratio = max(0, min(1, current_hp / max_hp))
        fill_width = int(width * hp_ratio)
        
        # Background (dark gray)
        pg.draw.rect(screen, (40, 40, 40), (x, y, width, height))
        
        # HP fill
        if fill_width > 0:
            color = self.get_hp_color(hp_ratio)
            pg.draw.rect(screen, color, (x, y, fill_width, height))
        
    
    def handle_menu_input(self):
        """Handle arrow key navigation and selection"""
        if not self.waiting_input or self.battle_over:
            return
        
        # Navigation
        if input_manager.key_pressed(pg.K_LEFT):
            if self.menu_index % 2 == 1:  # Right column -> Left column
                self.menu_index -= 1

                
        elif input_manager.key_pressed(pg.K_RIGHT):
            if self.menu_index % 2 == 0:  # Left column -> Right column
                self.menu_index += 1

                
        elif input_manager.key_pressed(pg.K_UP):
            if self.menu_index >= 2:  # Bottom row -> Top row
                self.menu_index -= 2

                
        elif input_manager.key_pressed(pg.K_DOWN):
            if self.menu_index <= 1:  # Top row -> Bottom row
                self.menu_index += 2

        
        # Selection (Enter, Space, or Z like Pokemon games)
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_z):
            self.menu_actions[self.menu_index]()
            
    def draw_menu_selector(self, screen: pg.Surface):
        """Draw a pointer/selector next to the selected menu option"""
        if not self.waiting_input or self.battle_over:
            return
        
        px = GameSettings.SCREEN_WIDTH // 2
        py = GameSettings.SCREEN_HEIGHT // 2
        
        # Menu positions (match your button positions)
        positions = [
            (px + 120, py + 205),  # FIGHT
            (px + 400, py + 205),  # BAG
            (px + 120, py + 280),  # CATCH
            (px + 400, py + 280),  # RUN
        ]
        
        x, y = positions[self.menu_index]
        
        # Draw a triangle pointer
        screen.blit(self.selector.image, (x, y))
    def update(self, dt: float):
        
        if self.battle_over and self.battle_end_timer > 0:
            self.battle_end_timer -= dt
            if self.battle_end_timer <= 0:
                # Return to game after timer expires
                self.run_from_battle()
                return
            
        if self.needs_show_menu:
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.waiting_input = True
                self.message = "What will you do?"
                self.needs_show_menu = False
                
        if input_manager.key_pressed(pg.K_e) or input_manager.key_pressed(pg.K_SPACE):
            if self.message_index < len(self.message):
            # Instantly show full message
                self.message_index = len(self.message)
                self.displayed_message = self.message
                
        if self.message_index < len(self.message):
            self.message_timer += dt
            
            add_char = int(self.message_timer / self.message_speed)
            if add_char > 0:
                self.message_index = min(self.message_index + add_char, len(self.message))
                self.displayed_message = self.message[:self.message_index]
                self.message_timer -= add_char * self.message_speed
        
        # Handle enemy attack timer
        if self.needs_enemy_attack and not self.battle_over:
            self.enemy_attack_timer -= dt
            if self.enemy_attack_timer <= 0:
                self.enemy_attack()
                self.needs_enemy_attack = False
            
        self.player_hp_display += (self.player.hp - self.player_hp_display) * 0.15
        self.enemy_hp_display += (self.enemy.hp - self.enemy_hp_display) * 0.15
        
        if self.waiting_input and not self.battle_over:
            self.handle_menu_input()
            self.fight_button.update(dt)
            self.bag_button.update(dt)
            self.pokemon_button.update(dt)
            self.run_button.update(dt)
    
    def draw(self, screen: pg.Surface):
        self.background.draw(screen)
         
        self.p_back_sprite.draw(screen)
        self.e_front_sprite.draw(screen)
        
            
        px = GameSettings.SCREEN_WIDTH // 2
        py = GameSettings.SCREEN_HEIGHT // 2
    
        screen.blit(self.message_box.image, (px - 640 , py + 150))
        screen.blit(self.player_menu.image, (px , py - 60))
        screen.blit(self.player_hp.image, (px + 170 , py + 20))
        
        screen.blit(self.enemy_menu.image, (px - 600 , py - 320))
        screen.blit(self.player_hp.image, (px - 450 , py - 240))
        
        
        font = pg.font.Font("assets/fonts/Pokemon.ttf", 50)
        name_font = pg.font.Font("assets/fonts/Pokemon.ttf", 70)
        
        p_name_text_shadow = name_font.render(self.player.name, True, (0,0,0))
        p_name_text_shadow.set_alpha(50)
        screen.blit(p_name_text_shadow, (px + 105 , py - 46))
        p_name_text = name_font.render(self.player.name, True, (0,0,0))
        screen.blit(p_name_text, (px + 100 , py - 48))
        
        p_level_text_shadow = name_font.render(f"Lv{str(self.player.level)}", True, (0,0,0))
        p_level_text_shadow.set_alpha(50)
        screen.blit(p_level_text_shadow, (px + 430 , py - 46))
        p_level_text = name_font.render(f"Lv{str(self.player.level)}", True, (0,0,0))
        screen.blit(p_level_text, (px + 425 , py - 48))
        
        
        e_name_text_shadow = name_font.render(self.enemy.name, True, (0,0,0))
        e_name_text_shadow.set_alpha(50)
        screen.blit(e_name_text_shadow, (px - 560 , py - 306))
        e_name_text = name_font.render(self.enemy.name, True, (0,0,0))
        screen.blit(e_name_text, (px - 565 , py - 308))
        
        e_level_text_shadow = name_font.render(f"Lv{str(self.enemy.level)}", True, (0,0,0))
        e_level_text_shadow.set_alpha(50)
        screen.blit(e_level_text_shadow, (px - 205 , py - 306))
        e_level_text = name_font.render(f"Lv{str(self.enemy.level)}", True, (0,0,0))
        screen.blit(e_level_text, (px - 200 , py - 308))
        
        
        
        text = font.render(self.displayed_message, True, (255, 255, 255))
        screen.blit(text, (px - 580 , py + 185))
        
        self.draw_hp_bar(screen, px + 260, py + 30, self.player_hp_display, self.player.max_hp, width=270, height=15)
        self.draw_hp_bar(screen, px - 360 , py - 230, self.enemy_hp_display, self.enemy.max_hp, width=270, height=15)
        
        if self.waiting_input and not self.battle_over:
            self.fight_button.draw(screen)
            self.pokemon_button.draw(screen)
            self.bag_button.draw(screen)
            self.run_button.draw(screen)
            
            button_font = pg.font.Font("assets/fonts/Pokemon.ttf", 70)
            screen.blit(self.menu.image, (px + 60, py + 150))
            screen.blit(button_font.render("FIGHT", True, (50, 50, 50)), (px + 160, py + 185))
            screen.blit(button_font.render("BAG", True, (50, 50, 50)), (px + 440, py + 185))
            screen.blit(button_font.render("CATCH", True, (50, 50, 50)), (px + 160, py + 260))
            screen.blit(button_font.render("RUN", True, (50, 50, 50)), (px + 440, py + 260))
            self.draw_menu_selector(screen)
