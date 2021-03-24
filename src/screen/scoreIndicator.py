import pygame

from datetime import datetime
from src.objectType import GameObjectType
from src.gameObject import GameObject

WHITE = (255, 255, 255)


class ScoreIndicator:
    """
    Class to manage game score and update matched objects
    """
    def __init__(self):
        """
        Additional variables initialization
        """
        self.font = pygame.font.Font('./font/verdana.ttf', 30)
        self.timer_text = "00:00:00"
        self.matched_text = ""
        self.output_images = []

    def update(self, game_state):
        """
        Function for updating game timer and matched figures
        :param game_state: current game state
        """
        game_time = pygame.time.get_ticks() - game_state.time_game_started
        game_time += (game_state.penalties * 5000)

        self.timer_text = datetime.fromtimestamp(game_time / 1000).strftime('%M:%S')

        self.output_images = []
        for figure in game_state.matched_sequence:
            figure_numb = GameObjectType[figure.name]
            image = GameObject.images[figure_numb - 1]
            self.output_images.append(image)

    def render(self, surface):
        """
        Render function for timer and matched objects
        :param surface: game status background
        """
        text_timer = self.font.render(self.timer_text, True, WHITE)
        text_rect_timer = text_timer.get_rect(center=(890, 550))
        surface.blit(text_timer, text_rect_timer)

        img_surface = pygame.Surface((100, 100))

        if len(self.output_images) == 1:
            rect1 = img_surface.get_rect(center=(900, 300))
            surface.blit(self.output_images[0], rect1)

        elif len(self.output_images) == 2:
            rect1 = img_surface.get_rect(center=(900, 300))
            rect2 = img_surface.get_rect(center=(900, 400))
            surface.blit(self.output_images[0], rect1)
            surface.blit(self.output_images[1], rect2)