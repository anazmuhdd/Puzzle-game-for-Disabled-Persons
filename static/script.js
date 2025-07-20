// Get canvas and context and other page elements
const canvas = document.getElementById('game-board');
const context = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const gameOverElement = document.getElementById('game-over');
const playAgainButton = document.getElementById('play-again');
const trackerFeed = document.getElementById('head-tracker-feed');

// --- WebSocket connection setup ---
const socket = io();

socket.on('connect', () => {
    console.log('Successfully connected to Python server!');
});

// Listener to update the video feed image from the server
socket.on('video_feed', (data) => {
    trackerFeed.src = 'data:image/jpeg;base64,' + data.image;
});


// --- Game control logic that moves only ONCE per tilt ---
let lastAction = 'Center'; // Keep track of the last command

socket.on('control_command', (data) => {
    if (isGameOver) return;

    const newAction = data.action;

    // Only trigger a move if the state CHANGES from "Center" to a new state
    if (newAction !== 'Center' && lastAction === 'Center') {
        if (newAction === 'Tilted Left') {
            piece.x--;
            if (collides(piece, board)) {
                piece.x++; // Undo if it collides
            }
        } else if (newAction === 'Tilted Right') {
            piece.x++;
            if (collides(piece, board)) {
                piece.x--; // Undo if it collides
            }
        } else if (newAction === 'Tilted Up') {
            // This will rotate the piece
            rotate(piece);
        } else if (newAction === 'Tilted Down') {
            // This will drop the piece one step
            pieceDrop();
        }
    }
    
    // Always update the last action to the current action
    lastAction = newAction;
});


// --- Game Constants ---
const COLS = 10;
const ROWS = 20;
const BLOCK_SIZE = 30;

const COLORS = [ null, 'cyan', 'blue', 'orange', 'yellow', 'green', 'purple', 'red' ];
const SHAPES = [ [], [[1, 1, 1, 1]], [[2, 0, 0], [2, 2, 2]], [[0, 0, 3], [3, 3, 3]], [[4, 4], [4, 4]], [[0, 5, 5], [5, 5, 0]], [[0, 6, 0], [6, 6, 6]], [[7, 7, 0], [0, 7, 7]] ];

// --- Game State Variables ---
let board;
let piece;
let score;
let lastTime;
let dropCounter;
let dropInterval;
let isGameOver;


// --- Game Core Functions ---

function createBoard() {
    return Array.from({ length: ROWS }, () => Array(COLS).fill(0));
}

function createPiece() {
    const typeId = Math.floor(Math.random() * (SHAPES.length - 1)) + 1;
    const shape = SHAPES[typeId];
    return {
        shape,
        color: COLORS[typeId],
        x: Math.floor(COLS / 2) - Math.floor(shape[0].length / 2),
        y: 0
    };
}

function draw() {
    context.fillStyle = '#000';
    context.fillRect(0, 0, canvas.width, canvas.height);
    drawMatrix(board, { x: 0, y: 0 });
    drawMatrix(piece.shape, { x: piece.x, y: piece.y }, piece.color);
}

function drawMatrix(matrix, offset, color) {
    matrix.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value !== 0) {
                context.fillStyle = color || COLORS[value];
                context.fillRect((x + offset.x) * BLOCK_SIZE, (y + offset.y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
                context.strokeStyle = '#222';
                context.strokeRect((x + offset.x) * BLOCK_SIZE, (y + offset.y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
            }
        });
    });
}

function merge(piece, board) {
    piece.shape.forEach((row, y) => {
        row.forEach((value, x) => {
            if (value !== 0) {
                board[y + piece.y][x + piece.x] = value;
            }
        });
    });
}

function collides(piece, board) {
    for (let y = 0; y < piece.shape.length; y++) {
        for (let x = 0; x < piece.shape[y].length; x++) {
            if (piece.shape[y][x] !== 0 && (board[y + piece.y] && board[y + piece.y][x + piece.x]) !== 0) {
                return true;
            }
        }
    }
    return false;
}

function rotate(piece) {
    const matrix = piece.shape;
    const N = matrix.length;
    const M = matrix[0].length;
    const result = Array.from({ length: M }, () => Array(N).fill(0));
    for (let y = 0; y < N; y++) {
        for (let x = 0; x < M; x++) {
            result[x][N - 1 - y] = matrix[y][x];
        }
    }
    const originalX = piece.x;
    let offset = 1;
    piece.shape = result;
    while (collides(piece, board)) {
        piece.x += offset;
        offset = -(offset + (offset > 0 ? 1 : -1));
        if (offset > piece.shape[0].length) {
            rotate(piece); // Revert if it can't fit
            piece.x = originalX;
            return;
        }
    }
}

function clearLines() {
    let linesCleared = 0;
    outer: for (let y = ROWS - 1; y >= 0; y--) {
        for (let x = 0; x < COLS; x++) {
            if (board[y][x] === 0) {
                continue outer;
            }
        }
        const row = board.splice(y, 1)[0].fill(0);
        board.unshift(row);
        y++;
        linesCleared++;
    }
    if (linesCleared > 0) {
        score += linesCleared * 10;
        scoreElement.innerText = score;
    }
}

function pieceDrop() {
    piece.y++;
    if (collides(piece, board)) {
        piece.y--;
        merge(piece, board);
        clearLines();
        piece = createPiece();
        if (collides(piece, board)) {
            isGameOver = true;
            gameOverElement.classList.remove('hidden');
        }
    }
    dropCounter = 0;
}

function update(time = 0) {
    if (isGameOver) return;
    
    const deltaTime = time - lastTime;
    lastTime = time;
    
    dropCounter += deltaTime;
    if (dropCounter > dropInterval) {
        pieceDrop();
    }
    
    draw();
    requestAnimationFrame(update);
}

function resetGame() {
    isGameOver = false;
    gameOverElement.classList.add('hidden');
    board = createBoard();
    piece = createPiece();
    score = 0;
    scoreElement.innerText = score;
    dropInterval = 1000;
    lastTime = 0;
    dropCounter = 0;
    update();
}

// --- Event Listeners & Game Start ---
playAgainButton.addEventListener('click', () => {
    resetGame();
});

resetGame();