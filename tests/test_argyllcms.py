"""Tests for ArgyllCMS wrapper."""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calibrex.argyllcms import ArgyllCMS


class TestArgyllCMS(unittest.TestCase):
    """Test cases for ArgyllCMS wrapper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.argyll = ArgyllCMS()
    
    def test_initialization(self):
        """Test ArgyllCMS initialization."""
        self.assertIsNotNone(self.argyll)
        self.assertIsNotNone(self.argyll.argyll_path)
    
    def test_tool_path(self):
        """Test tool path generation."""
        path = self.argyll._tool_path("dispcal")
        self.assertIsInstance(path, str)
        self.assertIn("dispcal", path)
    
    def test_check_dependencies(self):
        """Test dependency checking."""
        deps = self.argyll.check_dependencies()
        self.assertIsInstance(deps, dict)
        
        # Check that we get boolean values
        for tool, available in deps.items():
            self.assertIsInstance(available, bool)
            self.assertIn(tool, ["dispcal", "dispread", "targen", "colprof", 
                                 "dispwin", "spotread", "colormgr"])
    
    def test_list_displays(self):
        """Test display listing."""
        displays = self.argyll.list_displays()
        self.assertIsInstance(displays, list)
    
    def test_initialize_colorimeter(self):
        """Test colorimeter initialization."""
        # This will fail if no colorimeter is connected, but shouldn't crash
        result = self.argyll.initialize_colorimeter()
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
