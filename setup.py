"""Setup script for the FileCombinator package."""

from setuptools import find_packages, setup

setup(
    name="filecombinator",
    version="0.1.0",
    description="A tool to combine multiple files while preserving directory structure",
    author="Peiman Khorramshahi",
    author_email="peiman@khorramshahi.com",
    packages=find_packages(include=["filecombinator", "filecombinator.*"]),
    install_requires=[
        "python-magic>=0.4.27",
    ],
    python_requires=">=3.11,<3.12",
)