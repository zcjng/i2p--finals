import pygame as pg
import os

from src.scenes.scene import Scene
from src.utils import Logger


class SceneManager:
    
    _scenes: dict[str, Scene]
    _current_scene: Scene | None = None
    _next_scene: str | None = None
    
    
    _transitioning: bool = False
    _transition_alpha: int = 0
    _transition_speed: int = 600
    _transition_surface: pg.Surface | None = None
    
    _transition_frames: list[pg.Surface] | None = None
    _transition_index: int = 0
    _playing_frame_transition: bool = False
    _frame_speed: float = 25
    _frame_accumulator: float = 0
    _scene_switched: bool = False
    _pending_scene: Scene | None = None
    
    def __init__(self):
        Logger.info("Initializing SceneManager")
        self._scenes = {}
        
    def init_after_display(self):
        self._load_transition_frames()
        
    def _load_transition_frames(self):
        
        folder = os.path.join("assets", "transitions", "pngs", "battle1")
        self._transition_frames = []
        
        if not os.path.exists(folder):
            Logger.error(f"Transition folder not found: {folder}")
            return
        

        for i in range(1, 56):
            filename = os.path.join(folder, f"fixed_frame {i}.png")
            if not os.path.exists(filename):
                Logger.error(f"Missing frame: {filename}")
                continue
            
            img = pg.image.load(filename).convert_alpha()
            
                
            img = pg.transform.scale(img, pg.display.get_surface().get_size())
            self._transition_frames.append(img)
        
        Logger.info(f"Loaded {len(self._transition_frames)} transition frames!")
        
    def register_scene(self, name: str, scene: Scene):
        self._scenes[name] = scene
        
    def change_scene(self, scene_name: str):
        if scene_name in self._scenes:
            Logger.info(f"Changing scene to '{scene_name}'")
            self._next_scene = scene_name
            
            
            if scene_name == 'game':
                self._transitioning = True
                self._transition_alpha = 0
                
                if self._transition_surface is None:
                    self._transition_surface = pg.Surface((pg.display.get_surface().get_size()))
                    self._transition_surface.fill((0, 0, 0))
                    self._transition_surface.set_alpha(0)
            elif scene_name == 'battle':
                self._start_frame_transition()
            else:
                self._perform_scene_switch()
        else:
            raise ValueError(f"Scene '{scene_name}' not found")
    
    def _start_frame_transition(self):
        if not self._transition_frames:
            Logger.error("No transition frames were loaded, using fade transition")
            self._transitioning = True
            return
        
        Logger.info('Starting battle transition')
        self._playing_frame_transition = True
        self._transition_index = 0
        self._frame_accumulator = 0
        self._scene_switched = False
        self._pending_scene = None
        
    def update(self, dt: float):

        if self._playing_frame_transition and self._transition_frames:

            capped_dt = min(dt, 0.1)
            self._frame_accumulator += capped_dt * self._frame_speed
            

            frames_to_advance = 0
            while self._frame_accumulator >= 1 and frames_to_advance < 3:
                self._frame_accumulator -= 1
                self._transition_index += 1
                frames_to_advance += 1
                
    def update(self, dt: float):

        if self._playing_frame_transition and self._transition_frames:

            capped_dt = min(dt, 0.1)
            self._frame_accumulator += capped_dt * self._frame_speed
            

            frames_processed = 0
            max_frames_per_update = 5
            
            while self._frame_accumulator >= 1 and frames_processed < max_frames_per_update:
                self._frame_accumulator -= 1
                self._transition_index += 1
                frames_processed += 1
                

                if self._transition_index == 40 and not self._scene_switched:
                    if self._next_scene:

                        if self._current_scene:
                            self._current_scene.exit()
                        

                        self._pending_scene = self._scenes[self._next_scene]
                        self._current_scene = self._pending_scene
                        self._next_scene = None
                        self._scene_switched = True
                        Logger.info(f"Scene switched at frame 40 (dt={dt:.4f})")
                

                if self._transition_index >= len(self._transition_frames):
                    self._playing_frame_transition = False
                    self._scene_switched = False
                    

                    if self._pending_scene:
                        Logger.info("Transition complete - entering new scene")
                        self._pending_scene.enter()
                        self._pending_scene = None
                    
                    Logger.info("Battle transition complete")
                    return
            

            return
        

        if self._transitioning:
            if self._next_scene is not None:
                self._transition_alpha += self._transition_speed * dt
                
                if self._transition_alpha >= 255:
                    self._transition_alpha = 255        
                    self._perform_scene_switch()
            else:
                self._transition_alpha -= self._transition_speed * dt
                if self._transition_alpha <= 0:
                    self._transition_alpha = 0
                    self._transitioning = False
            
            if self._transition_surface:
                self._transition_surface.set_alpha(int(self._transition_alpha))
        

        if self._current_scene and not self._playing_frame_transition:
            self._current_scene.update(dt)
            
    def draw(self, screen: pg.Surface):
        if self._current_scene:
            self._current_scene.draw(screen)
            

        if self._playing_frame_transition and self._transition_frames:
            if self._transition_index < len(self._transition_frames):
                frame = self._transition_frames[self._transition_index]
                screen.blit(frame, (0, 0))
            

        if self._transitioning and self._transition_surface:
            screen.blit(self._transition_surface, (0, 0))
            
            
    def _perform_scene_switch(self):
        if self._next_scene is None:
            return
            

        if self._current_scene:
            self._current_scene.exit()
        
        
        self._current_scene = self._scenes[self._next_scene]
        

        if self._current_scene:
            Logger.info(f"Entering {self._next_scene} scene")
            self._current_scene.enter()
            

        self._next_scene = None