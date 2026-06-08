let myPlayerColorIndex = -1;
let playerColorTags = [
    "playerColor1BG","playerColor2BG","playerColor3BG","playerColor4BG","playerColor5BG","playerColor6BG",
    "playerColor7BG","playerColor8BG","playerColor9BG","playerColor10BG","playerColor11BG","playerColor12BG",
    "playerColor13BG","playerColor14BG","playerColor15BG","playerColor16BG",
]
let isHost = false

function getPlayerColorIndex(){ return myPlayerColorIndex }
function setPlayerColorIndex(index) {
    myPlayerColorIndex = index
    let elements = document.getElementsByClassName("makeMyColorBG")
    for(let i=0; i<elements.length; i++){
        let e = elements[i]
        for(let j=0; j<playerColorTags.length; j++){
            e.classList.remove(playerColorTags[j])
        }
        e.classList.add([playerColorTags[index-1]])
    }
}

function getPlayerIsHost(){ return isHost }
function setPlayerIsHost(areWeNowHost){
    // note this doesn't update it server side so we cannot elevate our privileges via this
    isHost = areWeNowHost
    isHostUpdate()
}

