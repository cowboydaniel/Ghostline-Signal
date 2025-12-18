"""
Setup script for Ghostline Signal.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Get the directory containing this setup.py file
here = Path(__file__).parent.resolve()

# Read the README file
readme_file = here / "README.md"
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")
else:
    long_description = "Ghostline Signal - Peer-to-peer communication system with privacy and locality focus"

setup(
    name="ghostline-signal",
    version="0.1.0",
    author="Ghostline",
    description="Peer-to-peer communication system with privacy and locality focus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.6.0",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ghostline-signal=main:main",
        ],
    },
)
