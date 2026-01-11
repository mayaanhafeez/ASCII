# Art, Squinting Can Improve It (ASCII)

A beautiful Python desktop application that converts images into ASCII art with real-time preview and extensive customization options.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 🖼️ **Image Preview**: Upload and preview images with automatic scaling
- 🎨 **Multiple ASCII Ramps**: Choose from Blocks, Classic, or Detailed character sets
- ⚙️ **Advanced Controls**:
  - Adjustable max width/height
  - Contrast and gamma correction
  - Optional dithering for smoother gradients
  - Invert colors
  - Double-width characters for better readability
- 📋 **Clipboard Integration**: Copy ASCII art with optional code block wrapping for chat apps
- 🖥️ **Terminal-Style Output**: Dark-themed monospace display that looks like a real terminal
- 🔄 **Real-Time Conversion**: Auto-updates as you adjust settings
- 🎯 **Two GUI Options**: PySide6 (Qt) with Tkinter fallback

## Screenshots

*Upload an image, adjust settings, and watch your ASCII art come to life!*

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd img_2_ascii
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the GUI Application

Simply run:
```bash
python img2ascii_gui.py
```

The application will automatically try to use PySide6 (Qt). If PySide6 is not available, it will fall back to Tkinter.

### Command-Line Interface

The project also includes a command-line version for batch processing:

```bash
python img2ascii.py path/to/image.jpg
```

**CLI Options:**
- `--max-width WIDTH` - Maximum width in characters (default: 80)
- `--max-height HEIGHT` - Maximum height in characters (default: 40)
- `--contrast VALUE` - Contrast enhancement (default: 1.4)
- `--gamma VALUE` - Gamma correction (default: 0.8)
- `--dither` - Enable dithering
- `--invert` - Invert colors
- `--double` - Double characters horizontally
- `--chat` - Wrap output in code block and use chat-friendly ramp
- `--chat-ramp {blocks,classic}` - Choose chat ramp style

**Example:**
```bash
python img2ascii.py image.jpg --max-width 100 --contrast 1.8 --chat --chat-ramp blocks
```

## GUI Controls

### Image Settings
- **Max Width**: Maximum number of characters per line (default: 70)
- **Max Height**: Maximum number of lines (default: 35)

### Ramp Selection
- **Blocks**: `█▓▒░ ` - Bold, high-contrast characters (great for chat)
- **Classic**: `@#S%?*+;:,. ` - Traditional ASCII art style
- **Detailed**: Long gradient ramp for fine detail

### Image Processing
- **Contrast**: Adjust contrast (1.0-3.0, default: 1.6)
- **Gamma**: Gamma correction (0.4-1.4, default: 0.75)
- **Dither**: Enable Floyd-Steinberg dithering for smoother gradients
- **Invert**: Invert the image colors
- **Double Width**: Repeat each character horizontally (better for some fonts)

### Output Options
- **Wrap in code block**: When copying, wrap the ASCII art in \`\`\`txt code blocks (useful for Discord, Slack, etc.)

## How It Works

1. **Image Loading**: The app accepts common image formats (PNG, JPG, GIF, BMP, WebP)
2. **Preprocessing**: 
   - Converts to grayscale
   - Applies autocontrast
   - Enhances contrast
   - Applies gamma correction
3. **Resizing**: Intelligently resizes to fit within max width/height while preserving aspect ratio
4. **Dithering** (optional): Applies Floyd-Steinberg dithering for smoother gradients
5. **Character Mapping**: Maps pixel brightness to characters from the selected ramp
6. **Output**: Displays in terminal-style text area and allows copying to clipboard

## Project Structure

```
img_2_ascii/
├── img2ascii.py          # Core ASCII conversion logic (CLI)
├── img2ascii_gui.py      # PySide6 (Qt) GUI application
├── img2ascii_gui_tk.py   # Tkinter fallback GUI
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .gitignore           # Git ignore rules
```

## Dependencies

- **PySide6** (>=6.5.0): Modern Qt-based GUI framework
- **Pillow** (>=10.0.0): Image processing library

If PySide6 is not available, the app automatically falls back to Tkinter (included with Python).

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## License

MIT License - feel free to use this project for any purpose.

## Acknowledgments

Inspired by the classic art of ASCII conversion, with a modern twist for the digital age.

---

**Art, Squinting Can Improve It (ASCII)** - Because sometimes the best way to see art is through characters.
