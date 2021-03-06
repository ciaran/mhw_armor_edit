# coding: utf-8
import logging
import os
import sys
from contextlib import contextmanager
from functools import partial

from PyQt5.QtCore import Qt, QSize, QPoint, QModelIndex
from PyQt5.QtGui import QKeySequence, QIcon, QTextDocument
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileSystemModel,
                             QTreeView, QStyle,
                             QFileDialog, QTabWidget, QBoxLayout,
                             QWidget, QMessageBox, QDockWidget, QLabel,
                             QVBoxLayout, QLineEdit, QStatusBar, QDialog,
                             QTextBrowser)

from mhw_armor_edit.assets import Assets
from mhw_armor_edit.editor.models import FilePluginRegistry
from mhw_armor_edit.import_export import ExportDialog, ImportDialog
from mhw_armor_edit.models import Workspace, Directory
from mhw_armor_edit.utils import create_action, AppSettings

STATUSBAR_MESSAGE_TIMEOUT = 10 * 1000
ABOUT_TEXT = """<h3>MHW Editor Suite</h3>
<table cellspacing="10">
<tr><td>Version:</td><td>v1.7.1-alpha</td></tr>
<tr><td>Release-Date:</td><td>2019-05-03</td></tr>
<tr><td>URL:</td><td><a href="https://github.com/fre-sch/mhw_armor_edit/releases">
    https://github.com/fre-sch/mhw_armor_edit/releases</a></td>
</tr>
</table>
"""
log = logging.getLogger()
LANG = (
    ("jpn", "Japanese"),
    ("eng", "English"),
    ("fre", "French"),
    ("spa", "Spanish"),
    ("ger", "German"),
    ("ita", "Italian"),
    ("kor", "Korean"),
    ("chT", "Chinese"),
    ("rus", "Russian"),
    ("pol", "Polish"),
    ("ptB", "Portuguese"),
    ("ara", "Arabic"),
)
QUICK_ACCESS_ITEMS = (
    ("Items", r"common\item\itemData.itm"),
    ("Armors", r"common\equip\armor.am_dat"),
    ("Great Sword", r"common\equip\l_sword.wp_dat"),
    ("Sword & Shield", r"common\equip\sword.wp_dat"),
    ("Dual Blades", r"common\equip\w_sword.wp_dat"),
    ("Longsword", r"common\equip\tachi.wp_dat"),
    ("Hammer", r"common\equip\hammer.wp_dat"),
    ("Hunting Horn", r"common\equip\whistle.wp_dat"),
    ("Lance", r"common\equip\lance.wp_dat"),
    ("Gun Lance", r"common\equip\g_lance.wp_dat"),
    ("Switch Axe", r"common\equip\s_axe.wp_dat"),
    ("Charge Blade", r"common\equip\c_axe.wp_dat"),
    ("Insect Glaive", r"common\equip\rod.wp_dat"),
    ("Bow", r"common\equip\bow.wp_dat_g"),
    ("Heavy Bowgun", r"common\equip\hbg.wp_dat_g"),
    ("Light Bowgun", r"common\equip\lbg.wp_dat_g"),
)
HELP_CONTENT = """
<style>code {background-color:#EEE;}</style>
<h2>Setup game content</h2>
<p>The game loads the chunks incremental, and each chunk overwrites files in
previous chunks.<br/>
Loosely speaking, the game loads files in <code>chunk0</code>, then loads files
in <code>chunk1</code> replacing all files it loaded from <code>chunk1</code>,
then it loads files in <code>chunk2</code>, again replacing all files it loaded
from <code>chunk0</code> or <code>chunk1</code>,
until it has loaded all chunks.<br/>
So to get the full database (so-to-speak), you should do the same:</p>
<ul>
<li>Extract all <code>&lt;GAMEDIR&gt;\chunk\chunk*.bin</code> using 
    <a href="https://www.nexusmods.com/monsterhunterworld/mods/6">worldchunktool on nexusmods</a>.</li>
<li>Using Windows File Explorer, merge all extracted chunk directories into one:
  <ul>
  <li>Create a new directory <code>merged</code></li>
  <li>Navigate into chunk directory <code>chunk0</code>, select all and copy.</li>
  <li>Navigate into <code>merged</code> directory, and paste. Wait for completion.</li>
  <li>Navigate to next chunk directory <code>chunk1</code>, select all and copy.</li>
  <li>Navigate to <code>merged</code> directory, and paste. In the popup
    "Confirm Folder Replace" choose "Yes". In the popup "Replace or Skip Files"
    choose "Replace the file in the destination". Make sure to replace all files.
    Wait for completion.</li>
  <li>Repeat for all remaining chunk directories in ascending order, eg.
    <code>chunk2</code>, <code>chunk3</code>, <code>chunk4</code>, <code>chunk5</code>.</li>
  </ul>
</li>
<li>Using windows File Explorer, create a directory <code>my-first-mod</code>.</li>
<li>Run <code>MHW-Editor-Suite.exe</code> and open directory <code>merged</code>
    using the menu <b>File</b> -&gt; <b>Open chunk directory ...</b>.</li>
<li>Open the directory <code>my-first-mod</code> using the menu <b>File</b> -&gt; <b>Open mod directory ...</b>.</li>
<li>Open files from the chunk directory browser, edit them and save them to add or update them to the mod directory</li>
<li>Open files from the mod directory browser, edit and save them in mod directory.</li>
</ul>

<h2>Export full file</h2>
<p>Using the <b>Export ...</b> action in the <b>File</b> menu, the contents of a
file can be exported in either JSON or CSV format.</p>
<p>After activating the <b>Export ...</b> action, the properties to be exported
can be selected. Only checked properties will be exported. By default, only
properties that are safe between game updates are checked. It's not critical to 
make a choice here, since it's also possible to specify properties when
importing.</p>
<p>After clicking the <b>OK</b> button, the target file can be selected.<br/>
Additionally, now the format for the export can be selected in the field
<b>Save as type</b> below the file name.</p>
<p>Finally, clicking save will export to the specified file.</p>

<h2>Export single item</h2>
<p>To export single items - such as one armor piece, or one weapon - open the
file containing the item.</p>
<p>In the items list, right-click the item to be exported and click the
<b>Export ...</b> action.</p>
<p>After activating the <b>Export ...</b> action, the properties to be exported
can be selected. Only checked properties will be exported. By default, only
properties that are safe between game updates are checked. It's not critical to 
make a choice here, since it's also possible to specify properties when
importing.</p>
<p>After clicking the <b>OK</b> button, the target file can be selected.<br/>
Additionally, now the format for the export can be selected in the field
<b>Save as type</b> below the file name.</p>
<p>Finally, clicking save will export to the specified file.</p>

<h2>Import full file</h2>
<p>Using the <b>Import ...</b> action in the <b>File</b> menu, the contents of a
file in either JSON or CSV format can be imported. This is meant to import the
contents of a previously exported file.<br/>
It's not possible to add additional items using the import.</p>
<p>After activating the <b>Import ...</b> action, use the file dialog to locate
a file to import. Use the field just after the file name to switch between JSON
or CSV files. Click the <b>Open</b> button to proceed with the import.</p>
<p>Now the properties to be imported can be selected. Only checked properties
will be imported and overwritten. By default, only properties that are safe
between game updates are checked.</p>
<p>Press the <b>OK</b> button to import the data. This will set all selected
properties for each item in the current game data file. Save the game file or
close and reopen the game data file to discard the import.</p>
<p>Items are imported in sequence, if the import data has more items than the
game data file, all additional items (from the import) are discarded.</p>
<p>There is no check for type, so take care to select the correct file when
importing.</p>

<h2>Import single item</h2>
<p>To import single items - such as one armor piece, or one weapon - open the
game data file containing the item.</p>
<p>In the items list, right-click the item to be imported and click the
<b>Import ...</b> action.</p>
<p>After activating the <b>Import ...</b> action, use the file dialog to locate
a file to import. Use the field just after the file name to switch between JSON
or CSV files. Click the <b>Open</b> button to proceed with the import.</p>
<p>Now the properties to be imported can be selected. Only checked properties
will be imported and overwritten. By default, only properties that are safe
between game updates are checked.</p>
<p>Press the <b>OK</b> button to import the data. This will set all selected
properties on the selected item. Save the game file or close and reopen the game
data file to discard the import.</p>
"""


@contextmanager
def show_error_dialog(parent, title="Error"):
    try:
        yield
    except Exception as e:
        QMessageBox.warning(parent, title, str(e), QMessageBox.Ok, QMessageBox.Ok)


class EditorView(QWidget):
    def __init__(self, workspace_file, child_widget, parent=None):
        super().__init__(parent)
        self.workspace_file = workspace_file
        layout = QBoxLayout(QBoxLayout.TopToBottom)
        self.setLayout(layout)
        child_widget.set_model(self.workspace_file)
        layout.addWidget(child_widget)
        self.workspace_file.reloaded.connect(
            lambda: child_widget.set_model(self.workspace_file)
        )
        self.workspace_file.modifiedChanged.connect(
            self.handle_workspace_file_modified_changed
        )

    def handle_workspace_file_modified_changed(self, modified):
        tab_widget = self.parent().parent()
        tab_index = tab_widget.indexOf(self)
        title = f"{self.workspace_file.directory.name}: {self.workspace_file.rel_path}"
        if modified:
            title += "*"
        tab_widget.setTabText(tab_index, title)

    @classmethod
    def factory(cls, parent, workspace_file):
        plugin = FilePluginRegistry.get_plugin(workspace_file.abs_path)
        widget_inst = plugin.widget_factory()
        inst = cls(workspace_file, widget_inst, parent)
        return inst


class DirectoryDockWidget(QWidget):
    def __init__(self, directory: Directory, filtered=False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(layout)
        self.path_label = QLineEdit()
        self.path_label.setReadOnly(True)
        layout.addWidget(self.path_label)
        self.tree_view = QTreeView()
        layout.addWidget(self.tree_view)
        self.directory = directory
        self.filtered = filtered
        self.tree_view.setModel(QFileSystemModel())
        for i in range(1, 4):
            self.tree_view.hideColumn(i)
        self.tree_view.setHeaderHidden(True)
        self.directory.changed.connect(self.handle_directory_path_changed)

    def handle_directory_path_changed(self, path):
        if not path:
            return
        self.path_label.setText(path)
        model = self.tree_view.model()
        model.setRootPath(path)
        self.tree_view.setRootIndex(model.index(path))
        if self.filtered:
            model.setNameFilters(
                plugin.pattern for plugin in FilePluginRegistry.plugins
            )


class HelpWidget(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        help_content = QTextDocument()
        help_content.setHtml(HELP_CONTENT)
        self.setOpenExternalLinks(True)
        self.setDocument(help_content)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chunk_directory = Directory(
            "CHUNK", QIcon(Assets.get_asset_path("document_a4_locked.png")),
            None)
        self.mod_directory = Directory(
            "MOD", QIcon(Assets.get_asset_path("document_a4.png")),
            None)
        self.workspace = Workspace([self.mod_directory, self.chunk_directory],
                                   parent=self)
        self.workspace.fileOpened.connect(self.handle_workspace_file_opened)
        self.workspace.fileClosed.connect(self.handle_workspace_file_closed)
        self.workspace.fileActivated.connect(self.handle_workspace_file_activated)
        self.workspace.fileLoadError.connect(self.handle_workspace_file_load_error)
        self.init_actions()
        self.init_menu_bar()
        self.init_toolbar()
        self.setStatusBar(QStatusBar())
        self.setWindowTitle("MHW-Editor-Suite")
        self.init_file_tree(self.chunk_directory, "Chunk directory",
                            self.open_chunk_directory_action, filtered=True)
        self.init_file_tree(self.mod_directory, "Mod directory",
                            self.open_mod_directory_action)
        self.init_help()
        self.setCentralWidget(self.init_editor_tabs())
        self.load_settings()

    def closeEvent(self, event):
        self.write_settings()

    def load_settings(self):
        self.settings = AppSettings()
        with self.settings.main_window() as group:
            size = group.get("size", QSize(1000, 800))
            position = group.get("position", QPoint(300, 300))
        with self.settings.application() as group:
            chunk_directory = group.get("chunk_directory", None)
            mod_directory = group.get("mod_directory", None)
            lang = group.get("lang", None)
        with self.settings.import_export() as group:
            self.import_export_default_attrs = {
                key: group.get(key, "").split(";")
                for key in group.childKeys()
            }
        # apply settings
        self.resize(size)
        self.move(position)
        if chunk_directory:
            self.chunk_directory.set_path(chunk_directory)
        if mod_directory:
            self.mod_directory.set_path(mod_directory)
        if lang:
            self.handle_set_lang_action(lang)

    def write_settings(self):
        with self.settings.main_window() as group:
            group["size"] = self.size()
            group["position"] = self.pos()
        with self.settings.application() as group:
            group["chunk_directory"] = self.chunk_directory.path
            group["mod_directory"] = self.mod_directory.path
            group["lang"] = FilePluginRegistry.lang
        with self.settings.import_export() as group:
            for key, value in self.import_export_default_attrs.items():
                group[key] = ";".join(value)

    def get_icon(self, name):
        return self.style().standardIcon(name)

    def init_actions(self):
        self.open_chunk_directory_action = create_action(
            self.get_icon(QStyle.SP_DirOpenIcon),
            "Open chunk_directory ...",
            self.handle_open_chunk_directory,
            None)
        self.open_mod_directory_action = create_action(
            self.get_icon(QStyle.SP_DirOpenIcon),
            "Open mod directory ...",
            self.handle_open_mod_directory,
            QKeySequence.Open)
        self.save_file_action = create_action(
            self.get_icon(QStyle.SP_DriveHDIcon),
            "Save file",
            self.handle_save_file_action,
            QKeySequence.Save)
        self.save_file_action.setDisabled(True)
        self.export_action = create_action(
            self.get_icon(QStyle.SP_FileIcon),
            "Export file ...",
            self.handle_export_file_action)
        self.export_action.setDisabled(True)
        self.import_action = create_action(
            self.get_icon(QStyle.SP_FileIcon),
            "Import file ...",
            self.handle_import_file_action)
        self.import_action.setDisabled(True)
        self.help_action = create_action(
            None, "Show help",
            self.handle_show_help_action
        )
        self.about_action = create_action(
            None, "About", self.handle_about_action)
        self.lang_actions = {
            lang: create_action(
                None, name, partial(self.handle_set_lang_action, lang),
                checkable=True)
            for lang, name in LANG
        }
        self.quick_access_actions = [
            create_action(
                None, title,
                partial(self.workspace.open_file_any_dir, file_rel_path))
            for title, file_rel_path in QUICK_ACCESS_ITEMS
        ]

    def init_menu_bar(self):
        menu_bar = self.menuBar()
        # file menu
        file_menu = menu_bar.addMenu("File")
        file_menu.insertAction(None, self.open_chunk_directory_action)
        file_menu.insertAction(None, self.open_mod_directory_action)
        file_menu.insertAction(None, self.export_action)
        file_menu.insertAction(None, self.import_action)
        file_menu.insertAction(None, self.save_file_action)

        quick_access_menu = menu_bar.addMenu("Quick Access")
        for action in self.quick_access_actions:
            quick_access_menu.insertAction(None, action)

        # lang menu
        lang_menu = menu_bar.addMenu("Language")
        for action in self.lang_actions.values():
            lang_menu.insertAction(None, action)

        # help menu
        help_menu = menu_bar.addMenu("Help")
        help_menu.insertAction(None, self.help_action)
        help_menu.insertAction(None, self.about_action)

    def init_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setFloatable(False)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.insertAction(None, self.open_mod_directory_action)
        toolbar.insertAction(None, self.save_file_action)

    def init_file_tree(self, directory, title, action, filtered=False):
        widget = DirectoryDockWidget(directory, filtered=filtered, parent=self)
        widget.path_label.addAction(action, QLineEdit.LeadingPosition)
        widget.tree_view.activated.connect(
            partial(self.handle_directory_tree_view_activated, directory))
        dock = QDockWidget(title, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable)
        dock.setWidget(widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def init_help(self):
        self.help_widget = HelpWidget(self)
        self.help_widget_dock = QDockWidget("Help", self)
        self.help_widget_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.help_widget_dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.help_widget_dock.setWidget(self.help_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.help_widget_dock)
        self.help_widget_dock.hide()

    def handle_show_help_action(self):
        if self.help_widget_dock.isVisible():
            self.help_widget_dock.hide()
        else:
            self.help_widget_dock.show()

    def handle_directory_tree_view_activated(self, directory, qindex: QModelIndex):
        if qindex.model().isDir(qindex):
            return
        file_path = qindex.model().filePath(qindex)
        self.workspace.open_file(directory, file_path)

    def init_editor_tabs(self):
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setDocumentMode(True)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(
            self.handle_editor_tab_close_requested)
        return self.editor_tabs

    def handle_workspace_file_opened(self, path, rel_path):
        ws_file = self.workspace.files[path]
        editor_view = EditorView.factory(self.editor_tabs, ws_file)
        editor_view.setObjectName(path)
        self.editor_tabs.addTab(editor_view,
                                ws_file.directory.file_icon,
                                f"{ws_file.directory.name}: {rel_path}")
        self.editor_tabs.setCurrentWidget(editor_view)
        self.save_file_action.setDisabled(False)
        self.export_action.setDisabled(False)
        self.import_action.setDisabled(False)

    def handle_workspace_file_activated(self, path, rel_path):
        widget = self.editor_tabs.findChild(QWidget, path)
        self.editor_tabs.setCurrentWidget(widget)

    def handle_workspace_file_closed(self, path, rel_path):
        widget = self.editor_tabs.findChild(QWidget, path)
        widget.deleteLater()
        has_no_files_open = not self.workspace.files
        self.save_file_action.setDisabled(has_no_files_open)
        self.export_action.setDisabled(has_no_files_open)
        self.import_action.setDisabled(has_no_files_open)

    def handle_workspace_file_load_error(self, path, rel_path, error):
        QMessageBox.warning(self, f"Error loading file `{rel_path}`",
                            f"Error while loading\n{path}:\n\n{error}",
                            QMessageBox.Ok, QMessageBox.Ok)

    def handle_editor_tab_close_requested(self, tab_index):
        editor_view = self.editor_tabs.widget(tab_index)
        self.workspace.close_file(editor_view.workspace_file)

    def handle_open_chunk_directory(self):
        path = QFileDialog.getExistingDirectory(parent=self,
                                                caption="Open chunk directory")
        if path:
            self.chunk_directory.set_path(os.path.normpath(path))

    def handle_open_mod_directory(self):
        path = QFileDialog.getExistingDirectory(parent=self,
                                                caption="Open mod directory")
        if path:
            self.mod_directory.set_path(os.path.normpath(path))

    def handle_save_file_action(self):
        main_ws_file = self.get_current_workspace_file()
        for ws_file in main_ws_file.get_files_modified():
            if ws_file.directory is self.chunk_directory:
                if self.mod_directory.is_valid:
                    self.transfer_file_to_mod_workspace(
                        ws_file, ws_file is main_ws_file)
                else:
                    self.save_base_content_file(ws_file)
            else:
                with show_error_dialog(self, "Error writing file"):
                    self.save_workspace_file(ws_file)

    def handle_export_file_action(self):
        ws_file = self.get_current_workspace_file()
        plugin = FilePluginRegistry.get_plugin(ws_file.abs_path)
        fields = plugin.data_factory.EntryFactory.fields()
        data = [it.as_dict() for it in ws_file.data.entries]
        dialog = ExportDialog.init(self, data, fields,
                                   plugin.import_export.get("safe_attrs"))
        dialog.open()

    def handle_import_file_action(self):
        ws_file = self.get_current_workspace_file()
        plugin = FilePluginRegistry.get_plugin(ws_file.abs_path)
        fields = plugin.data_factory.EntryFactory.fields()
        dialog = ImportDialog.init(self, fields,
                                   plugin.import_export.get("safe_attrs"),
                                   as_list=True)
        if dialog:
            dialog.import_accepted.connect(self.handle_import_accepted)
            dialog.open()

    def handle_import_accepted(self, import_data):
        ws_file = self.get_current_workspace_file()
        num_items = min(len(import_data), len(ws_file.data))
        for idx in range(num_items):
            ws_file.data[idx].update(import_data[idx])
        self.statusBar().showMessage(
            f"Import contains {len(import_data)} items. "
            f"Model contains {len(ws_file.data)} items. "
            f"Imported {num_items}.",
            STATUSBAR_MESSAGE_TIMEOUT)

    def handle_set_lang_action(self, lang):
        FilePluginRegistry.lang = lang
        for act in self.lang_actions.values():
            act.setChecked(False)
        self.lang_actions[lang].setChecked(True)

    def get_current_workspace_file(self):
        editor = self.editor_tabs.currentWidget()
        return editor.workspace_file

    def save_base_content_file(self, ws_file):
        result = QMessageBox.question(
            self, "Save base content file?",
            "Do you really want to update this chunk file?",
            QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
        if result == QMessageBox.Ok:
            with show_error_dialog(self, "Error writing file"):
                self.save_workspace_file(ws_file)

    def transfer_file_to_mod_workspace(self, ws_file, reopen=False):
        mod_abs_path, exists = self.mod_directory.get_child_path(ws_file.rel_path)
        if not exists:
            return self.transfer_file(ws_file, self.mod_directory, reopen)

        result = QMessageBox.question(
            self,
            "File exists, overwrite?",
            f"File '{ws_file.rel_path}' already found in mod directory, overwrite?",
            QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if result == QMessageBox.Ok:
            self.transfer_file(ws_file, self.mod_directory, reopen)

    def transfer_file(self, ws_file, target_directory, reopen=False):
        if target_directory is ws_file.directory:
            return
        self.workspace.close_file(ws_file)
        ws_file.set_directory(target_directory)
        self.save_workspace_file(ws_file)
        if reopen:
            self.workspace.open_file(target_directory, ws_file.abs_path)

    def save_workspace_file(self, ws_file):
        ws_file.save()
        self.statusBar().showMessage(
            f"File '{ws_file.abs_path}' saved.", STATUSBAR_MESSAGE_TIMEOUT)

    def handle_about_action(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("About MHW Editor Suite")
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        about_text = QLabel(ABOUT_TEXT)
        about_text.setTextFormat(Qt.RichText)
        about_text.setTextInteractionFlags(Qt.TextBrowserInteraction)
        about_text.setOpenExternalLinks(True)
        layout.addWidget(about_text)
        dialog.exec()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(Assets.get_asset_path("icon32.svg")))
    app.setStyleSheet("""
    QMainWindow::separator:vertical,
    QSplitter::handle:horizontal {
        width: 0px;
        margin: 0 6px;
        max-height: 100px;
        border-left: 1px dotted palette(dark);
        border-right: 1px dotted palette(base);
    }
    QMainWindow::separator:horizontal,
    QSplitter::handle:vertical {
        height: 0px;
        margin: 6px 0;
        border-top: 1px dotted palette(dark);
        border-bottom: 1px dotted palette(base);
    }
    QDockWidget::title {
        padding-top: 1ex;
        background-color: palette(window);
    }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
