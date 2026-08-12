from PyQt5.QtWidgets import QAction, QMessageBox, QApplication
from PyQt5.QtGui import QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QRectF, QObject, pyqtSignal
from models import Block
from .block import BasicBlock
from .edit_lesson_block_dialog import EditLessonBlockDialog
from functions import contrast_ratio
from db_config import settings
from data import TeacherDuty, Lesson

class BlockSignaler(QObject):
    block_moved = pyqtSignal(Block, int)
    block_updated = pyqtSignal(Block)


class LessonBlock(BasicBlock):
    def __init__(self, x, y, w, h, parent, db, visible_classes):
        super().__init__(x, y, w, h, parent, db, visible_classes)
        self.text_items = {}
        self.signal = BlockSignaler()
        # self.signal.block_moved.connect(self.move_and_check_collsions)

    def mousePressEvent(self, event):
        source = None
        if settings.move_lessons_from:
            source = settings.move_lessons_from
        if settings.swap_lessons_from:
            source = settings.swap_lessons_from
        if source:
            source_block = source.block
            if (source_block.class_ == self.block.class_ and source_block.class_\
              or source_block.subclass == self.block.subclass and source_block.subclass) \
              and source_block.length == self.block.length:
                if settings.move_lessons_from:
                    events = source_block.events.copy()
                    for event in events:
                        if isinstance(event, Lesson):
                            self.db.add_lesson_to_block(event, self.block, event.block_locked)
                else:
                    self.db.swap_lessons(self.block, source.block)

                QApplication.restoreOverrideCursor()
                source.draw_contents()
                self.draw_contents()
                settings.move_lessons_from = None
                settings.swap_lessons_from = None
            else:
                QMessageBox.warning(None, 'Uwaga!', 'Nie można przenieść lekcji do tego bloku.')
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        super().contextMenuEvent(event)
        # add_lesson_action =  QAction('Dodaj lekcję')
        # self.menu.insertAction(self.remove_action, add_lesson_action)
        # add_lesson_action.triggered.connect(self.add_subject)
        manage_classrooms_action =  QAction('Edytuj')
        self.menu.insertAction(self.remove_action, manage_classrooms_action)
        manage_classrooms_action.triggered.connect(self.edit)
        
        copy_action =  QAction('Kopiuj')
        self.menu.insertAction(self.remove_action, copy_action)
        copy_action.triggered.connect(self.copy)
        
        if len(self.block.events):
            # remove_lesson_action =  QAction('Usuń lekcję')
            # self.menu.insertAction(self.remove_action, remove_lesson_action)
            # remove_lesson_action.triggered.connect(self.remove_lesson)
            # manage_locked_action = QAction('Blokowanie lekcji')
            # self.menu.insertAction(self.remove_action, manage_locked_action)
            # manage_locked_action.triggered.connect(self.manage_locked)

            move_lessons_action = QAction('Przenieś lekcje')
            self.menu.insertAction(self.remove_action, move_lessons_action)
            move_lessons_action.triggered.connect(self.move_lessons)
            swap_lessons_action = QAction('Zamień lekcje')
            self.menu.insertAction(self.remove_action, swap_lessons_action)
            swap_lessons_action.triggered.connect(self.swap_lessons)
        action = self.menu.exec(event.globalPos())

    # def get_colliding_blocks(self):
    #     rect = self.mapRectToScene(self.boundingRect())

    #     return [bl for bl in self.scene().items() \
    #                         if isinstance(bl, LessonBlock) \
    #                         and (rect.top() <= bl.boundingRect().top() <= rect.bottom() \
    #                         or rect.top() <= bl.boundingRect().bottom() <= rect.bottom())]
    
    def move_and_check_collisions(self, lesson_block, start: int):
        self.write()
        return
    
    def edit(self):
        EditLessonBlockDialog(self).exec()

    def copy(self):
        self.db.copy_block_down(self.block)

    def delete(self):
        if len(self.block.events):
            if QMessageBox.question(
                None, 
                'Usuwanie',
                'Czy na pewno chcesz usunąć ten blok?', 
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return
        return super().delete()

    def move_lessons(self):
        QApplication.setOverrideCursor(Qt.DragMoveCursor)
        settings.move_lessons_from = self
        settings.swap_lessons_from = None

    def swap_lessons(self):
        QApplication.setOverrideCursor(Qt.DragMoveCursor)
        settings.swap_lessons_from = self
        settings.move_lessons_from = None

    def paint(self, painter, option, widget = ...):
        if not hasattr(self, 'block'):
            return super().paint(painter, option)
        
        painter.setPen(QPen(Qt.NoPen))
        rects, buckets, colors, _= self.get_rects()
        for rect, color in zip(rects, colors):
            if not color:
                continue
            brush = QBrush(color)
            painter.fillRect(rect, brush)
            painter.drawRect(rect)

        super().paint(painter, option)

    def get_rects(self):
        events = list(filter(self.filter, self.block.events))
        if self.db.settings().hide_empty_blocks and not len(events):
            self.hide()
        show_full_subject_names = False
        rect = self.rect().adjusted(0.5,0,-0.5,0)
        # split the rect
        duties = []
        lessons = []
        # only consider splitting if block is assigned to a full class
        split_the_rect = self.block.class_ is not None
        for event in events:
            if isinstance(event, TeacherDuty):
                duties.append(event)
            elif isinstance(event, Lesson):
                lessons.append(event)
                if event.subject.class_:
                    split_the_rect = False
        if len(lessons) == 0:
            split_the_rect = False
        if split_the_rect:
            rects = []
            buckets = {sub_class:[] for sub_class in self.block.class_.subclasses if sub_class in self.visible_classes}
            for lesson in lessons:
                buckets[lesson.subject.parent()].append(lesson)
            n_of_buckets = len(buckets)
            if not n_of_buckets:
                return (None, None, None)
            
            width = rect.width()/n_of_buckets
            height = rect.height() 
            y = rect.top()
            for n in range(n_of_buckets):
                if self.db.settings().draw_blocks_full_width:
                    rects.append(rect)
                else:
                    x = rect.left()
                    x += width * n
                    rects.append(QRectF(x, y, width, height))
        else:
            rects = [rect]
            buckets = {self.block.subclass: lessons}
            show_full_subject_names = True
        final_colors = []
        for rect, subclass, events in zip(rects, buckets.keys(), buckets.values()):
            if self.db.settings().hide_empty_blocks and not len(events):
                final_colors.append(None)
                continue
            # subclass, lessons = bucket
            colors = set()
            for lesson in events:
                if isinstance(lesson, TeacherDuty):
                    continue
                if lesson.subject.color:
                    colors.add(lesson.subject.color)

            colors = list(colors)

            if len(colors) == 0:
                color = self.block.color
            elif len(colors) == 1:
                color = colors[0]
            else:
                color =  '#c0c0c0'
            color = QColor(color)
            color.setAlpha(self.db.settings().alpha)
            final_colors.append(color)
        if len(rects)!= len(final_colors):
            print(len(rects), len(final_colors))
        return rects, buckets, final_colors, duties

       
    def write(self, specify_class=False):
        # print(f'writing: {self.block}')
        n=0
        rects, buckets, colors, duties = self.get_rects()
        if not rects:
            return
        for i in range(5):
            self.__getattribute__(f'text_item{i}').setHtml('')
        for rect, subclass, lessons, color in zip(rects, buckets.keys(), buckets.values(), colors):
            if self.db.settings().hide_empty_blocks and not len(duties) and not len(lessons):
                continue

            rect = self.mapRectToScene(rect)
            match(n):
                case 0:
                    text_item = self.text_item0
                case 1:
                    text_item = self.text_item1
                case 2: 
                    text_item = self.text_item2
                case 3:
                    text_item = self.text_item3
            n+=1
            
            text_item.set_h(rect.height())

            text_item.set_w(rect.width())

            # correct color
            if contrast_ratio(color, QColor('black')) < 4.5:
                text_item.setDefaultTextColor(QColor('white'))
            else:
                text_item.setDefaultTextColor(QColor('black'))
            # write on screen
            if self.db.settings().draw_blocks_full_width:
                specify_class = True
            specify_subclass = len([l for l in lessons if not l.subject.basic]) or specify_class
            text_item.write_lessons(lessons, duties, self.block, specify_class, specify_subclass)
            # recenter
            text_item.setZValue(self.zValue()+0.2)
            text_item.setPos(rect.center().x() - text_item.boundingRect().width()/2,\
                    rect.top() + rect.height()/2 - text_item.boundingRect().height()/2)
    

    def draw_contents(self):
        # self.draw_collisions()
        self.write()
        # self.update()
    
    # def draw_collisions(self):
    #     collisions = self.db.block_collisions(self.block)

    #     display_collisions = '\n'.join([c[1] for c in collisions])

    #     if display_collisions:
    #         self.setPen(QPen(QBrush(Qt.red),4))
    #         # QToolTip.showText(self.mapRectToScene(self.boundingRect().topLeft().toPoint()), self.time() + '\n' + collisions)
    #         self.setToolTip(self.time() + '\n' + display_collisions)
    #     else:
    #         self.setPen(QPen())
    #         self.setToolTip(self.time())
    #     return display_collisions

    def overlapping_lesson_blocks(self):
        return [bl for bl in self.collidingItems() \
                if isinstance(bl, LessonBlock) \
                and bl.block.day==self.block.day\
                and abs(bl.mapRectToScene(bl.boundingRect()).top() - self.mapRectToScene(self.boundingRect()).bottom()) > 3 \
                and abs(bl.mapRectToScene(bl.boundingRect()).bottom() - self.mapRectToScene(self.boundingRect()).top()) > 3] 
    