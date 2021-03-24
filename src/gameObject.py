import pygame


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
