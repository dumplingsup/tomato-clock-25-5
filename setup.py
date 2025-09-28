#!/usr/bin/env python3
"""Setup script for Tomato Clock package."""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r', encoding='utf-8') as f:
        return f.read()

# Read version from package
def read_version():
    import tomato_clock
    return tomato_clock.__version__

setup(
    name="tomato-clock",
    version=read_version(),
    author="dumplingsup",
    author_email="95017643+dumplingsup@users.noreply.github.com",
    description="A modular Pomodoro timer with terminal and GUI interfaces",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/dumplingsup/tomato-clock-25-5",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        # Core dependencies - no external requirements for basic functionality
    ],
    extras_require={
        "notifications": ["win10toast"],
        "gui": ["Pillow", "pystray"],
        "full": ["win10toast", "Pillow", "pystray"],
    },
    entry_points={
        "console_scripts": [
            "tomato-clock=tomato_clock.terminal_ui:main",
            "tomato-clock-gui=tomato_clock.overlay_ui:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)