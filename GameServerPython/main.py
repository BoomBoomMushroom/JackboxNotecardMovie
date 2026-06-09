from __future__ import annotations
from typing import Literal, get_args
from simple_websocket_server import WebSocket, WebSocketServer

import random
import json

_GameStates = Literal["PregameLobby", "PregameCountdown", "DrawNoteCards", "RecordScenes", "Voting", "GameFinished"]
_PromptType = Literal[
    "MostLeastQualified_PROFESSION", "Rookie_PROFESSION", "PoorlyDrawn_ANIMAL", "DrawSomeoneWearing__CLOTHING",
    
]
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

    def startDrawNoteCards(self):
        self.setCurrentGameState("DrawNoteCards")
        
        for i in range(0, self.getClientCount()):
            self.getClient(i).sendPacket(json.dumps({"packetPurpose": "GoToDrawNoteCardsScene"}))
        
        self.giveEachClientPrompts(2)

    def giveEachClientPrompts(self, numberOfPrompts=2):
        for i in range(0, self.getClientCount()):
            promptsPacket = {
                "packetPurpose": "DrawPrompts",
                "prompts": []
            }
            for _ in range(0, numberOfPrompts): promptsPacket["prompts"].append( self.generateNoteCardPrompt() )
            
            self.getClient(i).sendPacket( json.dumps(promptsPacket) )

    def generateNoteCardPrompt(self) -> str:
        # Okay so we must combine a few structures together
        usePromptType: _PromptType = random.choice(get_args(_PromptType))
        out = ""
        
        #usePromptType = "DrawSomeoneWearing__CLOTHING"
        
        if usePromptType == "MostLeastQualified_PROFESSION":
            with open("./lists/occupations.txt", "r") as f: professions = f.read().split("\n")
            adverb = random.choice(["most", "least"])
            profession: str = random.choice(professions).lower()
            out = f"The world's {adverb} qualified {profession}"
        
        elif usePromptType == "Rookie_PROFESSION":
            with open("./lists/occupations.txt", "r") as f: professions = f.read().split("\n")
            profession: str = random.choice(professions).lower()
            out = f"A {profession} on their first day"
        
        elif usePromptType == "PoorlyDrawn_ANIMAL":
            with open("./lists/animals.txt", "r") as f: animals = f.read().split("\n")
            animal: str = random.choice(animals).lower()
            out = f"A poorly drawn {animal}"
        
        elif usePromptType == "DrawSomeoneWearing__CLOTHING":
            with open("./lists/clothings.txt", "r") as f: clothes = f.read().split("\n")
            clothA: str = random.choice(clothes).lower()
            out = f"Someone wearing {clothA}"
        
        return out

class Client():
    def __init__(self, socket: GameServerWebsocket):
        self.socket: GameServerWebsocket = socket
        self.isHost: bool = False
        self.colorIndex: int = game.getRandomColor()
        
        self.characterDrawing: list[dict] = [] # Empty array of strokes
        self.soundBite: str = "" # Base64 audio clip
    
    def getSocket(self) -> GameServerWebsocket: return self.socket
    def getAddress(self): return self.socket.address
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
    
    def sendPacket(self, packet: str):
        self.getSocket().send_message(packet)
    
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
        
        # todo: make sure we cannot connect if we're not in the PregameLobby state unless we are reconnecting. Check via usernames
        
        clientObject = Client(self)
        if game.getClientCount() == 0: clientObject.setIsHost(True) # If they're the first to connect then make them the host
        for packet in clientObject.getInitPackets(): self.send_message(json.dumps(packet))
        
        game.addClient(clientObject)
        print(f"{self.address} connected!")
    
    def handlePacket_PregameLobby(self, data: dict, clientSentIndex: int, purpose: str):
        purpose = data["packetPurpose"]
        
        if purpose == "SendSoundBite":
            game.getClient(clientSentIndex).setSoundBite( data["audioBase64"] )
        elif purpose == "SendCharacterDrawing":
            game.getClient(clientSentIndex).setCharacterDrawing( data["drawingStrokes"] )
        elif purpose == "StartGame":
            if game.getClient(clientSentIndex).getIsHost() == False: return
            game.setCurrentGameState("PregameCountdown")
            # nothing much to do, the host client will send a follow up packet telling us when to start, since i dont want to thread a timer here
            # todo: Make sure we have at least 2 player or something
            # todo: on our gui server it should say the countdown starting now
        else:
            print(f"Unknown purpose! \"{purpose}\" in state PregameLobby")
    
    def handlePacket_PregameCountdown(self, data: dict, clientSentIndex: int, purpose: str):
        purpose = data["packetPurpose"]
        if purpose == "StartGameFollowUp":
            if game.getClient(clientSentIndex).getIsHost() == False: return
            
            print("Starting draw note cards...")
            game.startDrawNoteCards()
        elif purpose == "CancelStartGame":
            if game.getClient(clientSentIndex).getIsHost() == False: return
            game.setCurrentGameState("PregameLobby")
            # todo: make the gui server cancel the countdown
        else:
            print(f"Unknown purpose! \"{purpose}\" in state PregameCountdown")
    
    def handlePacket_DrawNoteCards(self, data: dict, clientSentIndex: int, purpose: str):
        purpose = data["packetPurpose"]
        if purpose == "PLACEHOLDER PURPOSE FOR LATER": pass
        else:
            print(f"Unknown purpose! \"{purpose}\" in state DrawNoteCards")
    
    def handle(self):
        # todo: when we receive the profile image they make we should go through each stroke and make sure it uses either -1 (black), -2 (white), or their color index, if not we'll fix it for them. to prevent them from using colors they shouldn't have
        
        try: data = json.loads(self.data)
        except:
            print(f"[!!!] Message received is not json! Received: '{self.data}'")
            return
        
        clientSentIndex: int = game.getClientIndexFromAddress(self.address)
        currentGameState: _GameStates = game.getCurrentGameState()
        
        purpose: str = data["packetPurpose"]
        if purpose == "PingKeepAlive": return
        
        if currentGameState == "PregameLobby":
            self.handlePacket_PregameLobby(data, clientSentIndex, purpose)
        elif currentGameState == "PregameCountdown":
            self.handlePacket_PregameCountdown(data, clientSentIndex, purpose)
        elif currentGameState == "DrawNoteCards":
            self.handlePacket_DrawNoteCards(data, clientSentIndex, purpose)
        else: print(f"Unhandled game state: {currentGameState}")
        
        
    
    def handle_close(self):
        print(f"{self.address} disconnected!")
        
        clientIndex = game.getClientIndexFromAddress(self.address)
        game.getClient(clientIndex).disconnectCleanup()
        game.removeClient(clientIndex)
        print("\tRemoved client from list")
        
        # this is only here to reset the lobby as im testing so i dont need to end the server and start it back up every time
        game.setCurrentGameState("PregameLobby")

server = WebSocketServer("0.0.0.0", 8080, GameServerWebsocket)

print("Server running!")
server.serve_forever()
