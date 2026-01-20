# Email Scraper

A Python application that automatically extracts email addresses from company websites listed in Excel files. Features an intuitive GUI and advanced scraping capabilities.

## Features

- **Multi-layer Email Detection**: 8-layer aggressive scanning system
  - Visible text scanning
  - Raw HTML parsing
  - Mailto link extraction
  - CloudFlare email decoding
  - Form field analysis
  - JavaScript email extraction
  - HTML attribute scanning
  - HTML comment parsing

- **Multi-language Support**: Detects contact pages in 11 languages (EN, FR, DE, ES, IT, PT, NL, PL, RU, AR, TR)

- **Smart Filtering**: Automatically filters out personal emails (Gmail, Hotmail) and system emails (Sentry, Wix)

- **Multi-sheet Excel Support**: Process Excel files with multiple sheets, preserving structure in output

- **User-friendly GUI**: Real-time progress tracking, live log display, and statistics dashboard

## Installation

### Option 1: Standalone Executable (Recommended)

1. Download the latest release
2. Extract `EmailScraper.exe`
3. Double-click to run (no Python required)

### Option 2: Run from Source

```bash
git clone https://github.com/yourusername/email-scraper.git
cd email-scraper
pip install -r requirements.txt
python gui.py
```

## Usage

### Excel File Format

Required columns:
- **Website** (required): Company website URL
- **Email** (required): Email column (program fills this)
- Company Name, Address, Phone, Sector (optional)

Column names are flexible - the program auto-normalizes variations.

### Quick Start

1. Launch `EmailScraper.exe` or `python gui.py`
2. Click "Select Excel File" and choose your file
3. Click "Start Analysis"
4. Results saved as `filename_result.xlsx`

## Configuration

Edit `config.py` to customize:
- Request timeout and retry settings
- Blacklisted email domains
- Contact page keywords

## Technical Details

**Success Rate**: 50-60% (typical)  
**Architecture**: Modular design with 8 core components  
**Requirements**: Python 3.8+, pandas, requests, beautifulsoup4, lxml

## Building Executable

```bash
pip install pyinstaller
python -m PyInstaller EmailScraper.spec
```

## License

MIT License

## Contributing

Pull requests welcome!

## Support

Open an issue on GitHub for questions or bug reports.
