from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog, QInputDialog, QLineEdit, QAction
from PyQt5.QtCore import QObject, pyqtSignal
from models import CustomBlock
from .block import BasicBlock
from .duty_dialog import DutyDialog
from functions import contrast_ratio
from db_config import settings

class BlockSignaler(QObject):
    block_moved = pyqtSignal(CustomBlock, int)
    block_updated = pyqtSignal(CustomBlock)

class CustomBlock(BasicBlock):
    def __init__(self, x, y, w, h, parent, db, visible_classes):
        super().__init__(x, y, w, h, parent, db, visible_classes)
        self.signal = BlockSignaler()

    def paint(self, painter, option, widget = ...):
        super().paint(painter, option)
        duties = list(filter(self.filter, self.block.duties))
        if not (len(duties) or settings.draw_custom_blocks):
            self.hide()

    def contextMenuEvent(self, event):
        super().contextMenuEvent(event)
        pick_color_action = QAction('Wybierz kolor')
        pick_color_action.triggered.connect(self.pick_color)
        self.menu.insertAction(self.remove_action, pick_color_action)
        set_text_action = QAction('Ustaw tekst')
        set_text_action.triggered.connect(self.set_text)
        self.menu.insertAction(self.remove_action, set_text_action)
        duties_action = QAction('Dyżury')
        duties_action.triggered.connect(self.edit_duties)
        self.menu.insertAction(self.remove_action, duties_action)
        self.menu.exec(event.globalPos())
    
    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.block.color))
        if color.isValid():
            self.setBrush(color)
            self.db.update_custom_block_color(self.block, color.name())

            if contrast_ratio(color, QColor('black')) < 4.5:
                self.text_item0.setDefaultTextColor(QColor('#ffffff'))

    def set_text(self):
        placeholder = self.text_item0.toPlainText().replace('\n', '<br>')
        text, ok = QInputDialog.getText(None, 'Podaj tekst', 'Tekst:', QLineEdit.Normal, placeholder) 
        if ok:
            self.text_item0.set_custom_text(text)
            self.recenter_text()
            self.db.update_custom_block_text(self.block, text)

    def edit_duties(self):
        if not self.block:
            return False
        dlg = DutyDialog(self.block, self.db)
        dlg.exec()
        self.signal.block_updated.emit(self.block)

    def draw_contents(self):

        color = QColor(self.block.color)
        color.setAlpha(settings.alpha)
        # color.setAlpha(210)
        self.setBrush(color)
        self.text_item0.set_custom_text(self.block.text)
        if contrast_ratio(color, QColor('black')) < 4.5:
            self.text_item0.setDefaultTextColor(QColor('#ffffff'))
        self.recenter_text()

    # def add_collision(*args):
    #     pass


    def mouseMoveEvent(self, event, show_tooltip=True):
        super().mouseMoveEvent(event, show_tooltip)
        self.recenter_text()