const preEverythingScreen = document.getElementById("preEverything")
const pregameScreen = document.getElementById("pregame")

let allScreens = [preEverythingScreen, pregameScreen]
showPreEverythingScreen() // as the default screen

function hideAllScreens(){
    for(let i=0; i<allScreens.length; i++){
        allScreens[i].classList.add("hidden")
    }
}
function unhideScreen(screenElement){
    screenElement.classList.remove("hidden")
}


function isHostUpdate(){
    let isHost = getPlayerIsHost()
    let startGameButton = document.getElementById("startGameButton")
    if(isHost){ startGameButton.classList.remove("hidden") }
    else{ startGameButton.classList.add("hidden") }
}

function showPreEverythingScreen(){
    hideAllScreens()
    unhideScreen(preEverythingScreen)
}

function showPregameScreen(){
    hideAllScreens()
    unhideScreen(pregameScreen)
}