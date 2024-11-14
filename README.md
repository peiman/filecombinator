# FileCombinator

[![PyPI version](https://img.shields.io/pypi/v/filecombinator.svg)](https://pypi.org/project/filecombinator/)
[![Build Status](https://github.com/peiman/filecombinator/actions/workflows/python-package.yml/badge.svg)](https://github.com/peiman/filecombinator/actions)
[![Coverage](https://codecov.io/gh/peiman/filecombinator/branch/main/graph/badge.svg)](https://codecov.io/gh/peiman/filecombinator)
[![License](https://img.shields.io/github/license/peiman/filecombinator.svg)](https://github.com/peiman/filecombinator/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/filecombinator.svg)](https://pypi.org/project/filecombinator/)

FileCombinator is a Python tool that creates a comprehensive, single-file representation of your codebase, optimized for AI analysis. It preserves directory structure and file content while handling binary files intelligently, making it perfect for sharing your codebase with AI assistants.

## Features

- Creates AI-friendly single-file codebase representation
- Preserves directory structure and file relationships
- Includes source code with proper encoding
- Handles binary/image files by including metadata only
- Configurable file and directory exclusions
- Rich terminal output with progress indication

## Installation

```bash
pip install filecombinator
```

## Usage

Basic usage:

```bash
filecombinator                    # Process current directory
filecombinator -d /path/to/dir    # Process specific directory
filecombinator -o output.txt      # Custom output file
filecombinator -e node_modules    # Exclude patterns
filecombinator -v                 # Verbose output
```

## File Handling

FileCombinator handles files in three different ways:

1. **Regular Files** - Full content included:
   - Source code files
   - Text files
   - Configuration files
   - Documentation

2. **Binary/Image Files** - Included with metadata only:
   - Binary files (executables, compiled files)
   - Image files (.jpg, .png, .gif, etc.)
   - These files appear in the output but their content is omitted

3. **Excluded Files/Directories** - Completely skipped:
   - Cache directories (`__pycache__`, `.cache`)
   - Virtual environments (`.venv`, `env`)
   - Version control (`.git`)
   - Build artifacts (`dist`, `build`)
   - Any patterns specified with `-e` flag

## Output Format

The tool creates a structured output file containing:

```text
# Directory structure
├── src
│   ├── main.py
│   └── utils.py
└── assets
    └── logo.png

# Text files - full content
================== FILE SEPARATOR ==================
FILEPATH: src/main.py
Metadata: Type: Text, Size: 1234 bytes, Last Modified: 2024-11-12 18:31:15
[Full file content included]

# Binary/Image files - metadata included, content omitted
================== FILE SEPARATOR ==================
FILEPATH: assets/logo.png
Metadata: Type: Image, Size: 45678 bytes, Last Modified: 2024-11-12 18:31:15
[Content excluded]

# Excluded files/directories - not included in output at all
.git/, .venv/, __pycache__/, etc.
```

## Configuration

Configuration files can be placed in (in order of priority):

1. Project: `./filecombinator.yaml` or `./.filecombinator.yaml`
2. User: `~/.config/filecombinator/config.yaml` (Unix) or `%APPDATA%\filecombinator\config.yaml` (Windows)
3. System: `/etc/filecombinator/config.yaml` (Unix)

Example configuration:

```yaml
exclude_patterns:
  - "__pycache__"
  - ".venv"
  - "node_modules"

logging:
  default_log_file: "logs/file_combinator.log"
  default_level: "INFO"

output:
  file_suffix: "_file_combinator_output.md"
```

## Development

```bash
git clone https://github.com/your-username/filecombinator.git
cd filecombinator
make venv                 # Create the virtual environment
source .venv/bin/activate # Activate the virtual environment
make install              # Install dependencies
make test                 # Run tests
make lint                 # Run linting
```

## License

MIT License - see [LICENSE](LICENSE) file.
