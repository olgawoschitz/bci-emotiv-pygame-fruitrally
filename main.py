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

MIN_SIGNAL_WEIGHT = 0.8


class GameObjectManager:
    move_tracks = [94, 281, 469, 656]
    active_objects = []
    time_last_object = 0
    next_random_delay = 0
    sequence_counter = 0

    def __init__(self, expected_sequence, max_objects=5):
        self.expected_sequence = expected_sequence
        self.max_objects = max_objects

    def on_loop(self):
        time_passed = pygame.time.get_ticks() - self.time_last_object
        if time_passed > (1500 + self.next_random_delay):
            if len(self.active_objects) < self.max_objects:
                self.active_objects.append(self.generate_new_objext())
                self.next_random_delay = random.randint(500, 1500)
                self.time_last_object = pygame.time.get_ticks()

    def generate_new_objext(self):
        x_pos = random.choice(self.move_tracks)
        object_type = random.choice(list(GameObjectType))
        return GameObject(object_type, x_pos)

    def update(self, player):
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
            self.active_objects.remove(obj)

    def render(self, screen):
        for obj in self.active_objects:
            obj.render(screen)


class GameObjectType(IntEnum):
    APPLE = 1
    BANANA = 2
    GRAPES = 3
    LEMON = 4
    ORANGE = 5
    PINEAPPLE = 6


class GameObject(pygame.sprite.Sprite):
    images = [
        pygame.image.load("img/apple.png"),
        pygame.image.load("img/banana.png"),
        pygame.image.load("img/grapes.png"),
        pygame.image.load("img/lemon.png"),
        pygame.image.load("img/orange.png"),
        pygame.image.load("img/pineapple.png")
    ]

    def __init__(self, object_type, track_x):
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
        return self.rect.bottom > 770

    def update(self):
        self.rect.move_ip(0, 1.5)

    def render(self, surface):
        img = self.images[self.object_type - 1]
        surface.blit(img, self.rect)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super(Player, self).__init__()
        self.image = pygame.image.load("img/Shopping_Cart.png")
        self.surface = pygame.Surface((141, 107))  # width and length -> same as the image
        self.rect = self.surface.get_rect(
            center=(100, 660)
        )

    def update(self, input_event):
        if input_event:
            if input_event[1] > MIN_SIGNAL_WEIGHT:  # power of the signal is the minimum for acceptance
                if input_event[0] == Input.RIGHT:
                    self.rect.move_ip(190, 0)  # step size in pics
                elif input_event[0] == Input.LEFT:
                    self.rect.move_ip(-190, 0)
        # dealing with the frame and movements
        if self.rect.left < 30:
            self.rect.left = 30
        if self.rect.right > 740:
            self.rect.right = 740

    def render(self, surface):
        surface.blit(self.image, self.rect)


# overview about the signals on the screen
class InputIndicator:
    left = 0.0
    right = 0.0

    def __init__(self):
        self.font = pygame.font.Font('verdana.ttf', 14)

    def update(self, input_event):
        if input_event:
            self.left = 0.0
            self.right = 0.0

            if input_event[0] == Input.RIGHT:
                self.right = input_event[1]
            elif input_event[0] == Input.LEFT:
                self.left = input_event[1]

    def render(self, surface):
        max_length = 115
        width_right = max_length * self.right
        width_left = max_length * self.left
        x_left = 780 + (max_length - width_left)

        # left
        pygame.draw.rect(surface, LIGHT_GREY, (780, 50, 115, 50))
        pygame.draw.rect(surface, LIGHT_GREEN, (x_left, 50, width_left, 50))

        # right
        pygame.draw.rect(surface, LIGHT_GREY, (895, 50, 115, 50))
        pygame.draw.rect(surface, LIGHT_GREEN, (895, 50, width_right, 50))

        pygame.draw.rect(surface, BLACK, (780, 50, 230, 50), 3)
        pygame.draw.line(surface, BLACK, (895, 50), (895, 100), 3)

        limit_left = 895 - (max_length * MIN_SIGNAL_WEIGHT)
        limit_right = 895 + (max_length * MIN_SIGNAL_WEIGHT)
        pygame.draw.line(surface, ORANGE, (limit_left, 45), (limit_left, 105), 3)
        pygame.draw.line(surface, ORANGE, (limit_right, 45), (limit_right, 105), 3)

        text_left = self.font.render("Left", True, WHITE)
        text_right = self.font.render("Right", True, WHITE)

        surface.blit(text_left, text_left.get_rect(center=(800, 120)))
        surface.blit(text_right, text_left.get_rect(center=(980, 120)))


class ScoreIndicator:
    def __init__(self):
        self.font = pygame.font.Font('verdana.ttf', 30)
        self.timer_text = "00:00:00"
        self.matched_text = ""
        self.output_images = []

    def update(self, game_state):
        game_time = pygame.time.get_ticks() - game_state.time_game_started
        game_time += (game_state.penalties * 5000)

        self.timer_text = datetime.fromtimestamp(game_time / 1000).strftime('%M:%S')

        self.output_images = []
        for figure in game_state.matched_sequence:
            figure_numb = GameObjectType[figure.name]
            image = GameObject.images[figure_numb - 1]
            self.output_images.append(image)

    def render(self, surface):
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
    LEFT = 1
    RIGHT = 2


class InputManager:
    queued_inputs = []
    cortex_connection = None
    cortex_command_min_weight = 0.3
    cortex_compute_interval = 300
    cortex_time_last_compute = 0

    use_test_server = False

    def init(self):  # similar to client test to decide which server to use
        receiver = self  # define receiver as a pointer to InputManager  -> needs as an argument CortexClient
        if self.use_test_server:
            self.cortex_connection = CortexClient(UserCredentials.credentials, receiver, url="ws://localhost:8765")
        else:
            self.cortex_connection = CortexClient(UserCredentials.credentials, receiver)

    def on_receive_cortex_data(self, data):
        logging.debug("received cortex data: " + str(data))
        self.queued_inputs.append(data["com"])

    def compute_cortex_event(self):
        time_passed = pygame.time.get_ticks() - self.cortex_time_last_compute  # time passed in ms

        if time_passed < self.cortex_compute_interval:
            return None

        self.cortex_time_last_compute = pygame.time.get_ticks()  # set to current

        logging.debug("computing cortex event")

        if len(self.queued_inputs) > 0:  # error catching
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
        event = self.compute_cortex_event()
        if event:
            logging.debug("computed cortex event: {0}".format(event))
            return event

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                return Input.RIGHT, 1.0  # move and power of the signal (100% for keyboard)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                return Input.LEFT, 1.0
        return None


class GameScreen:
    def __init__(self):
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
        screen.blit(self.background, (9, 9))
        screen.blit(self.game_status_background, (770, 9))
        screen.blit(self.list_text, self.list_rect)
        screen.blit(self.counter_text, self.content_rect)
        screen.blit(self.power_of_signal_text, self.power_of_signal_rect)
        #self.draw_lines(self.background)

    def draw_lines(self, background):
        # line(surface, color, start_pos, end_pos, width) -> Rect
        pygame.draw.line(background, WHITE, (187, 0), (187, 900), 3)
        pygame.draw.line(background, WHITE, (375, 0), (375, 900), 3)
        pygame.draw.line(background, WHITE, (562, 0), (562, 900), 3)


class MenuScreen:
    current_page = 0
    is_countdown = False
    time_countdown_start = 0
    countdown_in_seconds = 5
    output_images = []
    command = ""
    power_of_signal = "Signal power:"
    score = ""

    def __init__(self):
        self.font_text = pygame.font.Font('verdana.ttf', 30)
        self.font_command = pygame.font.Font('verdana.ttf', 36)

        menu_surface = pygame.Surface((750, 750))
        menu_background = pygame.image.load("img/menu1.png").convert(menu_surface)
        self.background = menu_background
        game_status_surface = pygame.Surface((750, 250))
        self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)


    def update(self, input_event, game_state):
        if not self.is_countdown:
            if input_event:
                if input_event[1] > MIN_SIGNAL_WEIGHT:
                    if self.current_page == 1:
                        if input_event[0] == Input.LEFT:
                            self.current_page += 1
                    else:
                        if input_event[0] == Input.RIGHT:
                            self.current_page += 1

            if self.current_page == 1:
                menu_surface = pygame.Surface((750, 750))
                menu_background = pygame.image.load("img/menu2.png").convert(menu_surface)
                self.background = menu_background

                game_status_surface = pygame.Surface((750, 250))
                self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

            elif self.current_page == 2:
                menu2_surface = pygame.Surface((750, 750))
                menu2_background = pygame.image.load("img/menu3.png").convert(menu2_surface)
                self.background = menu2_background

                game_status_surface = pygame.Surface((750, 250))
                self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

                game_state.new_expected_sequence()

                self.is_countdown = True
                self.time_countdown_start = pygame.time.get_ticks()

        else:
            time_passed = pygame.time.get_ticks() - self.time_countdown_start
            seconds_left = int(self.countdown_in_seconds - (time_passed / 1000))

            self.output_images = []
            for figure in game_state.expected_sequence:
                image_pos = figure - 1
                image = GameObject.images[image_pos]
                self.output_images.append(image)

            self.command = "{0} seconds".format(seconds_left)

            if seconds_left <= 0:
                event = pygame.event.Event(START_GAME_EVENT)
                pygame.event.post(event)

    def on_end_game(self):
        self.current_page = 1
        self.is_countdown = False
        self.command = ""
        self.score = "Previous score:"
        self.output_images = []

    def render(self, screen):
        screen.blit(self.background, (9, 9))
        screen.blit(self.game_status_background, (770, 9))

        i = 250
        for img in self.output_images:
            surface = pygame.Surface((100, 100))
            rect = surface.get_rect(center=(350, i))
            screen.blit(img, rect)
            i = i + 100

        content_text = self.font_command.render(self.command, True, DARK_BLUE)
        content_rect = content_text.get_rect(center=(375, 575))
        screen.blit(content_text, content_rect)

        power_of_signal_text = self.font_text.render(self.power_of_signal, True, WHITE)
        power_of_signal_rect = power_of_signal_text.get_rect(center=(890, 25))
        screen.blit(power_of_signal_text, power_of_signal_rect)

        score_text = self.font_text.render(self.score, True, WHITE)
        score_rect = score_text.get_rect(center=(890, 500))
        screen.blit(score_text, score_rect)


class GameState:
    matched_sequence = []
    time_game_started = 0
    penalties = 0
    expected_sequence = []

    def on_start_game(self):
        self.time_game_started = pygame.time.get_ticks()
        self.penalties = 0
        self.matched_sequence = []

    def new_expected_sequence(self):
        self.expected_sequence = random.sample(list(GameObjectType), 3)
        logging.info("expected_sequence: {0}".format(self.expected_sequence))
        return self.expected_sequence

    def on_score_change(self, event):
        self.matched_sequence = event.matched_objects
        self.penalties += event.penalty


class Game:
    running = False
    fps = 60

    def __init__(self):
        self.input_manager = InputManager()  # instance of InputManager
        self.clock = pygame.time.Clock()  # for fps and to calculate how long does the game is running

    def start(self):
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

        while running:
            events = pygame.event.get()
            input_event = self.input_manager.on_loop(events)

            if not in_menu:
                object_manager.on_loop()

            if input_event:
                logging.info("event from input_manager: {0}".format(input_event))

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
                    menu_screen.on_end_game()
                    logging.info("game ended")

            # update
            input_indicator.update(input_event)

            if in_menu:
                menu_screen.update(input_event, game_state)
            else:
                score_indicator.update(game_state)
                player.update(input_event)
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

            yield  # for concurrency in coop  - yield sequence generator - "manual" decision for loop - 60 fps - 60 times

        reactor.stop()


def main():
    logging.basicConfig(level=logging.DEBUG)

    game = Game()
    coop = Cooperator()
    coop.coiterate(game.start())
    reactor.run()


if __name__ == "__main__":
    main()
