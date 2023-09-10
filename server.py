import socket
import time
import threading
import json
import urllib.request

hostname = socket.gethostname()
server_ip = socket.gethostbyname(hostname)


class SimpleSocket:

    def __init__(self, *, ip=server_ip, port=1, auto_convert=False, debug=True):
        self.server_socket = None

        self.clients = {}
        self.threads = []

        self.ip = ip
        self.port = port

        # Variables
        self.auto_convert = auto_convert

        if debug:
            self.print = print
        else:
            self.print = lambda *args: 0

    def init(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_socket.bind((self.ip, self.port))

        self.server_socket.listen(1)

        self.print(f"Server listening on {self.ip}:{self.port}, connect with public ipv4 {self.get_public_ip()}")

        # Start listening for client connections
        self.make_thread(target=self._listen_for_clients, daemon=True).join()

    # Private methods
    def _new_socket_callback(self, client_socket):
        pass

    def _data_receive_callback(self, client_socket, data):
        self.print(self.clients[client_socket][0], "sent data:", data)
        pass

    def _disconnect_callback(self, client_socket):
        self.print(self.clients.get(client_socket, "Client"), "disconnected")

    def _start_receiving(self, client_socket):
        while True:
            try:
                if not server.clients.get(client_socket):
                    break
                data = client_socket.recv(1024 * 20).decode()

                if data:

                    if self.auto_convert:
                        data = self.from_json(data)

                    if type(data) == list:
                        for data in data:
                            self._data_receive_callback(client_socket, data)
                    else:
                        self._data_receive_callback(client_socket, data)
            except ConnectionResetError:
                self._disconnect_callback(client_socket)
                self.clients.pop(client_socket)
                break

    def _listen_for_clients(self):
        while True:
            self.print("Waiting for client to connect")
            client_socket, client_address = self.server_socket.accept()
            self.print(f"Connected with {client_address[0]}:{client_address[1]}")
            self.clients[client_socket] = client_address
            self._new_socket_callback(client_socket)
            self.make_thread(target=self._start_receiving, daemon=True, args=(client_socket,))

    # Bind / Decorator functions
    def BindNewSocket(self, func):
        self._new_socket_callback = func

    def BindReceive(self, func):
        self._data_receive_callback = func

    def BindDisconnect(self, func):
        self._disconnect_callback = func

    # Public functions
    def from_json(self, json_string):
        json_string = json_string.split("}{")

        if len(json_string) > 1:
            for i in range(0, len(json_string), 1):
                json_string[i] = "{" + json_string[i] + "}"
            json_string[0] = json_string[0][1:]
            json_string[-1] = json_string[-1][0:-1]

        data = []

        for json_string in json_string:
            try:
                data.append(json.loads(json_string))
            except json.decoder.JSONDecodeError:
                self.print("Could not convert JSON:", json_string)

        return data if len(data) > 1 else data[0]

    def to_json(self, data):
        try:
            return json.dumps(data)
        except Exception as e:
            self.print("Exception in to_json :: Could not convert data:", data, "due to", e)

    def to_client(self, client_socket, data, convert=False):
        if convert or not isinstance(data, str):
            data = self.to_json(data)

        client_socket.send(data.encode())

    def all_clients(self, data, convert=False):
        if convert or not isinstance(data, str):
            data = self.to_json(data)

        for client_socket in self.clients.keys():
            try:
                if not client_socket or client_socket is None:
                    continue
                self.to_client(client_socket, data, convert=False)
            except Exception as e:
                print(f"Exception in all_clients :: {e}")
                pass

    def get_socket_from_address(self, client_address):
        try:
            return list(self.clients.keys())[list(self.clients.values()).index(client_address)]
        except Exception as e:
            self.print(f"Exception in get_socket_from_address :: {e}")
            return None

    def get_address_from_socket(self, client_socket):
        return self.clients.get(client_socket, None)

    def make_thread(self, *args, **kwargs):
        thread = threading.Thread(*args, **kwargs)
        self.threads.append(thread)
        thread.start()
        return thread

    @staticmethod
    def get_public_ip():
        external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')

        return external_ip


server = SimpleSocket(port=1, ip="localhost", auto_convert=True)

server.messageHistory = {}
server.channels = ["General", "Discussion"]
server.lastSent = {}
server.client_names = {}
server.attemptedBotting = {}

maxMessages = 40

for channel in server.channels:
    server.messageHistory[channel] = []


def new_socket(client_socket):
    username = client_socket.recv(1024 * 20).decode()

    if not (username and username != "" and 0 < len(username) <= 20 and username not in list(server.clients.values())):
        username = f"IP: {server.clients[client_socket]}"

    server.client_names[client_socket] = username

    print("New client!", username)

    print("Connected clients:")
    for username in server.client_names.values():
        print("\t", username)

    history_data = server.messageHistory
    history_data["members"] = []
    for member in server.client_names.values():
        history_data["members"].append(member)

    history_data["isMessageHistory"] = True

    server.to_client(client_socket, history_data, convert=True)

    data = {
        "sender": "SYSTEM",
        "systemMessage": True,
        "message": username + " joined the chat room",
        "channel": "General",
        "member": username,
        "joinEvent": True
    }
    server.all_clients(data, convert=True)
    server.messageHistory[data.get("channel", "General")].append(data)


def onMessage(client_socket, data):
    if not server.clients.get(client_socket):
        return
    if data.get("message"):
        data["systemMessage"] = False

        if len(data["message"]) > 200:
            return
        if time.time() - server.lastSent.get(client_socket, 0) < 0.3:
            server.lastSent[client_socket] = time.time() + 1
            return
        server.lastSent[client_socket] = time.time()

        print(f"{server.client_names[client_socket]}: {data['message']}")
        server.all_clients(data, convert=True)
        server.messageHistory[data.get("channel", "General")].append(data)
    elif data.get("Invisible") or data.get("Online"):
        if time.time() - server.lastSent.get(client_socket, 0) < 0.5:
            server.lastSent[client_socket] = time.time() + 2
            last = server.attemptedBotting.get(client_socket, 0)
            server.attemptedBotting[client_socket] = last + 1
            print(last)
            if last + 1 > 20:
                name = server.client_names.get(client_socket, "User")

                if server.clients.get(client_socket):
                    server.clients.pop(client_socket)
                if server.client_names.get(client_socket):
                    server.client_names.pop(client_socket)

                data = {
                    "sender": "SYSTEM",
                    "systemMessage": True,
                    "message": name + " was kicked from the chat room",
                    "channel": "General",
                    "member": name,
                    "`leaveEve`nt": True
                }
                server.all_clients(data, convert=True)

                client_socket.shutdown(1)

            return
        server.lastSent[client_socket] = time.time()

        is_invisible = data.get("Invisible", False)

        print(f"{server.client_names[client_socket]} is appearing", "Invisible" if is_invisible else "Online")

        if is_invisible:
            data = {
                "sender": "SYSTEM",
                "systemMessage": True,
                "message": server.client_names[client_socket] + " left the chat room",
                "channel": "General",
                "member": server.client_names[client_socket],
                "leaveEvent": True
            }
            server.all_clients(data, convert=True)
        else:
            data = {
                "sender": "SYSTEM",
                "systemMessage": True,
                "message": server.client_names[client_socket] + " joined the chat room",
                "channel": "General",
                "member": server.client_names[client_socket],
                "joinEvent": True
            }
            server.all_clients(data, convert=True)
    elif data.get("getMessageHistory"):
        history_data = {
            data.get("channel", "General"): server.messageHistory[data.get("channel", "General")],
            "members": [],
            "isMessageHistory": True
        }
        for member in server.client_names.values():
            history_data["members"].append(member)

        server.to_client(client_socket, history_data, convert=True)

        print("Resent history to", server.client_names[client_socket])
    elif data.get("deleteMessage") or data.get("editMessage"):
        modified_channel = data["channel"]
        message_number = data["messageNumber"]

        last_messages = server.messageHistory.get(modified_channel or "General")[-maxMessages:]

        if (
                last_messages[message_number]["sender"] == data.get("sender", "")
                and
                server.client_names.get(client_socket, "") == data.get("sender", "")
        ):
            full_history = server.messageHistory.get(modified_channel or "General")
            full_index = message_number + (len(full_history) - maxMessages if len(full_history) > maxMessages else 0)

            if data.get("deleteMessage"):
                server.messageHistory.get(modified_channel or "General").pop(full_index)
            else:
                edited_message = data.get("newMessage", "User edited message to nothing.") + " (edited)"
                server.messageHistory.get(modified_channel or "General")[full_index]["message"] = edited_message
                server.messageHistory.get(modified_channel or "General")[full_index]["edited"] = True

            server.all_clients(data)


def onDisconnect(client_socket):
    print(f"{server.clients[client_socket]} | {server.client_names[client_socket]} disconnected!")
    data = {
        "sender": "SYSTEM",
        "systemMessage": True,
        "message": server.client_names[client_socket] + " left the chat room",
        "channel": "General",
        "member": server.client_names[client_socket],
        "leaveEvent": True
    }
    server.all_clients(data, convert=True)
    server.client_names.pop(client_socket)
    server.messageHistory[data.get("channel", "General")].append(data)


server.BindNewSocket(new_socket)
server.BindReceive(onMessage)
server.BindDisconnect(onDisconnect)

server.init()
