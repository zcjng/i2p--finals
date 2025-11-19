import pygame as pg
import threading
import time

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager


class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite

    
    def __init__(self, gm: GameManager):
        super().__init__()
        # Game Manager
        if gm is not None:
            self.game_manager = gm
        else:
            manager = GameManager.load("saves/game0.json")
            if manager is None:
                Logger.error("Failed to load game manager")
                exit(1)
            self.game_manager = manager

        self.game_manager.options.set_save_callback(self.save_game)
        self.game_manager.options.set_load_callback(self.load_game)
        
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        
        
    def save_game(self):
        save_path = 'saves/game1.json'
        save = self.game_manager.save(save_path)
        Logger.info('Game saved successfully into ' + save_path)
        
    def load_game(self):
        load_path = 'saves/game1.json'
        loaded_gm = GameManager.load(load_path)
        
        if loaded_gm:
            self.game_manager = loaded_gm
            
            self.game_manager.options.set_save_callback(self.save_game)
            self.game_manager.options.set_load_callback(self.load_game)
            
            Logger.info('Game loaded successfully')
        else:
            Logger.error('Failed to load game from ' + load_path)
            
        
    @override
    def enter(self):
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        
    @override
    def exit(self):
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        # Check if there is assigned next scene
        

        # Update player and other data

        if not self.game_manager.options.overlay and not self.game_manager.bag.overlay:
            self.game_manager.map_transition(dt)
            # Update others

            if self.game_manager.player and not self.game_manager.in_battle:
                moving = self.game_manager.player.moving
                
                
                self.game_manager.player.update(dt)
                
                just_stopped = moving and not self.game_manager.player.moving
                
                self.game_manager.bush_interaction(just_stopped)
                    
                for enemy in self.game_manager.current_enemy_trainers:
                    enemy.update(dt)
                    if enemy.detected and not self.game_manager.in_battle:
                        if just_stopped:
                            self.game_manager.in_battle = True
                            Logger.info('Encounter with an NPC!')
                            
                            self.game_manager.wild_encounter()
                            break
            
        if self.game_manager.options.overlay:
            self.game_manager.options.update(dt)  # updates ALL buttons and slider
        elif self.game_manager.bag.overlay:
            self.game_manager.bag.update(dt)
        else:
            # normal update
            self.game_manager.options.update(dt)
            self.game_manager.bag.update(dt)
            

            
            
        
        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )
        
        
    @override
    def draw(self, screen: pg.Surface):   
        player = self.game_manager.player
                
        if self.game_manager.player:
            
            
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            player.draw(screen, camera)
            
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)


        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)
        

        self.game_manager.options.options_button.draw(screen)
        self.game_manager.bag.bag_button.draw(screen)
        
        # Then draw overlays (which cover the buttons with dim effect)
        if self.game_manager.options.overlay:
            screen.blit(self.game_manager.options.dim_overlay, (0, 0))

            self.game_manager.options.draw(screen)
            self.game_manager.options.close_button.draw(screen)
            
        if self.game_manager.bag.overlay:
            screen.blit(self.game_manager.bag.dim_overlay, (0, 0))
            self.game_manager.bag.draw(screen)
            self.game_manager.bag.close_button.draw(screen)
        
        
        if self.game_manager._transitioning and self.game_manager._transition_surface:
            screen.blit(self.game_manager._transition_surface, (0, 0))
