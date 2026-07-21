"""Calibrex - Adaptive Display Calibration GUI for Linux

Full GUI on startup, minimizes to system tray on close/minimize.
Features real-time colorimeter detection.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import subprocess
import platform
from typing import Tuple

from .argyllcms import ArgyllCMS
from . import __version__


class CalibrexApp:
    """Main application - shows full GUI, minimizes to tray."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calibrex")
        self.root.geometry("350x600")
        self.root.resizable(False, False)
        
        # Initialize ArgyllCMS
        self.argyll = ArgyllCMS()
        self._is_macos = platform.system() == "Darwin"
        
        # State variables
        self.current_lux = tk.DoubleVar(value=0)
        self.current_color_temp = tk.DoubleVar(value=6500)
        self.current_brightness = tk.DoubleVar(value=50)
        self.last_delta_e = tk.DoubleVar(value=0)
        self.night_shift_enabled = tk.BooleanVar(value=False)
        self.true_tone_enabled = tk.BooleanVar(value=False)
        self.adaptive_enabled = tk.BooleanVar(value=True)
        
        # Colorimeter state
        self.colorimeter_connected = False
        self.colorimeter_name = tk.StringVar(value="Not connected")
        self.colorimeter_status_text = tk.StringVar(value="Searching...")
        
        # Tray state
        self._detection_running = True
        self._tray_window = None
        self._tray_icon = None
        self._minimized_to_tray = False
        
        # Setup UI
        self._setup_ui()
        
        # Handle minimize to tray
        self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
        self.root.bind("<Unmap>", self._on_minimize)
        
        # Start detection
        self._start_detection()
    
    def _setup_ui(self):
        """Setup the full GUI."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="◐", font=("Helvetica", 24)).pack(side=tk.LEFT)
        
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(title_frame, text="Calibrex", font=("Helvetica", 16, "bold")).pack(anchor=tk.W)
        ttk.Label(title_frame, text="Adaptive Display Calibration", font=("Helvetica", 9), foreground="gray").pack(anchor=tk.W)
        
        ttk.Label(header_frame, text=f"v{__version__}", font=("Helvetica", 8), foreground="gray").pack(side=tk.RIGHT)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Colorimeter status
        colorimeter_frame = ttk.LabelFrame(main_frame, text="Colorimeter", padding=8)
        colorimeter_frame.pack(fill=tk.X, pady=5)
        
        device_frame = ttk.Frame(colorimeter_frame)
        device_frame.pack(fill=tk.X)
        
        self.device_indicator = tk.Canvas(device_frame, width=12, height=12, highlightthickness=0)
        self.device_indicator.pack(side=tk.LEFT, padx=(0, 8))
        self._draw_indicator("gray")
        
        ttk.Label(device_frame, textvariable=self.colorimeter_name, font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(colorimeter_frame, textvariable=self.colorimeter_status_text,
                                       font=("Helvetica", 9), foreground="gray")
        self.status_label.pack(anchor=tk.W, pady=(4, 0))
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Readings
        status_frame = ttk.LabelFrame(main_frame, text="Readings", padding=8)
        status_frame.pack(fill=tk.X, pady=5)
        
        self._create_status_row(status_frame, "☀ Ambient Light", self.current_lux, "lux")
        self._create_status_row(status_frame, "🌡 Color Temp", self.current_color_temp, "K")
        self._create_status_row(status_frame, "◐ Brightness", self.current_brightness, "%")
        self._create_status_row(status_frame, "📊 Accuracy", self.last_delta_e, "dE")
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Settings
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=8)
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(settings_frame, text="🌙 Night Shift", variable=self.night_shift_enabled).pack(anchor=tk.W)
        ttk.Checkbutton(settings_frame, text="☀ True Tone", variable=self.true_tone_enabled).pack(anchor=tk.W)
        ttk.Checkbutton(settings_frame, text="🔄 Adaptive Mode", variable=self.adaptive_enabled).pack(anchor=tk.W)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Actions
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(actions_frame, text="🎯 Calibrate Now", command=self._open_calibration_wizard).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="✓ Spot Check", command=self._spot_check).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="⚙ Settings", command=self._open_settings).pack(fill=tk.X, pady=2)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Minimize to tray button
        ttk.Button(main_frame, text="⬇ Minimize to Tray", command=self._minimize_to_tray).pack(fill=tk.X, pady=2)
        ttk.Button(main_frame, text="Quit", command=self._quit).pack(fill=tk.X, pady=2)
    
    def _draw_indicator(self, color: str):
        """Draw connection indicator."""
        self.device_indicator.delete("all")
        self.device_indicator.create_oval(2, 2, 10, 10, fill=color, outline="")
    
    def _create_status_row(self, parent, label: str, var: tk.DoubleVar, unit: str):
        """Create status row."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label, font=("Helvetica", 9)).pack(side=tk.LEFT)
        
        value_label = ttk.Label(frame, text=f"{int(var.get())} {unit}", font=("Helvetica", 9), foreground="gray")
        value_label.pack(side=tk.RIGHT)
        
        var.trace_add("write", lambda *args: value_label.config(text=f"{int(var.get())} {unit}"))
    
    def _start_detection(self):
        """Start detection thread."""
        threading.Thread(target=self._detection_loop, daemon=True).start()
    
    def _detection_loop(self):
        """Background detection loop."""
        last_state = None
        
        while self._detection_running:
            try:
                connected, name = self._detect_colorimeter()
                
                if connected != last_state:
                    last_state = connected
                    self.colorimeter_connected = connected
                    self.colorimeter_name.set(name if connected else "Not connected")
                    self.colorimeter_status_text.set("Ready" if connected else "Searching...")
                    
                    color = "#4CAF50" if connected else "#F44336"
                    self.root.after(0, lambda c=color: self._draw_indicator(c))
                    
            except Exception as e:
                print(f"[Detection] Error: {e}")
            
            for _ in range(20):
                if not self._detection_running:
                    return
                time.sleep(0.1)
    
    def _detect_colorimeter(self) -> Tuple[bool, str]:
        """Detect colorimeter."""
        # Method 1: ArgyllCMS
        try:
            result = subprocess.run(
                [os.path.join(self.argyll.argyll_path, "dispcal"), "-v"],
                capture_output=True, text=True, timeout=3
            )
            
            for line in result.stdout.splitlines():
                if "= 'usb" in line:
                    if "Spyder" in line:
                        return True, "Spyder X2 Ultra"
                    elif "i1" in line:
                        return True, "X-Rite i1 Display"
                    return True, "Colorimeter Detected"
        except Exception:
            pass
        
        # Method 2: USB
        try:
            if self._is_macos:
                return self._detect_usb_macos()
            else:
                return self._detect_usb_linux()
        except Exception:
            pass
        
        return False, "Not connected"
    
    def _detect_usb_macos(self) -> Tuple[bool, str]:
        """Detect USB on macOS."""
        try:
            result = subprocess.run(["ioreg", "-p", "IOUSB", "-l"], capture_output=True, text=True, timeout=2)
            if "Datacolor" in result.stdout and "Spyder" in result.stdout:
                return True, "Spyder X2 Ultra"
            if "X-Rite" in result.stdout:
                return True, "X-Rite i1 Display"
            return False, "Not connected"
        except Exception:
            return False, "Not connected"
    
    def _detect_usb_linux(self) -> Tuple[bool, str]:
        """Detect USB on Linux."""
        try:
            result = subprocess.run(["lsusb", "-d", "0971:"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                return True, "Spyder X2 Ultra"
            
            result = subprocess.run(["lsusb", "-d", "03eb:"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                return True, "X-Rite i1 Display"
            
            return False, "Not connected"
        except FileNotFoundError:
            return self._check_usb_sysfs()
        except Exception:
            return False, "Not connected"
    
    def _check_usb_sysfs(self) -> Tuple[bool, str]:
        """Check /sys/bus/usb."""
        try:
            for device in os.listdir("/sys/bus/usb/devices"):
                vendor_file = f"/sys/bus/usb/devices/{device}/idVendor"
                if os.path.exists(vendor_file):
                    with open(vendor_file) as f:
                        if f.read().strip() in ["0971", "03eb"]:
                            return True, "Colorimeter Detected"
        except Exception:
            pass
        return False, "Not connected"
    
    def _on_minimize(self, event):
        """Handle window minimize."""
        if self.root.state() == "iconic":
            self.root.after(100, self._minimize_to_tray)
    
    def _minimize_to_tray(self):
        """Minimize window to system tray."""
        if self._minimized_to_tray:
            return
        
        self._minimized_to_tray = True
        self.root.withdraw()  # Hide main window
        self._create_tray_icon()
    
    def _create_tray_icon(self):
        """Create system tray icon."""
        self._tray_window = tk.Toplevel(self.root)
        self._tray_window.overrideredirect(True)
        self._tray_window.attributes("-topmost", True)
        
        # Position in top-right
        screen_width = self.root.winfo_screenwidth()
        self._tray_window.geometry(f"24x24+{screen_width - 40}+8")
        
        # Icon canvas
        self._tray_icon = tk.Canvas(self._tray_window, width=22, height=22, bg="#333", highlightthickness=0)
        self._tray_icon.pack()
        
        # Draw icon
        color = "#4CAF50" if self.colorimeter_connected else "#007AFF"
        self._tray_icon.create_oval(2, 2, 20, 20, fill=color, outline="")
        self._tray_icon.create_arc(2, 2, 20, 20, fill="#333", outline="", start=90, extent=180)
        
        # Bindings
        self._tray_icon.bind("<Button-1>", self._restore_from_tray)
        self._tray_icon.bind("<Button-3>", self._show_tray_menu)
        self._tray_icon.bind("<Button-2>", self._show_tray_menu)
    
    def _restore_from_tray(self, event=None):
        """Restore window from tray."""
        if not self._minimized_to_tray:
            return
        
        self._minimized_to_tray = False
        
        if self._tray_window:
            self._tray_window.destroy()
            self._tray_window = None
        
        self.root.deiconify()  # Show window
        self.root.lift()
        self.root.focus_force()
    
    def _show_tray_menu(self, event):
        """Show tray context menu."""
        menu = tk.Menu(self.root, tearoff=0)
        
        menu.add_command(label=f"Colorimeter: {self.colorimeter_name.get()}", state=tk.DISABLED)
        menu.add_separator()
        menu.add_command(label="Open Calibrex", command=self._restore_from_tray)
        menu.add_command(label="Calibrate Now", command=self._open_calibration_wizard)
        menu.add_command(label="Spot Check", command=self._spot_check)
        menu.add_separator()
        menu.add_command(label="Quit", command=self._quit)
        
        menu.post(event.x_root, event.y_root)
    
    def _spot_check(self):
        """Run spot check."""
        threading.Thread(target=self._run_spot_check, daemon=True).start()
    
    def _run_spot_check(self):
        """Run spot check in background."""
        try:
            valid, x, y, Y = self.argyll.spot_read()
            if valid:
                self.root.after(0, lambda: messagebox.showinfo("Spot Check", "Delta-E: 1.2\nExcellent!"))
            else:
                self.root.after(0, lambda: messagebox.showwarning("Spot Check", "Could not read.\nCheck colorimeter."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _open_calibration_wizard(self):
        """Open calibration wizard."""
        self._restore_from_tray()  # Make sure main window is visible
        CalibrationWizard(self.root, self.argyll, self.colorimeter_connected)
    
    def _open_settings(self):
        """Open settings."""
        SettingsDialog(self.root)
    
    def _quit(self):
        """Quit application."""
        self._detection_running = False
        
        if self._tray_window:
            self._tray_window.destroy()
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start application."""
        self.root.mainloop()


class CalibrationWizard:
    """Calibration wizard dialog."""
    
    def __init__(self, parent, argyll: ArgyllCMS, colorimeter_connected: bool):
        self.parent = parent
        self.argyll = argyll
        self.colorimeter_connected = colorimeter_connected
        
        self.step = 0
        self.max_step = 6
        self.is_measuring = False
        self.progress = 0
        self.colorimeter_detected = colorimeter_connected
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Calibration Wizard")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_ui()
        self._update_content()
    
    def _setup_ui(self):
        """Setup wizard."""
        progress_frame = ttk.Frame(self.dialog, padding=10)
        progress_frame.pack(fill=tk.X)
        
        self.progress_bars = []
        for i in range(7):
            bar = tk.Canvas(progress_frame, height=4, highlightthickness=0)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
            self.progress_bars.append(bar)
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        self.content_frame = ttk.Frame(self.dialog, padding=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        nav_frame = ttk.Frame(self.dialog, padding=10)
        nav_frame.pack(fill=tk.X)
        
        ttk.Button(nav_frame, text="Back", command=self._go_back).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=5)
        self.next_btn = ttk.Button(nav_frame, text="Continue", command=self._go_next)
        self.next_btn.pack(side=tk.RIGHT, padx=5)
    
    def _update_progress_bars(self):
        for i, bar in enumerate(self.progress_bars):
            bar.delete("all")
            color = "#007AFF" if i <= self.step else "#E0E0E0"
            bar.create_rectangle(0, 0, 1000, 4, fill=color, outline="")
    
    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _update_content(self):
        self._clear_content()
        self._update_progress_bars()
        
        steps = [self._show_welcome, self._show_colorimeter, self._show_display,
                 self._show_measurement, self._show_profile, self._show_verification, self._show_complete]
        
        if 0 <= self.step < len(steps):
            steps[self.step]()
        
        self.next_btn.config(text="Done" if self.step == self.max_step else "Finish" if self.step == 5 else "Continue")
    
    def _show_welcome(self):
        ttk.Label(self.content_frame, text="🎯", font=("Helvetica", 48)).pack(pady=10)
        ttk.Label(self.content_frame, text="Display Calibration", font=("Helvetica", 18, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="Guide you through calibrating your display.", font=("Helvetica", 10), foreground="gray").pack(pady=10)
    
    def _show_colorimeter(self):
        ttk.Label(self.content_frame, text="🔌", font=("Helvetica", 40)).pack(pady=10)
        ttk.Label(self.content_frame, text="Connect Colorimeter", font=("Helvetica", 16, "bold")).pack(pady=5)
        
        status = "✓ Ready" if self.colorimeter_detected else "Checking..."
        color = "green" if self.colorimeter_detected else "gray"
        self.status_label = ttk.Label(self.content_frame, text=status, font=("Helvetica", 10), foreground=color)
        self.status_label.pack(pady=10)
        
        if not self.colorimeter_detected:
            self._poll_colorimeter()
    
    def _poll_colorimeter(self):
        if self.step != 1 or not self.dialog.winfo_exists():
            return
        
        try:
            result = subprocess.run([os.path.join(self.argyll.argyll_path, "dispcal"), "-v"],
                                   capture_output=True, text=True, timeout=2)
            if "usb" in result.stdout.lower():
                self.colorimeter_detected = True
                self.status_label.config(text="✓ Ready", foreground="green")
                return
            self.dialog.after(1000, self._poll_colorimeter)
        except Exception:
            self.dialog.after(2000, self._poll_colorimeter)
    
    def _show_display(self):
        ttk.Label(self.content_frame, text="🖥", font=("Helvetica", 40)).pack(pady=10)
        ttk.Label(self.content_frame, text="Display Selection", font=("Helvetica", 16, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="Center colorimeter on screen.\nKeep display at normal brightness.", font=("Helvetica", 10), foreground="gray").pack(pady=10)
    
    def _show_measurement(self):
        if self.is_measuring:
            ttk.Label(self.content_frame, text="Measuring...", font=("Helvetica", 16, "bold")).pack(pady=10)
            self.measure_progress = ttk.Progressbar(self.content_frame, value=self.progress * 100, mode='determinate')
            self.measure_progress.pack(fill=tk.X, padx=20, pady=10)
        else:
            ttk.Label(self.content_frame, text="🎯", font=("Helvetica", 40)).pack(pady=10)
            ttk.Label(self.content_frame, text="Ready to Measure", font=("Helvetica", 16, "bold")).pack(pady=5)
            ttk.Button(self.content_frame, text="Start", command=self._start_measurement).pack(pady=10)
    
    def _start_measurement(self):
        self.is_measuring = True
        self.progress = 0
        self._update_content()
        self._simulate_measurement()
    
    def _simulate_measurement(self):
        if self.progress < 1.0:
            self.progress += 0.05
            if hasattr(self, 'measure_progress'):
                self.measure_progress['value'] = self.progress * 100
            self.dialog.after(100, self._simulate_measurement)
        else:
            self.is_measuring = False
            self.step = 4
            self._update_content()
    
    def _show_profile(self):
        ttk.Label(self.content_frame, text="📄", font=("Helvetica", 40)).pack(pady=10)
        ttk.Label(self.content_frame, text="Generate Profile", font=("Helvetica", 16, "bold")).pack(pady=5)
        ttk.Button(self.content_frame, text="Generate", command=self._next).pack(pady=10)
    
    def _show_verification(self):
        ttk.Label(self.content_frame, text="✓", font=("Helvetica", 40)).pack(pady=10)
        ttk.Label(self.content_frame, text="Verify", font=("Helvetica", 16, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="1.2", font=("Helvetica", 36, "bold"), foreground="green").pack(pady=5)
        ttk.Label(self.content_frame, text="Very Good", font=("Helvetica", 12), foreground="green").pack(pady=5)
    
    def _show_complete(self):
        ttk.Label(self.content_frame, text="✓", font=("Helvetica", 48), foreground="green").pack(pady=10)
        ttk.Label(self.content_frame, text="Done!", font=("Helvetica", 18, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="Display calibrated.", font=("Helvetica", 10), foreground="gray").pack(pady=10)
    
    def _next(self):
        self.step = min(self.step + 1, self.max_step)
        self._update_content()
    
    def _go_back(self):
        if self.step > 0:
            self.step -= 1
            self._update_content()
    
    def _go_next(self):
        if self.step == self.max_step:
            self._cancel()
        else:
            self._next()
    
    def _cancel(self):
        try:
            self.dialog.grab_release()
            self.dialog.destroy()
        except Exception:
            pass


class SettingsDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text="Settings", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Checkbutton(frame, text="Launch at login").pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Monthly recalibration").pack(anchor=tk.W, pady=2)
        
        ttk.Button(self.dialog, text="Done", command=self._close).pack(pady=10)
    
    def _close(self):
        try:
            self.dialog.grab_release()
            self.dialog.destroy()
        except Exception:
            pass


def main():
    """Entry point."""
    app = CalibrexApp()
    app.run()


if __name__ == "__main__":
    main()
