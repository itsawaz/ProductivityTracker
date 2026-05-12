# ProTrack — Productivity Tracking System

A local, privacy-first productivity tracker inspired by ProHance. Tracks keyboard/mouse activity when your VDI (Remote Desktop) client is in focus, classifies behavior into productivity states, and displays real-time analytics on a premium dashboard.

**All data stays on your machine. Nothing is sent externally.**

---

## Features

- 🎯 **VDI Focus Detection** — Tracks only when your Remote Desktop client is active
- ⌨️ **Input Activity Monitoring** — Keyboard, mouse, click, and scroll event counting
- 📊 **Activity Classification** — Idle → Passive → Active → High Focus states
- ⚖️ **Weighted Scoring** — Productivity hours calculated from classified intervals
- 🧠 **Behavioral Enhancements** — Focus continuity bonus, break penalty, noise filtering
- 📈 **Real-Time Dashboard** — Live stats, hourly timeline, distribution charts, trend analysis
- 🖥️ **Cross-Platform** — Works on macOS and Windows

---

## Prerequisites

- **Python 3.10+**
- **MySQL 8.x** installed and running
- **macOS**: Terminal must have Accessibility permissions
- **Windows**: No special permissions needed

---

## Quick Start

### 1. Clone / Navigate to the project

```bash
cd ProdctivityTracker
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

**macOS:**
```bash
pip install -r requirements-macos.txt
```

**Windows:**
```bash
pip install -r requirements-windows.txt
```

### 4. Configure MySQL

Edit `config.py` and set your MySQL credentials:

```python
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_password"
MYSQL_DATABASE = "productivity_tracker"
```

The database and tables will be created automatically on first run.

### 5. macOS Accessibility Permissions

For keyboard/mouse tracking to work on macOS, you must grant Accessibility permissions:

1. Open **System Settings → Privacy & Security → Accessibility**
2. Click the **+** button
3. Add your **Terminal app** (Terminal, iTerm2, VS Code, etc.)
4. Restart the terminal after granting permission

### 6. Run the tracker

```bash
python main.py
```
or 
```bash
 ./start.sh
```
The dashboard will automatically open at **http://localhost:8080**

---

## Dashboard

The web dashboard provides:

### Live Stats
| Card | Description |
|------|-------------|
| **Current State** | Real-time activity state (Idle / Passive / Active / High Focus) |
| **Productive Hours** | Total productive time today |
| **Efficiency** | Animated gauge showing efficiency percentage |
| **Focus Streak** | Current & best streak, interruption count |

### Insights
| Card | Description |
|------|-------------|
| **Total Time Worked** | Total tracked duration today |
| **VDI Focus Ratio** | % of time with VDI in focus vs total, with progress bar |
| **Peak Hour** | Your most productive hour of the day |
| **Deep Work** | Count & duration of sustained focus sessions (≥3 min) |
| **Idle Time** | Total idle time with percentage breakdown |
| **Input Activity** | Total keystrokes, clicks, scrolls, and mouse moves |

### Charts
| Chart | Description |
|-------|-------------|
| **Hourly Timeline** | Color-coded bar chart showing productivity by hour |
| **Activity Distribution** | Doughnut chart of time in each state |
| **Productivity Trend** | Line chart with 7/14/30 day history |
| **VDI Focus vs Non-VDI** | Stacked bar chart comparing VDI time per hour |
| **Input Activity Heatmap** | Visual heatmap of input intensity by type and hour |
| **Recent Intervals** | Timeline of the last 50 intervals |

---

## Configuration

All settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `INTERVAL_DURATION` | 30s | Length of each tracking interval |
| `IDLE_THRESHOLD` | 45s | Seconds of inactivity before idle state |
| `THRESHOLD_ACTIVE_MIN` | 6 | Min events for "Active" classification |
| `THRESHOLD_HIGH_FOCUS_MIN` | 21 | Min events for "High Focus" |
| `WEIGHT_ACTIVE` | 0.7 | Scoring weight for Active state |
| `WEIGHT_HIGH_FOCUS` | 0.95 | Scoring weight for High Focus state |
| `FOCUS_CONTINUITY_BONUS` | 0.05 | Bonus for sustained focus streaks |
| `AUTO_OPEN_BROWSER` | True | Open dashboard on start |

### Adding Custom VDI Apps

**macOS** — Add bundle IDs to `VDI_BUNDLE_IDS` in config.py:
```python
VDI_BUNDLE_IDS = {
    "com.microsoft.rdc.macos",
    "com.your.custom.app",
}
```

**Windows** — Add process names to `VDI_PROCESS_NAMES`:
```python
VDI_PROCESS_NAMES = {
    "mstsc.exe",
    "your_custom_app.exe",
}
```

---

## Architecture

```
Focus Detection → Input Tracking → Interval Aggregator → Classifier
       ↓                                    ↓
  (VDI active?)                    Scoring Engine + Behavioral
                                            ↓
                                    MySQL Database
                                            ↓
                                 Flask + SocketIO Server
                                            ↓
                                    Web Dashboard
```

---

## Troubleshooting

### "pynput is not capturing events" (macOS)
→ Grant Accessibility permission to your terminal app and restart it.

### "MySQL connection refused"
→ Make sure MySQL is running: `mysql.server start` (macOS) or check Services (Windows).

### "Module not found" errors
→ Make sure you're using the correct requirements file for your OS and the virtual environment is activated.

### Dashboard not updating
→ Check the browser console for WebSocket connection errors. The server must be running on port 8080.

---

## License

This project is for personal productivity tracking only. All data is stored locally.
