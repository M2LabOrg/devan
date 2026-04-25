# Tauri Desktop App

Wraps the existing Flask + Socket.IO backend in a native desktop application using [Tauri](https://tauri.app). No changes were needed to `client/app.py`.

## How it works

1. Tauri starts and shows a Zen-styled splash screen (`src-tauri/ui/index.html`)
2. Rust spawns `python app.py` in the `client/` directory as a child process
3. Rust polls `http://127.0.0.1:<port>` until Flask responds (up to 90 seconds)
4. Once Flask is ready, the webview navigates to the live app
5. When you close the window, Rust sends SIGTERM to Flask (Unix) then force-kills it

Port 5001 is used by default. If it's already in use, the app automatically picks the next free port.

---

## Prerequisites

Install these once on your machine:

### 1. Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. System dependencies

**macOS** — Install Xcode Command Line Tools (includes Python 3):
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
```

**Windows** — Install:
- [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (already on Windows 11)
- Python 3.10+ from [python.org](https://www.python.org/downloads/)

### 3. Node.js (for the Tauri CLI)
```bash
# macOS/Linux via nvm:
nvm install --lts

# Or download from https://nodejs.org
```

### 4. Python virtual environment (first time only)
The Tauri app will use the venv if it already exists. Run this once:
```bash
cd client
./start.sh   # sets up venv and verifies everything works
# Ctrl+C once you confirm it loads
```

---

## Running in development

```bash
# From the project root:
npm install        # installs @tauri-apps/cli (first time only)
npm run dev        # compiles Rust + spawns Flask + opens the app window
```

First run will take a few minutes while Rust compiles dependencies. Subsequent runs are fast.

---

## Building a distributable installer

```bash
npm run build
```

Output files are in `src-tauri/target/release/bundle/`:

| Platform | File |
|---|---|
| macOS | `.dmg` and `.app` |
| Windows | `.msi` and `.exe` |
| Linux | `.deb` and `.AppImage` |

---

## Adding an app icon

1. Create or export a 1024×1024 PNG of your icon
2. Run:
   ```bash
   npx tauri icon path/to/your-icon-1024.png
   ```
   This generates all required sizes into `src-tauri/icons/` automatically.

---

## Project structure

```
mcp-design-deploy/
├── package.json              # npm scripts (tauri dev / tauri build)
├── src-tauri/
│   ├── tauri.conf.json       # window config, bundle settings, CSP
│   ├── Cargo.toml            # Rust dependencies
│   ├── build.rs              # Tauri build script
│   ├── icons/                # App icons (generate with `tauri icon`)
│   ├── ui/
│   │   └── index.html        # Splash screen shown while Flask boots
│   └── src/
│       └── main.rs           # All lifecycle logic (spawn, poll, shutdown)
└── client/                   # Unchanged — Flask app as-is
```

---

## Architecture decisions

| Decision | Rationale |
|---|---|
| `std::process::Command` to spawn Flask | Direct `Child` handle needed for clean shutdown; simpler than Tauri sidecar (which requires pre-compiled binaries) |
| HTTP polling instead of fixed sleep | Startup time varies widely (first run downloads easyocr/docling models); polling is reliable |
| `WERKZEUG_RUN_MAIN=true` env var | Prevents werkzeug's dev-mode reloader from forking a second Python process, which would orphan on Windows |
| `"csp": null` in tauri.conf.json | Tauri's default CSP injection blocks Socket.IO WebSocket connections |
| Venv Python preferred over system Python | If `client/venv` exists, its Python already has all dependencies installed |
| Docker becomes optional | Desktop users don't need Docker; it remains available for CI and server deployments |

---

## Troubleshooting

**App shows "Backend did not start"**
- Run `cd client && ./start.sh` in a terminal to verify Flask starts and the venv is set up
- Check that Python 3.10+ is on your PATH: `python3 --version`

**Port conflict**
- The app auto-detects a free port — this should be transparent. If it fails, check for processes stuck on 5001–5100.

**Slow first launch**
- On first run, `easyocr` and `docling` may download ML models (~1GB). This is normal. Subsequent launches are fast.

**macOS Gatekeeper warning**
- Without code signing, macOS shows a security warning on first open. Right-click the `.app` → Open to bypass it once.
- For signed builds you need an Apple Developer account ($99/yr).

**Windows: Python not found**
- Ensure Python is added to PATH during installation (tick the checkbox in the Python installer).
