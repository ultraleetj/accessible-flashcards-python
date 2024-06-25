import wx, random

class FlashcardPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.flashcards, self.current_flashcard = [], None

        self.flashcard_listbox = wx.ListBox(self, style=wx.LB_SINGLE)
        self.flashcard_listbox.Bind(wx.EVT_LISTBOX, self.on_listbox_select)

        open_button = wx.Button(self, label="Open (control+o)")
        open_button.Bind(wx.EVT_BUTTON, self.on_open)
        shuffle_button = wx.Button(self, label="Shuffle (control+s)")
        shuffle_button.Bind(wx.EVT_BUTTON, self.on_shuffle)
        reveal_button = wx.Button(self, label="Reveal (press space on selected item)")
        reveal_button.Bind(wx.EVT_BUTTON, self.on_reveal)

        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('O'), open_button.GetId()),(wx.ACCEL_CTRL, ord('S'), shuffle_button.GetId()), (wx.ACCEL_NORMAL, wx.WXK_SPACE, reveal_button.GetId())])
        self.SetAcceleratorTable(accel_tbl)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.flashcard_listbox, 1, wx.EXPAND)
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        sizer.Add(wx.StaticText(self, -1, "Flashcard Actions"), 0, wx.ALIGN_CENTER|wx.TOP, 5)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(open_button, 0, wx.RIGHT, 5)
        button_sizer.Add(shuffle_button, 0, wx.RIGHT, 5)
        button_sizer.Add(reveal_button)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 5)
        self.SetSizer(sizer)
    def load_flashcards(self, filename):
        with open(filename, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]

        self.flashcards = []
        for line in lines:
            parts = line.split('-')
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                self.flashcards.append((term, definition))

        self.update_flashcard_list()

    def update_flashcard_list(self):
        self.flashcard_listbox.Clear()
        for term, _ in self.flashcards:
            self.flashcard_listbox.Append(term)

    def on_listbox_select(self, event):
        index = self.flashcard_listbox.GetSelection()
        if index >= 0:
            _, definition = self.flashcards[index]
            self.current_flashcard = definition

    def on_open(self, event):
        wildcard = "Text files (*.txt)|*.txt"
        dialog = wx.FileDialog(None, "Open flashcards file", wildcard=wildcard, style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.load_flashcards(dialog.GetPath())
        dialog.Destroy()

    def on_shuffle(self, event):
        random.shuffle(self.flashcards)
        self.update_flashcard_list()

    def on_reveal(self, event):
        if self.current_flashcard:
            dialog = wx.MessageDialog(None, self.current_flashcard, "Definition", wx.OK)
            dialog.ShowModal()
            dialog.Destroy()

class FlashcardFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Flashcards", size=(400, 300))
        FlashcardPanel(self)
        self.Center()
        self.Show()

if __name__ == '__main__':
    app = wx.App()
    frame = FlashcardFrame()
    app.MainLoop()
