from __future__ import annotations
import pygame as pg
from typing import Optional, Callable, List, Dict
from .component import UIComponent
from src.core.services import input_manager
from src.utils import Logger


class ChatOverlay(UIComponent):
    """Lightweight chat UI similar to Minecraft: toggle with a key, type, press Enter to send."""
    is_open: bool
    _input_text: str
    _cursor_timer: float
    _cursor_visible: bool
    _just_opened: bool
    _send_callback: Callable[[str], bool] | None
    _get_messages: Callable[[int], list[dict]] | None
    _font_msg: pg.font.Font
    _font_input: pg.font.Font

    def __init__(
        self,
        send_callback: Callable[[str], bool] | None = None,
        get_messages: Callable[[int], list[dict]] | None = None,
        *,
        font_path: str = "assets/fonts/Minecraft.ttf"
    ) -> None:
        self.is_open = False
        self._input_text = ""
        self._cursor_timer = 0.0
        self._cursor_visible = True
        self._just_opened = False
        self._send_callback = send_callback
        self._get_messages = get_messages

        # Load fonts
        try:
            self._font_msg = pg.font.Font(font_path, 16)
            self._font_input = pg.font.Font(font_path, 18)
        except Exception:
            Logger.warning(f"Could not load font {font_path}, using system font")
            self._font_msg = pg.font.SysFont("monospace", 16)
            self._font_input = pg.font.SysFont("monospace", 18)

    def open(self) -> None:
        if not self.is_open:
            self.is_open = True
            self._cursor_timer = 0.0
            self._cursor_visible = True
            self._just_opened = True

    def close(self) -> None:
        self.is_open = False

    def _handle_typing(self) -> None:
        """Handle text input from keyboard"""
        # Check for shift key
        shift = input_manager.key_down(pg.K_LSHIFT) or input_manager.key_down(pg.K_RSHIFT)
        
        # Letters (a-z)
        for k in range(pg.K_a, pg.K_z + 1):
            if input_manager.key_pressed(k):
                ch = chr(ord('a') + (k - pg.K_a))
                self._input_text += (ch.upper() if shift else ch)
        
        # Numbers (0-9)
        for k in range(pg.K_0, pg.K_9 + 1):
            if input_manager.key_pressed(k):
                if shift:
                    # Shift + number gives symbols
                    symbols = ")!@#$%^&*("
                    self._input_text += symbols[k - pg.K_0]
                else:
                    self._input_text += chr(ord('0') + (k - pg.K_0))
        
        # Space
        if input_manager.key_pressed(pg.K_SPACE):
            self._input_text += " "
        
        # Backspace
        if input_manager.key_pressed(pg.K_BACKSPACE):
            if self._input_text:
                self._input_text = self._input_text[:-1]
        
        # Common punctuation
        punctuation_map = {
            pg.K_PERIOD: (".", ">"),
            pg.K_COMMA: (",", "<"),
            pg.K_SLASH: ("/", "?"),
            pg.K_SEMICOLON: (";", ":"),
            pg.K_QUOTE: ("'", '"'),
            pg.K_LEFTBRACKET: ("[", "{"),
            pg.K_RIGHTBRACKET: ("]", "}"),
            pg.K_BACKSLASH: ("\\", "|"),
            pg.K_MINUS: ("-", "_"),
            pg.K_EQUALS: ("=", "+"),
            pg.K_BACKQUOTE: ("`", "~"),
        }
        
        for key, (normal, shifted) in punctuation_map.items():
            if input_manager.key_pressed(key):
                self._input_text += (shifted if shift else normal)
        
        # Enter to send
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(pg.K_KP_ENTER):
            txt = self._input_text.strip()
            if txt and self._send_callback:
                ok = False
                try:
                    ok = self._send_callback(txt)
                except Exception as e:
                    Logger.error(f"Failed to send chat message: {e}")
                    ok = False
                if ok:
                    self._input_text = ""
                    Logger.info(f"Sent chat message: {txt}")

    def update(self, dt: float) -> None:
        if not self.is_open:
            return
        
        # Close on Escape
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.close()
            return
        
        # Typing
        if self._just_opened:
            self._just_opened = False
        else:
            self._handle_typing()
        
        # Cursor blink
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

    def draw(self, screen: pg.Surface) -> None:
        # Always draw recent messages faintly, even when closed
        msgs = self._get_messages(8) if self._get_messages else []
        sw, sh = screen.get_size()
        x = 10
        
        # Calculate sizes
        line_height = self._font_msg.get_height() + 4
        box_h = 28
        num_lines = min(len(msgs), 8)
        
        # Position everything from bottom up
        input_box_y = sh - box_h - 6
        messages_height = num_lines * line_height + 16
        messages_y = input_box_y - messages_height - 4
        
        # Draw background for messages
        if msgs:
            container_w = max(100, int((sw - 20) * 0.6))
            bg = pg.Surface((container_w, messages_height), pg.SRCALPHA)
            bg.fill((0, 0, 0, 90 if self.is_open else 60))
            screen.blit(bg, (x, messages_y))
            
            # Render last messages from top to bottom (oldest to newest)
            lines = list(msgs)[-8:]
            draw_y = messages_y + 8
            for m in lines:
                sender = str(m.get("from", ""))
                text = str(m.get("text", ""))
                surf = self._font_msg.render(f"Player {sender}: {text}", True, (255, 255, 255))
                screen.blit(surf, (x + 10, draw_y))
                draw_y += line_height
        
        # If not open, skip input field
        if not self.is_open:
            return
        
        # Input box
        box_w = max(100, int((sw - 20) * 0.6))
        
        # Background box
        bg2 = pg.Surface((box_w, box_h), pg.SRCALPHA)
        bg2.fill((0, 0, 0, 160))
        screen.blit(bg2, (x, input_box_y))
        
        # Render input text
        txt = self._input_text
        text_surf = self._font_input.render(txt, True, (255, 255, 255))
        screen.blit(text_surf, (x + 8, input_box_y + 4))
        
        # Caret (cursor)
        if self._cursor_visible:
            cx = x + 8 + text_surf.get_width() + 2
            cy = input_box_y + 6
            pg.draw.rect(screen, (255, 255, 255), pg.Rect(cx, cy, 2, box_h - 12))