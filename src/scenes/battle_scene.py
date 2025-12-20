import pygame as pg
from src.utils import GameSettings
from src.sprites import BackgroundSprite, Sprite
from src.scenes.scene import Scene
from src.utils import Logger, Position
from src.core.services import sound_manager, scene_manager, input_manager
from src.interface.components import Button
from typing import override


ELEMENT_CHART = {
    "Fire": {"strong": ["Grass", "Ice"], "weak": ["Water", "Ground", "Rock"]},
    "Water": {"strong": ["Fire", "Ground", "Rock"], "weak": ["Grass", "Lightning"]},
    "Grass": {"strong": ["Water", "Ground", "Rock"], "weak": ["Fire", "Ice", "Flying"]},
    "Lightning": {"strong": ["Water", "Flying"], "weak": ["Ground"]},
    "Ice": {"strong": ["Grass", "Ground", "Flying"], "weak": ["Fire", "Rock"]},
    "Flying": {"strong": ["Grass", "Fighting"], "weak": ["Lightning", "Ice", "Rock"]},
    "Ground": {"strong": ["Fire", "Lightning", "Rock"], "weak": ["Water", "Grass", "Ice"]},
    "Rock": {"strong": ["Fire", "Ice", "Flying"], "weak": ["Water", "Grass", "Ground"]},
    "Normal": {"strong": [], "weak": []}
}

class Attack:
    def __init__(self, name: str, element: str, power: int, accuracy: float = 1.0):
        self.name = name
        self.element = element
        self.power = power
        self.accuracy = accuracy

class Character:
    def __init__(self, pokemon_data):
        self.name = pokemon_data['name']
        self.max_hp = float(pokemon_data.get('max_hp', pokemon_data.get('hp', 20)))
        self.hp = float(pokemon_data.get('hp', self.max_hp))
        self.base_attack = float(pokemon_data.get('attack', 40))
        self.base_defense = float(pokemon_data.get('defense', 5))
        self.attack = self.base_attack
        self.defense = self.base_defense
        self.battle_sprite = pokemon_data['battle_sprite']
        self.level = pokemon_data.get('level', 1)
        self.element = pokemon_data.get('element', 'Normal')
        

        attack_data = pokemon_data.get('attacks', [])
        self.attacks = []
        for atk in attack_data:
            self.attacks.append(Attack(
                atk.get('name', 'Tackle'),
                atk.get('element', self.element),
                atk.get('power', 40),
                atk.get('accuracy', 1.0)
            ))
        

        if not self.attacks:
            self.attacks = [
                Attack("Tackle", "Normal", 40, 1.0),
                Attack(f"{self.element} Blast", self.element, 60, 0.9)
            ]
        

        self.attack_buff = 0
        self.defense_buff = 0
  
    def is_alive(self):
        return self.hp > 0
    
    def apply_attack_buff(self, amount: int):
        """Apply attack buff from Strength Potion"""
        self.attack_buff += amount
        self.attack = self.base_attack + self.attack_buff
        
    def apply_defense_buff(self, amount: int):
        """Apply defense buff from Defense Potion"""
        self.defense_buff += amount
        self.defense = self.base_defense + self.defense_buff
    
    def heal(self, amount: int):
        """Heal pokemon by amount"""
        self.hp = min(self.hp + amount, self.max_hp)
  
    def take_damage(self, amount):
        self.hp -= float(amount)
    
    def calculate_damage(self, attack: Attack, defender):
        """Calculate damage with element effectiveness using Pokemon-style formula"""
    


        level_modifier = (2 * self.level / 5 + 2)
        base_damage = (level_modifier * attack.power * self.attack) / (defender.defense * 50) + 2
        

        base_damage = max(1.0, base_damage)
        

        multiplier = 1.0
        if attack.element in ELEMENT_CHART:
            chart = ELEMENT_CHART[attack.element]
            if defender.element in chart["strong"]:
                multiplier = 1.5
                Logger.info(f"It's super effective! ({attack.element} vs {defender.element})")
            elif defender.element in chart["weak"]:
                multiplier = 0.5
                Logger.info(f"It's not very effective... ({attack.element} vs {defender.element})")
        

        final_damage = base_damage * multiplier
        

        import random
        random_factor = random.uniform(0.85, 1.0)
        final_damage = final_damage * random_factor
        
        return final_damage, multiplier
  
    def attack_target(self, attack: Attack, other):
        damage, multiplier = self.calculate_damage(attack, other)
        other.take_damage(damage)
        return damage, multiplier

class BattleScene(Scene):
    def __init__(self, player_pokemon, enemy_pokemon, game_manager, enemy_trainer=None):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.game_manager = game_manager
        
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        self.player = Character(player_pokemon)
        self.enemy = Character(enemy_pokemon)
        
        self.player_pokemon = player_pokemon
        self.enemy_pokemon = enemy_pokemon
        
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
        

        self.in_main_menu = True
        self.in_attack_menu = False
        self.menu_index = 0
        self.enemy_trainer = enemy_trainer
        

        self.main_menu_actions = [
            lambda: self.open_attack_menu(),
            lambda: self.open_bag(),
            lambda: self.game_manager.pokemon.open(),
            lambda: self.run_from_battle()
        ]
        

        self.attack_menu_index = 0
        

        self.fight_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 150, py + 150, 200, 90,
            lambda: self.open_attack_menu()
        )
        
        self.bag_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 390, py + 150, 200, 90,
            lambda: self.open_bag()
        )
        
        self.pokemon_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 150, py + 260, 200, 90,
            lambda: self.game_manager.pokemon.open()
        )
        
        self.run_button = Button(
            "UI/raw/UI_Flat_InputField01a.png", "UI/raw/UI_Flat_InputField01a.png",
            px + 390, py + 260, 200, 90,
            lambda: self.run_from_battle()
        )
        
    def open_attack_menu(self):
        """Switch to attack selection menu"""
        if not self.waiting_input or not self.player_turn or self.battle_over:
            return
        self.in_main_menu = False
        self.in_attack_menu = True
        self.attack_menu_index = 0
        self.set_message("Choose an attack!")
        
    def open_bag(self):
        """Open bag for item usage"""
        if not self.waiting_input or not self.player_turn or self.battle_over:
            return
        
        self.game_manager.bag.in_battle = True
        self.game_manager.bag.open()
        
    def use_item(self, item_name: str):
        """Use an item from the bag on the player's pokemon"""
        if item_name == "Potion":
            heal_amount = 50
            self.player.heal(heal_amount)
            self.set_message(f"Used Heal Potion! Restored {heal_amount} HP!")
            
        elif item_name == "Strength Potion":
            buff_amount = 10
            self.player.apply_attack_buff(buff_amount)
            self.set_message(f"Used Strength Potion! Attack increased by {buff_amount}!")
            
        elif item_name == "Defense Potion":
            buff_amount = 10
            self.player.apply_defense_buff(buff_amount)
            self.set_message(f"Used Defense Potion! Defense increased by {buff_amount}!")
        

        for item in self.game_manager.bag._items_data:
            if item["name"] == item_name:
                item["count"] -= 1
                if item["count"] <= 0:
                    self.game_manager.bag._items_data.remove(item)
                break
        
        self.waiting_input = False
        

        self.player_turn = False
        self.enemy_attack_timer = 1.5
        self.needs_enemy_attack = True
        
    def back_to_main_menu(self):
        """Return to main battle menu"""
        self.in_attack_menu = False
        self.in_main_menu = True
        self.menu_index = 0
        self.set_message("What will you do?")
        
    def player_attack(self, attack_index: int):
        """Player uses selected attack"""
        if not self.waiting_input or not self.player_turn or self.battle_over:
            return
        
        if attack_index >= len(self.player.attacks):
            return
        
        attack = self.player.attacks[attack_index]
        self.waiting_input = False
        self.in_attack_menu = False
        self.in_main_menu = True
        
        damage, multiplier = self.player.attack_target(attack, self.enemy)
        

        effectiveness = ""
        if multiplier > 1.0:
            effectiveness = " It's super effective!"
        elif multiplier < 1.0:
            effectiveness = " It's not very effective..."
            
        self.set_message(f"{self.player.name} used {attack.name}! {self.enemy.name} took {int(damage)} damage!{effectiveness}")
        
        if not self.enemy.is_alive():
            self.battle_over = True
            if self.enemy_trainer is not None:
                self.enemy_trainer.mark_as_defeated()
                Logger.info(f"Trainer defeated! Trainer will no longer initiate battles.")
            self.set_message(f"{self.enemy.name} fainted! You win!")
            self.battle_end_timer = 2.0
            return
        
        self.player_turn = False
        self.enemy_attack_timer = 1.5
        self.needs_enemy_attack = True
        
    def enemy_attack(self):
        """Enemy chooses and uses an attack"""
        import random
        attack = random.choice(self.enemy.attacks)
        
        damage, multiplier = self.enemy.attack_target(attack, self.player)
        
        effectiveness = ""
        if multiplier > 1.0:
            effectiveness = " It's super effective!"
        elif multiplier < 1.0:
            effectiveness = " It's not very effective..."
            
        self.set_message(f"{self.enemy.name} used {attack.name}! {self.player.name} took {int(damage)} damage!{effectiveness}")
        
        if not self.player.is_alive():
            self.battle_over = True
            self.set_message(f"{self.player.name} fainted! You lost!")
            self.battle_end_timer = 2.0
            return
        
        self.player_turn = True
        self.waiting_input = True
        
    def run_from_battle(self):
        """Exit battle and return to game"""
        self.sync_pokemon_to_bag()
        self.game_manager.in_battle = False
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        scene_manager.change_scene('game')
            
    def sync_pokemon_to_bag(self):
        """Sync the battle pokemon's HP back to the pokemon party"""
        if not self.game_manager.pokemon._monsters_data:
            return
        
        for monster in self.game_manager.pokemon._monsters_data:
            if monster.get('name') == self.player.name:
                monster['hp'] = max(0, self.player.hp)
                Logger.info(f"Updated {self.player.name} HP to {self.player.hp}")
                break
                
    def catch_pokemon(self, enemy_pokemon):
        caught_pokemon = enemy_pokemon.copy()
        caught_pokemon['hp'] = max(0, self.enemy.hp)
        
        self.waiting_input = False
        
        if self.game_manager.pokemon.max_party_size <= len(self.game_manager.pokemon._monsters_data):
            self.game_manager.pc_storage.deposit_pokemon(caught_pokemon)
            self.set_message(f"Caught {self.enemy.name}! Sent to PC (Party full)")
        else:
            self.game_manager.pokemon._monsters_data.append(caught_pokemon)
            self.set_message(f"You caught {self.enemy.name}!")
            
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
        self.needs_show_menu = True
        
    def get_hp_color(self, hp_ratio: float):
        """Get HP bar color based on HP percentage"""
        if hp_ratio > 0.5:
            t = (hp_ratio - 0.5) / 0.5
            r = int(255 * (1 - t))
            g = 200
            b = 50
        else:
            t = hp_ratio / 0.5
            r = 255
            g = int(200 * t)
            b = 50
        return (r, g, b)

    def draw_hp_bar(self, screen: pg.Surface, x: int, y: int, 
                    current_hp: float, max_hp: float, width: int = 200, height: int = 16):
        """Draw HP bar"""
        hp_ratio = max(0, min(1, current_hp / max_hp))
        fill_width = int(width * hp_ratio)
        
        pg.draw.rect(screen, (40, 40, 40), (x, y, width, height))
        
        if fill_width > 0:
            color = self.get_hp_color(hp_ratio)
            pg.draw.rect(screen, color, (x, y, fill_width, height))
    
    def handle_main_menu_input(self):
        """Handle main battle menu navigation"""
        if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
            if self.menu_index % 2 == 1:
                self.menu_index -= 1
                
        elif input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
            if self.menu_index % 2 == 0:
                self.menu_index += 1
                
        elif input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            if self.menu_index >= 2:
                self.menu_index -= 2
                
        elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            if self.menu_index <= 1:
                self.menu_index += 2
        
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e) or input_manager.key_pressed(pg.K_z):
            self.main_menu_actions[self.menu_index]()
            
    def handle_attack_menu_input(self):
        """Handle attack selection menu navigation"""
        max_attacks = len(self.player.attacks)
        
        if input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
            self.attack_menu_index = (self.attack_menu_index - 1) % max_attacks
            
        elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
            self.attack_menu_index = (self.attack_menu_index + 1) % max_attacks
        
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_e) or input_manager.key_pressed(pg.K_z):
            self.player_attack(self.attack_menu_index)
            
        if input_manager.key_pressed(pg.K_ESCAPE) or input_manager.key_pressed(pg.K_x):
            self.back_to_main_menu()
            
    def draw_main_menu_selector(self, screen: pg.Surface):
        """Draw selector for main menu"""
        px = GameSettings.SCREEN_WIDTH // 2
        py = GameSettings.SCREEN_HEIGHT // 2
        
        positions = [
            (px + 120, py + 205),
            (px + 400, py + 205),
            (px + 120, py + 280),
            (px + 400, py + 280),
        ]
        
        x, y = positions[self.menu_index]
        screen.blit(self.selector.image, (x, y))
        
    def draw_attack_menu_selector(self, screen: pg.Surface):
        """Draw selector for attack menu"""
        px = GameSettings.SCREEN_WIDTH // 2
        py = GameSettings.SCREEN_HEIGHT // 2
        
        y_offset = 205 + (self.attack_menu_index * 70)
        screen.blit(self.selector.image, (px + 100, py + y_offset))
    
    def update(self, dt: float):
        if self.battle_over and self.battle_end_timer > 0:
            self.battle_end_timer -= dt
            if self.battle_end_timer <= 0:
                self.run_from_battle()
                return
            
        if self.needs_show_menu:
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.waiting_input = True
                self.message = "What will you do?"
                self.needs_show_menu = False
                
        if input_manager.key_pressed(pg.K_SPACE):
            if self.message_index < len(self.message):
                self.message_index = len(self.message)
                self.displayed_message = self.message
                
        if self.message_index < len(self.message):
            self.message_timer += dt
            add_char = int(self.message_timer / self.message_speed)
            if add_char > 0:
                self.message_index = min(self.message_index + add_char, len(self.message))
                self.displayed_message = self.message[:self.message_index]
                self.message_timer -= add_char * self.message_speed
        
        if self.needs_enemy_attack and not self.battle_over:
            self.enemy_attack_timer -= dt
            if self.enemy_attack_timer <= 0:
                self.enemy_attack()
                self.needs_enemy_attack = False
            
        self.player_hp_display += (self.player.hp - self.player_hp_display) * 0.15
        self.enemy_hp_display += (self.enemy.hp - self.enemy_hp_display) * 0.15
        

        if self.game_manager.bag.overlay:
            self.game_manager.bag.update(dt)
            if self.game_manager.bag.item_used:

                selected_items = self.game_manager.bag.get_current_category_items()
                if self.game_manager.bag.selected_item_index < len(selected_items):
                    used_item = selected_items[self.game_manager.bag.selected_item_index]
                    item_name = used_item["name"]
                    
                    if item_name == "Pokeball":
                        self.catch_pokemon(self.enemy_pokemon)
                    elif item_name in ["Potion", "Strength Potion", "Defense Potion"]:
                        self.use_item(item_name)
                        
                self.game_manager.bag.item_used = None
                
        elif self.game_manager.pokemon.overlay:
            self.game_manager.pokemon.update(dt)
            
        else:
            if self.waiting_input and not self.battle_over:
                if self.in_attack_menu:
                    self.handle_attack_menu_input()
                elif self.in_main_menu:
                    self.handle_main_menu_input()
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
    
        screen.blit(self.message_box.image, (px - 640, py + 150))
        screen.blit(self.player_menu.image, (px, py - 60))
        screen.blit(self.player_hp.image, (px + 170, py + 20))
        screen.blit(self.enemy_menu.image, (px - 600, py - 320))
        screen.blit(self.player_hp.image, (px - 450, py - 240))
        
        font = pg.font.Font("assets/fonts/Pokemon.ttf", 50)
        name_font = pg.font.Font("assets/fonts/Pokemon.ttf", 70)
        

        p_name_text_shadow = name_font.render(self.player.name, True, (0,0,0))
        p_name_text_shadow.set_alpha(50)
        screen.blit(p_name_text_shadow, (px + 105, py - 46))
        p_name_text = name_font.render(self.player.name, True, (0,0,0))
        screen.blit(p_name_text, (px + 100, py - 48))
        
        p_level_text = name_font.render(f"Lv{self.player.level}", True, (0,0,0))
        screen.blit(p_level_text, (px + 425, py - 48))
        

        e_name_text = name_font.render(self.enemy.name, True, (0,0,0))
        screen.blit(e_name_text, (px - 565, py - 308))
        
        e_level_text = name_font.render(f"Lv{self.enemy.level}", True, (0,0,0))
        screen.blit(e_level_text, (px - 200, py - 308))
        

        text = font.render(self.displayed_message, True, (255, 255, 255))
        screen.blit(text, (px - 580, py + 185))
        

        self.draw_hp_bar(screen, px + 260, py + 30, self.player_hp_display, self.player.max_hp, width=270, height=15)
        self.draw_hp_bar(screen, px - 360, py - 230, self.enemy_hp_display, self.enemy.max_hp, width=270, height=15)
        

        if self.waiting_input and not self.battle_over:
            if self.in_attack_menu:

                screen.blit(self.menu.image, (px + 60, py + 150))
                button_font = pg.font.Font("assets/fonts/Pokemon.ttf", 60)
                buttons_font = pg.font.Font("assets/fonts/Pokemon.ttf", 70)
                for i, attack in enumerate(self.player.attacks):
                    y_pos = py + 185 + (i * 70)
                    attack_text = buttons_font.render(f"{attack.name} ({attack.element})", True, (50, 50, 50))
                    screen.blit(attack_text, (px + 140, y_pos))
                


                
                self.draw_attack_menu_selector(screen)
                
            elif self.in_main_menu:

                self.fight_button.draw(screen)
                self.pokemon_button.draw(screen)
                self.bag_button.draw(screen)
                self.run_button.draw(screen)
                
                screen.blit(self.menu.image, (px + 60, py + 150))
                button_font = pg.font.Font("assets/fonts/Pokemon.ttf", 70)
                screen.blit(button_font.render("FIGHT", True, (50, 50, 50)), (px + 160, py + 185))
                screen.blit(button_font.render("BAG", True, (50, 50, 50)), (px + 440, py + 185))
                screen.blit(button_font.render("POKEMON", True, (50, 50, 50)), (px + 160, py + 260))
                screen.blit(button_font.render("RUN", True, (50, 50, 50)), (px + 440, py + 260))
                self.draw_main_menu_selector(screen)


        if self.game_manager.bag.overlay:
            screen.blit(self.game_manager.bag.dim_overlay, (0, 0))
            self.game_manager.bag.draw(screen)
        elif self.game_manager.pokemon.overlay:
            screen.blit(self.game_manager.pokemon.dim_overlay, (0, 0))
            self.game_manager.pokemon.draw(screen)