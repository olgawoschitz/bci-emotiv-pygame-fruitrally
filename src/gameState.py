import pygame
import logging
import random

from src.objectType import GameObjectType
from src.input import Input


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
        """
        Reset weight of signals
        """
        self.min_signal_weight_left = 0.0
        self.min_signal_weight_right = 0.0

    def update_signal_weight(self, input_event, direction):
        """
        Function that specified the min. signal weight for playing the game
        :param input_event: received signal
        :param direction: signal input direction
        """
        if input_event:
            # use 30% less than maximum
            weight = input_event[1] - (input_event[1] * 0.3)
            if input_event[0] == Input.LEFT and direction == Input.LEFT and weight > self.min_signal_weight_left:
                self.min_signal_weight_left = weight
            if input_event[0] == Input.RIGHT and direction == Input.RIGHT and weight > self.min_signal_weight_right:
                self.min_signal_weight_right = weight
