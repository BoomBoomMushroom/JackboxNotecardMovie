from __future__ import annotations
from typing import Literal
from simple_websocket_server import WebSocket, WebSocketServer

import random
import json

_GameStates = Literal["PregameLobby", "DrawNoteCards", "RecordScenes", "Voting", "GameFinished"]
MAX_CONNECTIONS = 16

BLACK_COLOR_INDEX = -1
WHITE_COLOR_INDEX = -2

class Game():
    def __init__(self):
        self.currentGameState: _GameStates = "PregameLobby"
        self.untakenColors: list[int] = list(range(1,16+1))
        self.clients: list[Client] = []

    def getClientCount(self) -> int: return len(self.clients)
    def addClient(self, newClient: Client): self.clients.append(newClient)
    def removeClient(self, clientIndex: int): self.clients.pop(clientIndex)
    def getClient(self, index: int) -> Client: return self.clients[index]
    def getClientIndexFromAddress(self, address) -> int:
        for i in range(0, len(self.clients)):
            if self.getClient(i).getAddress() == address: return i
        return -1

    def getRandomColor(self) -> int: return self.untakenColors.pop( random.randint(0, len(self.untakenColors)-1) )
    def giveBackColorIndex(self, index: int): self.untakenColors.append(index)

    def getCurrentGameState(self) -> _GameStates: return self.currentGameState
    def setCurrentGameState(self, newState: _GameStates): self.currentGameState = newState

class Client():
    def __init__(self, address):
        self.address = address
        self.isHost = False
        self.colorIndex: int = game.getRandomColor()
        
        self.characterDrawing: list[dict] = [] # Empty array of strokes
        self.soundBite: str = "" # Base64 audio clip
    
    def getAddress(self): return self.address
    def getColorIndex(self) -> int: return self.colorIndex
    
    def setSoundBite(self, soundBiteBase64: str):
        self.soundBite = soundBiteBase64
        print(f"Got sound bite base64: {self.soundBite}")
    
    
    def setCharacterDrawing(self, data: list[dict]):
        """
        Each stroke is formatted like this:
        {
            "colorIndex": -1, -2, or the self.colorIndex,
            "points": list[int, int], (usually each int is 0-200) # maybe clamp each value later
            "lineSize": int, (typically 2 or 8)
            "isMarker": bool, (if true we draw it first and under the pencil) 
        }
        """
        
        for i in range(0, len(data)):
            colorIndex = data[i]["colorIndex"]
            if colorIndex != BLACK_COLOR_INDEX and colorIndex != WHITE_COLOR_INDEX and colorIndex != self.getColorIndex():
                data[i]["colorIndex"] = self.getColorIndex() # make sure we're using our color and not whatever color we feel like
        
        self.characterDrawing = data
    
    def setIsHost(self, isHost: bool): self.isHost = isHost
    def getIsHost(self) -> bool: return self.isHost
    
    
    def getInitPackets(self) -> list[dict]:
        packets = []
        packets.append({
            "packetPurpose": "SetPlayerColor",
            "colorIndex": self.getColorIndex()
        })
        packets.append({
            "packetPurpose": "SetHostStatus",
            "isHost": self.getIsHost()
        })
        
        return packets
    def disconnectCleanup(self):
        game.giveBackColorIndex( self.getColorIndex() ) # add our color index back into the pool


game: Game = Game()

class GameServerWebsocket(WebSocket):
    def connected(self):
        if game.getClientCount() >= MAX_CONNECTIONS:
            disconnectPacket = {
                "packetPurpose": "disconnect",
                "reason": "Lobby is full!",
            }
            self.send_message( json.dumps(disconnectPacket) )
            self.close() # We are not accepting them, full lobby
        
        clientObject = Client(self.address)
        if game.getClientCount() == 0: clientObject.setIsHost(True) # If they're the first to connect then make them the host
        for packet in clientObject.getInitPackets(): self.send_message(json.dumps(packet))
        
        game.addClient(clientObject)
        print(f"{self.address} connected!")
    
    def handle(self):
        # todo: when we receive the profile image they make we should go through each stroke and make sure it uses either -1 (black), -2 (white), or their color index, if not we'll fix it for them. to prevent them from using colors they shouldn't have
        
        try: data = json.loads(self.data)
        except:
            print(f"[!!!] Message received is not json! Received: '{self.data}'")
            return
        
        clientSentIndex: int = game.getClientIndexFromAddress(self.address)
        purpose = data["packetPurpose"]
        if purpose == "SendSoundBite":
            if game.getCurrentGameState() != "PregameLobby": return
            game.getClient(clientSentIndex).setSoundBite( data["audioBase64"] )
        elif purpose == "SendCharacterDrawing":
            if game.getCurrentGameState() != "PregameLobby": return
            game.getClient(clientSentIndex).setCharacterDrawing( data["drawingStrokes"] )
        elif purpose == "StartGame":
            if game.getCurrentGameState() != "PregameLobby": return
            # todo: Make sure we have at least 2 player or something
            
        elif purpose == "CancelStartGame":
            if game.getCurrentGameState() != "PregameLobby": return
            
        elif purpose == "PingKeepAlive":
            pass # Cool we got a ping, anyways...
        
        else:
            print(f"Unknown purpose! \"{purpose}\"")
        
    
    def handle_close(self):
        print(f"{self.address} disconnected!")
        
        clientIndex = game.getClientIndexFromAddress(self.address)
        game.getClient(clientIndex).disconnectCleanup()
        game.removeClient(clientIndex)
        print("\tRemoved client from list")

server = WebSocketServer("0.0.0.0", 8080, GameServerWebsocket)

print("Server running!")
server.serve_forever()
