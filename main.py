import pygame
import logging
import random

from cortex import CortexClient
from twisted.internet import reactor
from twisted.internet.task import Cooperator
from enum import Enum, IntEnum

from game_config import GameConfig

WHITE = (255, 255, 255)
LIGHT_GREY = (240, 240, 240)
DARK_BLUE = (14, 7, 112)

START_GAME_EVENT = pygame.USEREVENT + 1


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
                if obj.object_type == self.expected_sequence[self.sequence_counter]:
                    pygame.mixer.Sound("sound/magic-chime.wav").play()
                    self.sequence_counter = self.sequence_counter + 1
                else:
                    pygame.mixer.Sound("sound/fail-buzzer.wav").play()
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
            if input_event[1] > 0.8:  # power of the signal is the minimum for acceptance
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
    def __init__(self):
        self.font = pygame.font.Font('verdana.ttf', 30)
        self.text = "0% L | R 0%"  # output on the screen starter

    def update(self, input_event):
        left = 0.0
        right = 0.0

        if input_event:
            if input_event[0] == Input.RIGHT:
                right = input_event[1]
            elif input_event[0] == Input.LEFT:
                left = input_event[1]
            self.text = "{0}% L | R {1}%".format(round(left, 2), round(right, 2))  # update if input

    def render(self, surface):
        text = self.font.render(self.text, True, WHITE)
        text_rect = text.get_rect(center=(900, 100))
        surface.blit(text, text_rect)


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

    def __init__(self, config):
        self.config = config

    def init(self):  # similar to client test to decide which server to use
        receiver = self  # define receiver as a pointer to InputManager  -> needs as an argument CortexClient
        if self.use_test_server:
            self.cortex_connection = CortexClient(self.config.credentials, receiver, url="ws://localhost:8765")
        else:
            self.cortex_connection = CortexClient(self.config.credentials, receiver)

    def close(self):
        pass

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
        game_surface = pygame.Surface((750, 750))
        self.background = pygame.image.load("img/background.png").convert(game_surface)

        game_status_surface = pygame.Surface((750, 250))
        self.game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)

    def render(self, screen):
        screen.blit(self.background, (9, 9))
        screen.blit(self.game_status_background, (770, 9))
        self.draw_lines(self.background)

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
    title = ""
    command = ""
    text = ""
    item1 = ""
    item2 = ""
    item3 = ""


    def __init__(self):
        self.font_title = pygame.font.Font('verdana.ttf', 45)
        self.font_text = pygame.font.Font('verdana.ttf', 30)
        self.font_command = pygame.font.Font('verdana.ttf', 36)

        menu_surface = pygame.Surface((750, 750))
        menu_background = pygame.image.load("img/menu1.png").convert(menu_surface)
        menu_surface.fill((220, 220, 220))
        self.background = menu_background

    def update(self, input_event, expected_sequence):
        if not self.is_countdown:
            if input_event:
                if input_event[0] == Input.RIGHT:
                    self.current_page += 1

            if self.current_page == 1:
                menu_surface = pygame.Surface((750, 750))
                menu_background = pygame.image.load("img/menu2.png").convert(menu_surface)
                menu_surface.fill((220, 220, 220))
                self.background = menu_background

            elif self.current_page == 2:
                menu_surface = pygame.Surface((750, 750))
                menu_background = pygame.image.load("img/menu3.png").convert(menu_surface)
                menu_surface.fill((220, 220, 220))
                self.background = menu_background

                self.is_countdown = True
                self.time_countdown_start = pygame.time.get_ticks()
        else:
            time_passed = pygame.time.get_ticks() - self.time_countdown_start
            seconds_left = int(self.countdown_in_seconds - (time_passed / 1000))

            output = []
            for figure in expected_sequence:
                if GameObjectType(figure) == 1:
                    output.append("Apple")
                elif GameObjectType(figure) == 2:
                    output.append("Banana")
                elif GameObjectType(figure) == 3:
                    output.append("Grapes")
                elif GameObjectType(figure) == 4:
                    output.append("Lemon")
                elif GameObjectType(figure) == 5:
                    output.append("Orange")
                elif GameObjectType(figure) == 6:
                    output.append("Pineapple")

            self.item1 = "{0}".format(output[0])
            self.item2 = "{0}".format(output[1])
            self.item3 = "{0}".format(output[2])

            self.command = "{0} seconds".format(seconds_left)

            if seconds_left <= 0:
                event = pygame.event.Event(START_GAME_EVENT)
                pygame.event.post(event)

    def render(self, screen):
        screen.blit(self.background, (9, 9))

        title_text = self.font_title.render(self.title, True, WHITE)
        content_text = self.font_command.render(self.command, True, DARK_BLUE)
        text_text = self.font_text.render(self.text, True, LIGHT_GREY)

        item1_text = self.font_text.render(self.item1, True, DARK_BLUE)
        item2_text = self.font_text.render(self.item2, True, DARK_BLUE)
        item3_text = self.font_text.render(self.item3, True, DARK_BLUE)

        title_rect = title_text.get_rect(center=(250, 100))
        text_rect = text_text.get_rect(center=(375, 200))
        content_rect = content_text.get_rect(center=(375, 575))

        item1_rect = item1_text.get_rect(center=(500, 250))
        item2_rect = item2_text.get_rect(center=(500, 300))
        item3_rect = item3_text.get_rect(center=(500, 350))

        screen.blit(title_text, title_rect)
        screen.blit(content_text, content_rect)
        screen.blit(text_text, text_rect)

        screen.blit(item1_text, item1_rect)
        screen.blit(item2_text, item2_rect)
        screen.blit(item3_text, item3_rect)

class Game:
    running = False
    fps = 60
    SPEED = 1

    def __init__(self, config):
        self.config = config
        self.input_manager = InputManager(config)  # instance of InputManager
        self.clock = pygame.time.Clock()  # for fps and to calculate how long does the game is running

    def start(self):
        pygame.init()
        pygame.font.init()

        pygame.display.set_caption("My game")  # set the title of the window

        screen = pygame.display.set_mode((self.config.screen_width, self.config.screen_height))

        game_screen = GameScreen()
        menu_screen = MenuScreen()

        self.input_manager.init()  # non blocking operation

        running = True
        in_menu = True

        expected_sequence = random.sample(list(GameObjectType), 3)
        logging.info("expected_sequence: {0}".format(expected_sequence))

        object_manager = GameObjectManager(expected_sequence)
        input_indicator = InputIndicator()
        player = Player()

        logging.info("game started")

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
                    self.input_manager.close()
                    running = False
                if event.type == START_GAME_EVENT:
                    in_menu = False

            # update objects
            if in_menu:
                menu_screen.update(input_event, expected_sequence)
            else:
                input_indicator.update(input_event)
                player.update(input_event)
                object_manager.update(player)

            # render objects
            screen.fill((0, 0, 0))

            if in_menu:
                menu_screen.render(screen)
            else:
                game_screen.render(screen)
                input_indicator.render(screen)
                player.render(screen)
                object_manager.render(screen)

            # game update
            pygame.display.update()
            # logging.debug("fps: {0}".format(self.clock.get_fps()))
            self.clock.tick(self.fps)

            yield  # for concurrency in coop  - yield sequence generator - "manual" decision for loop - 60 fps - 60 times

        reactor.stop()


def main():
    logging.basicConfig(level=logging.DEBUG)

    config = GameConfig(1024, 768)
    game = Game(config)

    coop = Cooperator()
    coop.coiterate(game.start())
    reactor.run()


if __name__ == "__main__":
    main()