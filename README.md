# FileCombinator

FileCombinator is a Python tool that combines multiple files while preserving their directory structure, making it easy to share or inspect collections of files.

## Features

- Preserves directory structure when combining files
- Handles various file types (text, binary, image)
- Configurable file and directory exclusions
- Detailed logging with customizable output
- Command-line interface for easy use

## Installation

```bash
pip install filecombinator
```

## Quick Start

```bash
# Process current directory
filecombinator

# Process specific directory
filecombinator -d /path/to/dir

# Exclude specific patterns
filecombinator -e node_modules dist

# Specify output file
filecombinator -o combined_output.txt

# Enable verbose output
filecombinator -v
```

## Configuration

FileCombinator can be configured via a YAML file. Default patterns to exclude:

- `__pycache__`
- `.venv`
- `.git`
- `node_modules`
- And more...

Create a custom config file to override defaults.

## Development

```bash
# Clone the repository
git clone https://github.com/your-username/filecombinator.git
cd filecombinator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
make install

# Run tests
make test

# Run linting
make lint
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
