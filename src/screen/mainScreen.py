import pygame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 140, 0)
GREEN = (0, 128, 0)
LIGHT_GREEN = (50, 205, 50)
YELLOW = (255, 255, 0)
LIGHT_GREY = (240, 240, 240)
DARK_BLUE = (14, 7, 112)

class GameScreen:
    """
     Class for game screen management and visualisation
     """
    def __init__(self):
        """
        Initializes fonts, backgrounds and additional game info
        """
        self.font_text = pygame.font.Font('./font/verdana.ttf', 30)

        game_surface = pygame.Surface((750, 750))
        self.background = pygame.image.load("img/background.png").convert(game_surface)

        game_status_surface = pygame.Surface((750, 250))
        self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

        self.list_text = self.font_text.render("Shopping list:", True, WHITE)
        self.list_rect = self.list_text.get_rect(center=(890, 200))

        self.counter_text = self.font_text.render("Game timer:", True, WHITE)
        self.content_rect = self.counter_text.get_rect(center=(890, 500))

        self.power_of_signal_text = self.font_text.render("Signal power:", True, WHITE)
        self.power_of_signal_rect = self.power_of_signal_text.get_rect(center=(890, 25))

    def render(self, screen):
        """
        Render function for the background and information on the game screen
        :param screen: main game screen
        """
        screen.blit(self.background, (9, 9))
        screen.blit(self.game_status_background, (770, 9))
        screen.blit(self.list_text, self.list_rect)
        screen.blit(self.counter_text, self.content_rect)
        screen.blit(self.power_of_signal_text, self.power_of_signal_rect)
        # for debugging
        self.draw_lines(self.background)

    def draw_lines(self, background):
        """
        Draw lines for equal split of the game screen
        Only for Debug mode
        :param background: game background
        """
        # line(surface, color, start_pos, end_pos, width) -> Rect
        pygame.draw.line(background, WHITE, (187, 0), (187, 900), 3)
        pygame.draw.line(background, WHITE, (375, 0), (375, 900), 3)
        pygame.draw.line(background, WHITE, (562, 0), (562, 900), 3)

