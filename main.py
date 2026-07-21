#!/usr/bin/env python3
"""
Calibrex - Adaptive Display Calibration for Linux

A display calibration tool that continuously measures ambient conditions
and adapts display output for optimal color accuracy.
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calibrex.gui import main

if __name__ == "__main__":
    main()
