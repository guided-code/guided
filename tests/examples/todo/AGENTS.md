# AGENTS.md

Todo is a browser-based task management app built with HTML5 and vanilla JavaScript. Users can add, complete, and delete tasks, with state persisted to `localStorage`.

## Running the App

Open `index.html` in a browser. No build step or server is required.

## Architecture

The app is structured as plain JavaScript modules loaded via `<script>` tags in `index.html`.

### Module layout (`js/`)

- `store.js` — State management; loads and saves tasks to `localStorage`; exposes `addTask`, `toggleTask`, `deleteTask`, and `getTasks`
- `render.js` — DOM rendering; builds the task list from current state and re-renders on changes
- `filter.js` — Filter logic; supports `all`, `active`, and `completed` views
- `app.js` — Entry point; wires event listeners to store actions and triggers re-renders

### Styling (`css/`)

- `styles.css` — Layout and UI styles for the task list, input field, filter bar, and empty state

### UI Elements

- **Input field** — adds a new task on Enter
- **Task list** — displays tasks with a checkbox to toggle completion and a delete button
- **Filter bar** — switches between All, Active, and Completed views
- **Footer** — shows count of remaining active tasks

## Data Model

Each task is a plain object:

```json
{
  "id": "string (uuid)",
  "text": "string",
  "completed": "boolean",
  "createdAt": "ISO 8601 timestamp"
}
```

Tasks are stored as a JSON array under the `todos` key in `localStorage`.

## Workspace

This project was initialized with `guide workspace init`. Configuration is stored in `.workspace/config.yaml`.
