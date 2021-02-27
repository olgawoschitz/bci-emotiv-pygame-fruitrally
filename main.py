import pygame
import logging
import random
import time

from cortex import CortexClient
from twisted.internet import reactor
from twisted.internet.task import Cooperator
from enum import Enum, IntEnum

from game_config import GameConfig

WHITE = (255, 255, 255)


class GameObjectManager:
    move_tracks = [94, 281, 469, 656]
    active_objects = []
    time_last_object = 0
    next_random_delay = 0
    current_object_to_recall = 0

    def __init__(self, max_objects=5):
        self.max_objects = max_objects

    def on_loop(self):
        time_passed = pygame.time.get_ticks() - self.time_last_object
        if time_passed > (1500 + self.next_random_delay):
            if len(self.active_objects) < self.max_objects:
                self.active_objects.append(self.generate_new_object())
                self.next_random_delay = random.randint(500, 1500)
                self.time_last_object = pygame.time.get_ticks()

    def generate_new_object(self):
        x_pos = random.choice(self.move_tracks)
        object_type = random.choice(list(GameObjectType))
        return GameObject(object_type, x_pos)

    def update(self, player, level_sequence):
        to_delete = []
        for obj in self.active_objects:
            obj.update()
            if pygame.sprite.collide_rect(player, obj):
                logging.info("Sprite collision with {0}".format(obj.object_type.name))
                logging.info("Sprite collision with TYPE {0}".format(obj.object_type))
                logging.info("CURRENT OBJ {0}".format(level_sequence[self.current_object_to_recall]))
                if obj.object_type == level_sequence[self.current_object_to_recall]:
                    logging.info("Sprite collision with {0}".format(obj.object_type.name))
                    pygame.mixer.Sound("magic-chime.wav").play()
                    self.current_object_to_recall = self.current_object_to_recall + 1
                else:
                    pygame.mixer.Sound("fail-buzzer.wav").play()
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
    def __init__(self, config):
        super(Player, self).__init__()
        self.config = config
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
        self.font = pygame.font.Font('verdana.ttf', 28)
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
        textRect = text.get_rect(center=(900, 100))
        surface.blit(text, textRect)


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


class SurfaceManager:
    def __init__(self, config):
        self.screen = pygame.display.set_mode((config.screen_width, config.screen_height))
        self.screen.fill((0, 0, 0))
        pygame.display.update()

    def set_game_background(self):
        game_surface = pygame.Surface((750, 750))
        background = pygame.image.load("img/background.png").convert(game_surface)
        self.screen.blit(background, (9, 9))

        game_status_surface = pygame.Surface((750, 250))
        game_status_background = pygame.image.load("img/game_status.png").convert(game_status_surface)
        self.screen.blit(game_status_background, (770, 9))
        self.draw_lines(background)
        pygame.display.update()

    def draw_lines(self, game_background):
        pygame.draw.line(game_background, WHITE, (187, 0), (187, 900),
                         3)  # line(surface, color, start_pos, end_pos, width) -> Rect
        pygame.draw.line(game_background, WHITE, (375, 0), (375, 900), 3)
        pygame.draw.line(game_background, WHITE, (562, 0), (562, 900), 3)
        pygame.display.update()

    def set_menu_background(self):
        menu_surface = pygame.Surface((0, 0))
        menu_background = pygame.image.load("img/background_menu.png").convert(menu_surface)
        self.screen.blit(menu_background, (0, 0))
        pygame.display.update()


class Game:
    running = False
    fps = 60
    SPEED = 1

    def __init__(self, config):
        self.config = config
        self.input_manager = InputManager(self.config)  # instance of InputManager
        self.clock = pygame.time.Clock()  # for fps and to calculate how long does the game is running
        self.surface = SurfaceManager(self.config)
        pygame.font.init()
        pygame.init()

    def start(self):
        pygame.display.set_caption("My game")  # set the title of the window
        object_manager = GameObjectManager()

        self.input_manager.init()  # non blocking operation
        running = True

        # game indicators - input_indicator and player - for future development
        input_indicator = InputIndicator()
        player = Player(self.config)

        game_objects = [GameObjectType(1), GameObjectType(2), GameObjectType(3),
                        GameObjectType(4), GameObjectType(5), GameObjectType(6)]
        level_sequence = random.sample(game_objects, 3)
        logging.info(
            "objects_to_remember {0}, {1}, {2},".format(level_sequence[0], level_sequence[1], level_sequence[2]))
        logging.info("game started")

        self.surface.set_menu_background()
        pygame.display.update()

        pygame.mixer.music.load("GameSong.wav")
        pygame.mixer.music.play(-1, fade_ms=1000)
        pygame.mixer.music.set_volume(0.5)
        start_menu = True

        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.input_manager.close()
                    running = False
            #logging.info("EVENT AND K_RIGHT: {0}, {1}".format(event.type, pygame.K_RIGHT))

            if event.type == 768 and start_menu:
                start_menu = False
                input_event = self.input_manager.on_loop(events)

                if input_event:
                    logging.info("event from input_manager: {0}".format(input_event))

                self.surface.screen.fill((0, 0, 0))
                self.surface.set_game_background()
                pygame.display.update()

                object_manager.on_loop()

                # update game objects
                input_indicator.update(input_event)
                player.update(input_event)
                object_manager.update(player, level_sequence)

                # render game objects
                input_indicator.render(self.surface.screen)
                player.render(self.surface.screen)
                object_manager.render(self.surface.screen)

                if object_manager.current_object_to_recall == 1:
                    # self.surface.screen.blit(self.surface.menu_background, (0, 0))

                    pygame.display.update()

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
