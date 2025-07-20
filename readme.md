# Accessible Falling Blocks Game

This project is a web-based, Tetris-like puzzle game designed with accessibility as a primary focus. It allows users to play the game entirely without using their hands, offering control through both head movements and voice commands.

The application uses a Python backend with Flask to handle real-time computer vision and speech recognition, streaming the results to a JavaScript frontend via WebSockets.

---

## Features

- **Head-Tracking Control:** Play the game by tilting your head.
  - **Tilt Left/Right:** Moves the piece horizontally.
  - **Tilt Up:** Rotates the piece.
  - **Tilt Down:** Drops the piece one level.
- **Voice Command Control:** Use simple voice commands to control the game.
  - Recognizes keywords like "left," "right," "rotate," and "drop."
- **Multimodal Input:** Both head-tracking and voice commands can be used simultaneously.
- **Real-time Feedback:** A live video feed shows the user's head position and the detected command status.
- **Offline Speech Recognition:** Utilizes the Vosk library for fast, offline speech-to-text, ensuring privacy and functionality without an internet connection.
- **Assistive Gameplay:** Features a predictable piece sequence instead of random generation to create a more controlled and less frustrating game experience.

---

## Technology Stack

- **Backend:** Python, Flask, Flask-SocketIO
- **Head Tracking:** OpenCV, MediaPipe
- **Voice Recognition:** Vosk, SoundDevice
- **Frontend:** HTML, CSS, JavaScript (with Socket.IO Client)

---

## Project Structure

For the application to run correctly, your project must follow this folder structure:

```
project-folder/
├── app.py
├── requirements.txt
│
├── vosk-model-small-en-us-0.15/   <-- The downloaded Vosk model folder
│   ├── ... (model files)
│
├── static/
│   ├── style.css
│   └── script.js
│
└── templates/
    └── index.html
```

---

## Setup and Installation

Follow these steps to set up and run the project locally.

#### 1. Prerequisites

- Python 3.8+
- A webcam and a microphone

#### 2. Clone the Repository

Clone this project repository to your local machine.

```bash
git clone <your-repository-url>
cd <your-project-folder>
```

#### 3. Download the Vosk Language Model

This project requires a language model for offline speech recognition.

- Download the small English model here: [Vosk Models Page](https://alphacephei.com/vosk/models) (look for `vosk-model-small-en-us-0.15`).
- Unzip the file.
- Place the resulting folder (e.g., `vosk-model-small-en-us-0.15`) into the root of the project directory, alongside `app.py`.

#### 4. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

- **On Windows:**
  ```bash
  python -m venv myenv
  myenv\Scripts\activate
  ```
- **On macOS / Linux:**
  ```bash
  python3 -m venv myenv
  source myenv/bin/activate
  ```

#### 5. Install Dependencies

Install all the required Python libraries using the `requirements.txt` file. This ensures you have the correct versions of all packages.

```bash
pip install -r requirements.txt
```

**Note:** If `PyAudio` (a dependency of some libraries) fails on Windows, you may need to install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

---

## How to Run the Application

1.  Make sure your virtual environment is activated.
2.  Run the Flask server from the root of the project directory:
    ```bash
    python app.py
    ```
3.  The terminal will show that the server is running and provide a URL.
4.  Open a web browser and navigate to your local IP address, for example: `http://192.168.1.10:5000` or `http://127.0.0.1:5000`.

---

## How to Play

Once the game is running in your browser, control the falling blocks using either of the following methods:

- **Head Movements:**
  - Tilt your head left or right to move the piece.
  - Tilt your head up to rotate the piece.
  - Tilt your head down to drop the piece one level.
- **Voice Commands:**
  - Clearly say "left", "right", "rotate", "up", "drop", or "down".

---

## Advantages and Disadvantages

#### Advantages

- **Highly Accessible:** Provides two different hands-free ways to play (multimodal input).
- **Fully Offline:** Both head-tracking and voice recognition run locally, ensuring privacy and functionality without an internet connection.
- **Real-time Feedback:** The on-screen video feed gives users immediate confirmation that their movements are being detected correctly.
- **Self-Contained:** The application is served entirely by the Python backend, making it easy to run.

#### Disadvantages

- **Hardware Dependent:** Performance relies on the user's CPU. Running two real-time processing threads (video and audio) can be demanding on older machines.
- **Environment Sensitive:** Voice recognition accuracy can be affected by background noise. Head tracking can be affected by poor lighting.
- **Manual Setup:** Requires a one-time manual download and placement of the Vosk model folder.
