import json
import logging

from autobahn.twisted.websocket import WebSocketClientProtocol


class CortexClientProtocol(WebSocketClientProtocol):
    """
    Class for connection establishing and handling all requests and responses for cortex API
    """
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
        """
        Function for Debug mode
        """
        logging.debug("CortexClient - {0}".format(msg))

    def send_request(self, msg_id, method, params):
        """
        Function for creating a request body
        :param msg_id: current request id (update by respond)
        :param method: current method
        :param params: current parameters for request
        """
        request = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params
        }

        self.log_client("request: {0}".format(request))
        # twisted expects binary
        self.sendMessage(json.dumps(request).encode('utf8'))

    def onOpen(self):
        """
        Function for first request
        """
        self.log_client("connection established")
        self.send_request(self.ID_QUERY_HEADSET, "queryHeadsets", {})

    def onMessage(self, payload, isBinary):
        """
        Function for dealing with all communication between client and server(Emotiv) by using
        autobahn.websocket.interfaces.IWebSocketChannel.onMessage

        Implements steps (sequence) from Cortex API documentation to get to the data stream
         (https://emotiv.gitbook.io/cortex-api/overview-of-api-flow)
        :param payload: current message
        :param isBinary: boolean for check
        """
        decoded = payload.decode('utf8')
        self.log_client("response: {0}".format(decoded))
        response = json.loads(decoded)

        if not self.is_subscribed:

            if response["id"] == self.ID_QUERY_HEADSET:
                # connection established -> response: try to connect
                self.headset_id = response['result'][0]['id']
                self.send_request(self.ID_CONTROL_DEVICE, "controlDevice", {
                    "command": "connect",
                    "headset": self.headset_id
                })

            elif response["id"] == self.ID_CONTROL_DEVICE:
                # connected -> response: access
                self.send_request(self.ID_REQUEST_ACCESS, "requestAccess", {
                    "clientId": self.factory.credentials['client_id'],
                    "clientSecret": self.factory.credentials['client_secret']
                })

            elif response["id"] == self.ID_REQUEST_ACCESS:
                # accessed -> response: authorize
                self.send_request(self.ID_AUTHORIZE, "authorize", {
                    "clientId": self.factory.credentials['client_id'],
                    "clientSecret": self.factory.credentials['client_secret'],
                    "license": self.factory.credentials['license'],
                    "debit": self.factory.credentials['debit']
                })

            elif response["id"] == self.ID_AUTHORIZE:
                # authorize -> response: create new session
                self.auth_token = response['result']['cortexToken']
                self.send_request(self.ID_CREATE_SESSION, "createSession", {
                    "cortexToken": self.auth_token,
                    "headset": self.headset_id,
                    "status": "active"
                })

            elif response["id"] == self.ID_CREATE_SESSION:
                # created new session -> response: subscribe for "com" (mental commands)
                self.session_id = response['result']['id']
                self.send_request(self.ID_SUBSCRIBE, "subscribe", {
                    "cortexToken": self.auth_token,
                    "session": self.session_id,
                    "streams": ['com']
                })

            elif response["id"] == self.ID_SUBSCRIBE:
                # subscribed -> check data
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
            # subscribed -> get data
            self.factory.receiver.on_receive_cortex_data(response)

    def onClose(self, wasClean, code, reason):
        """
        Function for debug mode (autobahn.websocket.interfaces.IWebSocketChannel.onClose)
        """
        self.log_client("connection closed: {0}".format(reason))
