const wsURI = "ws://127.0.0.1:8080"
const websocket = new WebSocket(wsURI)
let pingFrequencyMs = 5000
let pingInterval = null
let pingNumberCount = 0

function sendMessage(data){
    websocket.send(data)
}

function handleReceiveMessage(data){
    //console.log(`RECEIVED: "${e.data}"`);
    try{ data = JSON.parse(data) }
    catch{
        console.log(`[!!!] Data received is not JSON!`)
        console.log(data)
        return
    }

    let packetPurpose = data["packetPurpose"]
    switch(packetPurpose){
        case "SetPlayerColor":
            setPlayerColorIndex( data["colorIndex"] )
            return
        default:
            console.log(`Unknown packet purpose! "${packetPurpose}"`)
            return
    }

    console.log(data)

}

websocket.addEventListener("open", () => {
    console.log("Connected to server!")

    showPregameScreen() // we have connected to our lobby, show the pregame lobby screen
    // set up a ping keep alive
    pingInterval = setInterval(() => {
        pingNumberCount++
        pingJson = {
            "packetPurpose": "PingKeepAlive",
            "data": `Ping ${pingNumberCount}`
        }
        sendMessage(JSON.stringify(pingJson))
    }, pingFrequencyMs);
});

websocket.addEventListener("message", (e) => {
    handleReceiveMessage(e.data)
});

websocket.addEventListener("error", (e) => {
    console.error(`Error: ${e}`);
});