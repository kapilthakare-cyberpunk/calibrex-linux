"""Setup script for Calibrex Linux."""

from setuptools import setup, find_packages

setup(
    name="calibrex",
    version="0.1.0",
    description="Adaptive Display Calibration for Linux",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Calibrex Team",
    author_email="calibrex@example.com",
    url="https://github.com/kapilthakare-cyberpunk/calibrex",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "calibrex": ["*.png", "*.ico"],
    },
    python_requires=">=3.8",
    install_requires=[
        # Tkinter is included with Python on most systems
        # No additional dependencies required
    ],
    entry_points={
        "console_scripts": [
            "calibrex=calibrex.gui:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Hardware",
        "Topic :: Multimedia :: Graphics",
    ],
)
