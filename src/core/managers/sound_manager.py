import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None      
        self.current_bgm_path = None
        
    def play_bgm(self, filepath: str):
        if self.current_bgm_path == filepath:
            return
        if self.current_bgm:
            self.current_bgm.stop()
            
        audio = load_sound(filepath)
        audio.set_volume(GameSettings.AUDIO_VOLUME)
        audio.play(-1)
        self.current_bgm = audio
        self.current_bgm_path = filepath
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=0.1):
        sound = load_sound(filepath)
        sound.set_volume(volume)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None
        
    def set_volume(self, volume):
        GameSettings.AUDIO_VOLUME = volume
        if self.current_bgm:
            self.current_bgm.set_volume(volume)
            
    def set_mute(self, mute: bool):
        

        if mute:
            self.previous_volume = GameSettings.AUDIO_VOLUME
            GameSettings.AUDIO_VOLUME = 0
            GameSettings.IS_MUTE = True
            self.set_volume(0)
        else:
            GameSettings.AUDIO_VOLUME =  getattr(self, 'previous_volume', 0.1)
            GameSettings.IS_MUTE = False
            self.set_volume(GameSettings.AUDIO_VOLUME)
        
        