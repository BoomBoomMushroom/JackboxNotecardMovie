const pregameCanvas = document.getElementById("makeCharacterCanvas")
const pregameCTX = pregameCanvas.getContext("2d")

const canvasDisplayWidth = pregameCanvas.clientWidth;
const canvasDisplayHeight = pregameCanvas.clientHeight;
pregameCanvas.width = canvasDisplayWidth;
pregameCanvas.height = canvasDisplayHeight;

pregameCTX.fillStyle = "#000000"
//pregameCTX.fillRect(0,0, 100, 100)

let isMouseDown = false

function pregameSetColor(ele){
    let color = window.getComputedStyle(ele).getPropertyValue("background-color");
    pregameCTX.fillStyle = color
    pregameCTX.strokeStyle = color
}

pregameCanvas.addEventListener("mousedown", (e)=>{ isMouseDown = true })
pregameCanvas.addEventListener("mouseup", (e)=>{ isMouseDown = false })

previousPos = [-1, -1]
pregameCanvas.addEventListener("mousemove", (e)=>{
    let rect = pregameCanvas.getBoundingClientRect()
    let canvasOffsetX = rect.left;
    let canvasOffsetY = rect.top;

    pos = [e.clientX - canvasOffsetX, e.clientY - canvasOffsetY]
    let missingLastPos = previousPos[0] == -1 && previousPos[1] == -1
    if(missingLastPos || !isMouseDown){
        previousPos = pos
        return
    }

    //pregameCTX.fillRect(pos[0]-1, pos[1]-1, 2, 2)

    pregameCTX.beginPath()
    pregameCTX.moveTo(previousPos[0], previousPos[1])
    pregameCTX.lineTo(pos[0], pos[1])
    pregameCTX.lineWidth = 2;
    pregameCTX.stroke()
    previousPos = pos
})

