# coding: utf-8
from PyQt5.QtWidgets import QWidget, QStackedLayout

from mhw_armor_edit.editor.models import EditorPlugin
from mhw_armor_edit.ftypes.wep_saxe import WepSaxe, WepSaxeEntry
from mhw_armor_edit.struct_table import StructTableModel, SortFilterTableView


class WepSaxeEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self.table_model = StructTableModel(WepSaxeEntry.fields(), self)
        self.table_view = SortFilterTableView(self)
        self.table_view.setModel(self.table_model)
        self.setLayout(QStackedLayout(self))
        self.layout().addWidget(self.table_view)

    def set_model(self, model):
        self.model = model
        if model is None:
            self.table_model.update([])
        else:
            self.table_model.update(model.data.entries)


class WepSaxePlugin(EditorPlugin):
    pattern = "*.wep_saxe"
    data_factory = WepSaxe
    widget_factory = WepSaxeEditor
    relations = {}
