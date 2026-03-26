# AGENTS.md

Snake is a browser-based game built with HTML5 Canvas and WebGL. The player controls a snake that grows longer as it eats food, and the game ends if the snake collides with itself.

## Running the Game

Open `index.html` in a browser. No build step or server is required.

## Architecture

The game is structured as a set of plain JavaScript modules loaded in order via `<script>` tags in `index.html`.

### Module layout (`js/`)

- `renderer.js` — WebGL rendering layer; draws the grid, snake, and food onto the canvas
- `input.js` — Keyboard input handling; maps WASD keys to direction changes
- `snake.js` — Snake state: position, direction, body segments, growth logic
- `food.js` — Food placement logic; spawns food at random unoccupied grid cells
- `camera.js` — Camera/viewport logic for the infinite grid; follows the snake
- `game.js` — Core game loop; updates state each tick, detects collisions, manages score
- `app.js` — Entry point; initializes all modules and starts the game loop

### Styling (`css/`)

- `styles.css` — Layout and UI styles for the canvas container, score display, and game-over overlay

### UI Elements

- **Score** — increments each time the snake eats food
- **Length** — displays current snake length
- **Game Over overlay** — shown on collision; includes final score and a restart button

## Game Rules

- The snake moves continuously in the current direction
- Eating food increases the snake's length and score
- Colliding with the snake's own body ends the game
- The grid is infinite; the camera follows the snake

## Workspace

This project was initialized with `guide workspace init`. Configuration is stored in `.workspace/config.yaml`.
