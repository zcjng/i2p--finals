from pygame import Rect
from .settings import GameSettings
from dataclasses import dataclass
from enum import Enum
from typing import overload, TypedDict, Protocol

MouseBtn = int
Key = int

Direction = Enum('Direction', ['UP', 'DOWN', 'LEFT', 'RIGHT', 'NONE'])

@dataclass
class Position:
    x: float
    y: float
    
    def copy(self):
        return Position(self.x, self.y)
        
    def distance_to(self, other: "Position"):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        
@dataclass
class PositionCamera:
    x: int
    y: int
    
    def copy(self):
        return PositionCamera(self.x, self.y)
        
    def to_tuple(self):
        return (self.x, self.y)
        
    def transform_position(self, position: Position):
        return (int(position.x) - self.x, int(position.y) - self.y)
        
    def transform_position_as_position(self, position: Position):
        return Position(int(position.x) - self.x, int(position.y) - self.y)
        
    def transform_rect(self, rect: Rect):
        return Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)

@dataclass
class Teleport:
    pos: Position
    destination: str
    spawn_pos: Position | None = None
    
    @overload
    def __init__(self, x: int, y: int, destination: str, spawn_pos: Position = None): ...
    @overload
    def __init__(self, pos: Position, destination: str, spawn_pos: Position = None): ...

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], Position):
            self.pos = args[0]
            self.destination = args[1]
            self.spawn_pos = args[2] if len(args) > 2 else kwargs.get('spawn_pos', None)
        else:
            x, y, dest = args
            self.pos = Position(x, y)
            self.destination = dest
            self.spawn_pos = args[3] if len(args) > 3 else kwargs.get('spawn_pos', None)
    
    def to_dict(self):
        result = {
            "x": self.pos.x // GameSettings.TILE_SIZE,
            "y": self.pos.y // GameSettings.TILE_SIZE,
            "destination": self.destination
        }
        if self.spawn_pos:
            result["spawn_x"] = self.spawn_pos.x // GameSettings.TILE_SIZE
            result["spawn_y"] = self.spawn_pos.y // GameSettings.TILE_SIZE
        return result
    
    @classmethod
    def from_dict(cls, data: dict):

        print(f"DEBUG: Loading teleport from data: {data}")  # ADD THIS

        pos = Position(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE
        )
        
        spawn_pos = None
        if "spawn_x" in data and "spawn_y" in data:
            spawn_pos = Position(
                data["spawn_x"] * GameSettings.TILE_SIZE,
                data["spawn_y"] * GameSettings.TILE_SIZE
            )
            print(f"DEBUG: Created spawn_pos: ({spawn_pos.x}, {spawn_pos.y})")  # ADD THIS
        else:
            print(f"DEBUG: No spawn_x/spawn_y in data!")  # ADD THIS
        
        teleporter = cls(pos, data["destination"], spawn_pos)
        print(f"DEBUG: Teleporter spawn_pos after creation: {teleporter.spawn_pos}")  # ADD THIS
        return teleporter
class Monster(TypedDict):
    name: str
    hp: int
    max_hp: int
    level: int
    sprite_path: str
    battle_sprite: str

class Item(TypedDict):
    name: str
    count: int
    sprite_path: str
    
@dataclass
class PC:
    pos: Position
    name: str = "PC Storage"
    
    def to_dict(self):
        return {
            "x": self.pos.x // GameSettings.TILE_SIZE,
            "y": self.pos.y // GameSettings.TILE_SIZE,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            Position(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE),
            data.get("name", "PC Storage")
        )