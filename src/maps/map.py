import pygame as pg
import pytmx

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport
from src.utils.definition import PC
class Map:
    # Map Properties
    path_name: str
    tmxdata: pytmx.TiledMap
    # Position Argument
    spawn: Position
    teleporters: list[Teleport]
    # Rendering Properties
    _surface: pg.Surface
    _collision_map: list[pg.Rect]

    def __init__(self, path: str, tp: list[Teleport], spawn: Position):
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp
        self.width = self.tmxdata.width
        self.height = self.tmxdata.height

        pixel_w = self.width * GameSettings.TILE_SIZE
        pixel_h = self.height * GameSettings.TILE_SIZE

        # Prebake the map
        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        # Prebake the collision map
        self._collision_map = self._create_collision_map()

        self.bushes = self.bush_map()
        self.pc_tiles = self.pc_map()
        
        
    def update(self, dt: float):
        return

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))
        
        # Draw the hitboxes collision map
        
        
        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
        
        for tile_x, tile_y in self.bushes:
            rect = pg.Rect(
                tile_x * GameSettings.TILE_SIZE,
                tile_y * GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE
            )
            pg.draw.rect(screen, (0, 255, 0), camera.transform_rect(rect), 1)
            
        for tile_x, tile_y in self.pc_tiles:
            rect = pg.Rect(
                tile_x * GameSettings.TILE_SIZE,
                tile_y * GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE
            )
            pg.draw.rect(screen, (0, 0, 255), camera.transform_rect(rect), 2)
            
    def check_collision(self, rect: pg.Rect):
        '''
        [TODO HACKATHON 4]
        Return True if collide if rect param collide with self._collision_map
        Hint: use API colliderect and iterate each rectangle to check
        '''
        for collision_rect in self._collision_map:
            if rect.colliderect(collision_rect):
                return True
        return False
        
    def bush_map(self):
        bush_tiles = set()
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("PokemonBush" in layer.name):
                for x, y, gid in layer:
                    if gid == 81:
                        bush_tiles.add((x, y))
                break
        return bush_tiles
                        
    def bush_zone(self, tile_x: int, tile_y: int):
        return (tile_x, tile_y) in self.bushes
    
    def is_in_bush(self, pos: Position):
        tile_x = int(pos.x // GameSettings.TILE_SIZE)
        tile_y = int(pos.y // GameSettings.TILE_SIZE)
        
        return self.bush_zone(tile_x, tile_y)
    
    def pc_map(self):
        """Load PC tile positions from the map"""
        pc_tiles = set()
        PC_TILE_ID = 200  # Change this to match your tile ID
        
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("PC" in layer.name):
                for x, y, gid in layer:
                    if gid >= PC_TILE_ID:
                        pc_tiles.add((x, y))
                break
        

        return pc_tiles

    def is_near_pc(self, pos: Position):
        """Check if position is on or near a PC tile"""
        tile_x = int(pos.x // GameSettings.TILE_SIZE)
        tile_y = int(pos.y // GameSettings.TILE_SIZE)
        
        return (tile_x, tile_y) in self.pc_tiles

    def check_teleport(self, pos: Position): 
        TELEPORT_SIZE = GameSettings.TILE_SIZE * 1.15
        
        for teleporter in self.teleporters:
            teleport_rect = pg.Rect(
                teleporter.pos.x, 
                teleporter.pos.y, 
                TELEPORT_SIZE, 
                TELEPORT_SIZE
            )
        
            if teleport_rect.collidepoint(pos.x, pos.y):
                return teleporter
        
        return None

    def _render_all_layers(self, target: pg.Surface):
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            # elif isinstance(layer, pytmx.TiledImageLayer) and layer.image:
            #     target.blit(layer.image, (layer.x or 0, layer.y or 0))
 
    def _render_tile_layer(self, target: pg.Surface, layer: pytmx.TiledTileLayer):
        for x, y, gid in layer:
            if gid == 0:
                continue
            image = self.tmxdata.get_tile_image_by_gid(gid)
            if image is None:
                continue

            image = pg.transform.scale(image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            target.blit(image, (x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE))
    
    def _create_collision_map(self):
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("collision" in layer.name.lower() or "house" in layer.name.lower()):
                for x, y, gid in layer:
                    if gid != 0:
                        '''
                        [TODO HACKATHON 4]
                        rects.append(pg.Rect(...))
                        Append the collision rectangle to the rects[] array
                        Remember scale the rectangle with the TILE_SIZE from settings
                        '''
                        rect = pg.Rect(
                            x * GameSettings.TILE_SIZE,
                            y * GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE  
                        )
                        rects.append(rect)
                        
        return rects

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        tp = [Teleport.from_dict(t) for t in data["teleport"]]
        pos = Position(data["player"]["x"] * GameSettings.TILE_SIZE, data["player"]["y"] * GameSettings.TILE_SIZE)
        return cls(data["path"], tp, pos)

    def to_dict(self):
        return {
            "path": self.path_name,
            "teleport": [t.to_dict() for t in self.teleporters],
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            }
        }
