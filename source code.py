import wx
import random
import re
import unicodedata
from typing import List, Tuple, Optional

class Flashcard:
    """Represents a single flashcard with term and definition."""
    __slots__ = ('term', 'definition')  # Memory optimization
    
    def __init__(self, term: str, definition: str):
        self.term = term.strip()
        self.definition = definition.strip()
    
    def __repr__(self):
        return f"Flashcard('{self.term}', '{self.definition}')"

class FlashcardManager:
    """Manages flashcard data and operations."""
    
    # Characters that look like dashes but aren't the standard hyphen-minus
    DASH_VARIANTS = {
        '–': 'en dash',           # U+2013
        '—': 'em dash',           # U+2014
        '−': 'minus sign',        # U+2212
        '‒': 'figure dash',       # U+2012
        '⸺': 'two-em dash',      # U+2E3A
        '⸻': 'three-em dash',    # U+2E3B
    }
    
    # Precompiled regex patterns for better performance
    NUMBERING_PATTERNS = [
        re.compile(r'^\s*\d+\.\s*'),      # "1. term"
        re.compile(r'^\s*\d+\)\s*'),      # "1) term"
        re.compile(r'^\s*\d+\s+-\s*'),    # "1 - term"
        re.compile(r'^\s*\d+\s+'),        # "1 term"
        re.compile(r'^\s*\(\d+\)\s*'),    # "(1) term"
    ]
    
    HYPHEN_FIX_PATTERN = re.compile(r'(\S)\s*-\s*(\S)')
    HYPHEN_CONTEXT_PATTERN = re.compile(r'.{0,3}-.{0,3}')
    MULTIPLE_NUMBERING_PATTERNS = [
        re.compile(r'\d+\.'),      # "1."
        re.compile(r'\d+\)'),      # "1)"
        re.compile(r'\(\d+\)'),    # "(1)"
    ]
    
    def __init__(self):
        self.flashcards: List[Flashcard] = []
        self.parent_window = None
        self.debug_window = None
    
    def set_parent_window(self, parent):
        """Set the parent window for dialogs."""
        self.parent_window = parent
    
    def debug_log(self, message):
        """Log debug message to console and debug window if available."""
        print(message)
        if self.debug_window:
            self.debug_window.log(message)
    
    def _detect_and_fix_dash_variants(self, content: str) -> Tuple[str, List[str]]:
        """Detect dash variants and optionally replace them."""
        replacements_made = []
        found_variants = {}
        
        # Find all dash variants in the content
        for variant, name in self.DASH_VARIANTS.items():
            if variant in content:
                count = content.count(variant)
                # Get first 3 example lines
                examples = []
                for line_num, line in enumerate(content.split('\n'), 1):
                    if variant in line and len(examples) < 3:
                        examples.append(f"Line {line_num}: {line.strip()}")
                
                found_variants[variant] = {
                    'name': name,
                    'count': count,
                    'examples': examples
                }
        
        if not found_variants:
            return content, replacements_made
        
        # Build message for user
        message_parts = ["Found non-standard dash characters in your flashcard file:\n"]
        
        for variant, info in found_variants.items():
            message_parts.append(f"\n• '{variant}' ({info['name']}) - found {info['count']} time(s)")
            message_parts.extend(f"  {example}" for example in info['examples'])
        
        message_parts.extend([
            "\nThese should be replaced with ' - ' (space-hyphen-space) for proper parsing.",
            "Would you like to automatically replace them?"
        ])
        
        dialog = wx.MessageDialog(
            self.parent_window,
            ''.join(message_parts),
            "Dash Character Replacement",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        try:
            if dialog.ShowModal() == wx.ID_YES:
                modified_content = content
                for variant in found_variants:
                    # Replace variant with standard format
                    pattern = rf'(\S)\s*{re.escape(variant)}\s*(\S)'
                    modified_content = re.sub(pattern, r'\1 - \2', modified_content)
                    replacements_made.append(f"Replaced '{variant}' ({found_variants[variant]['name']})")
                content = modified_content
        finally:
            dialog.Destroy()
        
        return content, replacements_made
    
    def _validate_flashcard_line(self, line: str, line_num: int) -> Tuple[bool, str]:
        """Validate a flashcard line for severe malformations."""
        # Check for multiple numbering patterns
        matches = []
        for pattern in self.MULTIPLE_NUMBERING_PATTERNS:
            matches.extend(pattern.findall(line))
        
        if len(matches) > 1:
            return False, f"Multiple numbering patterns found: {matches}"
        
        # Check for too many dash characters
        total_dash_chars = sum(line.count(char) for char in ['-', '–', '—'])
        
        if total_dash_chars > 2:
            return False, f"Too many dash characters ({total_dash_chars} found), unclear separation"
        
        # Check for missing separator
        if not any(char in line for char in ['-', '–', '—']):
            # Skip empty lines or comments
            if line.strip() and not line.strip().startswith('#') and len(line.strip().split()) > 1:
                return False, "No separator found (missing hyphen/dash)"
        
        return True, ""
    
    def _clean_line(self, line: str) -> str:
        """Clean line of invisible characters and normalize spaces."""
        return ''.join(
            ' ' if unicodedata.category(char) == 'Zs' else char 
            if char.isprintable() or char == ' ' else '' 
            for char in line
        )
    
    def _remove_numbering(self, line: str, line_num: int) -> str:
        """Remove numbering patterns from the beginning of a line."""
        original_line = line
        
        for pattern in self.NUMBERING_PATTERNS:
            if pattern.match(line):
                new_line = pattern.sub('', line)
                self.debug_log(f"Line {line_num}: Removed numbering pattern")
                self.debug_log(f"Line {line_num}: Before: {repr(line)}")
                self.debug_log(f"Line {line_num}: After: {repr(new_line)}")
                return new_line
        
        return line
    
    def _fix_hyphen_spacing(self, line: str, line_num: int) -> str:
        """Fix spacing around hyphens."""
        separator = ' - '
        
        if separator not in line and '-' in line:
            # Fix patterns like "word -word", "word- word", "word-word"
            if self.HYPHEN_FIX_PATTERN.search(line):
                fixed_line = self.HYPHEN_FIX_PATTERN.sub(r'\1 - \2', line)
                self.debug_log(f"Line {line_num}: Auto-fixed spacing around hyphen")
                self.debug_log(f"Line {line_num}: Before: {repr(line)}")
                self.debug_log(f"Line {line_num}: After: {repr(fixed_line)}")
                return fixed_line
        
        return line
    
    def _parse_flashcard_line(self, line: str, line_num: int) -> Optional[Flashcard]:
        """Parse a single line into a flashcard."""
        original_line = line
        
        # Validate for severe malformations
        is_valid, error_msg = self._validate_flashcard_line(line, line_num)
        if not is_valid:
            self.debug_log(f"Line {line_num}: SEVERE MALFORMATION - {error_msg}")
            self.debug_log(f"Line {line_num}: {repr(line)}")
            raise ValueError(f"Line {line_num}: {error_msg} - '{line.strip()}'")
        
        # Clean and process the line
        cleaned_line = self._clean_line(line)
        cleaned_line = self._remove_numbering(cleaned_line, line_num)
        cleaned_line = self._fix_hyphen_spacing(cleaned_line, line_num)
        
        separator = ' - '
        
        if separator not in cleaned_line:
            # Debug information
            if '-' in cleaned_line:
                hyphen_contexts = self.HYPHEN_CONTEXT_PATTERN.findall(cleaned_line)
                self.debug_log(f"Line {line_num}: Found hyphens but not ' - '. Contexts: {hyphen_contexts}")
                self.debug_log(f"Line {line_num}: Original: {repr(original_line)}")
                self.debug_log(f"Line {line_num}: Cleaned: {repr(cleaned_line)}")
            else:
                self.debug_log(f"Line {line_num}: No hyphen found in line: {repr(cleaned_line)}")
            return None
        
        # Split on first occurrence of separator
        parts = cleaned_line.split(separator, 1)
        if len(parts) == 2:
            term = parts[0].strip()
            definition = parts[1].strip()
            
            if term and definition:
                self.debug_log(f"Line {line_num}: Successfully parsed - Term: '{term}', Definition: '{definition}'")
                return Flashcard(term, definition)
            else:
                self.debug_log(f"Line {line_num}: Empty term or definition - Term: '{term}', Definition: '{definition}'")
        else:
            self.debug_log(f"Line {line_num}: Split resulted in {len(parts)} parts instead of 2")
        
        return None
    
    def load_from_file(self, filename: str) -> Tuple[bool, List[str], bool]:
        """Load flashcards from a file."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Detect and optionally fix dash variants
            content, replacements = self._detect_and_fix_dash_variants(content)
            
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            self.flashcards.clear()
            skipped_lines = []
            processing_issues = []
            
            # First pass: validate all lines
            try:
                for line_num, line in enumerate(lines, 1):
                    self._validate_flashcard_line(line, line_num)
            except ValueError as e:
                error_msg = str(e)
                self.debug_log(f"REFUSING TO LOAD FILE: {error_msg}")
                return False, [f"File refused due to severe formatting issues:\n{error_msg}\n\nPlease fix the formatting and try again."], True
            
            # Second pass: parse lines
            for line_num, line in enumerate(lines, 1):
                try:
                    flashcard = self._parse_flashcard_line(line, line_num)
                    if flashcard:
                        self.flashcards.append(flashcard)
                    else:
                        skipped_lines.append(f"Line {line_num}: {line}")
                except ValueError:
                    skipped_lines.append(f"Line {line_num}: {line}")
            
            # Prepare status messages
            messages = []
            if replacements:
                messages.extend(replacements)
                processing_issues.extend(replacements)
            
            if skipped_lines:
                messages.append(f"Skipped {len(skipped_lines)} malformed line(s):")
                messages.extend(skipped_lines[:5])
                if len(skipped_lines) > 5:
                    messages.append(f"... and {len(skipped_lines) - 5} more")
                messages.append("\nValid format: 'term - definition' (with spaces around the hyphen)")
                processing_issues.append(f"Skipped malformed lines: {len(skipped_lines)}")
            
            has_issues = bool(processing_issues or skipped_lines)
            return len(self.flashcards) > 0, messages, has_issues
            
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            return False, [f"Error loading file: {e}"], False
    
    def shuffle(self):
        """Shuffle the flashcards."""
        random.shuffle(self.flashcards)
    
    def get_flashcard(self, index: int) -> Optional[Flashcard]:
        """Get flashcard by index."""
        if 0 <= index < len(self.flashcards):
            return self.flashcards[index]
        return None
    
    def get_terms(self) -> List[str]:
        """Get list of all terms."""
        return [card.term for card in self.flashcards]
    
    def __len__(self):
        return len(self.flashcards)

class FlashcardPanel(wx.Panel):
    """Main panel containing the flashcard interface."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.flashcard_manager = FlashcardManager()
        self.flashcard_manager.set_parent_window(self)
        self.current_selection = -1
        
        self._create_ui()
        self._setup_accelerators()
        self._setup_layout()
    
    def _create_ui(self):
        """Create UI components."""
        # Listbox for flashcard terms
        self.flashcard_listbox = wx.ListBox(self, style=wx.LB_SINGLE)
        self.flashcard_listbox.Bind(wx.EVT_LISTBOX, self.on_listbox_select)
        
        # Buttons
        self.open_button = wx.Button(self, label="Open (Ctrl+O)")
        self.open_button.Bind(wx.EVT_BUTTON, self.on_open)
        
        self.shuffle_button = wx.Button(self, label="Shuffle (Ctrl+S)")
        self.shuffle_button.Bind(wx.EVT_BUTTON, self.on_shuffle)
        
        self.reveal_button = wx.Button(self, label="Reveal (Space)")
        self.reveal_button.Bind(wx.EVT_BUTTON, self.on_reveal)
        
        # Status text
        self.status_text = wx.StaticText(self, label="No flashcards loaded")
    
    def _setup_accelerators(self):
        """Setup keyboard accelerators."""
        accel_entries = [
            (wx.ACCEL_CTRL, ord('O'), self.open_button.GetId()),
            (wx.ACCEL_CTRL, ord('S'), self.shuffle_button.GetId()),
            (wx.ACCEL_NORMAL, wx.WXK_SPACE, self.reveal_button.GetId())
        ]
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)
    
    def _setup_layout(self):
        """Setup the layout of UI components."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        main_sizer.Add(self.flashcard_listbox, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        main_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # Button layout
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for button in [self.open_button, self.shuffle_button, self.reveal_button]:
            button_sizer.Add(button, 0, wx.RIGHT, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(main_sizer)
    
    def _update_flashcard_list(self):
        """Update the listbox with current flashcards."""
        self.flashcard_listbox.Clear()
        terms = self.flashcard_manager.get_terms()
        
        for term in terms:
            self.flashcard_listbox.Append(term)
        
        # Update status
        count = len(self.flashcard_manager)
        if count > 0:
            self.status_text.SetLabel(f"Loaded {count} flashcard{'s' if count != 1 else ''}")
        else:
            self.status_text.SetLabel("No flashcards loaded")
        
        self.current_selection = -1
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button enabled states."""
        has_flashcards = len(self.flashcard_manager) > 0
        has_selection = self.current_selection >= 0
        
        self.shuffle_button.Enable(has_flashcards)
        self.reveal_button.Enable(has_selection)
    
    def on_listbox_select(self, event):
        """Handle listbox selection change."""
        self.current_selection = self.flashcard_listbox.GetSelection()
        self._update_button_states()
    
    def _show_load_results(self, success, messages, has_issues, filepath):
        """Show appropriate dialog based on load results."""
        if not success:
            error_msg = "Failed to load flashcards."
            if messages:
                error_msg += "\n\n" + "\n".join(messages)
            
            wx.MessageBox(error_msg, "Load Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Success case
        success_msg = f"Successfully loaded {len(self.flashcard_manager)} flashcard{'s' if len(self.flashcard_manager) != 1 else ''}"
        
        if has_issues:
            # Show dialog directing user to debug console
            full_message = success_msg + "\n\n⚠️ Some issues were detected during parsing:\n" + "\n".join(messages)
            full_message += "\n\n📋 Check the Debug Console (F12) for detailed parsing information."
            
            dialog = wx.MessageDialog(
                self, full_message, "Load Complete with Issues", wx.OK | wx.ICON_WARNING
            )
            dialog.SetOKLabel("Continue Anyway")
            dialog.ShowModal()
            dialog.Destroy()
            
            # Auto-show debug console
            parent_frame = self.GetParent()
            if hasattr(parent_frame, 'set_last_opened_file'):
                parent_frame.set_last_opened_file(filepath)
            if hasattr(parent_frame, 'on_show_debug'):
                parent_frame.on_show_debug(None)
                
        elif messages:
            # Show info about successful auto-fixes
            full_message = success_msg + "\n\n✅ Auto-corrections applied:\n" + "\n".join(messages)
            wx.MessageBox(full_message, "Load Successful", wx.OK | wx.ICON_INFORMATION)
        else:
            # Simple success message
            wx.MessageBox(success_msg, "Load Successful", wx.OK | wx.ICON_INFORMATION)
    
    def on_open(self, event):
        """Handle open file button click."""
        wildcard = "Text files (*.txt)|*.txt|All files (*.*)|*.*"
        
        with wx.FileDialog(
            self, 
            "Open flashcards file",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            
            if dialog.ShowModal() == wx.ID_OK:
                filepath = dialog.GetPath()
                
                # Track opened file for debug reloading
                parent_frame = self.GetParent()
                if hasattr(parent_frame, 'set_last_opened_file'):
                    parent_frame.set_last_opened_file(filepath)
                
                success, messages, has_issues = self.flashcard_manager.load_from_file(filepath)
                
                if success:
                    self._update_flashcard_list()
                
                self._show_load_results(success, messages, has_issues, filepath)
    
    def on_shuffle(self, event):
        """Handle shuffle button click."""
        if len(self.flashcard_manager) > 0:
            self.flashcard_manager.shuffle()
            self._update_flashcard_list()
    
    def on_reveal(self, event):
        """Handle reveal button click."""
        if self.current_selection >= 0:
            flashcard = self.flashcard_manager.get_flashcard(self.current_selection)
            if flashcard:
                with wx.MessageDialog(
                    self,
                    flashcard.definition,
                    f"Definition: {flashcard.term}",
                    wx.OK | wx.CENTRE
                ) as dialog:
                    dialog.ShowModal()

class FlashcardFrame(wx.Frame):
    """Main application frame."""
    
    def __init__(self):
        super().__init__(
            None,
            title="Flashcard Study Tool",
            size=(500, 400),
            style=wx.DEFAULT_FRAME_STYLE
        )
        
        self.panel = FlashcardPanel(self)
        self._setup_accelerators()
        
        # Debug window and file tracking
        self.debug_window = None
        self.last_opened_file = None
        
        self.CenterOnScreen()
        self.Show()
    
    def _setup_accelerators(self):
        """Setup keyboard accelerators."""
        debug_id = wx.NewIdRef()
        
        accel_entries = [(wx.ACCEL_NORMAL, wx.WXK_F12, debug_id)]
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)
        
        self.Bind(wx.EVT_MENU, self.on_show_debug, id=debug_id)
    
    def on_show_debug(self, event):
        """Show or create the debug window."""
        if self.debug_window is None or not self.debug_window:
            self.debug_window = DebugWindow(self)
            self.panel.flashcard_manager.debug_window = self.debug_window
        
        self.debug_window.Show()
        self.debug_window.Raise()
        
        # Reload file for debug analysis if available
        if self.last_opened_file:
            self.debug_window.log(f"Reloading file for debug analysis: {self.last_opened_file}")
            self.debug_window.log("=" * 50)
            success, messages, has_issues = self.panel.flashcard_manager.load_from_file(self.last_opened_file)
            if not success:
                self.debug_window.log("ERROR: Failed to reload file for debug analysis")
            else:
                self.debug_window.log(f"Reload complete. Found {len(self.panel.flashcard_manager)} valid flashcards.")
                self.panel._update_flashcard_list()
    
    def set_last_opened_file(self, filepath):
        """Set the last opened file path for debug reloading."""
        self.last_opened_file = filepath

class DebugWindow(wx.Frame):
    """Debug console window."""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            title="Debug Console",
            size=(600, 300),
            style=wx.DEFAULT_FRAME_STYLE
        )
        
        # Create text control for debug output
        self.debug_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        self.debug_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Create clear button
        clear_btn = wx.Button(self, label="Clear")
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.debug_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(clear_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(sizer)
        
        self.log("Debug console initialized. Ready for flashcard parsing debug info.")
    
    def log(self, message):
        """Add a message to the debug console."""
        self.debug_text.AppendText(f"{message}\n")
    
    def on_clear(self, event):
        """Clear the debug console."""
        self.debug_text.Clear()
        self.log("Debug console cleared.")

class FlashcardApp(wx.App):
    """Main application class."""
    
    def OnInit(self):
        frame = FlashcardFrame()
        return True

if __name__ == '__main__':
    app = FlashcardApp()
    app.MainLoop()
 
