#!/usr/bin/env python3
"""
Setup script for LISA-IR
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lisa-ir",
    version="1.0.0",
    author="LISA-IR Team",
    author_email="lisa-ir@example.com",
    description="Lifting Intermediate Semantic Analysis for Python/C API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lisa-ir/lisa-ir",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "lisa-lift=lisa_ir.cli:main",
        ],
    },
)