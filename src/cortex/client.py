from autobahn.twisted.websocket import connectWS
from src.cortex.clientFactory import CortexClientFactory


class CortexClient:
    """
     Class for setting up the factory and init additional info for connection
    """

    def __init__(self, credentials, receiver, url="wss://localhost:6868"):
        """
        Factory initialisation
        :param credentials: user credentials from user_credentials.py
        :param receiver: pointer to an InputManger class
        :param url: Cortex API url
        """
        factory = CortexClientFactory(url, credentials, receiver)
        # if secure -> ssl, if not -> tcp
        connectWS(factory)
