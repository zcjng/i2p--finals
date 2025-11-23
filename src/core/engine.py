import pygame as pg

from src.utils import GameSettings, Logger
from .services import scene_manager, input_manager

from src.scenes.menu_scene import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.setting_scene import SettingScene

class Engine:

    screen: pg.Surface              # Screen Display of the Game
    clock: pg.time.Clock            # Clock for FPS control
    running: bool                   # Running state of the game

    def __init__(self):
        Logger.info("Initializing Engine")

        pg.init()

        self.screen = pg.display.set_mode((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True

        pg.display.set_caption(GameSettings.TITLE)

        scene_manager.register_scene("menu", MenuScene())
        scene_manager.register_scene("game", GameScene(None))
        scene_manager.register_scene("setting", SettingScene())
        scene_manager.init_after_display()
        '''
        [TODO HACKATHON 5]
        Register the setting scene here
        
        '''
        scene_manager.change_scene("menu")
        self.drawing = False
        self.draw_positions = []

    def run(self):
        Logger.info("Running the Game Loop ...")

        while self.running:
            dt = self.clock.tick(GameSettings.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

    def handle_events(self):
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.drawing = True
                elif event.button == 2:  # Right mouse button
                    self.draw_positions.clear()
            elif event.type == pg.MOUSEBUTTONUP:
                self.drawing = False
            elif event.type == pg.MOUSEMOTION and self.drawing:
                self.draw_positions.append(event.pos)
            input_manager.handle_events(event)

            
    def update(self, dt: float):
        scene_manager.update(dt)
        input_manager.reset()

    def render(self):
        self.screen.fill((0, 0, 0))     # Make sure the display is cleared
        scene_manager.draw(self.screen)
        # Draw the current scene
        '''
        for pos in self.draw_positions:
            pg.draw.circle(self.screen, 'RED', pos, 2)
            
            
        cursor_pos = pg.mouse.get_pos()
            
        pg.draw.circle(self.screen, 'RED', cursor_pos, 5)
        '''
        pg.display.flip()             # Render the display
