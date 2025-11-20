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
        self.max_hp = float(pokemon_data.get('hp', 20))
        self.hp = self.max_hp
        self.attack = float(pokemon_data.get('attack', 40))
        self.defense = float(pokemon_data.get('defense', 5))
        self.battle_sprite = pokemon_data['battle_sprite']

  
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
        
        self.message_box = Sprite("UI/raw/UI_Flat_Banner03a.png", (750, 200))

        
        # Battle state
        self.message = f"A wild {self.enemy.name} appeared!"
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
        
        self.fight_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 150, py + 150, 200, 90,
            lambda: self.player_attack()
        )
        
        self.bag_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 390, py + 150, 200, 90,
            lambda: scene_manager.change_scene("menu")
        )
        
        self.pokemon_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 150, py + 260, 200, 90,
            lambda: scene_manager.change_scene("menu")
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
        self.message = f"{self.player.name} attacked! {self.enemy.name} took {damage:.1f}"
        
        if not self.enemy.is_alive():
            self.battle_over = True
            self.message = f"{self.enemy.name} has fainted! You win!"
            self.battle_end_timer = 2.0
            
            return
        
        self.player_turn = False
        self.enemy_attack_timer = 1.5  # 1.5 seconds
        self.needs_enemy_attack = True
        
    def enemy_attack(self):

        damage = self.enemy.attack_target(self.player)
        self.message = f"{self.enemy.name} attacked! {self.player.name} took {damage:.1f}"
        
        if not self.player.is_alive():
            self.battle_over = True
            self.message = f"{self.player.name} has fainted! You lost!"
            self.battle_end_timer = 2.0
            
            return
        
        self.player_turn = True
        self.waiting_input = True
        
    @override
    def enter(self):
        if not sound_manager.current_bgm:
            sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
        
        self.waiting_input = False
        self.intro_timer = 2.0  # 2 seconds
        self.needs_show_menu = True

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
        
        # Handle enemy attack timer
        if self.needs_enemy_attack and not self.battle_over:
            self.enemy_attack_timer -= dt
            if self.enemy_attack_timer <= 0:
                self.enemy_attack()
                self.needs_enemy_attack = False
            
        self.player_hp_display += (self.player.hp - self.player_hp_display) * 0.15
        self.enemy_hp_display += (self.enemy.hp - self.enemy_hp_display) * 0.15
        
        if self.waiting_input and not self.battle_over:
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
    
        screen.blit(self.message_box.image, (px - 635 , py + 150))

        

        
        font = pg.font.Font(None, 40)
        text = font.render(self.message, True, (50, 50, 50))
        screen.blit(text, (px - 580 , py + 200))
        
        if self.waiting_input and not self.battle_over:
            self.fight_button.draw(screen)
            self.pokemon_button.draw(screen)
            self.bag_button.draw(screen)
            self.run_button.draw(screen)
            
            button_font = pg.font.Font(None, 36)
            screen.blit(button_font.render("FIGHT", True, (50, 50, 50)), (px + 200, py + 180))
            screen.blit(button_font.render("BAG", True, (50, 50, 50)), (px + 445, py + 180))
            screen.blit(button_font.render("POKEMON", True, (50, 50, 50)), (px + 175, py + 290))
            screen.blit(button_font.render("RUN", True, (50, 50, 50)), (px + 450, py + 290))
