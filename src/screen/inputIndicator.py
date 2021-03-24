import pygame
from src.input import Input

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 140, 0)
GREEN = (0, 128, 0)
LIGHT_GREEN = (50, 205, 50)
YELLOW = (255, 255, 0)
LIGHT_GREY = (240, 240, 240)
DARK_BLUE = (14, 7, 112)


class InputIndicator:
    """
    Class for signals power update and show
    """
    left = 0.0
    right = 0.0

    min_left = 0.8
    min_right = 0.8

    def __init__(self):
        """
        For Font initialization
        """
        self.font = pygame.font.Font('./font/verdana.ttf', 14)

    def update(self, input_event, game_state):
        """
        Function for updating and showing signals power on the game status
        :param input_event:
        :param game_state:
        """
        if input_event:
            self.left = 0.0
            self.right = 0.0

            if input_event[0] == Input.RIGHT:
                self.right = input_event[1]
            elif input_event[0] == Input.LEFT:
                self.left = input_event[1]

        if game_state.min_signal_weight_right != self.min_right:
            self.min_right = game_state.min_signal_weight_right
        if game_state.min_signal_weight_left != self.min_left:
            self.min_left = game_state.min_signal_weight_left

    def render(self, surface):
        """
        Render function for input indicator
        :param surface: game status background
        """
        max_length = 115
        width_right = max_length * self.right
        width_left = max_length * self.left
        x_left = 780 + (max_length - width_left)

        pygame.draw.rect(surface, LIGHT_GREY, (780, 50, 115, 50))
        pygame.draw.rect(surface, LIGHT_GREEN, (x_left, 50, width_left, 50))

        pygame.draw.rect(surface, LIGHT_GREY, (895, 50, 115, 50))
        pygame.draw.rect(surface, LIGHT_GREEN, (895, 50, width_right, 50))

        pygame.draw.rect(surface, BLACK, (780, 50, 230, 50), 3)
        pygame.draw.line(surface, BLACK, (895, 50), (895, 100), 3)

        limit_left = 895 - (max_length * self.min_left)
        limit_right = 895 + (max_length * self.min_right)
        pygame.draw.line(surface, ORANGE, (limit_left, 45), (limit_left, 105), 3)
        pygame.draw.line(surface, ORANGE, (limit_right, 45), (limit_right, 105), 3)

        text_left = self.font.render("Left", True, WHITE)
        text_right = self.font.render("Right", True, WHITE)

        surface.blit(text_left, text_left.get_rect(center=(800, 120)))
        surface.blit(text_right, text_left.get_rect(center=(980, 120)))