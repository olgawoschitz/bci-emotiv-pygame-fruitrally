import pygame
from src.input import Input


class Player(pygame.sprite.Sprite):
    """
    Class to manage and update player moves (Shopping cart)
    """
    time_last_move = 0

    def __init__(self):
        """
        Function that defines a player and its frame
        """
        super(Player, self).__init__()
        self.image = pygame.image.load("img/Shopping_Cart.png")
        self.surface = pygame.Surface((141, 107))  # width and length -> same as the image
        self.rect = self.surface.get_rect(
            center=(100, 660)
        )

    def update(self, input_event, game_state):
        """
        Manage input signals, defines the move frame and steps
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
        Render function for move update
        :param surface: main game background
        """
        surface.blit(self.image, self.rect)
