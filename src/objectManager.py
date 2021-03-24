from src.objectType import GameObjectType
from src.gameObject import GameObject

import pygame
import logging
import random

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
        Function that generates random game objects to shown on the screen.

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
                    "matched_objects": self.expected_sequence[:self.sequence_counter]
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
