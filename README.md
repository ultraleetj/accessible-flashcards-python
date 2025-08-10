# 📚 Flashcard Study Tool

A simple, accessible flashcard application built with Python and wxPython. Perfect for language learning, studying, and memorization.
Download: from releases page (windows executable)

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![wxPython](https://img.shields.io/badge/wxpython-4.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- **Simple Text Format**: Use plain `.txt` files with `term - definition` format
- **Screen Reader Accessible**: Full keyboard navigation and screen reader support
- **Smart Parsing**: Automatically fixes common formatting issues
- **Robust Validation**: Detects and handles malformed entries intelligently
- **Debug Console**: Built-in debugging for file parsing issues
- **Shuffle Mode**: Randomize flashcard order for better learning
- **Portable**: Can be compiled to a single executable file

## 🚀 Quick Start

### Running from Source
1. Install Python 3.7+
2. Install dependencies:
   ```bash
   pip install wxpython
   ```
3. Run the application:
   ```bash
   python flashcard_app.py
   ```

### Flashcard File Format
Create a `.txt` file with this format:
```
term - definition
bonjour - hello
au revoir - goodbye
l'escalier (le) - the staircase
```

**Requirements:**
- Use ` - ` (space-hyphen-space) as separator
- One flashcard per line
- Terms and definitions can contain hyphens

## 🎯 Usage

1. **Open File**: Click "Open" to load your flashcard file, or press control plus o.
2. **Select Card**: Click on any term in the list
3. **Reveal Answer**: Press `Space` or click "Reveal" to see the definition
4. **Shuffle**: Press `Ctrl+S` or click "Shuffle" to randomize order
5. **Debug**: Press `F12` to open debug console for file parsing details

## 🔧 Smart Auto-Fixes

The app automatically corrects common issues:
- **Numbering**: `1. term - definition` → `term - definition`
- **Spacing**: `term-definition` → `term - definition`
- **Dash variants**: `term – definition` → `term - definition`
- **Unicode spaces**: Converts non-breaking spaces to regular spaces

## ⚠️ Validation

Files with severe malformations are **rejected** to maintain quality:
- Multiple numbering patterns: `1. 2. term - definition`
- Too many separators: `term - with - many - separators`
- Missing separators: `term definition`

## 🔨 Building Executable

Create a portable executable with PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "FlashcardApp" flashcard_app.py
```

## 📝 Example File

```
# French Vocabulary
bonjour - hello
bonsoir - good evening
merci - thank you
s'il vous plaît - please
au revoir - goodbye
```

## 🎮 Keyboard Shortcuts

- `Ctrl+O`: Open file
- `Ctrl+S`: Shuffle flashcards
- `Space`: Reveal definition (when card selected)
- `F12`: Open debug console

## 🔍 Accessibility

- Full keyboard navigation
- Screen reader compatible

## 📄 License

MIT License - feel free to use, modify, and distribute.

## 🐛 Troubleshooting

**File won't load?**
- Check the debug console (`F12`) for detailed parsing information
- Ensure proper ` - ` format (space-hyphen-space)
- Remove severely malformed lines

**Can't see definitions?**
- Select a flashcard from the list first
- Press `Space` or click "Reveal"

---

