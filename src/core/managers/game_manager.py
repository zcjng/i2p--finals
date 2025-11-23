from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
import json, os
import pygame as pg
import random
from typing import TYPE_CHECKING
from src.data.options import Options
from src.core.services import scene_manager, input_manager, sound_manager
if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag


class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    bag: "Bag"
    options: "Options"
    
    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    
    # Changing Scene properties
    should_change_scene: bool
    next_map: str
    _transitioning: bool = False
    _transition_alpha: int = 0
    _transition_speed: int = 600
    _transition_surface: pg.Surface | None = None
    
    def __init__(self, maps: dict[str, Map], start_map: str, 
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]], 
                 bag: Bag | None = None,
                 options: Options | None = None,
                 pc_storage = None):
                     
        from src.data.bag import Bag
        from src.data.pc import PCStorage
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.bag = bag if bag is not None else Bag([], [])
        self.options = options if options is not None else Options()
        self.pc_storage = pc_storage if pc_storage is not None else PCStorage()
        self.steps_per_check = 1
        self.steps_last = 0
        self.encounter_rate = 0.2
        self.in_battle = False
        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""
        
    @property
    def current_map(self):
        return self.maps[self.current_map_key]
        
    @property
    def current_enemy_trainers(self):
        return self.enemy_trainers[self.current_map_key]
        
    @property
    def current_teleporter(self):
        return self.maps[self.current_map_key].teleporters
    
    def switch_map(self, target: str, player_direction):
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
        
        self.next_map = target
        self.last_direction = player_direction
        self.should_change_scene = True
        self._transitioning = True
        self._transition_alpha = 0

        
        if self._transition_surface is None:
            self._transition_surface = pg.Surface((pg.display.get_surface().get_size()))
            self._transition_surface.fill((0, 0, 0))
            self._transition_surface.set_alpha(0)

    def try_switch_map(self) :
        if not self.should_change_scene:
            return
        
        self.current_map_key = self.next_map
        self.next_map = ""
        if self.player:
            self.player.position = self.maps[self.current_map_key].spawn
            self.player.animation.update_pos(self.player.position)
            self.player.moving = False
            self.player.move_target = Position(self.player.position.x, self.player.position.y)
            self.player.move_start = Position(self.player.position.x, self.player.position.y)
   
    def map_transition(self, dt):
        if not self._transitioning:
            return
        
        if self.should_change_scene:
            self._transition_alpha += self._transition_speed * dt
                
            if self._transition_alpha >= 255:
                    self._transition_alpha = 255        
                    self.try_switch_map()
                    self.should_change_scene = False
        else:
            self._transition_alpha -= self._transition_speed * dt
            if self._transition_alpha <= 0:
                self._transition_alpha = 0
                self._transitioning = False
        
        if self._transition_surface:
            self._transition_surface.set_alpha(int(self._transition_alpha))
                
        

    def check_collision(self, rect: pg.Rect):
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in self.enemy_trainers[self.current_map_key]:
            if rect.colliderect(entity.animation.rect):
                return True
        
        return False
        
    def bush_interaction(self, just_stopped):
        if not self.player:
            return
        
        if self.player.moving:
            return
        
        if self.in_battle:
            return
        
        
        
        
        if not self.current_map.is_in_bush(self.player.position):
            return
        
        if input_manager.key_pressed(pg.K_e):
            Logger.info('Player forced encounter!')
            self.wild_encounter()
            return
        
        if just_stopped:
            
            Logger.info('Check!!!!')
            self.steps_last += 1
        
            if self.steps_last < self.steps_per_check:
                return
            
            self.steps_last = 0
            if random.random() < self.encounter_rate:
                Logger.info('Wild pokemon has appeared!')
                self.wild_encounter()


    def wild_encounter(self):
        
        self.in_battle = True
        sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
        
        
        wild_pokemon = self.get_random_wild_pokemon()
        
        player_pokemon = self.get_player_lead_pokemon()
            
        if not player_pokemon:
            Logger.warning('Player has no pokemon!')
            return
        
        from src.scenes.battle_scene import BattleScene
        battle_scene = BattleScene(player_pokemon, wild_pokemon, self)
        scene_manager.register_scene('battle', battle_scene)
        scene_manager.change_scene('battle')
        
    def get_random_wild_pokemon(self):
        area_pokemon = {
            "map3.tmx" : [
                { "name": "Venusaur",  "hp": 160,  "max_hp": 160, "level": 30, "sprite_path": "menu_sprites/menusprite4.png", "battle_sprite": "sprites/sprite4.png"},
                { "name": "Gengar",    "hp": 140, "max_hp": 140, "level": 28, "sprite_path": "menu_sprites/menusprite5.png", "battle_sprite": "sprites/sprite5.png"},
                { "name": "Dragonite", "hp": 220, "max_hp": 220, "level": 40, "sprite_path": "menu_sprites/menusprite6.png", "battle_sprite": "sprites/sprite6.png"}
            ]
        }

        pokemon_list = area_pokemon.get(self.current_map_key, [])
        if not pokemon_list:
            return {"name": "Venusaur",  "hp": 160,  "max_hp": 160, "level": 30, "sprite_path": "menu_sprites/menusprite4.png", "battle_sprite": "sprites/sprite4.png"}
        
        return random.choice(pokemon_list)
    
    def get_player_lead_pokemon(self):
        if not self.bag._monsters_data:
            return None
        
        for monster in self.bag._monsters_data:
            if monster.get('hp', 0) > 0:
                return monster
            
        return None
    
    def save(self, path: str):
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")
             
    @classmethod
    def load(cls, path: str):
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self):
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            
            if self.player and self.current_map_key == key:
                player_pos = self.player.position
            else:
                player_pos = m.spawn
                
            block["player"] = {
                "x": player_pos.x / GameSettings.TILE_SIZE,
                "y": player_pos.y / GameSettings.TILE_SIZE
            }
            map_blocks.append(block)
        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player is not None else None,
            "bag": self.bag.to_dict(),
            "options": {},
            "pc_storage": self.pc_storage.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]):
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag
        from src.data.pc import PCStorage
        
        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}

        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE,
                    sp["y"] * GameSettings.TILE_SIZE
                )
        current_map = data["current_map"]
        gm = cls(
            maps, current_map,
            None, # Player
            trainers,
            bag=None
        )
        gm.current_map_key = current_map
        
        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m["enemy_trainers"]
            gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]
        
        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)
        
        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])
        gm.options = Options()
        
        Logger.info("Loading PC Storage")
        gm.pc_storage = PCStorage.from_dict(data.get("pc_storage", {})) if data.get("pc_storage") else PCStorage()

        return gm