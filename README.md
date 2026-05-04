# Universal Downloader

> The high‑fidelity universal media downloader and **VFR → CFR** converter built for video editors. Download from YouTube, TikTok, Instagram, Twitch, and 15+ other sites in 4K, trim before downloading, and get edit‑ready CFR MP4s that won't glitch in Premiere Pro or DaVinci Resolve.

![Universal Downloader screenshot](screenshot.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Windows-supported-success?logo=windows&logoColor=white)](#supported-operating-systems)
[![Platform: macOS](https://img.shields.io/badge/macOS-supported-success?logo=apple&logoColor=white)](#supported-operating-systems)
[![Platform: Linux](https://img.shields.io/badge/Linux-supported-success?logo=linux&logoColor=white)](#supported-operating-systems)
[![Electron](https://img.shields.io/badge/Electron-UI-47848F?logo=electron&logoColor=white)](https://www.electronjs.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/Powered%20by-yt--dlp-red)](https://github.com/yt-dlp/yt-dlp)

A free, open‑source, cross‑platform desktop app that wraps **yt‑dlp**, **FFmpeg**, and **HandBrakeCLI** behind a clean glassmorphism UI. Built specifically to solve the most painful problem video editors hit when sourcing footage online: **variable frame rate (VFR)** clips that drift out of sync, glitch on cuts, or refuse to render properly in NLEs.

---

## Table of contents

- [Why Universal Downloader](#why-universal-downloader)
- [Features](#features)
- [Supported sites](#supported-sites)
- [Supported operating systems](#supported-operating-systems)
- [How it works](#how-it-works)
- [Installation](#installation)
- [Running the app](#running-the-app)
- [How to use](#how-to-use)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Donations](#donations)
- [License](#license)

---

## Why Universal Downloader

If you've ever pulled a clip from YouTube, TikTok, or Twitch into **Premiere Pro** or **DaVinci Resolve** and watched it stutter, drift, or throw a "media offline" warning halfway through the timeline — that's **Variable Frame Rate (VFR)** footage. Web platforms encode in VFR to save bandwidth; professional NLEs expect **Constant Frame Rate (CFR)**. The mismatch is the #1 cause of broken edits with downloaded source clips.

Universal Downloader fixes that end‑to‑end:

1. **Downloads** the highest‑quality stream available (up to **4K HDR** where supported).
2. **Trims** to the exact in/out timecodes you specify — no wasted bandwidth on a 2‑hour stream when you only need 45 seconds.
3. **Optimizes** through HandBrake to a **CFR MP4** with the right preset for the resolution.
4. **Delivers** an edit‑ready file you can drop straight onto a Premiere or Resolve timeline.

No more *"Why is this clip de‑syncing?"* No more re‑exporting through Shutter Encoder or Adobe Media Encoder before you can even start cutting.

If you've searched for a *"yt‑dlp GUI"*, *"4K YouTube downloader"*, *"VFR to CFR converter"*, *"TikTok downloader without watermark"*, or *"video editor download tool"*, this is the one app that does all of it.

---

## Features

- **🎨 Modern UI** — sleek dark glassmorphism interface (Electron).
- **🐍 yt‑dlp under the hood** — the most reliable downloader in the open‑source world.
- **🎯 4K / HDR support** — pulls the best stream the site exposes, including 2160p60.
- **✂️ Precision trim** — set start/end timecodes (`00:30` → `01:15`) and only those bytes are downloaded.
- **⚙️ Auto HandBrake** — detects 4K / 1080p / 720p and applies the right CFR preset automatically.
- **🎧 Audio extraction** — one‑click rip to **MP3, WAV, M4A, or FLAC**.
- **⚡ Smart Mode** — picks optimal settings based on the URL and your selected use case.
- **🌐 Proxy fallback** — automatically rotates through `proxies.txt` if the direct connection fails (5 retries).
- **🚫 Watermark‑free** — TikTok and similar sites are downloaded without overlay watermarks.
- **🛑 Stop anytime** — abort an in‑progress download mid‑stream.
- **📦 Standalone build** — packaged as a single Windows `.exe` via PyInstaller (see [Releases](https://github.com/amolbangare08/Universal-Downloader/releases)).

---

## Supported sites

Anything **yt‑dlp** supports works in principle. The following are explicitly tested and tuned:

| Category | Sites |
|---|---|
| **Video platforms** | YouTube *(4K, Shorts, Live, Playlists)*, Vimeo, Dailymotion, Bilibili, Rutube, BBC iPlayer |
| **Social** | TikTok *(no watermark)*, Instagram *(Reels, Posts)*, Facebook *(Watch, Reels, Public)*, Twitter / X, LinkedIn *(Posts + Learning)*, Reddit *(video + audio merged)*, 9GAG, VK |
| **Streaming / clips** | Twitch *(Clips + VODs)* |
| **Audio** | SoundCloud *(high‑quality)* |
| **Adult** | Pornhub |

> If you hit a site that isn't listed but is supported by yt‑dlp, paste the URL anyway — it will likely just work.

---

## Supported operating systems

| OS | Status | Notes |
|---|---|---|
| **Windows** 10 / 11 | ✅ First‑class | Standalone `.exe` available in Releases |
| **macOS** | ✅ Supported | Run from source via `npm start` |
| **Linux** | ✅ Supported | Run from source via `npm start` |

---

## How it works

Universal Downloader is a **hybrid Electron + Python** app. Electron handles the UI; Python does the heavy lifting.

```
┌────────────────────┐   IPC    ┌────────────────────┐   spawn    ┌────────────────────┐
│  Electron Renderer │ ──────►  │ Electron Main (JS) │ ─────────► │ Python CLI (cli.py)│
│  (script.js + UI)  │ ◄──────  │  (frontend/main.js)│ ◄───stdout─│  yt-dlp + FFmpeg + │
└────────────────────┘  events  └────────────────────┘   JSON     │   HandBrakeCLI     │
                                                                  └────────────────────┘
```

1. You paste a URL and hit **START DOWNLOAD**.
2. The renderer (`script.js`) fires an IPC message to the Electron main process.
3. Main spawns `python backend/cli.py <url> --folder <path> ...` as a child process.
4. `cli.py` runs `yt‑dlp` to fetch the stream, optionally trims with `download_range_func`, then pipes through FFmpeg if audio extraction was requested, or HandBrakeCLI if "Optimize" is on.
5. Progress is emitted as **line‑delimited JSON on stdout** (`{type, data}`), parsed by Electron, and rendered as a live progress bar.
6. The final file lands in the destination folder you picked. CFR. Edit‑ready.

If the direct connection fails (geo‑block, rate limit, ISP throttle), the Python layer transparently rotates through proxies listed in `proxies.txt` — up to 5 retries before surfacing an error.

---

## Installation

### Option 1 — Standalone build (Windows, easiest)

Download the latest pre‑built `.exe` from the [**Releases**](https://github.com/amolbangare08/Universal-Downloader/releases) page. Double‑click and you're done — FFmpeg and HandBrakeCLI are bundled.

### Option 2 — Run from source

#### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| **Node.js** | v14+ | Electron frontend |
| **Python** | 3.8+ | Download backend |
| **FFmpeg** | latest static build | Merge video+audio, audio extraction |
| **HandBrakeCLI** | latest | VFR → CFR optimization (only if Optimize is on) |

`ffmpeg.exe` and `HandBrakeCLI.exe` should live either in your **system PATH** or directly inside the `backend/` folder. The app will auto‑download them if missing on first run.

#### 1. Clone

```bash
git clone https://github.com/amolbangare08/Universal-Downloader.git
cd Universal-Downloader
```

#### 2. Backend (Python)

```bash
# Windows
pip install -r requirements.txt

# macOS / Linux
pip3 install -r requirements.txt
```

#### 3. Frontend (Electron)

```bash
cd frontend
npm install
```

---

## Running the app

From the `frontend/` directory:

```bash
npm start
```

Or from the project root:

```bash
npx electron .
```

The Universal Downloader window will launch.

---

## How to use

1. **Paste a URL** — copy any supported link to your clipboard and click **PASTE**.
2. **Pick a mode**:
   - **Video + Audio** — standard download.
   - **Video Only** — silent footage, perfect for B‑roll / stock cuts.
   - **Audio Only** — extract music, voiceover, or interview audio.
3. **Choose options**:
   - **Quality** — auto, 4K, 1080p, 720p, 480p, 360p.
   - **Cut / Trim** — toggle on, then enter `Start` and `End` timecodes (`HH:MM:SS`).
   - **Optimize** — toggle on to push the result through HandBrake and force CFR. *Recommended for any clip headed into an NLE.*
   - **Audio format** (Audio Only mode) — MP3, WAV, M4A, FLAC.
4. **Click START DOWNLOAD**, choose a destination folder, and watch the progress bar.
5. The finished file opens in Explorer / Finder when complete.

---

## Tech stack

- **Frontend** — [Electron](https://www.electronjs.org/), HTML5, CSS3 (glassmorphism), Vanilla JS
- **Backend** — Python 3, [yt‑dlp](https://github.com/yt-dlp/yt-dlp), [FFmpeg](https://ffmpeg.org/), [HandBrakeCLI](https://handbrake.fr/)
- **Packaging** — [PyInstaller](https://pyinstaller.org/) for the standalone build
- **Fonts** — Poppins (bundled)
- **IPC** — Node `ipcRenderer` / `ipcMain` + line‑delimited JSON over Python stdout

---

## Project structure

```
Universal-Downloader/
├── main.js                      # Electron entry (root)
├── frontend/                    # The face — Electron UI
│   ├── main.js                  # Electron main process + IPC handlers
│   ├── index.html               # UI layout
│   ├── style.css                # Glassmorphism styling
│   ├── script.js                # Renderer logic
│   └── package.json
├── backend/                     # The brains — Python
│   ├── cli.py                   # Headless entry, JSON-over-stdout bridge
│   ├── core.py                  # Configs + tool auto-download
│   ├── downloaders.py           # yt-dlp + HandBrake orchestration
│   ├── ffmpeg.exe               # (optional) bundled binary
│   └── HandBrakeCLI.exe         # (optional) bundled binary
├── old-folder/                  # Legacy standalone tkinter version
├── proxies.txt                  # (gitignored) proxy fallback list
├── requirements.txt             # Python deps
├── universal_downloader.spec    # PyInstaller spec
└── README.md
```

---

## Troubleshooting

### Download doesn't start

- Verify Python is installed and on your PATH: `python --version`.
- Open the app's DevTools with <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>I</kbd> and check the Console for errors.
- Make sure the URL is publicly accessible (not a private/unlisted page).

### "FFmpeg not found"

- Drop a static `ffmpeg.exe` into the `backend/` folder, **or** add FFmpeg to your system PATH.
- On first run the app tries to auto‑download it; if your network blocks the fetch, do it manually.

### "HandBrakeCLI not found"

- Only required when **Optimize** is toggled on. Place `HandBrakeCLI.exe` in `backend/` or your PATH.

### Downloads are slow / timing out

- Add working proxies to `proxies.txt` (one `host:port` per line) — the app rotates through them automatically.

### TikTok / Instagram returns nothing

- These sites change their HTML frequently. Update yt‑dlp:
  ```bash
  pip install --upgrade yt-dlp
  ```

### Clip still glitches in Premiere

- Ensure **Optimize** was toggled on for the download. If you've already downloaded without Optimize, re‑run on the same URL with Optimize enabled, or push the file through HandBrake manually with a CFR preset.

---

## Contributing

Pull requests are welcome.

1. Fork the project.
2. Create a feature branch — `git checkout -b feature/MyFeature`.
3. Commit — `git commit -m "Add MyFeature"`.
4. Push — `git push origin feature/MyFeature`.
5. Open a Pull Request describing the change.

For larger changes (new site support, UI refactors, packaging changes), open an issue first to discuss the approach.

---

## Donations

If Universal Downloader saved you hours of re‑encoding, consider tipping the project.

**Bitcoin:**

```
1FVP7EdQZ4GmDpv4VvZUBUMm3B5MLLq2P3
```

---

## License

Distributed under the [MIT License](LICENSE). See `LICENSE` for full terms.

**Built by editors, for editors.**

---

### Keywords

*yt-dlp gui, 4k youtube downloader, vfr to cfr converter, video editor download tool, tiktok downloader no watermark, instagram reels downloader, twitch vod downloader, twitch clip downloader, youtube to mp3, youtube to mp4, premiere pro vfr fix, davinci resolve vfr fix, handbrake gui downloader, ffmpeg gui, electron downloader app, free video downloader, open source video downloader, universal video downloader, batch video trimmer, soundcloud downloader*
