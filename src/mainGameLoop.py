import pygame
import logging

from src.screen.inputIndicator import InputIndicator
from src.objectManager import GameObjectManager
from src.screen.mainScreen import GameScreen
from src.gameState import GameState
from twisted.internet import reactor
from twisted.internet.task import Cooperator
from src.player import Player

from src.inputManager import InputManager
from src.screen.menuScreen import MenuScreen
from src.screen.scoreIndicator import ScoreIndicator

START_GAME_EVENT = pygame.USEREVENT + 1
END_GAME_EVENT = pygame.USEREVENT + 2
SCORE_CHANGE_EVENT = pygame.USEREVENT + 3

BLACK = (0, 0, 0)


class Game:
    # properties
    running = False
    fps = 60

    def __init__(self):
        """
        Instances InputManager class and sets up the game clock
        """
        self.input_manager = InputManager()
        # for fps and to calculate how long does the game is running
        self.clock = pygame.time.Clock()

    def start(self):
        """
        Main game loop function
        """
        pygame.init()
        pygame.font.init()

        # set the title of the window
        pygame.display.set_caption("Fruit Rally")

        screen = pygame.display.set_mode((1024, 768))

        game_screen = GameScreen()
        menu_screen = MenuScreen()
        # non blocking operation
        self.input_manager.init()

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
            self.clock.tick(self.fps)
            # yield sequence generator(for concurrency in coop)
            yield

        reactor.stop()


def main():
    """
    Starter function
    """
    logging.basicConfig(level=logging.DEBUG)

    game = Game()
    coop = Cooperator()
    # for control of game loop and ws connection -> yield (only for cooperator)
    coop.coiterate(game.start())
    # uses scheduler
    reactor.run()


if __name__ == "__main__":
    main()
