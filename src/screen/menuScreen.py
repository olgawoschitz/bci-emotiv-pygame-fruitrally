from datetime import datetime
import pygame
from src.input import Input
from src.gameObject import GameObject

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 140, 0)
GREEN = (0, 128, 0)
LIGHT_GREEN = (50, 205, 50)
YELLOW = (255, 255, 0)
LIGHT_GREY = (240, 240, 240)
DARK_BLUE = (14, 7, 112)

START_GAME_EVENT = pygame.USEREVENT + 1
END_GAME_EVENT = pygame.USEREVENT + 2
SCORE_CHANGE_EVENT = pygame.USEREVENT + 3


class MenuScreen:
    """
    Class for menu screen management and visualisation
    """
    current_page = 0
    is_countdown = False
    is_collecting_signals = False
    direction_collecting_signal = None
    is_end_of_game = False
    time_countdown_start = 0
    time_page_shown = 0
    countdown_in_seconds = 0
    output_images = []
    command = ""
    power_of_signal = "Signal power:"
    score = ""
    score_time = ""

    def __init__(self):
        """
        Initializes fonts and backgrounds
        """
        self.font_text = pygame.font.Font('./font/verdana.ttf', 30)
        self.font_command = pygame.font.Font('./font/verdana.ttf', 36)
        self.font_title = pygame.font.Font('./font/verdana.ttf', 40)

        menu_surface = pygame.Surface((750, 750))
        menu_background = pygame.image.load("img/menu1.png").convert(menu_surface)
        self.background = menu_background
        game_status_surface = pygame.Surface((750, 250))
        self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

    def set_menu_page(self, page_number):
        self.time_page_shown = pygame.time.get_ticks()
        self.current_page = page_number

    def update(self, input_event, game_state):
        """
        Function that updates menu by managing inputs from the player based on the signal power
        :param input_event: type of the input
        :param game_state: current game state
        """
        if not self.is_countdown:
            time_passed = pygame.time.get_ticks() - self.time_page_shown

            # show every page at least 2 seconds
            if time_passed > 2000:
                if input_event and self.current_page != 1:
                    if self.current_page == 2:
                        if input_event[0] == Input.LEFT and input_event[1] > game_state.min_signal_weight_left:
                            self.set_menu_page(self.current_page + 1)
                    else:
                        if input_event[0] == Input.RIGHT and input_event[1] > game_state.min_signal_weight_right:
                            self.set_menu_page(self.current_page + 1)

            if self.current_page == 1:
                menu_surface = pygame.Surface((750, 750))
                menu_background = pygame.image.load("img/menu_focus.png").convert(menu_surface)
                self.background = menu_background

                game_status_surface = pygame.Surface((750, 250))
                self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

                game_state.reset_signal_weight()

                self.is_countdown = True
                self.is_collecting_signals = True
                self.direction_collecting_signal = Input.LEFT
                self.countdown_in_seconds = 15
                self.time_countdown_start = pygame.time.get_ticks()

            if self.current_page == 2:
                menu_surface = pygame.Surface((750, 750))
                menu_background = pygame.image.load("img/menu2.png").convert(menu_surface)
                self.background = menu_background

                game_status_surface = pygame.Surface((750, 250))
                self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

            elif self.current_page == 3:
                menu2_surface = pygame.Surface((750, 750))
                menu2_background = pygame.image.load("img/menu3.png").convert(menu2_surface)
                self.background = menu2_background

                game_status_surface = pygame.Surface((750, 250))
                self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

                game_state.new_expected_sequence()

                self.is_countdown = True
                self.countdown_in_seconds = 7
                self.time_countdown_start = pygame.time.get_ticks()

        else:
            time_passed = pygame.time.get_ticks() - self.time_countdown_start
            seconds_left = int(self.countdown_in_seconds - (time_passed / 1000))

            self.command = "{0} seconds".format(seconds_left)

            if self.is_collecting_signals:
                game_state.update_signal_weight(input_event, self.direction_collecting_signal)

                if seconds_left <= 0:
                    if self.direction_collecting_signal == Input.LEFT:
                        self.is_countdown = True
                        self.is_collecting_signals = True
                        self.direction_collecting_signal = Input.RIGHT
                        self.countdown_in_seconds = 15
                        self.time_countdown_start = pygame.time.get_ticks()
                    else:
                        self.is_countdown = False
                        self.is_collecting_signals = False
                        self.direction_collecting_signal = None
                        self.set_menu_page(self.current_page + 1)
                        self.command = ""
            else:
                self.output_images = []
                for figure in game_state.expected_sequence:
                    image_pos = figure - 1
                    image = GameObject.images[image_pos]
                    self.output_images.append(image)

                if seconds_left <= 0:
                    event = pygame.event.Event(START_GAME_EVENT)
                    pygame.event.post(event)

    def on_end_game(self, game_state):
        """
        Function to react on end of the game event
        :param game_state: current game state
        """
        self.set_menu_page(2)
        self.is_countdown = False
        self.is_end_of_game = True
        self.command = ""
        self.output_images = []

        self.score = "Previous score:"
        self.score_time = pygame.time.get_ticks() - game_state.time_game_started
        self.score_time += (game_state.penalties * 5000)
        self.score_time /= 1000

    def render(self, screen):
        """
        Render function for the background and information in menu
        :param screen: main game screen
        """
        screen.blit(self.background, (9, 9))
        screen.blit(self.game_status_background, (770, 9))

        i = 250
        for img in self.output_images:
            surface = pygame.Surface((100, 100))
            rect = surface.get_rect(center=(350, i))
            screen.blit(img, rect)
            i = i + 100

        content_text = self.font_command.render(self.command, True, WHITE)
        content_rect = content_text.get_rect(center=(375, 575))
        screen.blit(content_text, content_rect)

        if self.is_collecting_signals:
            calibration_text = self.font_title.render("On {0}".format(self.direction_collecting_signal.name), True, DARK_BLUE)
            calibration_rect = calibration_text.get_rect(center=(375, 355))
            screen.blit(calibration_text, calibration_rect)

        power_of_signal_text = self.font_text.render(self.power_of_signal, True, WHITE)
        power_of_signal_rect = power_of_signal_text.get_rect(center=(890, 25))
        screen.blit(power_of_signal_text, power_of_signal_rect)

        score_text = self.font_text.render(self.score, True, WHITE)
        score_rect = score_text.get_rect(center=(890, 500))
        screen.blit(score_text, score_rect)

        if self.is_end_of_game:
            score_time_text = datetime.fromtimestamp(self.score_time).strftime('%M:%S')
            text_timer = self.font_text.render(score_time_text, True, WHITE)
            text_rect_timer = text_timer.get_rect(center=(890, 550))
            screen.blit(text_timer, text_rect_timer)