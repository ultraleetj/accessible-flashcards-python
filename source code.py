import wx
import random
import re
from typing import List, Tuple, Optional

class Flashcard:
    """Represents a single flashcard with term and definition."""
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
    
    def __init__(self):
        self.flashcards: List[Flashcard] = []
        self.parent_window = None  # Will be set by the panel
        self.debug_window = None   # Will be set when debug window is created
    
    def set_parent_window(self, parent):
        """Set the parent window for dialogs."""
        self.parent_window = parent
    
    def debug_log(self, message):
        """Log debug message to console and debug window if available."""
        print(message)  # Always print to console
        if self.debug_window:
            self.debug_window.log(message)
    
    def _detect_and_fix_dash_variants(self, content: str) -> Tuple[str, List[str]]:
        """
        Detect dash variants and optionally replace them.
        Returns (potentially_modified_content, list_of_replacements_made)
        """
        replacements_made = []
        
        # Find all dash variants in the content
        found_variants = {}
        for variant, name in self.DASH_VARIANTS.items():
            if variant in content:
                # Count occurrences and find example lines
                count = content.count(variant)
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
        
        # Ask user about replacements
        message_parts = ["Found non-standard dash characters in your flashcard file:\n"]
        
        for variant, info in found_variants.items():
            message_parts.append(f"\n• '{variant}' ({info['name']}) - found {info['count']} time(s)")
            for example in info['examples']:
                message_parts.append(f"  {example}")
        
        message_parts.append(f"\nThese should be replaced with ' - ' (space-hyphen-space) for proper parsing.")
        message_parts.append(f"Would you like to automatically replace them?")
        
        dialog = wx.MessageDialog(
            self.parent_window,
            ''.join(message_parts),
            "Dash Character Replacement",
            wx.YES_NO | wx.ICON_QUESTION
        )
        
        if dialog.ShowModal() == wx.ID_YES:
            modified_content = content
            for variant in found_variants:
                # Replace variant with standard format, but be smart about spacing
                # Replace "word[variant]word" with "word - word"
                pattern = rf'(\S)\s*{re.escape(variant)}\s*(\S)'
                modified_content = re.sub(pattern, r'\1 - \2', modified_content)
                replacements_made.append(f"Replaced '{variant}' ({found_variants[variant]['name']})")
            
            content = modified_content
        
        dialog.Destroy()
        return content, replacements_made
    
    def _validate_flashcard_line(self, line: str, line_num: int) -> Tuple[bool, str]:
        """
        Validate a flashcard line for severe malformations that should refuse loading.
        Returns (is_valid, error_message)
        """
        import re
        
        # Check for multiple numbering patterns (e.g., "2. 2. term - definition")
        numbering_patterns = [
            r'\d+\.',      # "1."
            r'\d+\)',      # "1)"
            r'\(\d+\)',    # "(1)"
        ]
        
        matches = []
        for pattern in numbering_patterns:
            matches.extend(re.findall(pattern, line))
        
        if len(matches) > 1:
            return False, f"Multiple numbering patterns found: {matches}"
        
        # Check for multiple hyphens that could be confusing
        hyphen_count = line.count('-')
        en_dash_count = line.count('–')
        em_dash_count = line.count('—')
        total_dash_chars = hyphen_count + en_dash_count + em_dash_count
        
        if total_dash_chars > 2:  # Allow for one separator plus one in term/definition
            return False, f"Too many dash characters ({total_dash_chars} found), unclear separation"
        
        # Check for severely malformed patterns
        # Pattern like "term definition" with no separator at all
        if '-' not in line and '–' not in line and '—' not in line:
            # Skip empty lines or lines that are clearly just headers/comments
            if line.strip() and not line.strip().startswith('#') and len(line.strip().split()) > 1:
                return False, "No separator found (missing hyphen/dash)"
        
        return True, ""
    def _parse_flashcard_line(self, line: str, line_num: int) -> Optional[Flashcard]:
        """
        Parse a single line into a flashcard.
        Valid format: "term - definition" (space-hyphen-space)
        """
        original_line = line
        
        # First, validate for severe malformations that should refuse loading
        is_valid, error_msg = self._validate_flashcard_line(line, line_num)
        if not is_valid:
            self.debug_log(f"Line {line_num}: SEVERE MALFORMATION - {error_msg}")
            self.debug_log(f"Line {line_num}: {repr(line)}")
            raise ValueError(f"Line {line_num}: {error_msg} - '{line.strip()}'")
        
        # Clean the line of any invisible characters (except regular spaces)
        # Also normalize different types of spaces to regular spaces
        import unicodedata
        cleaned_line = ''.join(
            ' ' if unicodedata.category(char) == 'Zs' else char 
            if char.isprintable() or char == ' ' else '' 
            for char in line
        )
        
        # Remove leading numbers and numbering patterns
        import re
        numbering_patterns = [
            r'^\s*\d+\.\s*',      # "1. term"
            r'^\s*\d+\)\s*',      # "1) term"
            r'^\s*\d+\s+-\s*',    # "1 - term" (when number is separate from actual separator)
            r'^\s*\d+\s+',        # "1 term"
            r'^\s*\(\d+\)\s*',    # "(1) term"
        ]
        
        original_cleaned = cleaned_line
        for pattern in numbering_patterns:
            if re.match(pattern, cleaned_line):
                new_line = re.sub(pattern, '', cleaned_line)
                self.debug_log(f"Line {line_num}: Removed numbering pattern")
                self.debug_log(f"Line {line_num}: Before: {repr(cleaned_line)}")
                self.debug_log(f"Line {line_num}: After: {repr(new_line)}")
                cleaned_line = new_line
                break
        
        # Look for the exact pattern: space, hyphen, space
        separator = ' - '
        
        # Also try to fix common malformed patterns
        if separator not in cleaned_line:
            # Try to fix patterns like "word -word", "word- word", "word-word"
            pattern = r'(\S)\s*-\s*(\S)'
            if re.search(pattern, cleaned_line):
                # Replace with proper format
                fixed_line = re.sub(pattern, r'\1 - \2', cleaned_line)
                self.debug_log(f"Line {line_num}: Auto-fixed spacing around hyphen")
                self.debug_log(f"Line {line_num}: Before: {repr(cleaned_line)}")
                self.debug_log(f"Line {line_num}: After: {repr(fixed_line)}")
                cleaned_line = fixed_line
        
        if separator not in cleaned_line:
            # Debug: show what characters we actually have around hyphens
            if '-' in cleaned_line:
                hyphen_contexts = re.findall(r'.{0,3}-.{0,3}', cleaned_line)
                self.debug_log(f"Line {line_num}: Found hyphens but not ' - '. Contexts: {hyphen_contexts}")
                self.debug_log(f"Line {line_num}: Original: {repr(original_line)}")
                self.debug_log(f"Line {line_num}: Cleaned: {repr(cleaned_line)}")
            else:
                self.debug_log(f"Line {line_num}: No hyphen found in line: {repr(cleaned_line)}")
            return None
        
        # Split only on the first occurrence of ' - '
        parts = cleaned_line.split(separator, 1)
        if len(parts) == 2:
            term = parts[0].strip()
            definition = parts[1].strip()
            
            if term and definition:  # Both parts must be non-empty
                self.debug_log(f"Line {line_num}: Successfully parsed - Term: '{term}', Definition: '{definition}'")
                return Flashcard(term, definition)
            else:
                self.debug_log(f"Line {line_num}: Empty term or definition - Term: '{term}', Definition: '{definition}'")
        else:
            self.debug_log(f"Line {line_num}: Split resulted in {len(parts)} parts instead of 2")
        
        return None
    
    def load_from_file(self, filename: str) -> Tuple[bool, List[str]]:
        """
        Load flashcards from a file. 
        Returns (success, list_of_messages, has_issues)
        """
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Detect and optionally fix dash variants
            content, replacements = self._detect_and_fix_dash_variants(content)
            
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            self.flashcards.clear()
            skipped_lines = []
            processing_issues = []
            
            # First pass: check for severe malformations that should refuse loading
            try:
                for line_num, line in enumerate(lines, 1):
                    # This will raise ValueError if severely malformed
                    self._parse_flashcard_line(line, line_num)
            except ValueError as e:
                # Severe malformation found - refuse to load the file
                error_msg = str(e)
                self.debug_log(f"REFUSING TO LOAD FILE: {error_msg}")
                return False, [f"File refused due to severe formatting issues:\n{error_msg}\n\nPlease fix the formatting and try again."], True
            
            # Second pass: actual parsing (we know it won't crash now)
            for line_num, line in enumerate(lines, 1):
                try:
                    flashcard = self._parse_flashcard_line(line, line_num)
                    if flashcard:
                        self.flashcards.append(flashcard)
                    else:
                        skipped_lines.append(f"Line {line_num}: {line}")
                except ValueError:
                    # This shouldn't happen since we pre-validated, but just in case
                    skipped_lines.append(f"Line {line_num}: {line}")
            
            # Prepare status messages
            messages = []
            if replacements:
                messages.extend(replacements)
                processing_issues.extend(replacements)
            
            if skipped_lines:
                messages.append(f"Skipped {len(skipped_lines)} malformed line(s):")
                messages.extend(skipped_lines[:5])  # Show first 5 skipped lines
                if len(skipped_lines) > 5:
                    messages.append(f"... and {len(skipped_lines) - 5} more")
                messages.append("\nValid format: 'term - definition' (with spaces around the hyphen)")
                processing_issues.extend([f"Skipped malformed lines: {len(skipped_lines)}"])
            
            # Check if we had any processing issues that warrant showing debug console
            has_issues = len(processing_issues) > 0 or len(skipped_lines) > 0
            
            return len(self.flashcards) > 0, messages, has_issues
            
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            return False, [f"Error loading file: {e}"], False
    
    def shuffle(self):
        """Shuffle the flashcards."""
        random.shuffle(self.flashcards)
    
    def get_flashcard(self, index: int) -> Optional[Flashcard]:
        """Get flashcard by index, returns None if index is invalid."""
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
        self.flashcard_manager.set_parent_window(self)  # Set parent for dialogs
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
        
        # Add listbox
        main_sizer.Add(self.flashcard_listbox, 1, wx.EXPAND | wx.ALL, 5)
        
        # Add separator
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # Add status
        main_sizer.Add(self.status_text, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # Add buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.open_button, 0, wx.RIGHT, 5)
        button_sizer.Add(self.shuffle_button, 0, wx.RIGHT, 5)
        button_sizer.Add(self.reveal_button, 0)
        
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
        
        # Reset selection
        self.current_selection = -1
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button enabled states based on current state."""
        has_flashcards = len(self.flashcard_manager) > 0
        has_selection = self.current_selection >= 0
        
        self.shuffle_button.Enable(has_flashcards)
        self.reveal_button.Enable(has_selection)
    
    def on_listbox_select(self, event):
        """Handle listbox selection change."""
        self.current_selection = self.flashcard_listbox.GetSelection()
        self._update_button_states()
    
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
                
                # Track the opened file for debug reloading
                parent_frame = self.GetParent()
                if hasattr(parent_frame, 'set_last_opened_file'):
                    parent_frame.set_last_opened_file(filepath)
                
                success, messages, has_issues = self.flashcard_manager.load_from_file(filepath)
                
                if success:
                    self._update_flashcard_list()
                    
                    # Prepare success message
                    success_msg = f"Successfully loaded {len(self.flashcard_manager)} flashcard{'s' if len(self.flashcard_manager) != 1 else ''}"
                    
                    if has_issues:
                        # Show dialog directing user to debug console
                        full_message = success_msg + "\n\n⚠️ Some issues were detected during parsing:\n" + "\n".join(messages)
                        full_message += "\n\n📋 Check the Debug Console (F12) for detailed parsing information."
                        
                        # Create custom dialog with "Continue Anyway" button
                        dialog = wx.MessageDialog(
                            self,
                            full_message,
                            "Load Complete with Issues",
                            wx.OK | wx.ICON_WARNING
                        )
                        
                        # Change the OK button text to "Continue Anyway"
                        dialog.SetOKLabel("Continue Anyway")
                        
                        dialog.ShowModal()
                        dialog.Destroy()
                        
                        # Auto-show debug console and track file for reloading
                        parent_frame = self.GetParent()
                        if hasattr(parent_frame, 'set_last_opened_file'):
                            parent_frame.set_last_opened_file(filepath)
                        if hasattr(parent_frame, 'on_show_debug'):
                            parent_frame.on_show_debug(None)
                        
                    elif messages:
                        # Show info about successful auto-fixes
                        full_message = success_msg + "\n\n✅ Auto-corrections applied:\n" + "\n".join(messages)
                        wx.MessageBox(
                            full_message,
                            "Load Successful",
                            wx.OK | wx.ICON_INFORMATION
                        )
                    else:
                        # Simple success message
                        wx.MessageBox(
                            success_msg,
                            "Load Successful",
                            wx.OK | wx.ICON_INFORMATION
                        )
                else:
                    # Show error messages
                    error_msg = "Failed to load flashcards."
                    if messages:
                        error_msg += "\n\n" + "\n".join(messages)
                    
                    wx.MessageBox(
                        error_msg,
                        "Load Error",
                        wx.OK | wx.ICON_ERROR
                    )
    
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
        
        # Create main panel
        self.panel = FlashcardPanel(self)
        
        # Setup F12 key for debug window
        self._setup_accelerators()
        
        # Debug window (initially hidden)
        self.debug_window = None
        self.last_opened_file = None  # Track the last opened file for reloading
        
        # Center and show
        self.CenterOnScreen()
        self.Show()
    
    def _setup_accelerators(self):
        """Setup keyboard accelerators."""
        # Create a unique ID for the debug command
        debug_id = wx.NewIdRef()
        
        # Add F12 accelerator for debug window
        accel_entries = [(wx.ACCEL_NORMAL, wx.WXK_F12, debug_id)]
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)
        
        # Bind the debug command
        self.Bind(wx.EVT_MENU, self.on_show_debug, id=debug_id)
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        open_item = file_menu.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open flashcard file")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit application")
        
        # Tools menu
        tools_menu = wx.Menu()
        shuffle_item = tools_menu.Append(wx.ID_ANY, "&Shuffle\tCtrl+S", "Shuffle flashcards")
        
        # Debug menu
        debug_menu = wx.Menu()
        debug_window_item = debug_menu.Append(wx.ID_ANY, "&Show Debug Window\tF12", "Show debug console")
        
        menubar.Append(file_menu, "&File")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(debug_menu, "&Debug")
        
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self.panel.on_open, open_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.panel.on_shuffle, shuffle_item)
        self.Bind(wx.EVT_MENU, self.on_show_debug, debug_window_item)
        
        # Add F12 accelerator for debug window
        accel_entries = [(wx.ACCEL_NORMAL, wx.WXK_F12, debug_window_item.GetId())]
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)
    
    def on_show_debug(self, event):
        """Show or create the debug window."""
        if self.debug_window is None or not self.debug_window:
            self.debug_window = DebugWindow(self)
            # Set the debug window as the target for our debug messages
            self.panel.flashcard_manager.debug_window = self.debug_window
        
        self.debug_window.Show()
        self.debug_window.Raise()
        
        # If we have a last opened file, reload it to show debug info
        if self.last_opened_file:
            self.debug_window.log(f"Reloading file for debug analysis: {self.last_opened_file}")
            self.debug_window.log("=" * 50)
            # Reload the file to capture all debug messages
            success, messages, has_issues = self.panel.flashcard_manager.load_from_file(self.last_opened_file)
            if not success:
                self.debug_window.log("ERROR: Failed to reload file for debug analysis")
            else:
                self.debug_window.log(f"Reload complete. Found {len(self.panel.flashcard_manager)} valid flashcards.")
                # Update the UI with the reloaded data
                self.panel._update_flashcard_list()
    
    def set_last_opened_file(self, filepath):
        """Set the last opened file path for debug reloading."""
        self.last_opened_file = filepath
    
    def on_exit(self, event):
        """Handle exit menu item."""
        if self.debug_window:
            self.debug_window.Close()
        self.Close()

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
 
