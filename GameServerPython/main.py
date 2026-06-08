from __future__ import annotations
from simple_websocket_server import WebSocket, WebSocketServer

import random
import json


MAX_CONNECTIONS = 16

untakenColors = list(range(1,16+1))
clients: list[Client] = []

class Client():
    def __init__(self, address):
        self.address = address
        self.colorIndex = untakenColors.pop( random.randint(0, len(untakenColors)-1) )
    
    def getAddress(self): return self.address
    def getColorIndex(self): return self.colorIndex
    
    def getInitPackets(self) -> list[dict]:
        packets = []
        packets.append({
            "packetPurpose": "SetPlayerColor",
            "colorIndex": self.colorIndex
        })
        
        return packets
    def disconnectCleanup(self):
        untakenColors.append(self.colorIndex) # add our color index back into the pool

class GameServer(WebSocket):
    def connected(self):
        if len(clients) >= MAX_CONNECTIONS:
            disconnectPacket = {
                "packetPurpose": "disconnect",
                "reason": "Lobby is full!",
            }
            self.send_message( json.dumps(disconnectPacket) )
            self.close() # We are not accepting them, full lobby
        
        clientObject = Client(self.address)
        for packet in clientObject.getInitPackets(): self.send_message(json.dumps(packet))
        
        clients.append(clientObject)
        print(f"{self.address} connected!")
    
    def handle(self):
        # todo: when we receive the profile image they make we should go through each stroke and make sure it uses either -1 (black), -2 (white), or their color index, if not we'll fix it for them. to prevent them from using colors they shouldn't have
        print(f"Received `{self.data}`")
        self.send_message(f"Echo: {self.data}")
    
    def handle_close(self):
        print(f"{self.address} disconnected!")
        
        for i in range(0, len(clients)):
            if clients[i].getAddress() != self.address: continue
            clients[i].disconnectCleanup()
            clients.pop(i)
            print("\tRemoved client from list")
            break

server = WebSocketServer("0.0.0.0", 8080, GameServer)

print("Server running!")
server.serve_forever()
