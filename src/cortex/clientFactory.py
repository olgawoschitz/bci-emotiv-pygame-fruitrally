from autobahn.twisted.websocket import WebSocketClientFactory
from src.cortex.clientProtocol import CortexClientProtocol


class CortexClientFactory(WebSocketClientFactory):
    """
     Class for twisted client factory (Twisted-based WebSocket client factories) to combine additional parameters
     of the client with the receiver
    """
    # from WebSocketClientFactory protocol
    protocol = CortexClientProtocol

    def __init__(self, url, credentials, receiver):
        """
        Set up WebSocketClientFactory and init variables
        :param url: Cortex API url
        :param credentials: user credentials from user_credentials.py
        :param receiver: pointer to an InputManger class
        """
        WebSocketClientFactory.__init__(self, url)
        self.receiver = receiver
        self.credentials = credentials
