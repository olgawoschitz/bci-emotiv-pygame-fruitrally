from datetime import datetime

import pygame
import logging
import random

from cortex import CortexClient
from twisted.internet import reactor
from twisted.internet.task import Cooperator
from enum import Enum, IntEnum

from user_credentials import UserCredentials

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


class GameObjectManager:
    """
    Class to manage all objects in a game
    """
    move_tracks = [94, 281, 469, 656]
    active_objects = []
    time_last_object = 0
    next_random_delay = 0
    sequence_counter = 0

    def __init__(self, expected_sequence, max_objects=5):
        """
        Python method as a construct to initialize variables

        :param expected_sequence: list of generated objects on the shopping list
        :param max_objects: max number of objects on the screen on the same time
        """
        self.expected_sequence = expected_sequence
        self.max_objects = max_objects

    def on_loop(self):
        """
        Function that generates random objects to shown on the screen.

        """
        time_passed = pygame.time.get_ticks() - self.time_last_object
        if time_passed > (1500 + self.next_random_delay):
            if len(self.active_objects) < self.max_objects:
                self.active_objects.append(self.generate_new_object())
                self.next_random_delay = random.randint(500, 1500)
                self.time_last_object = pygame.time.get_ticks()

    def generate_new_object(self):
        """
        Object and position generator
        :return: GameObject with the new generated object and its position
        """
        x_pos = random.choice(self.move_tracks)
        object_type = random.choice(list(GameObjectType))
        return GameObject(object_type, x_pos)

    def update(self, player):
        """
        Function that updates objects on the screen and detect any collisions between an object and the player
        :param player: object of Player class
        """
        to_delete = []

        for obj in self.active_objects:
            obj.update()

            if pygame.sprite.collide_rect(player, obj):
                logging.info("Sprite collision with {0}".format(obj.object_type.name))
                logging.info("Expected object: {0}".format(self.expected_sequence[self.sequence_counter].name))

                penalty = 0
                if obj.object_type == self.expected_sequence[self.sequence_counter]:
                    pygame.mixer.Sound("sound/magic-chime.wav").play()
                    self.sequence_counter = self.sequence_counter + 1

                    if self.sequence_counter >= len(self.expected_sequence):
                        event = pygame.event.Event(END_GAME_EVENT)
                        pygame.event.post(event)
                else:
                    pygame.mixer.Sound("sound/fail-buzzer.wav").play()
                    penalty += 1
                event = pygame.event.Event(SCORE_CHANGE_EVENT, {
                    "penalty": penalty,
                    "matched_objects":  self.expected_sequence[:self.sequence_counter]
                })
                pygame.event.post(event)
                to_delete.append(obj)

            if obj.is_at_bottom():
                to_delete.append(obj)

        for obj in to_delete:
            if obj in self.active_objects:
                self.active_objects.remove(obj)

    def render(self, screen):
        """
        Function to render objects on the screen
        :param screen: game screen
        """
        for obj in self.active_objects:
            obj.render(screen)


class GameObjectType(IntEnum):
    """
    Class from generic enumeration.
    To define enumerations for game objects
    """
    APPLE = 1
    BANANA = 2
    GRAPES = 3
    LEMON = 4
    ORANGE = 5
    PINEAPPLE = 6


class GameObject(pygame.sprite.Sprite):
    """
    Class that defines and managed objects
    """
    images = [
        pygame.image.load("img/apple.png"),
        pygame.image.load("img/banana.png"),
        pygame.image.load("img/grapes.png"),
        pygame.image.load("img/lemon.png"),
        pygame.image.load("img/orange.png"),
        pygame.image.load("img/pineapple.png")
    ]

    def __init__(self, object_type, track_x):
        """
        Python method as a construct to initialize variables

        :param object_type: type of an object
        :param track_x: defines the position of an object
        """
        super(GameObject, self).__init__()
        self.object_type = object_type
        self.surface = pygame.Surface((96, 96))
        self.rect = self.surface.get_rect(
            center=(
                track_x,
                -100
            )
        )

    def is_at_bottom(self):
        """
        Function to check if object reached  bottom of the game screen
        :return: boolean (reached or not)
        """
        return self.rect.bottom > 770

    def update(self):
        """
        Defines the speed of an object
        """
        self.rect.move_ip(0, 1.5)

    def render(self, surface):
        """
        Render function for updating objects moves
        :param surface: main game background
        """
        img = self.images[self.object_type - 1]
        surface.blit(img, self.rect)


class Player(pygame.sprite.Sprite):
    """
    Class to manage and update player moves
    """
    time_last_move = 0

    def __init__(self):
        """
        Defines player
        """
        super(Player, self).__init__()
        self.image = pygame.image.load("img/Shopping_Cart.png")
        self.surface = pygame.Surface((141, 107))  # width and length -> same as the image
        self.rect = self.surface.get_rect(
            center=(100, 660)
        )

    def update(self, input_event, game_state):
        """
        Manage input signals and defines the move frame and steps
        :param input_event: current input
        :param game_state: current game state
        """
        time_passed = pygame.time.get_ticks() - self.time_last_move
        moved = False

        if time_passed > 1000:
            if input_event:
                if input_event[0] == Input.RIGHT and input_event[1] > game_state.min_signal_weight_right:
                    self.rect.move_ip(190, 0)
                    moved = True
                elif input_event[0] == Input.LEFT and input_event[1] > game_state.min_signal_weight_left:
                    self.rect.move_ip(-190, 0)
                    moved = True
            # dealing with the frame and movements
            if self.rect.left < 30:
                self.rect.left = 30
            if self.rect.right > 740:
                self.rect.right = 740

        if moved:
            self.time_last_move = pygame.time.get_ticks()

    def render(self, surface):
        """
        Render function for player move update
        :param surface: main game background
        """
        surface.blit(self.image, self.rect)


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
        self.font = pygame.font.Font('verdana.ttf', 14)

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


class ScoreIndicator:
    """
    Class to manage game score and update matched objects
    """
    def __init__(self):
        """
        Additional variables initialization
        """
        self.font = pygame.font.Font('verdana.ttf', 30)
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


class Input(Enum):
    """ Class from generic enumeration.
    To define enumerations for game moves
    """
    LEFT = 1
    RIGHT = 2


class InputManager:
    """
    Class to deal with any game inputs
    """
    queued_inputs = []
    cortex_connection = None
    cortex_command_min_weight = 0.1
    cortex_compute_interval = 300
    cortex_time_last_compute = 0

    use_test_server = False

    def init(self):
        """
        Function to initialize the connection
        """
        self.cortex_connection = CortexClient(UserCredentials.credentials, self)

    def on_receive_cortex_data(self, data):
        """
        Function for putting new received date from cortex in to the queue
        :param data: input message
        """
        logging.debug("received cortex data: " + str(data))
        self.queued_inputs.append(data["com"])

    def compute_cortex_event(self):
        """
        Function that helps dealing with input from cortex API by taking data from the queue and split the input into
        the power(weight) of the signal and the player move
        :return: tuple of the move and the weight of the signal
        """
        time_passed = pygame.time.get_ticks() - self.cortex_time_last_compute

        if time_passed < self.cortex_compute_interval:
            return None

        self.cortex_time_last_compute = pygame.time.get_ticks()

        logging.debug("computing cortex event")

        if len(self.queued_inputs) > 0:
            best_match = [None, 0]

            while len(self.queued_inputs) > 0:
                data = self.queued_inputs.pop()
                command, weight = data
                if weight > best_match[1]:
                    best_match = data
            if best_match[1] >= self.cortex_command_min_weight:
                command = best_match[0]
                if command == "left":
                    return Input.LEFT, best_match[1]
                elif command == "right":
                    return Input.RIGHT, best_match[1]
        return None

    def on_loop(self, events):
        """
        Function for updating moves
        :param events: pygame.event.get()
        :return: tuple of the move and the weight of the signal (move and power of the signal 100% for keyboard)
        """
        # Cortex data input
        event = self.compute_cortex_event()
        if event:
            logging.debug("computed cortex event: {0}".format(event))
            return event

        # Keyboard input (ignored if cortex data input exists )
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                return Input.RIGHT, 1.0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                return Input.LEFT, 1.0
        return None


class GameScreen:
    """
     Class for game screen management and visualisation
     """
    def __init__(self):
        """
        Initializes fonts, backgrounds and additional game info
        """
        self.font_text = pygame.font.Font('verdana.ttf', 30)

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
        self.font_text = pygame.font.Font('verdana.ttf', 30)
        self.font_command = pygame.font.Font('verdana.ttf', 36)
        self.font_title = pygame.font.Font('verdana.ttf', 40)

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


class GameState:
    """
    Class that contains all info about current game state
    """
    matched_sequence = []
    time_game_started = 0
    penalties = 0
    expected_sequence = []
    min_signal_weight_left = 0.65
    min_signal_weight_right = 0.65

    def on_start_game(self):
        """
        Function to initialize variables for the start of the game
        """
        self.time_game_started = pygame.time.get_ticks()
        self.penalties = 0
        self.matched_sequence = []

    def new_expected_sequence(self):
        """
        Function that create a new object sequence for the game (Shopping list)
        :return: An array with objects in a sequence
        """
        self.expected_sequence = random.sample(list(GameObjectType), 3)
        logging.info("expected_sequence: {0}".format(self.expected_sequence))
        return self.expected_sequence

    def on_score_change(self, event):
        """
        Update game state variables for later output
        :param event: pygame event
        """
        self.matched_sequence = event.matched_objects
        self.penalties += event.penalty

    def reset_signal_weight(self):
        self.min_signal_weight_left = 0.0
        self.min_signal_weight_right = 0.0

    def update_signal_weight(self, input_event, direction):
        if input_event:
            # use 30% less than maximum
            weight = input_event[1] - (input_event[1] * 0.3)
            if input_event[0] == Input.LEFT and direction == Input.LEFT and weight > self.min_signal_weight_left:
                self.min_signal_weight_left = weight
            if input_event[0] == Input.RIGHT and direction == Input.RIGHT and weight > self.min_signal_weight_right:
                self.min_signal_weight_right = weight


class Game:
    running = False
    fps = 60

    def __init__(self):
        """
        Instances InputManager class and sets up the game clock
        """
        self.input_manager = InputManager()  # instance of InputManager
        self.clock = pygame.time.Clock()  # for fps and to calculate how long does the game is running

    def start(self):
        """
        Main game loop function
        """
        pygame.init()
        pygame.font.init()

        pygame.display.set_caption("My game")  # set the title of the window

        screen = pygame.display.set_mode((1024, 768))

        game_screen = GameScreen()
        menu_screen = MenuScreen()

        self.input_manager.init()  # non blocking operation

        running = True
        in_menu = True

        input_indicator = InputIndicator()
        game_state = GameState()

        object_manager = None
        score_indicator = None
        player = None

        pygame.mixer.music.load("sound/GameSong.wav")
        pygame.mixer.music.play(-1, fade_ms=1000)
        pygame.mixer.music.set_volume(0.5)

        # main game loop
        while running:
            events = pygame.event.get()
            input_event = self.input_manager.on_loop(events)

            if not in_menu:
                object_manager.on_loop()

            if input_event:
                logging.info("event from input_manager: {0}".format(input_event))

            # dealing with inputs
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == START_GAME_EVENT:
                    game_state.on_start_game()

                    object_manager = GameObjectManager(game_state.expected_sequence)
                    score_indicator = ScoreIndicator()
                    player = Player()

                    in_menu = False
                    logging.info("game started")
                elif event.type == SCORE_CHANGE_EVENT:
                    game_state.on_score_change(event)
                elif event.type == END_GAME_EVENT:
                    in_menu = True
                    menu_screen.on_end_game(game_state)
                    logging.info("game ended")

            # update
            input_indicator.update(input_event, game_state)

            if in_menu:
                menu_screen.update(input_event, game_state)
            else:
                score_indicator.update(game_state)
                player.update(input_event, game_state)
                object_manager.update(player)

            # render
            screen.fill(BLACK)

            if in_menu:
                menu_screen.render(screen)
            else:
                game_screen.render(screen)
                score_indicator.render(screen)
                player.render(screen)
                object_manager.render(screen)

            input_indicator.render(screen)

            # game update
            pygame.display.update()
            # logging.debug("fps: {0}".format(self.clock.get_fps()))
            self.clock.tick(self.fps)

            yield  # yield sequence generator(for concurrency in coop) - "manual" decision for loop - 60 fps - 60 times

        reactor.stop()


def main():
    """
    Starter function

    """
    logging.basicConfig(level=logging.DEBUG)

    game = Game()
    coop = Cooperator()
    coop.coiterate(game.start())
    reactor.run()


if __name__ == "__main__":
    main()
