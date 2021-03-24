from src.cortex.client import CortexClient
from user_credentials import UserCredentials
from src.input import Input

import pygame
import logging


class InputManager:
    """
    Class to deal with any game inputs (keyboard or BCI)
    """
    queued_inputs = []
    cortex_connection = None
    cortex_command_min_weight = 0.1
    cortex_compute_interval = 300
    cortex_time_last_compute = 0

    use_test_server = False

    def init(self):
        """
        Function to initialize the connection to cortex API
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
        Function for updating moves of a player
        :param events: pygame.event.get()
        :return: tuple of the move and the weight of the signal (for keyboard power of the signal 100%)
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
