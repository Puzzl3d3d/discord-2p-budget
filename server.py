import socket
import time
import threading
import json
import urllib.request

hostname = socket.gethostname()
server_ip = socket.gethostbyname(hostname)

class simpleSocket:
    def __init__(self, *args, ip=server_ip, port=1, auto_convert=False, debug=True):
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

        self.print(f"Server listening on {self.ip}:{self.port}, connect with public ipv4 {self.getPublicIP()}")

        # Start listening for client connections
        self.makeThread(target=self._listenForClients, daemon=True).join()

    # Private methods
    def _onNewSocket(self, client_socket):
        pass
    def _onDataRecieve(self, client_socket, data):
        self.print(self.clients[client_socket][0],"sent data:",data)
        pass
    def _onDisconnect(self, client_socket):
        self.print(self.clients.get(client_socket, "Client"),"disconnected")
    def _startRecieving(self, client_socket):
        while True:
            try:
                if not server.clients.get(client_socket): break
                data = client_socket.recv(1024 * 20).decode()

                if data:

                    if self.auto_convert:
                        data = self.fromJSON(data)

                    if type(data) == list:
                        for data in data:
                            self._onDataRecieve(client_socket, data)
                    else:
                        self._onDataRecieve(client_socket, data)
            except ConnectionResetError:
                self._onDisconnect(client_socket)
                self.clients.pop(client_socket)
                break
    def _listenForClients(self):
            while True:
                self.print("Waiting for client to connect")
                client_socket, client_address = self.server_socket.accept()
                self.print(f"Connected with {client_address[0]}:{client_address[1]}")
                self.clients[client_socket] = client_address
                self._onNewSocket(client_socket)
                self.makeThread(target=self._startRecieving, daemon=True, args=(client_socket,))

    # Bind / Decorator functions
    def bindNewSocket(self, func):
        self._onNewSocket = func
    def bindRecieve(self, func):
        self._onDataRecieve = func
    def bindDisconnect(self, func):
        self._onDisconnect = func

    # Public functions
    def fromJSON(self, json_string):
        json_string = json_string.split("}{")
                
        if len(json_string) > 1:
            for i in range(0, len(json_string), 1):
                json_string[i] = "{"+json_string[i]+"}"
            json_string[0] = json_string[0][1:]
            json_string[-1] = json_string[-1][0:-1]

        data = []

        for json_string in json_string:
            try:
                data.append(json.loads(json_string))
            except json.decoder.JSONDecodeError:
                self.print("Could not convert JSON:",json_string)
        
        return data if len(data) > 1 else data[0]
    def toJSON(self, data):
        try:
            return json.dumps(data)
        except:
            self.print("Could not convert data:",data)
    def toClient(self, client_socket, data, convert=False):
        if convert or not isinstance(data, str):
            data = self.toJSON(data)
        
        client_socket.send(data.encode())
    def allClients(self, data, convert=False):
        if convert or not isinstance(data, str):
            data = self.toJSON(data)

        for client_socket in self.clients.keys():
            try:
                if not client_socket or client_socket == None: continue
                self.toClient(client_socket, data, convert=False)
            except:
                pass
    def getSocketFromAddress(self, client_address):
        try:
            return list(self.clients.keys())[list(self.clients.values()).index(client_address)]
        except:
            return None
    def getAddressFromSocket(self, client_socket):
        return self.clients.get(client_socket, None)
    def makeThread(self, *args, **kwargs):
        thread = threading.Thread(*args, **kwargs)
        self.threads.append(thread)
        thread.start()
        return thread
    def getPublicIP(self):
        external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
      
        return external_ip

server = simpleSocket(port=1, ip="localhost", auto_convert=True)

server.messageHistory = {}
server.channels = ["General", "Discussion"]
server.lastSent = {}
server.client_names = {}
server.attemptedBotting = {}

maxMessages = 40

for channel in server.channels:
    server.messageHistory[channel] = []

def newSocket(client_socket):
    username = client_socket.recv(1024 * 20).decode()

    if not (username and username != "" and 0 < len(username) <= 20 and username not in list(server.clients.values())):
        username = f"IP: {server.clients[client_socket]}"

    server.client_names[client_socket] = username

    print("New client!", username)
    
    print("Connected clients:")
    for username in server.client_names.values():
        print("\t",username)

    historyData = server.messageHistory
    historyData["members"] = []
    for member in server.client_names.values():
        historyData["members"].append(member)

    historyData["isMessageHistory"] = True

    server.toClient(client_socket, historyData, convert=True)

    data = {
        "sender": "SYSTEM",
        "systemMessage": True,
        "message": username+" joined the chat room",
        "channel": "General",
        "member": username,
        "joinEvent": True
    }
    server.allClients(data, convert=True)
    server.messageHistory[data.get("channel", "General")].append(data)
def onMessage(client_socket, data):
    if not server.clients.get(client_socket): return 
    if data.get("message"):
        data["systemMessage"] = False

        if len(data["message"]) > 200:
            return
        if time.time() - server.lastSent.get(client_socket, 0) < 0.3:
            server.lastSent[client_socket] = time.time() + 1
            return
        server.lastSent[client_socket] = time.time()

        print(f"{server.client_names[client_socket]}: {data['message']}")
        server.allClients(data, convert=True)
        server.messageHistory[data.get("channel", "General")].append(data)
    elif data.get("Invisible") or data.get("Online"):
        if time.time() - server.lastSent.get(client_socket, 0) < 0.5:
            server.lastSent[client_socket] = time.time() + 2
            last = server.attemptedBotting.get(client_socket, 0)
            server.attemptedBotting[client_socket] = last + 1
            print(last)
            if last+1 > 20:
                name = server.client_names.get(client_socket, "User")

                if server.clients.get(client_socket): server.clients.pop(client_socket)
                if server.client_names.get(client_socket): server.client_names.pop(client_socket)

                data = {
                    "sender": "SYSTEM",
                    "systemMessage": True,
                    "message": name+" was kicked from the chat room",
                    "channel": "General",
                    "member": name,
                    "`leaveEve`nt": True
                }
                server.allClients(data, convert=True)

                client_socket.shutdown(1)

            return
        server.lastSent[client_socket] = time.time()

        isInvisible = data.get("Invisible", False)

        print(f"{server.client_names[client_socket]} is appearing", "Invisible" if isInvisible else "Online")

        if isInvisible:
            data = {
                "sender": "SYSTEM",
                "systemMessage": True,
                "message": server.client_names[client_socket]+" left the chat room",
                "channel": "General",
                "member": server.client_names[client_socket],
                "leaveEvent": True
            }
            server.allClients(data, convert=True)
        else:
            data = {
                "sender": "SYSTEM",
                "systemMessage": True,
                "message": server.client_names[client_socket]+" joined the chat room",
                "channel": "General",
                "member": server.client_names[client_socket],
                "joinEvent": True
            }
            server.allClients(data, convert=True)
    elif data.get("getMessageHistory"):
        historyData = {data.get("channel", "General"): server.messageHistory[data.get("channel", "General")]}
        historyData["members"] = []
        for member in server.client_names.values():
            historyData["members"].append(member)

        historyData["isMessageHistory"] = True

        server.toClient(client_socket, historyData, convert=True)

        print("Resent history to", server.client_names[client_socket])
    elif data.get("deleteMessage") or data.get("editMessage"):
        channel = data["channel"]
        messageNumber = data["messageNumber"]

        lastMessages = server.messageHistory.get(channel or "General")[-maxMessages:]

        if lastMessages[messageNumber]["sender"] == data.get("sender", "") and server.client_names.get(client_socket, "") == data.get("sender", ""):
            fullHistory = server.messageHistory.get(channel or "General")
            fullIndex = messageNumber + (len(fullHistory)-maxMessages if len(fullHistory) > maxMessages else 0)

            if data.get("deleteMessage"):
                print(fullIndex)
                server.messageHistory.get(channel or "General").pop(fullIndex)
            else:
                server.messageHistory.get(channel or "General")[fullIndex]["message"] = data.get("newMessage", "User edited message to nothing.") + " (edited)"
                server.messageHistory.get(channel or "General")[fullIndex]["edited"] = True
                print(lastMessages[messageNumber])

            server.allClients(data)

def onDisconnect(client_socket):
    print(f"{server.clients[client_socket]} | {server.client_names[client_socket]} disconnected!")
    data = {
        "sender": "SYSTEM",
        "systemMessage": True,
        "message": server.client_names[client_socket]+" left the chat room",
        "channel": "General",
        "member": server.client_names[client_socket],
        "leaveEvent": True
    }
    server.allClients(data, convert=True)
    server.client_names.pop(client_socket)
    server.messageHistory[data.get("channel", "General")].append(data)
    
server.bindNewSocket(newSocket)
server.bindRecieve(onMessage)
server.bindDisconnect(onDisconnect)

server.init()
