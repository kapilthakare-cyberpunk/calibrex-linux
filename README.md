# Calibrex - Adaptive Display Calibration for Linux

An always-on, context-aware display calibration system that continuously measures ambient conditions and adapts your display output for optimal color accuracy — with zero user intervention after initial setup.

## Features

- **Colorimeter Detection** — Auto-detects Spyder X2 Ultra and other ArgyllCMS-compatible devices
- **Pre-initialization Fix** — Automatically initializes colorimeter before calibration (Spyder X2 Ultra fix)
- **Display Calibration** — Full ICC profile generation using ArgyllCMS
- **Spot Check** — Quick verification readings
- **Adaptive Mode** — Continuous adjustment based on ambient conditions
- **Night Shift** — Automatic color temperature adjustment
- **True Tone** — Ambient-adapted display output

## Requirements

### System Dependencies

```bash
# Debian/Ubuntu
sudo apt-get install argyllcms python3-tk

# Fedora/RHEL
sudo dnf install argyllcms python3-tkinter

# Arch Linux
sudo pacman -S argyllcms tk
```

### Python Dependencies

- Python 3.8+
- Tkinter (usually included with Python)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/kapilthakare-cyberpunk/calibrex.git
cd calibrex

# Install
pip install .

# Or run directly
python main.py
```

### Using pip

```bash
pip install calibrex
```

## Usage

### Quick Start

1. Connect your colorimeter (Spyder X2 Ultra recommended)
2. Run `calibrex` or `python main.py`
3. Click "Calibrate Now" to start calibration wizard
4. Follow the on-screen instructions

### Command Line

```bash
# Run the application
calibrex

# Or directly
python main.py
```

## Calibration Process

1. **Connect Colorimeter** — Plug in your Spyder X2 Ultra via USB
2. **Scan for Device** — Calibrex will detect and initialize the colorimeter
3. **Position Colorimeter** — Place on screen center, away from ambient light
4. **Run Measurement** — Display shows color patches for measurement
5. **Generate Profile** — Creates ICC profile from measurements
6. **Verify** — Checks Delta-E accuracy (target: < 2.0)

## ArgyllCMS Integration

Calibrex uses ArgyllCMS for color management. The following tools are used:

- `dispcal` — Display calibration
- `dispread` — Display patch measurement
- `targen` — Target generation
- `colprof` — Profile generation
- `dispwin` — Display window (profile application)
- `spotread` — Spot color readings

### Path Configuration

Calibrex automatically detects ArgyllCMS installation. If not found in PATH, set the path:

```python
from calibrex.argyllcms import ArgyllCMS

argyll = ArgyllCMS(argyll_path="/usr/local/bin")
```

## Troubleshooting

### Colorimeter Not Detected

1. Ensure colorimeter is connected via USB
2. Run `dispread -d1 -v -e` manually to test
3. Check USB permissions: `ls -la /dev/bus/usb/`
4. Try running with `sudo` (not recommended for regular use)

### Permission Issues

If you get permission errors accessing USB devices:

```bash
# Add your user to the plugdev group
sudo usermod -aG plugdev $USER

# Or create a udev rule
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0971", MODE="0666"' | sudo tee /etc/udev/rules.d/99-colorimeter.rules
sudo udevadm control --reload-rules
```

### Tkinter Not Found

```bash
# Debian/Ubuntu
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

## Development

### Setup

```bash
# Clone and install in development mode
git clone https://github.com/kapilthakare-cyberpunk/calibrex.git
cd calibrex
pip install -e .
```

### Running Tests

```bash
python -m pytest tests/
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [ArgyllCMS](http://www.argyllcms.com/) — Color management system
- Spyder X2 Ultra — Colorimeter hardware
- Python Tkinter — GUI framework
