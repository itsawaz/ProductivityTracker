"""
Productivity Tracker — Central Configuration
All tunable parameters for the tracking system.
"""

# =============================================================================
# Interval & Timing
# =============================================================================
INTERVAL_DURATION = 30          # seconds per tracking interval
IDLE_THRESHOLD = 45             # seconds of no input before marking idle
FOCUS_POLL_INTERVAL = 1         # seconds between focus detection polls
MOUSE_SAMPLE_INTERVAL = 0.05   # seconds — throttle raw mouse move events

# =============================================================================
# VDI Application Identifiers
# =============================================================================

# macOS: Bundle identifiers for VDI/Remote Desktop clients
VDI_BUNDLE_IDS = {
    "com.microsoft.rdc.macos",       # Windows App (new name)
    "com.microsoft.rdc.osx",         # Microsoft Remote Desktop (legacy)
    "com.apple.remotedesktop",       # Apple Remote Desktop
    "com.citrix.XenAppViewer",       # Citrix Workspace (if applicable)
    "com.vmware.horizon",            # VMware Horizon (if applicable)
}

# Windows: Process names for VDI/Remote Desktop clients
VDI_PROCESS_NAMES = {
    "mstsc.exe",                     # Classic Remote Desktop Connection
    "msrdcw.exe",                    # Modern Windows App / Azure VD
    "rdclient.windows.exe",          # Older MS Store version
    "wfica32.exe",                   # Citrix Workspace (if applicable)
    "vmware-view.exe",               # VMware Horizon (if applicable)
}

# Windows: Window title substrings (fallback detection)
VDI_TITLE_PATTERNS = [
    "Remote Desktop Connection",
    "Windows App",
]

# =============================================================================
# Activity Classification Thresholds (events per interval)
# =============================================================================
THRESHOLD_PASSIVE_MIN = 1       # >= this → Passive
THRESHOLD_ACTIVE_MIN = 6        # >= this → Active
THRESHOLD_HIGH_FOCUS_MIN = 21   # >= this → High Focus

# =============================================================================
# Productivity Scoring Weights
# =============================================================================
WEIGHT_IDLE = 0.0
WEIGHT_PASSIVE = 0.4
WEIGHT_ACTIVE = 0.7
WEIGHT_HIGH_FOCUS = 0.95

# =============================================================================
# Behavioral Enhancements
# =============================================================================
FOCUS_CONTINUITY_BONUS = 0.05   # bonus weight for 3+ consecutive active intervals
FOCUS_CONTINUITY_MIN_STREAK = 3 # minimum consecutive intervals for bonus
WEIGHT_CAP = 1.0                # maximum weight after bonuses

BREAK_PENALTY_MULTIPLIER = 0.8  # weight multiplier after long idle
BREAK_PENALTY_IDLE_THRESHOLD = 5  # consecutive idle intervals to trigger penalty
BREAK_PENALTY_DURATION = 2      # intervals the penalty lasts

ROLLING_AVERAGE_WINDOW = 5      # number of intervals for rolling average

# Noise filtering: isolated single-event intervals surrounded by idle → demoted
NOISE_FILTER_ENABLED = True

# =============================================================================
# MySQL Database Configuration
# =============================================================================
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""             # Set your MySQL password here
MYSQL_DATABASE = "productivity_tracker"
MYSQL_POOL_SIZE = 5

# =============================================================================
# Web Server Configuration
# =============================================================================
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080
SERVER_DEBUG = False

# =============================================================================
# Dashboard
# =============================================================================
AUTO_OPEN_BROWSER = True        # Open dashboard in browser on start
