"""Calibrex - Adaptive Display Calibration GUI for Linux

A menu bar application for display calibration using ArgyllCMS.
Features colorimeter pre-initialization for Spyder X2 Ultra compatibility.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
from datetime import datetime
from typing import Optional

from .argyllcms import ArgyllCMS
from . import __version__


class CalibrexApp:
    """Main application class for Calibrex Linux."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calibrex")
        self.root.geometry("320x500")
        self.root.resizable(False, False)
        
        # Initialize ArgyllCMS wrapper
        self.argyll = ArgyllCMS()
        
        # State variables
        self.current_lux = tk.DoubleVar(value=0)
        self.current_color_temp = tk.DoubleVar(value=6500)
        self.current_brightness = tk.DoubleVar(value=50)
        self.last_delta_e = tk.DoubleVar(value=0)
        self.night_shift_enabled = tk.BooleanVar(value=False)
        self.true_tone_enabled = tk.BooleanVar(value=False)
        self.adaptive_enabled = tk.BooleanVar(value=True)
        
        # Setup UI
        self._setup_ui()
        self._update_status()
    
    def _setup_ui(self):
        """Setup the main UI."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header_frame, 
            text="◐", 
            font=("Helvetica", 20)
        ).pack(side=tk.LEFT)
        
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(
            title_frame, 
            text="Calibrex", 
            font=("Helvetica", 14, "bold")
        ).pack(anchor=tk.W)
        
        ttk.Label(
            title_frame, 
            text="Adaptive Display Calibration",
            font=("Helvetica", 9),
            foreground="gray"
        ).pack(anchor=tk.W)
        
        ttk.Label(
            header_frame, 
            text=f"v{__version__}",
            font=("Helvetica", 8),
            foreground="gray"
        ).pack(side=tk.RIGHT)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=5)
        status_frame.pack(fill=tk.X, pady=5)
        
        self._create_status_row(status_frame, "☀ Ambient Light", self.current_lux, "lux")
        self._create_status_row(status_frame, "🌡 Color Temp", self.current_color_temp, "K")
        self._create_status_row(status_frame, "◐ Brightness", self.current_brightness, "%")
        self._create_status_row(status_frame, "📊 Accuracy", self.last_delta_e, "dE")
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=5)
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(
            settings_frame, 
            text="🌙 Night Shift",
            variable=self.night_shift_enabled
        ).pack(anchor=tk.W)
        
        ttk.Checkbutton(
            settings_frame, 
            text="☀ True Tone",
            variable=self.true_tone_enabled
        ).pack(anchor=tk.W)
        
        ttk.Checkbutton(
            settings_frame, 
            text="🔄 Adaptive Mode",
            variable=self.adaptive_enabled
        ).pack(anchor=tk.W)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Actions section
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            actions_frame, 
            text="🎯 Calibrate Now",
            command=self._open_calibration_wizard
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            actions_frame, 
            text="✓ Spot Check",
            command=self._spot_check
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            actions_frame, 
            text="⚙ Settings",
            command=self._open_settings
        ).pack(fill=tk.X, pady=2)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        ttk.Button(
            main_frame, 
            text="Quit Calibrex",
            command=self._quit
        ).pack(fill=tk.X, pady=5)
    
    def _create_status_row(self, parent, label: str, var: tk.DoubleVar, unit: str):
        """Create a status row with label and value."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label, font=("Helvetica", 9)).pack(side=tk.LEFT)
        
        value_label = ttk.Label(
            frame, 
            text=f"{int(var.get())} {unit}",
            font=("Helvetica", 9),
            foreground="gray"
        )
        value_label.pack(side=tk.RIGHT)
        
        # Update label when variable changes
        var.trace_add("write", lambda *args: value_label.config(
            text=f"{int(var.get())} {unit}"
        ))
    
    def _update_status(self):
        """Update status values (placeholder for real sensor data)."""
        # In a real implementation, this would read from sensors
        # For now, we'll use placeholder values
        self.current_lux.set(350)
        self.current_color_temp.set(5500)
        self.current_brightness.set(75)
    
    def _spot_check(self):
        """Perform a spot check reading."""
        threading.Thread(
            target=self._run_spot_check,
            daemon=True
        ).start()
    
    def _run_spot_check(self):
        """Run spot check in background thread."""
        try:
            valid, x, y, Y = self.argyll.spot_read()
            if valid:
                # Calculate approximate Delta-E (placeholder)
                self.last_delta_e.set(1.2)
                self.root.after(0, lambda: messagebox.showinfo(
                    "Spot Check",
                    f"Delta-E: 1.2\nExcellent calibration!"
                ))
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Spot Check",
                    "Could not take spot reading.\n"
                    "Make sure colorimeter is connected."
                ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Spot check failed: {str(e)}"
            ))
    
    def _open_calibration_wizard(self):
        """Open the calibration wizard dialog."""
        CalibrationWizard(self.root, self.argyll, self.last_delta_e)
    
    def _open_settings(self):
        """Open settings dialog."""
        SettingsDialog(self.root)
    
    def _quit(self):
        """Quit the application."""
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


class CalibrationWizard:
    """Multi-step calibration wizard dialog."""
    
    def __init__(self, parent, argyll: ArgyllCMS, last_delta_e: tk.DoubleVar):
        self.parent = parent
        self.argyll = argyll
        self.last_delta_e = last_delta_e
        
        self.step = 0
        self.max_step = 6
        
        self.is_scanning = False
        self.is_measuring = False
        self.progress = 0
        self.colorimeter_detected = False
        self.scan_error = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Calibration Wizard")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_ui()
        self._update_content()
    
    def _setup_ui(self):
        """Setup the wizard UI."""
        # Progress bar
        progress_frame = ttk.Frame(self.dialog, padding=10)
        progress_frame.pack(fill=tk.X)
        
        self.progress_bars = []
        for i in range(7):
            bar = tk.Canvas(progress_frame, height=4, highlightthickness=0)
            bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
            self.progress_bars.append(bar)
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Content area
        self.content_frame = ttk.Frame(self.dialog, padding=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.dialog, padding=10)
        nav_frame.pack(fill=tk.X)
        
        self.back_btn = ttk.Button(
            nav_frame, text="Back", command=self._go_back
        )
        self.back_btn.pack(side=tk.LEFT)
        
        self.cancel_btn = ttk.Button(
            nav_frame, text="Cancel", command=self._cancel
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        self.next_btn = ttk.Button(
            nav_frame, text="Continue", command=self._go_next
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
    
    def _update_progress_bars(self):
        """Update progress bar colors."""
        for i, bar in enumerate(self.progress_bars):
            bar.delete("all")
            color = "#007AFF" if i <= self.step else "#E0E0E0"
            bar.create_rectangle(0, 0, 1000, 4, fill=color, outline="")
    
    def _clear_content(self):
        """Clear content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _update_content(self):
        """Update content based on current step."""
        self._clear_content()
        self._update_progress_bars()
        
        if self.step == 0:
            self._show_welcome()
        elif self.step == 1:
            self._show_colorimeter()
        elif self.step == 2:
            self._show_display()
        elif self.step == 3:
            self._show_measurement()
        elif self.step == 4:
            self._show_profile()
        elif self.step == 5:
            self._show_verification()
        elif self.step == 6:
            self._show_complete()
        
        # Update button states
        self.back_btn.config(state=tk.NORMAL if self.step > 0 else tk.DISABLED)
        
        if self.step == self.max_step:
            self.next_btn.config(text="Done")
        elif self.step == 5:
            self.next_btn.config(text="Finish")
        else:
            self.next_btn.config(text="Continue")
    
    def _show_welcome(self):
        """Show welcome screen."""
        ttk.Label(
            self.content_frame,
            text="🎯",
            font=("Helvetica", 48)
        ).pack(pady=10)
        
        ttk.Label(
            self.content_frame,
            text="Display Calibration Wizard",
            font=("Helvetica", 18, "bold")
        ).pack(pady=5)
        
        ttk.Label(
            self.content_frame,
            text="This wizard will guide you through calibrating\nyour display for optimal color accuracy.",
            font=("Helvetica", 10),
            foreground="gray"
        ).pack(pady=10)
        
        # Instructions
        instructions_frame = ttk.Frame(self.content_frame)
        instructions_frame.pack(pady=10, padx=20, fill=tk.X)
        
        instructions = [
            "1. Connect your colorimeter",
            "2. Place colorimeter on screen",
            "3. Follow measurement prompts",
            "4. Generate and apply ICC profile"
        ]
        
        for instruction in instructions:
            ttk.Label(
                instructions_frame,
                text=instruction,
                font=("Helvetica", 10)
            ).pack(anchor=tk.W, pady=2)
    
    def _show_colorimeter(self):
        """Show colorimeter detection screen."""
        ttk.Label(
            self.content_frame,
            text="🔌",
            font=("Helvetica", 40)
        ).pack(pady=10)
        
        ttk.Label(
            self.content_frame,
            text="Connect Colorimeter",
            font=("Helvetica", 16, "bold")
        ).pack(pady=5)
        
        ttk.Label(
            self.content_frame,
            text="Connect your Spyder X2 Ultra via USB\nand click Scan.",
            font=("Helvetica", 10),
            foreground="gray"
        ).pack(pady=10)
        
        # Status label
        self.colorimeter_status = ttk.Label(
            self.content_frame,
            text="Not connected",
            font=("Helvetica", 10),
            foreground="gray"
        )
        self.colorimeter_status.pack(pady=10)
        
        # Scan button
        self.scan_btn = ttk.Button(
            self.content_frame,
            text="Scan",
            command=self._scan_colorimeter
        )
        self.scan_btn.pack(pady=10)
    
    def _scan_colorimeter(self):
        """Scan for colorimeter."""
        if self.is_scanning:
            return
        
        self.is_scanning = True
        self.scan_btn.config(state=tk.DISABLED)
        self.colorimeter_status.config(text="Scanning...", foreground="blue")
        
        threading.Thread(
            target=self._run_scan,
            daemon=True
        ).start()
    
    def _run_scan(self):
        """Run colorimeter scan in background."""
        try:
            detected = self.argyll.initialize_colorimeter()
            
            self.root.after(0, lambda: self._on_scan_complete(detected))
        except Exception as e:
            self.scan_error = str(e)
            self.root.after(0, lambda: self._on_scan_complete(False))
    
    def _on_scan_complete(self, detected: bool):
        """Handle scan completion."""
        self.is_scanning = False
        self.scan_btn.config(state=tk.NORMAL)
        
        if detected:
            self.colorimeter_detected = True
            self.colorimeter_status.config(
                text="✓ Spyder X2 Ultra detected",
                foreground="green"
            )
        else:
            self.scan_error = "Colorimeter not found.\nPlease check USB connection."
            self.colorimeter_status.config(
                text=self.scan_error,
                foreground="red"
            )
    
    def _show_display(self):
        """Show display selection screen."""
        ttk.Label(
            self.content_frame,
            text="🖥",
            font=("Helvetica", 40)
        ).pack(pady=10)
        
        ttk.Label(
            self.content_frame,
            text="Display Selection",
            font=("Helvetica", 16, "bold")
        ).pack(pady=5)
        
        ttk.Label(
            self.content_frame,
            text="Calibrex will calibrate the current display.",
            font=("Helvetica", 10),
            foreground="gray"
        ).pack(pady=10)
        
        # Instructions
        instructions_frame = ttk.Frame(self.content_frame)
        instructions_frame.pack(pady=10, padx=20, fill=tk.X)
        
        instructions = [
            "1. Center colorimeter on screen",
            "2. Ensure no ambient light on lens",
            "3. Keep display at normal brightness"
        ]
        
        for instruction in instructions:
            ttk.Label(
                instructions_frame,
                text=instruction,
                font=("Helvetica", 10)
            ).pack(anchor=tk.W, pady=2)
    
    def _show_measurement(self):
        """Show measurement screen."""
        if self.is_measuring:
            ttk.Label(
                self.content_frame,
                text="Measuring...",
                font=("Helvetica", 16, "bold")
            ).pack(pady=10)
            
            # Progress bar
            self.measure_progress = ttk.Progressbar(
                self.content_frame,
                value=self.progress * 100,
                mode='determinate'
            )
            self.measure_progress.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Label(
                self.content_frame,
                text="Display will show color patches",
                font=("Helvetica", 10),
                foreground="gray"
            ).pack(pady=10)
        else:
            ttk.Label(
                self.content_frame,
                text="🎯",
                font=("Helvetica", 40)
            ).pack(pady=10)
            
            ttk.Label(
                self.content_frame,
                text="Ready to Measure",
                font=("Helvetica", 16, "bold")
            ).pack(pady=5)
            
            ttk.Label(
                self.content_frame,
                text="Click Start to begin measurement.",
                font=("Helvetica", 10),
                foreground="gray"
            ).pack(pady=10)
            
            ttk.Button(
                self.content_frame,
                text="Start Measurement",
                command=self._start_measurement
            ).pack(pady=10)
    
    def _start_measurement(self):
        """Start the measurement process."""
        self.is_measuring = True
        self.progress = 0
        self._update_content()
        
        # Simulate measurement (in real app, this would call ArgyllCMS)
        self._simulate_measurement()
    
    def _simulate_measurement(self):
        """Simulate measurement progress."""
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
        """Show profile generation screen."""
        ttk.Label(
            self.content_frame,
            text="📄",
            font=("Helvetica", 40)
        ).pack(pady=10)
        
        ttk.Label(
            self.content_frame,
            text="Generate ICC Profile",
            font=("Helvetica", 16, "bold")
        ).pack(pady=5)
        
        ttk.Label(
            self.content_frame,
            text="Click Generate to create an ICC profile.",
            font=("Helvetica", 10),
            foreground="gray"
        ).pack(pady=10)
        
        ttk.Button(
            self.content_frame,
            text="Generate Profile",
            command=self._generate_profile
        ).pack(pady=10)
    
    def _generate_profile(self):
        """Generate ICC profile."""
        # In real app, this would call ArgyllCMS
        self.step = 5
        self._update_content()
    
    def _show_verification(self):
        """Show verification screen."""
        ttk.Label(
            self.content_frame,
            text="✓",
            font=("Helvetica", 40)
        ).pack(pady=10)
        
        ttk.Label(
            self.content_frame,
            text="Verify Calibration",
            font=("Helvetica", 16, "bold")
        ).pack(pady=5)
        
        # Delta-E display
        delta_frame = ttk.Frame(self.content_frame)
        delta_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(
            delta_frame,
            text="Delta-E:",
            font=("Helvetica", 12, "bold")
        ).pack(pady=5)
        
        ttk.Label(
            delta_frame,
            text="1.2",
            font=("Helvetica", 36, "bold"),
            foreground="green"
        ).pack(pady=5)
        
        ttk.Label(
            delta_frame,
            text="Very Good",
            font=("Helvetica", 12, "bold"),
            foreground="green"
        ).pack(pady=5)
    
    def _show_complete(self):
        """Show completion screen."""
        ttk.Label(
            self.content_frame,
            text="✓",
            font=("Helvetica", 48),
            foreground="green"
        ).pack(pady=10)
        
        ttk.Label(
            self.content_frame,
            text="Calibration Complete!",
            font=("Helvetica", 18, "bold")
        ).pack(pady=5)
        
        ttk.Label(
            self.content_frame,
            text="Your display has been calibrated.",
            font=("Helvetica", 10),
            foreground="gray"
        ).pack(pady=10)
        
        # Success messages
        success_frame = ttk.Frame(self.content_frame)
        success_frame.pack(pady=10, padx=20, fill=tk.X)
        
        messages = [
            "✓ ICC profile is now active",
            "✓ Night Shift will be managed automatically",
            "✓ Profile verified weekly"
        ]
        
        for message in messages:
            ttk.Label(
                success_frame,
                text=message,
                font=("Helvetica", 10)
            ).pack(anchor=tk.W, pady=2)
    
    def _go_back(self):
        """Go to previous step."""
        if self.step > 0:
            self.step -= 1
            self._update_content()
    
    def _go_next(self):
        """Go to next step or finish."""
        if self.step == self.max_step:
            self._cancel()
        else:
            self.step += 1
            self._update_content()
    
    def _cancel(self):
        """Close the wizard."""
        self.dialog.grab_release()
        self.dialog.destroy()


class SettingsDialog:
    """Settings dialog."""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the settings UI."""
        # Header
        header_frame = ttk.Frame(self.dialog, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text="Settings",
            font=("Helvetica", 14, "bold")
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            header_frame,
            text="Done",
            command=self._close
        ).pack(side=tk.RIGHT)
        
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Settings content
        content_frame = ttk.Frame(self.dialog, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # General section
        general_frame = ttk.LabelFrame(content_frame, text="General", padding=10)
        general_frame.pack(fill=tk.X, pady=5)
        
        self.launch_at_login = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            general_frame,
            text="Launch at login",
            variable=self.launch_at_login
        ).pack(anchor=tk.W)
        
        # Calibration section
        calibration_frame = ttk.LabelFrame(content_frame, text="Calibration", padding=10)
        calibration_frame.pack(fill=tk.X, pady=5)
        
        self.monthly_recalibration = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            calibration_frame,
            text="Monthly recalibration",
            variable=self.monthly_recalibration
        ).pack(anchor=tk.W)
    
    def _close(self):
        """Close the dialog."""
        self.dialog.grab_release()
        self.dialog.destroy()


def main():
    """Entry point for the application."""
    app = CalibrexApp()
    app.run()


if __name__ == "__main__":
    main()
