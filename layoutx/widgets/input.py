from .widget     import Widget
import tkinter as tk
from tkinter     import ttk, StringVar
from ttkwidgets.autocomplete  import AutocompleteEntry
from ttkwidgets.autocomplete  import AutocompleteCombobox
from ..tkDnD import DND_FILES
from pathlib import Path


class BaseInput(Widget):
  def __init__(self, tk, **kwargs):
    super().__init__(tk=tk, **kwargs)

    self._setter = self.connect_to_prop("value", self.on_changed_value)
    self._trace = self._textv.trace_add("write", 
      lambda *_: self._setter(self._textv.get())
    )
    self.connect_to_prop("suggestion", self.on_changed_suggestion)
  
  def on_changed_suggestion(self, value):
    if self._textv.get() == None or self._textv.get() == "":
      if value and len(value) > 0:
        self._setter(value[0])
    self._tk.set_completion_list(value if value else [])

  def on_changed_value(self, value):
    self._textv.set(value)

  def on_disposed(self):
    self._textv.trace_remove("write", self._trace)
    self._setter = None

class FileInput(BaseInput):
  def __init__(self, master, **kwargs):
    self._onlydir = False
    self._ext = ('Any File', '.*')
    self._rootdir = None
    self._excludefiles = []
    self._suggestions = []
    self._file_suggestions = None

    self._textv = StringVar()
    self._box = ttk.Frame(master=master)
    self._box.grid_columnconfigure(0, weight=1)
    self._box.grid_columnconfigure(1, weight=0)
    self._box.grid_rowconfigure(0, weight=1)
    
    self._input = AutocompleteCombobox(
      master=self._box,
      completevalues=[],
      textvariable=self._textv
    )

    # Redirect configure to input
    setattr(self._box, "config", self._input.config)
    setattr(self._box, "configure", self._input.configure)
    setattr(self._box, "keys", self._input.keys)
    setattr(self._box, "cget", self._input.cget)
    setattr(self._box, "winfo_class", self._input.winfo_class)
    setattr(self._box, "bind", self._input.bind)
    setattr(self._box, "set_completion_list", self._input.set_completion_list)

    super().__init__(tk=self._box, **kwargs)
    self.connect_to_prop("onlydir", self._on_onlydir_changed)
    self.connect_to_prop("ext", self._on_ext_changed)
    self.connect_to_prop("rootdir", self._on_rootdir_changed)
    self.connect_to_prop("excludefiles", self._on_excludefiles_changed)
    #self.connect_to_prop("suggestion", self.on_changed_suggestion)
    
    self._input.drop_target_register(DND_FILES)
    self._input.dnd_bind('<<Drop>>', self._drop)
    self._input.grid(row=0, column=0, sticky="news")

    self._btn = ttk.Button(master=self._box, command=self._load_file, text="Browse...")
    self._btn.grid(row=0, column=1)

  def _on_excludefiles_changed(self, value):
    self._excludefiles = value if value else []
    self._set_suggestions() 
  
  def _on_onlydir_changed(self, value):
    self._onlydir = value
  
  def on_changed_suggestion(self, value):
    if value:
      self._suggestions = value
      self._set_suggestions()

  def _set_suggestions(self):
    if self._rootdir and Path(self._rootdir).exists() and self._file_suggestions == None:
      get_suggestion_from_ext = lambda ext: list(filter(lambda fn: Path(fn).stem not in self._excludefiles, [str(fn) for fn in Path(self._rootdir).rglob(f"*{ext[1]}")]))
      
      if isinstance(self._ext, list):
        from functools import reduce
        self._file_suggestions = reduce(lambda a, curr: a + get_suggestion_from_ext(curr), [])
      else:
        self._file_suggestions = get_suggestion_from_ext(self._ext)
    if isinstance(self._file_suggestions, list):
      self._input.set_completion_list(self._suggestions + self._file_suggestions)
    else:
      self._input.set_completion_list(self._suggestions)

  def _on_ext_changed(self, value):
    self._ext = value if value else ('Any File', '.*')
    self._set_suggestions()
    
  def _on_rootdir_changed(self, value):
    self._rootdir = value
    self._set_suggestions()

  @property
  def container(self):
    return self._box

  def on_disposed(self):
    self._box.destroy()
    self._btn.destroy()
    super().on_disposed()
  
  def _load_file(self):
    if self._onlydir:
      f = tk.filedialog.askdirectory() 
    else:
      f = tk.filedialog.askopenfilename(filetypes=self._ext if isinstance(self._ext, list) else [self._ext])
    if f is None or f == '':
      return
    self._textv.set(str(Path(f)))

  def _drop(self, event):
    if event.data:
      files = self._tk.tk.splitlist(event.data)
      for f in files:
        self._textv.set(f)
        break
    return event.action

class Input(BaseInput):
  def __init__(self, master, **kwargs):
    self._textv = StringVar()
    super().__init__(
      tk=AutocompleteEntry(
        master=master,
        completevalues=[],
        textvariable=self._textv
      ), **kwargs
    )