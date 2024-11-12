"""Setup script for the FileCombinator package."""

from setuptools import find_packages, setup

setup(
    name="filecombinator",
    use_scm_version=True,
    description="A tool to combine multiple files while preserving directory structure",
    author="Peiman Khorramshahi",
    author_email="peiman@khorramshahi.com",
    packages=find_packages(include=["filecombinator", "filecombinator.*"]),
    install_requires=[
        "python-magic>=0.4.27",
        "click>=8.1.7",
        "rich>=13.9.4",
    ],
    python_requires=">=3.11,<3.12",
    setup_requires=["setuptools_scm"],
    entry_points={
        "console_scripts": [
            "filecombinator=filecombinator.cli:main",
        ],
    },
    include_package_data=True,  # Add this line to include non-Python files
    package_data={
        "filecombinator": [
            "core/*.txt",
            "core/*.yaml",
            "py.typed",
        ],
    },
)
