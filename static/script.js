// Get canvas and context and other page elements
const canvas = document.getElementById("game-board");
const context = canvas.getContext("2d");
const scoreElement = document.getElementById("score");
const gameOverElement = document.getElementById("game-over");
const playAgainButton = document.getElementById("play-again");
const trackerFeed = document.getElementById("head-tracker-feed");

// --- NEW: Get the modal and start button elements ---
const startupModal = document.getElementById("startup-modal");
const startButton = document.getElementById("start-game-button");

// --- WebSocket connection setup ---
const socket = io();
socket.on("connect", () => {
  console.log("Successfully connected to Python server!");
});
socket.on("video_feed", (data) => {
  trackerFeed.src = "data:image/jpeg;base64," + data.image;
});

// --- Head Movement Control Logic ---
let lastHeadAction = "Center";
socket.on("control_command", (data) => {
  if (isGameOver) return;
  const newAction = data.action;
  if (newAction !== "Center" && lastHeadAction === "Center") {
    if (newAction === "Tilted Left") {
      piece.x--;
      if (collides(piece, board)) piece.x++;
    } else if (newAction === "Tilted Right") {
      piece.x++;
      if (collides(piece, board)) piece.x--;
    } else if (newAction === "Tilted Up") {
      rotate(piece);
    } else if (newAction === "Tilted Down") {
      pieceDrop();
    }
  }
  lastHeadAction = newAction;
});

// --- Voice Command Control Logic with Cooldown ---
let canProcessVoice = true;
const voiceCooldown = 500;

socket.on("voice_command", (data) => {
  if (isGameOver || !canProcessVoice) return;
  const command = data.command.trim();
  console.log("Voice command received:", command);
  let commandProcessed = false;
  if (command === "left") {
    piece.x--;
    if (collides(piece, board)) piece.x++;
    commandProcessed = true;
  } else if (command === "right") {
    piece.x++;
    if (collides(piece, board)) piece.x--;
    commandProcessed = true;
  } else if (command === "rotate" || command === "up") {
    rotate(piece);
    commandProcessed = true;
  } else if (command === "drop" || command === "down") {
    pieceDrop();
    commandProcessed = true;
  }
  if (commandProcessed) {
    canProcessVoice = false;
    setTimeout(() => {
      canProcessVoice = true;
    }, voiceCooldown);
  }
});

// --- Game Constants & Logic (This section is unchanged) ---
const COLS = 10,
  ROWS = 20,
  BLOCK_SIZE = 30;
const COLORS = [
  null,
  "cyan",
  "blue",
  "orange",
  "yellow",
  "green",
  "purple",
  "red",
];
const SHAPES = [
  [],
  [[1, 1, 1, 1]],
  [
    [2, 0, 0],
    [2, 2, 2],
  ],
  [
    [0, 0, 3],
    [3, 3, 3],
  ],
  [
    [4, 4],
    [4, 4],
  ],
  [
    [0, 5, 5],
    [5, 5, 0],
  ],
  [
    [0, 6, 0],
    [6, 6, 6],
  ],
  [
    [7, 7, 0],
    [0, 7, 7],
  ],
];
const PIECE_SEQUENCE = [1, 4, 2, 3, 5, 7, 6];
let pieceSequenceIndex = 0;
let board, piece, score, lastTime, dropCounter, dropInterval, isGameOver;
function createPiece() {
  const typeId = PIECE_SEQUENCE[pieceSequenceIndex];
  pieceSequenceIndex = (pieceSequenceIndex + 1) % PIECE_SEQUENCE.length;
  const shape = SHAPES[typeId];
  return {
    shape,
    color: COLORS[typeId],
    x: Math.floor(COLS / 2) - Math.floor(shape[0].length / 2),
    y: 0,
  };
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
      gameOverElement.classList.remove("hidden");
    }
  }
  dropCounter = 0;
}
function resetGame() {
  isGameOver = false;
  gameOverElement.classList.add("hidden");
  board = createBoard();
  score = 0;
  scoreElement.innerText = score;
  dropInterval = 1000;
  lastTime = 0;
  dropCounter = 0;
  pieceSequenceIndex = 0;
  piece = createPiece();
  update();
}
function draw() {
  if (isGameOver || !piece) return;
  context.fillStyle = "#000";
  context.fillRect(0, 0, canvas.width, canvas.height);
  drawMatrix(board, { x: 0, y: 0 });
  drawMatrix(piece.shape, { x: piece.x, y: piece.y }, piece.color);
}
function drawMatrix(matrix, offset, color) {
  matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value !== 0) {
        context.fillStyle = color || COLORS[value];
        context.fillRect(
          (x + offset.x) * BLOCK_SIZE,
          (y + offset.y) * BLOCK_SIZE,
          BLOCK_SIZE,
          BLOCK_SIZE
        );
        context.strokeStyle = "#222";
        context.strokeRect(
          (x + offset.x) * BLOCK_SIZE,
          (y + offset.y) * BLOCK_SIZE,
          BLOCK_SIZE,
          BLOCK_SIZE
        );
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
      if (
        piece.shape[y][x] !== 0 &&
        (board[y + piece.y] && board[y + piece.y][x + piece.x]) !== 0
      ) {
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
      rotate(piece);
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
function createBoard() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(0));
}

// --- Event Listeners & Game Start ---

playAgainButton.addEventListener("click", () => {
  resetGame();
});

// NEW: Event listener for the main start button on the popup
startButton.addEventListener("click", () => {
  startupModal.style.display = "none"; // Hide the popup
  resetGame(); // Start the game
  // Note: We only call resetGame() here, not when the page loads
});

// IMPORTANT: The final resetGame() call that was here is now GONE.
// The game will not start until the user clicks the button.
