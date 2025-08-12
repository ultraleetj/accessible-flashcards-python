# Flashcard Study Tool

A simple, accessible flashcard application built with Python and wxPython. Ideal for language learning, studying terms.
Download: from releases page (windows executable)

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![wxPython](https://img.shields.io/badge/wxpython-4.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

##  So what this thing does
- **Flashcards from Simple Text Format**: Use plain `.txt` files with `term - definition` format
- **Screen Reader Accessible**: Full keyboard navigation and screen reader support
- **Smart Parsing**: Hopefully fixes common formatting issues
- **Robust Validation**: Detects and handles malformed entries intelligently
- **Debug Console**: Built-in debugging for file parsing issues
- **Shuffle button**: Just what oyou would expect, randomize flashcard order.
- **Portable**:  single executable file

##  How to use

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
Create a `.txt` file with this format, example:
```
term - definition
bonjour - hello
au revoir - goodbye
l'escalier (le) - the staircase
```

**Requirements:**
- Use ` - ` (space-hyphen-space) as separator between term and definition
- One flashcard per line
- Terms and definitions can contain hyphens

##  Using the program

1. **Open File**: Click "Open" to load your flashcard file, or press control plus o.
2. **Select Card**: Click on any term in the list
3. **Reveal Answer**: Press `Space` or click "Reveal" to see the definition
4. **Shuffle**: Press `Ctrl+S` or click "Shuffle" to randomize order
5. **Debug**: Press `F12` to open debug console to better understand  file parsing issues, if any.

##  Auto-Fixes

The app automatically corrects common issues:
- **Numbering**: `1. term - definition` becomes `term - definition`
- **Spacing**: `term-definition` becomes `term - definition`
- **Wrong dashes used**: `term – definition` becomes `term - definition`
- **Unicode spaces**: Converts non-breaking spaces to regular spaces, useful if you copy paste something from the web.

## Validation

Files with severe malformations are **rejected**:
- Multiple numbering patterns: `1. 2. term - definition`
- Too many separators: `term - with - many - separators`
- Missing separators: `term definition`

##  Building Executable (is this even needed?)

Create a portable executable with PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "FlashcardApp" flashcard_app.py
```

## 📝 Example plain text file

```
# French Vocabulary
bonjour - hello
bonsoir - good evening
merci - thank you
s'il vous plaît - please
au revoir - goodbye
```

##  Keyboard Shortcuts

- `Ctrl+O`: Open file
- `Ctrl+S`: Shuffle flashcards
- `Space`: Reveal definition (when card selected)
- `F12`: Open debug console


## not much else to say, contributions welcome perhaps
As this is fully out there people could do whatever else with this I suppose.
