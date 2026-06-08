const pregameCanvas = document.getElementById("makeCharacterCanvas")
const pregameCTX = pregameCanvas.getContext("2d")

const canvasDisplayWidth = pregameCanvas.clientWidth;
const canvasDisplayHeight = pregameCanvas.clientHeight;
pregameCanvas.width = canvasDisplayWidth;
pregameCanvas.height = canvasDisplayHeight;

//pregameCTX.fillStyle = "#000000" // default color is black

let allStrokes = []
let currentStroke = null

let isMouseDown = false
let isMarker = false

const BLACK_COLOR_INDEX = -1
const WHITE_COLOR_INDEX = -2
let currentColorIndex = BLACK_COLOR_INDEX;

class CanvasStroke{
    constructor(colorIndex, points, lineSize, isMarker){
        this.colorIndex = colorIndex
        this.points = points
        this.lineSize = lineSize
        this.isMarker = isMarker
    }
    isMarkerStroke(){ return this.isMarker }
    isEmpty(){ return this.points.length == 0 }
    addPoint(pos){
        this.points.push(pos)
    }
    setColor(canvasCTX){
        let colorToSet = ""
        if(this.colorIndex == BLACK_COLOR_INDEX){ colorToSet = "#000000" }
        else if(this.colorIndex == WHITE_COLOR_INDEX){ colorToSet = "#ffffff" }
        else{ colorToSet = getColorFromIndex(this.colorIndex) }
        canvasCTX.fillStyle = colorToSet
        canvasCTX.strokeStyle = colorToSet
    }
    drawStroke(canvasCTX){
        if(this.isEmpty()){ return }

        this.setColor(canvasCTX)

        for(let i=1; i<this.points.length; i++){
            let a = this.points[i-1]
            let b = this.points[i]

            let dist = distanceBetween(a, b)
            let angle = angleBetween(a, b)
            for (let i = 0; i < dist; i += 1) {
                let x = a[0] + (Math.sin(angle) * i) - (this.lineSize/2)
                let y = a[1] + (Math.cos(angle) * i) - (this.lineSize/2)

                canvasCTX.beginPath();
                canvasCTX.arc(x, y, this.lineSize, 0, 2*Math.PI);
                canvasCTX.fill()
            }
        }
    }
}

function getColorFromIndex(colorIndex){
    let root = document.documentElement
    let color = window.getComputedStyle(root).getPropertyValue(`--playerColor${colorIndex}`)
    return color
}

function pregameSetColor(ele){
    let classes = ele.classList
    for(let i=0; i<classes.length; i++){
        let c = classes[i]
        if(c == "whiteBG"){ currentColorIndex = WHITE_COLOR_INDEX; break }
        if(c == "blackBG"){ currentColorIndex = BLACK_COLOR_INDEX; break }
        if(c.startsWith("playerColor")){
            let indexStr = c.split("playerColor")[1].split("BG")[0]
            currentColorIndex = parseInt(indexStr)
            break
        }
    }
}

function distanceBetween (point1, point2) {
  return Math.sqrt(Math.pow(point2[0] - point1[0], 2) + Math.pow(point2[1] - point1[1], 2))
}
function angleBetween (point1, point2) {
  return Math.atan2(point2[0] - point1[0], point2[1] - point1[1])
}

function clearAndDrawStrokes(){
    // clear the entire canvas
    pregameCTX.fillStyle = "#ffffff"
    pregameCTX.fillRect(0, 0, pregameCanvas.width, pregameCanvas.height)

    // draw all marker strokes
    for(let i=0; i<allStrokes.length; i++){
        if(allStrokes[i].isMarkerStroke() == false){ continue; }
        allStrokes[i].drawStroke(pregameCTX)
    }

    // draw all pencil strokes
    for(let i=0; i<allStrokes.length; i++){
        if(allStrokes[i].isMarkerStroke() == true){ continue; }
        allStrokes[i].drawStroke(pregameCTX)
    }
}

function pregameUndoStroke(){
    allStrokes.pop()
    clearAndDrawStrokes()
}

pregameCanvas.addEventListener("mousedown", (e)=>{
    isMouseDown = true
    currentStroke = new CanvasStroke(currentColorIndex, [], isMarker ? 8 : 2, isMarker)
})
pregameCanvas.addEventListener("mouseup", (e)=>{
    isMouseDown = false

    if(currentStroke == null){ return; }
    if(currentStroke.isEmpty()){ currentStroke = null; return }
    
    allStrokes.push(currentStroke)
    currentStroke = null
    clearAndDrawStrokes();
})

pregameCanvas.addEventListener("mousemove", (e)=>{
    let rect = pregameCanvas.getBoundingClientRect()
    let canvasOffsetX = rect.left;
    let canvasOffsetY = rect.top;

    pos = [e.clientX - canvasOffsetX, e.clientY - canvasOffsetY]
    pos = [ Math.round(pos[0]), Math.round(pos[1]) ]
    if(!isMouseDown){ return }
    
    currentStroke.addPoint(pos)

    // push and pop it so it will draw how it will actually look. for ex if we draw using marker it will display under the pencil
    allStrokes.push(currentStroke)
    clearAndDrawStrokes();
    allStrokes.pop()
})

