import json
import ssl
import logging

from autobahn.twisted.websocket import (
    WebSocketClientProtocol, WebSocketClientFactory, connectWS
)


class CortexClientProtocol(WebSocketClientProtocol):
    ID_QUERY_HEADSET = 1
    ID_CONTROL_DEVICE = 2
    ID_REQUEST_ACCESS = 3
    ID_AUTHORIZE = 4
    ID_CREATE_SESSION = 5
    ID_SUBSCRIBE = 6

    is_subscribed = False
    headset_id = None
    auth_token = None
    session_id = None

    @staticmethod
    def log_client(msg):
        logging.debug("CortexClient - {0}".format(msg))

    def send_request(self, id, method, params):
        request = {
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": params
        }

        self.log_client("request: {0}".format(request))
        self.sendMessage(json.dumps(request).encode('utf8')) # twisted expect binary

    def onOpen(self):
        self.log_client("connection established")
        self.send_request(self.ID_QUERY_HEADSET, "queryHeadsets", {})

    def onMessage(self, payload, isBinary):
        decoded = payload.decode('utf8')
        self.log_client("response: {0}".format(decoded))
        response = json.loads(decoded)

        if not self.is_subscribed:
            if response["id"] == self.ID_QUERY_HEADSET:
                self.headset_id = response['result'][0]['id']
                self.send_request(self.ID_CONTROL_DEVICE, "controlDevice", {
                    "command": "connect",
                    "headset": self.headset_id
                })
            elif response["id"] == self.ID_CONTROL_DEVICE:
                self.send_request(self.ID_REQUEST_ACCESS, "requestAccess", {
                    "clientId": self.factory.credentials['client_id'],
                    "clientSecret": self.factory.credentials['client_secret']
                })
            elif response["id"] == self.ID_REQUEST_ACCESS:
                self.send_request(self.ID_AUTHORIZE, "authorize", {
                    "clientId": self.factory.credentials['client_id'],
                    "clientSecret": self.factory.credentials['client_secret'],
                    "license": self.factory.credentials['license'],
                    "debit": self.factory.credentials['debit']
                })
            elif response["id"] == self.ID_AUTHORIZE:
                self.auth_token = response['result']['cortexToken']

                self.send_request(self.ID_CREATE_SESSION, "createSession", {
                    "cortexToken": self.auth_token,
                    "headset": self.headset_id,
                    "status": "active"
                })
            elif response["id"] == self.ID_CREATE_SESSION:
                self.session_id = response['result']['id']
                self.send_request(self.ID_SUBSCRIBE, "subscribe", {
                    "cortexToken": self.auth_token,
                    "session": self.session_id,
                    "streams": ['com']
                })
            elif response["id"] == self.ID_SUBSCRIBE:
                if len(response["result"]["success"]) > 0:
                    self.is_subscribed = True
                else:
                    # retry on failure
                    self.send_request(self.ID_SUBSCRIBE, "subscribe", {
                        "cortexToken": self.auth_token,
                        "session": self.session_id,
                        "streams": ['com']
                    })
        else:
            self.factory.receiver.on_receive_cortex_data(response)

    def onClose(self, wasClean, code, reason):
        self.log_client("connection closed: {0}".format(reason))


class CortexClientFactory(WebSocketClientFactory): # twisted client factory to combine additional parameters client with receiver
    protocol = CortexClientProtocol # from WebSocketClientFactory protocol

    def __init__(self, url, credentials, receiver):
        WebSocketClientFactory.__init__(self, url)
        self.receiver = receiver
        self.credentials = credentials


class CortexClient:
    def __init__(self, credentials, receiver, url="wss://localhost:6868"):
        factory = CortexClientFactory(url, credentials, receiver)
        connectWS(factory) # autom. if secure -> ssl if not -> tcp
