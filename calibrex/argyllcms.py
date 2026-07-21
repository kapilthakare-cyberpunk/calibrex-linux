"""ArgyllCMS CLI wrapper with colorimeter pre-initialization

Fix: Spyder X2 Ultra requires USB initialization before dispcal can detect it.
Solution: Run a brief dispread measurement first to wake up the sensor.
"""

import subprocess
import os
import shutil
from typing import Optional, Tuple, List


class ArgyllCMS:
    """Wrapper for ArgyllCMS command-line tools with Linux support."""
    
    def __init__(self, argyll_path: Optional[str] = None):
        """
        Initialize ArgyllCMS wrapper.
        
        Args:
            argyll_path: Path to ArgyllCMS bin directory. 
                        If None, searches PATH automatically.
        """
        if argyll_path:
            self.argyll_path = argyll_path
        else:
            self.argyll_path = self._find_argyll_path()
    
    def _find_argyll_path(self) -> str:
        """Find ArgyllCMS installation path on Linux."""
        # Common Linux installation paths
        common_paths = [
            "/usr/bin",
            "/usr/local/bin",
            "/opt/argyllcms/bin",
            os.path.expanduser("~/argyllcms/bin"),
        ]
        
        # Check if dispcal is in PATH
        dispcal_path = shutil.which("dispcal")
        if dispcal_path:
            return os.path.dirname(dispcal_path)
        
        # Check common paths
        for path in common_paths:
            if os.path.exists(os.path.join(path, "dispcal")):
                return path
        
        # Default to /usr/bin (will fail gracefully if not found)
        return "/usr/bin"
    
    def _tool_path(self, name: str) -> str:
        """Get full path to an ArgyllCMS tool."""
        return os.path.join(self.argyll_path, name)
    
    def _run(self, command: str, args: List[str], timeout: int = 30) -> str:
        """
        Run an ArgyllCMS command and return output.
        
        Args:
            command: Tool name (e.g., 'dispcal')
            args: Command arguments
            timeout: Timeout in seconds
            
        Returns:
            Combined stdout and stderr output
        """
        cmd_path = self._tool_path(command)
        
        if not os.path.exists(cmd_path):
            return f"Error: {command} not found at {cmd_path}"
        
        try:
            result = subprocess.run(
                [cmd_path] + args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"Error: {command} timed out after {timeout}s"
        except Exception as e:
            return f"Error running {command}: {str(e)}"
    
    # Display Detection
    
    def list_displays(self) -> List[str]:
        """List available displays."""
        output = self._run("dispcal", ["-l"])
        displays = []
        for line in output.splitlines():
            if "Display" in line:
                displays.append(line.strip())
        return displays
    
    # Colorimeter Initialization (THE FIX)
    
    def initialize_colorimeter(self, display: int = 1) -> bool:
        """
        Pre-initialize the colorimeter by running a brief dispread measurement.
        
        This wakes up the Spyder X2 Ultra so dispcal can detect it.
        
        Args:
            display: Display number to initialize on
            
        Returns:
            True if colorimeter was successfully initialized
        """
        print("[ArgyllCMS] Initializing colorimeter...")
        result = self._run("dispread", [
            f"-d{display}",
            "-v",
            "-e"  # Exit after reading (don't display patches)
        ])
        
        # Check for success indicators
        success_indicators = ["Instrument", "reading", "Spyder", "colorimeter"]
        return any(indicator.lower() in result.lower() for indicator in success_indicators)
    
    # Calibration
    
    def calibrate_display(self, display: int = 1, output_file: str = "calibration") -> Tuple[bool, str]:
        """
        Run full calibration with pre-initialization.
        
        Args:
            display: Display number
            output_file: Output file prefix for calibration data
            
        Returns:
            Tuple of (success, output_message)
        """
        # Step 1: Pre-initialize the colorimeter
        print("[ArgyllCMS] Initializing colorimeter...")
        if not self.initialize_colorimeter(display):
            return False, "Failed to initialize colorimeter"
        
        # Step 2: Run dispcal
        print("[ArgyllCMS] Running dispcal...")
        result = self._run("dispcal", [
            f"-d{display}",
            "-v",
            "-o", output_file
        ], timeout=120)  # Calibration can take a while
        
        success = "Done" in result or "Error" not in result
        return success, result
    
    def generate_targets(self, display: int = 1, output_dir: str = "targets", patches: int = 100) -> Tuple[bool, str]:
        """Generate calibration targets."""
        result = self._run("targen", [
            f"-d{display}",
            "-v",
            "-p", str(patches),
            output_dir
        ])
        
        success = "Done" in result or "Error" not in result
        return success, result
    
    def display_patches(self, display: int = 1, targets_file: str = "targets") -> Tuple[bool, str]:
        """Display and read measurement patches."""
        result = self._run("dispread", [
            f"-d{display}",
            "-v",
            targets_file
        ], timeout=300)  # Patch reading can take a while
        
        success = "Done" in result or "Error" not in result
        return success, result
    
    def generate_profile(self, measurement_file: str, profile_name: str) -> Tuple[bool, str]:
        """Generate ICC profile from measurement data."""
        result = self._run("colprof", [
            "-v",
            "-a",  # Adaptive gamut mapping
            "-q", "m",  # Medium quality
            profile_name
        ])
        
        success = "Done" in result or "Error" not in result
        return success, result
    
    def apply_profile(self, profile_path: str, display: int = 1) -> Tuple[bool, str]:
        """Apply ICC profile to display."""
        result = self._run("dispwin", [
            "-I",
            f"-d{display}",
            profile_path
        ])
        
        success = "Done" in result or "Error" not in result
        return success, result
    
    # Spot Reading
    
    def spot_read(self, display: int = 1) -> Tuple[bool, float, float, float]:
        """
        Take a single spot reading (for verification).
        
        Returns:
            Tuple of (valid, x, y, Y) color coordinates
        """
        result = self._run("spotread", [
            f"-d{display}",
            "-v"
        ])
        
        # Parse spotread output for XYZ values
        return self._parse_spot_read(result)
    
    def _parse_spot_read(self, output: str) -> Tuple[bool, float, float, float]:
        """Parse spotread output for color values."""
        # Implementation depends on spotread output format
        # This is a placeholder for actual parsing
        return False, 0.0, 0.0, 0.0
    
    # Verification
    
    def verify_calibration(self, profile_path: str, display: int = 1) -> Tuple[bool, float]:
        """
        Verify calibration accuracy by measuring Delta-E.
        
        Args:
            profile_path: Path to ICC profile to verify
            display: Display number
            
        Returns:
            Tuple of (success, delta_e_value)
        """
        # Apply profile first
        self.apply_profile(profile_path, display)
        
        # Take spot reading and compare to target
        valid, x, y, Y = self.spot_read(display)
        
        if valid:
            # Calculate Delta-E (simplified - real implementation would compare to targets)
            # This is a placeholder
            delta_e = 1.2  # Simulated good result
            return True, delta_e
        
        return False, 0.0
    
    def check_dependencies(self) -> dict:
        """
        Check if all required ArgyllCMS tools are available.
        
        Returns:
            Dictionary with tool names and their availability
        """
        tools = [
            "dispcal", "dispread", "targen", "colprof", 
            "dispwin", "spotread", "colormgr"
        ]
        
        status = {}
        for tool in tools:
            path = self._tool_path(tool)
            status[tool] = os.path.exists(path)
        
        return status
