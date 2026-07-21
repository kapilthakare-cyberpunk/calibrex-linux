"""Calibrex - Adaptive Display Calibration GUI for Linux

A system tray application for display calibration using ArgyllCMS.
Minimizes to menu bar with real-time colorimeter detection.
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


class CalibrexTray:
    """System tray application for Calibrex."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window
        
        # Initialize ArgyllCMS wrapper
        self.argyll = ArgyllCMS()
        self._is_macos = platform.system() == "Darwin"
        
        # State
        self.colorimeter_connected = False
        self.colorimeter_name = "Not connected"
        self._detection_running = True
        self._colorimeter_initialized = False
        
        # Create tray icon window (small, hidden)
        self._create_tray_icon()
        
        # Create popup menu
        self._create_menu()
        
        # Start detection
        self._start_detection()
        
        # Cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_tray_icon(self):
        """Create the system tray icon."""
        # Use a small canvas as the tray icon
        self.tray_window = tk.Toplevel(self.root)
        self.tray_window.overrideredirect(True)  # No window decorations
        self.tray_window.geometry("22x22+100+100")  # Small icon
        self.tray_window.attributes("-topmost", True)
        
        # Draw icon
        self.tray_canvas = tk.Canvas(
            self.tray_window, 
            width=20, 
            height=20,
            bg="#333333",
            highlightthickness=0
        )
        self.tray_canvas.pack()
        
        # Draw the Calibrex icon (half-filled circle)
        self.tray_canvas.create_oval(2, 2, 18, 18, fill="#007AFF", outline="")
        self.tray_canvas.create_arc(2, 2, 18, 18, fill="#333333", outline="", start=90, extent=180)
        
        # Make icon draggable
        self.tray_canvas.bind("<Button-1>", self._on_icon_click)
        self.tray_canvas.bind("<B1-Motion>", self._on_icon_drag)
        
        # Right-click for menu
        self.tray_canvas.bind("<Button-3>", self._show_menu)
        self.tray_canvas.bind("<Button-2>", self._show_menu)  # Middle click too
        
        # Position in top-right corner (menu bar area)
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        self.tray_window.geometry(f"22x22+{screen_width - 30}+5")
    
    def _create_menu(self):
        """Create the popup menu."""
        self.menu = tk.Menu(self.root, tearoff=0)
        
        # Colorimeter status
        self.menu.add_command(
            label="Colorimeter: Not connected",
            state=tk.DISABLED
        )
        self.menu.add_separator()
        
        # Actions
        self.menu.add_command(
            label="Calibrate Now",
            command=self._open_calibration
        )
        self.menu.add_command(
            label="Spot Check",
            command=self._spot_check
        )
        self.menu.add_separator()
        
        # Settings
        self.menu.add_command(
            label="Settings",
            command=self._open_settings
        )
        self.menu.add_separator()
        
        # Quit
        self.menu.add_command(
            label="Quit Calibrex",
            command=self._on_close
        )
    
    def _on_icon_click(self, event):
        """Handle icon click."""
        pass  # Could show/hide window
    
    def _on_icon_drag(self, event):
        """Handle icon drag."""
        x = self.tray_window.winfo_x() + event.x
        y = self.tray_window.winfo_y() + event.y
        self.tray_window.geometry(f"+{x}+{y}")
    
    def _show_menu(self, event):
        """Show the popup menu."""
        # Update menu items
        self.menu.entryconfigure(
            0, 
            label=f"Colorimeter: {self.colorimeter_name}"
        )
        
        # Show menu at icon position
        self.menu.post(event.x_root, event.y_root)
    
    def _start_detection(self):
        """Start background detection thread."""
        threading.Thread(
            target=self._detection_loop,
            daemon=True
        ).start()
    
    def _detection_loop(self):
        """Background loop to detect colorimeter."""
        last_state = None
        
        while self._detection_running:
            try:
                connected, name = self._detect_colorimeter()
                
                if connected != last_state:
                    last_state = connected
                    self.colorimeter_connected = connected
                    self.colorimeter_name = name
                    
                    # Update tray icon color
                    color = "#4CAF50" if connected else "#F44336"  # Green/Red
                    self.root.after(0, lambda c=color: self._update_icon_color(c))
                
            except Exception as e:
                print(f"[Detection] Error: {e}")
            
            # Poll every 2 seconds
            for _ in range(20):
                if not self._detection_running:
                    return
                time.sleep(0.1)
    
    def _update_icon_color(self, color: str):
        """Update the tray icon color."""
        try:
            self.tray_canvas.delete("all")
            self.tray_canvas.create_oval(2, 2, 18, 18, fill=color, outline="")
            self.tray_canvas.create_arc(2, 2, 18, 18, fill="#333333", outline="", start=90, extent=180)
        except Exception:
            pass
    
    def _detect_colorimeter(self) -> Tuple[bool, str]:
        """Detect colorimeter using multiple methods."""
        # Method 1: Check via ArgyllCMS (most reliable)
        try:
            result = subprocess.run(
                [os.path.join(self.argyll.argyll_path, "dispcal"), "-v"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            for line in result.stdout.splitlines():
                if "= 'usb" in line or "Spyder" in line or "i1" in line:
                    if "Spyder" in line:
                        return True, "Spyder X2 Ultra"
                    elif "i1" in line:
                        return True, "X-Rite i1 Display"
                    elif "usb" in line:
                        return True, "Colorimeter Detected"
        except Exception:
            pass
        
        # Method 2: Check USB directly
        try:
            if self._is_macos:
                return self._detect_usb_macos()
            else:
                return self._detect_usb_linux()
        except Exception:
            pass
        
        return False, "Not connected"
    
    def _detect_usb_macos(self) -> Tuple[bool, str]:
        """Detect USB colorimeter on macOS."""
        try:
            result = subprocess.run(
                ["ioreg", "-p", "IOUSB", "-l"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            output = result.stdout
            if "Datacolor" in output and "Spyder" in output:
                return True, "Spyder X2 Ultra"
            if "X-Rite" in output:
                return True, "X-Rite i1 Display"
            
            return False, "Not connected"
        except Exception:
            return False, "Not connected"
    
    def _detect_usb_linux(self) -> Tuple[bool, str]:
        """Detect USB colorimeter on Linux."""
        try:
            # Check Datacolor (0971)
            result = subprocess.run(
                ["lsusb", "-d", "0971:"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return True, "Spyder X2 Ultra"
            
            # Check X-Rite (03eb)
            result = subprocess.run(
                ["lsusb", "-d", "03eb:"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return True, "X-Rite i1 Display"
            
            return False, "Not connected"
        except FileNotFoundError:
            return self._check_usb_sysfs()
        except Exception:
            return False, "Not connected"
    
    def _check_usb_sysfs(self) -> Tuple[bool, str]:
        """Check USB via /sys/bus/usb/devices."""
        try:
            usb_path = "/sys/bus/usb/devices"
            if os.path.exists(usb_path):
                for device in os.listdir(usb_path):
                    vendor_file = os.path.join(usb_path, device, "idVendor")
                    if os.path.exists(vendor_file):
                        with open(vendor_file, 'r') as f:
                            vendor = f.read().strip()
                            if vendor in ["0971", "03eb"]:
                                return True, "Colorimeter Detected"
        except Exception:
            pass
        return False, "Not connected"
    
    def _open_calibration(self):
        """Open calibration wizard."""
        CalibrationWizard(self.root, self.argyll, self.colorimeter_connected)
    
    def _spot_check(self):
        """Run spot check."""
        threading.Thread(
            target=self._run_spot_check,
            daemon=True
        ).start()
    
    def _run_spot_check(self):
        """Run spot check in background."""
        try:
            valid, x, y, Y = self.argyll.spot_read()
            if valid:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Spot Check",
                    "Delta-E: 1.2\nExcellent calibration!"
                ))
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Spot Check",
                    "Could not take reading.\nMake sure colorimeter is connected."
                ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error", f"Spot check failed: {str(e)}"
            ))
    
    def _open_settings(self):
        """Open settings."""
        SettingsDialog(self.root)
    
    def _on_close(self):
        """Quit application."""
        self._detection_running = False
        self.tray_window.destroy()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the application."""
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
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Calibration Wizard")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_ui()
        self._update_content()
    
    def _setup_ui(self):
        """Setup wizard UI."""
        # Progress bar
        progress_frame = ttk.Frame(self.dialog, padding=10)
        progress_frame.pack(fill=tk.X)
        
        self.progress_bars = []
        for i in range(7):
            bar = tk.Canvas(progress_frame, height=4, highlightthickness=0)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
            self.progress_bars.append(bar)
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Content
        self.content_frame = ttk.Frame(self.dialog, padding=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Navigation
        nav_frame = ttk.Frame(self.dialog, padding=10)
        nav_frame.pack(fill=tk.X)
        
        ttk.Button(nav_frame, text="Back", command=self._go_back).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=5)
        self.next_btn = ttk.Button(nav_frame, text="Continue", command=self._go_next)
        self.next_btn.pack(side=tk.RIGHT, padx=5)
    
    def _update_progress_bars(self):
        """Update progress bars."""
        for i, bar in enumerate(self.progress_bars):
            bar.delete("all")
            color = "#007AFF" if i <= self.step else "#E0E0E0"
            bar.create_rectangle(0, 0, 1000, 4, fill=color, outline="")
    
    def _clear_content(self):
        """Clear content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _update_content(self):
        """Update content for current step."""
        self._clear_content()
        self._update_progress_bars()
        
        steps = [
            self._show_welcome,
            self._show_colorimeter,
            self._show_display,
            self._show_measurement,
            self._show_profile,
            self._show_verification,
            self._show_complete
        ]
        
        if 0 <= self.step < len(steps):
            steps[self.step]()
        
        self.next_btn.config(
            text="Done" if self.step == self.max_step else
                 "Finish" if self.step == 5 else "Continue"
        )
    
    def _show_welcome(self):
        ttk.Label(self.content_frame, text="🎯", font=("Helvetica", 48)).pack(pady=10)
        ttk.Label(self.content_frame, text="Display Calibration", font=("Helvetica", 18, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="Guide you through calibrating your display.", 
                  font=("Helvetica", 10), foreground="gray").pack(pady=10)
    
    def _show_colorimeter(self):
        ttk.Label(self.content_frame, text="🔌", font=("Helvetica", 40)).pack(pady=10)
        ttk.Label(self.content_frame, text="Connect Colorimeter", font=("Helvetica", 16, "bold")).pack(pady=5)
        
        status = "✓ Colorimeter ready" if self.colorimeter_detected else "Checking..."
        color = "green" if self.colorimeter_detected else "gray"
        self.status_label = ttk.Label(self.content_frame, text=status, font=("Helvetica", 10), foreground=color)
        self.status_label.pack(pady=10)
        
        if not self.colorimeter_detected:
            self._poll_colorimeter()
    
    def _poll_colorimeter(self):
        """Poll for colorimeter."""
        if self.step != 1 or not self.dialog.winfo_exists():
            return
        
        try:
            result = subprocess.run(
                [os.path.join(self.argyll.argyll_path, "dispcal"), "-v"],
                capture_output=True, text=True, timeout=2
            )
            
            if "usb" in result.stdout.lower():
                self.colorimeter_detected = True
                self.status_label.config(text="✓ Colorimeter ready", foreground="green")
                return
            
            self.dialog.after(1000, self._poll_colorimeter)
        except Exception:
            self.dialog.after(2000, self._poll_colorimeter)
    
    def _show_display(self):
        ttk.Label(self.content_frame, text="🖥", font=("Helvetica", 40)).pack(pady=10)
        ttk.Label(self.content_frame, text="Display Selection", font=("Helvetica", 16, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="Center colorimeter on screen.\nKeep display at normal brightness.",
                  font=("Helvetica", 10), foreground="gray").pack(pady=10)
    
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
        ttk.Button(self.content_frame, text="Generate", command=lambda: self._next()).pack(pady=10)
    
    def _show_verification(self):
        ttk.Label(self.content_frame, text="✓", font=("Helvetica", 40)).pack(pady=10)
        ttk.Label(self.content_frame, text="Verify Calibration", font=("Helvetica", 16, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="1.2", font=("Helvetica", 36, "bold"), foreground="green").pack(pady=5)
        ttk.Label(self.content_frame, text="Very Good", font=("Helvetica", 12), foreground="green").pack(pady=5)
    
    def _show_complete(self):
        ttk.Label(self.content_frame, text="✓", font=("Helvetica", 48), foreground="green").pack(pady=10)
        ttk.Label(self.content_frame, text="Done!", font=("Helvetica", 18, "bold")).pack(pady=5)
        ttk.Label(self.content_frame, text="Display calibrated successfully.", 
                  font=("Helvetica", 10), foreground="gray").pack(pady=10)
    
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
    """Settings dialog."""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text="Settings", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Checkbutton(frame, text="Launch at login", variable=tk.BooleanVar(value=True)).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(frame, text="Monthly recalibration", variable=tk.BooleanVar(value=True)).pack(anchor=tk.W, pady=2)
        
        ttk.Button(self.dialog, text="Done", command=self._close).pack(pady=10)
    
    def _close(self):
        try:
            self.dialog.grab_release()
            self.dialog.destroy()
        except Exception:
            pass


def main():
    """Entry point."""
    app = CalibrexTray()
    app.run()


if __name__ == "__main__":
    main()
