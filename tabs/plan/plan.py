from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog,\
      QGraphicsTextItem, QCheckBox, QApplication, QMessageBox, QComboBox
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt
from data import Data
from .mode_btn import ModeBtn
from .plan_view import MyView
from .filter import FilterWidget
from .stats import Statistic, StudentDensityStat
from db_config import settings
from coloring import ColoringThread
import os
from pathlib import Path
from matplotlib import pyplot as plt
from PyQt5.QtPrintSupport import QPrinter
from progress_dialog import ProgressDialog
        

class PlanWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.db: Data = parent.db
        self.rem_les_win = None
        self.need_redrawing = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)




        toolbar = QWidget()
        toolbar.setLayout(QHBoxLayout())
        toolbar.layout().setContentsMargins(10,0,10,5)

        # modes
        self.tool_add_block = ModeBtn("Nowy blok zajęciowy", self.set_mode_new, toolbar)
        toolbar.layout().addWidget(self.tool_add_block)
        self.tool_move_block = ModeBtn("Przesuwanie", self.set_mode_move ,toolbar)
        toolbar.layout().addWidget(self.tool_move_block)
        self.tool_add_custom = ModeBtn("Nowy blok", self.set_mode_new_custom ,toolbar)
        toolbar.layout().addWidget(self.tool_add_custom)

        # scale
        toolbar.layout().addWidget(QLabel('Skala:'))
        self.scale_slider = QSlider(Qt.Horizontal, self)
        self.scale_slider.setMaximumWidth(150)
        self.scale_slider.setMinimumWidth(70)
        self.scale_slider.setMinimum(100)
        self.scale_slider.setMaximum(300)
        self.scale_slider.setSingleStep(10)
        self.scale_slider.setPageStep(50)
        self.scale_slider.setTickPosition(QSlider.TicksAbove | QSlider.TicksBelow)
        self.scale_slider.setTickInterval(50)
        self.scale_slider.valueChanged.connect(self.update_scale)
        toolbar.layout().addWidget(self.scale_slider)
        self.scale_label = QLabel('100%', self.scale_slider)
        toolbar.layout().addWidget(self.scale_label)

        # alpha
        toolbar.layout().addWidget(QLabel('Przezroczystość:'))
        self.alpha_slider = QSlider(Qt.Horizontal, self)
        self.alpha_slider.setMaximumWidth(80)
        self.alpha_slider.setMinimumWidth(40)
        self.alpha_slider.setMinimum(0)
        self.alpha_slider.setMaximum(5)
        # self.alpha_slider.setSingleStep(5)
        self.alpha_slider.setPageStep(1)
        self.alpha_slider.setTickPosition(QSlider.TicksAbove | QSlider.TicksBelow)
        self.alpha_slider.setTickInterval(1)
        self.alpha_slider.valueChanged.connect(self.update_alpha)
        toolbar.layout().addWidget(self.alpha_slider)
        self.alpha_label = QLabel('0%')
        toolbar.layout().addWidget(self.alpha_label)

        allow_conflicts = QCheckBox(toolbar)
        allow_conflicts.clicked.connect(self.toggle_allow_conflicts)
        toolbar.layout().addWidget(allow_conflicts)
        toolbar.layout().addWidget(QLabel('Zezwalaj na konflikty'))


        toolbar.layout().addWidget(QLabel('Statystyki:'))
        self.stats = QComboBox()
        self.default_stat = Statistic(self.db)
        self.student_density_stat = StudentDensityStat(self.db)
        self.stats.addItem('---', self.default_stat)
        self.stats.addItem('Zagęszczenie uczniów', self.student_density_stat)
        self.stats.currentIndexChanged.connect(self.set_stat)
        toolbar.layout().addWidget(self.stats)

        toolbar.layout().addStretch()

        self.view = MyView(self)
        self.hidden_view = MyView(self, (2970, 2100))
        self.class_filter = FilterWidget(self)
        
        self.container = QWidget()
        self.container.setAttribute(Qt.WA_DontShowOnScreen, True)
        conlayout = QVBoxLayout(self.container)
        conlayout.addWidget(self.hidden_view)

        # self.container.show()
        # self.hidden_view.resize(2970, 2100)
        # self.container.hide()

        layout.addWidget(self.class_filter)
        layout.addWidget(toolbar)
        layout.addWidget(self.view)
        self.load_data(self.db)
        self.class_filter.updated.connect(self.view.update_filters)
        self.class_filter.set_mode_normal.connect(self.uncheck_all_modes)
        self.view.load_data(self.db)
        self.view.set_classes(self.db.all_subclasses())
        self.db.update_block.connect(self.view.redraw_block)
        self.db.update_custom_block.connect(self.view.redraw_block)
        self.db.redraw_plan.connect(self.stage_redraw)

    def stage_redraw(self):
        self.need_redrawing = True


    def redraw(self):
        if self.need_redrawing:
            self.class_filter.load_data(self.db)
            self.class_filter.update_filter()
            self.need_redrawing = False

    def export(self):
        settings.alpha = 255 
        settings.hide_empty_blocks = True
        settings.draw_blocks_full_width = False
        settings.draw_custom_blocks = True
        settings.italicize_unlocked_lessons = False


        scene = self.hidden_view.scene()
        parent_folder = QFileDialog.getExistingDirectory(self, 'Wybierz folder', str(Path.home()))
        if not parent_folder:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        rect = scene.sceneRect()

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPaperSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Landscape)


        pix = QPixmap(rect.size().toSize())
        for subclass in self.db.all_subclasses():
            os.makedirs(f'{parent_folder}/{subclass.full_name()}', exist_ok=True)
            def filter_func(l):
                return not hasattr(l, 'subject') \
                    or l.subject.parent() in [subclass, subclass.my_class]
            self.hidden_view.filter_func = filter_func
            self.hidden_view.set_classes([subclass])
            self.hidden_view.draw()
            self.hidden_view.narrow_overlapping_blocks()

            filename = f'{parent_folder}/{subclass.full_name()}/{subclass.full_name()}'
            self.render(filename, pix, printer, scene)

            for student in subclass.students:
                filename = f'{parent_folder}/{subclass.full_name()}/{student.name}'
                def filter_func(l):
                    return not hasattr(l, 'subject')\
                        or student in l.subject.students
                self.hidden_view.filter_func = filter_func
                self.hidden_view.set_classes([subclass])
                self.hidden_view.draw()
                self.render(filename, pix, printer, scene)

        settings.draw_custom_blocks = False
        settings.draw_blocks_full_width = True


        os.makedirs(f'{parent_folder}/nauczyciele', exist_ok=True)
        for teacher in self.db.all_teachers():
            filename = f'{parent_folder}/nauczyciele/{teacher.name}'
            def filter_func(l):
                return l.teacher == teacher
            self.hidden_view.filter_func = filter_func
            self.hidden_view.set_classes(self.db.all_subclasses())
            self.hidden_view.draw()
            self.render(filename, pix, printer, scene)

        os.makedirs(f'{parent_folder}/sale', exist_ok=True)
        for classroom in self.db.all_classrooms():
            filename = f'{parent_folder}/sale/{classroom.name}'
            def filter_func(l):
                return l.classroom == classroom
            self.hidden_view.filter_func = filter_func
            self.hidden_view.set_classes(self.db.all_subclasses())
            self.hidden_view.draw()
            self.render(filename, pix, printer, scene)


                       
        settings.hide_empty_blocks = False
        settings.draw_blocks_full_width = False
        settings.draw_custom_blocks = True
        settings.italicize_unlocked_lessons = True
        self.update_alpha(self.alpha_slider.value())
     
        QApplication.restoreOverrideCursor()
        QMessageBox.information(self, 'Gotowe', 'Eksport zakończony')

    def render(self, filename, pix, printer, scene):
        pix.fill(Qt.white)
        painter = QPainter(pix)
        scene.render(painter)
        pix.save(filename + '.png', 'PNG', 100)
        painter.end()

        printer.setOutputFileName(filename + '.pdf')
        painter_pdf = QPainter(printer)
        scene.render(painter_pdf)
        painter_pdf.end()



    def render_scene_to_pixmap(self):
        self.container.show()
        scene = self.hidden_view.scene()
        for text in [i for i in scene.items() if isinstance(i, QGraphicsTextItem)]:
            text.ensureVisible()
        rect = scene.sceneRect()

        pix = QPixmap(rect.size().toSize())
        pix.fill(Qt.white)

        painter = QPainter(pix)
        scene.render(painter)
        painter.end()
        filename, _ = QFileDialog.getSaveFileName(self, 'Eksportuj', 'plan.png')
        pix.save(filename, 'PNG', 100)
        self.container.hide()
 


    def update_scale(self, value):
        self.scale_label.setText(f'{value}%')
        self.view.resetTransform()
        self.view.scale(value/100, value/100)
        
    def set_mode_new(self, checked):
        if checked:
            self.class_filter.go_to_class_filter()
            self.view.set_mode('new')
        else:
            self.view.set_mode('normal')

    def set_mode_new_custom(self, checked):
        if checked:
            self.class_filter.go_to_class_filter(True)
            self.class_filter
            self.view.set_mode('new_custom')

        else:
            self.view.set_mode('normal')
    
    def set_mode_move(self, checked):
        if checked:
            self.class_filter.go_to_class_filter()
            self.view.set_mode('move')
        else:
            self.view.set_mode('normal')

    def uncheck_all_modes(self):
        self.tool_add_block.uncheck()
        self.tool_add_custom.uncheck()
        self.tool_move_block.uncheck()
        self.view.set_mode('normal')
    
    def update_alpha(self, value):
        alpha = 255 - value*25
        settings.alpha = alpha
        percent = int(value*10)
        self.alpha_label.setText(f'{percent}%')
        self.view.draw()

    def toggle_allow_conflicts(self):
        settings.allow_creating_conflicts = self.sender().isChecked()

    def set_stat(self):
        stat = self.stats.currentData()
        self.view.set_stat(self.stats.currentData())

    def color(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.db.blockSignals(True)
        self.db.clear_all_lesson_blocks(leave_locked=True)
        self.bar = ProgressDialog('Uzupełnianie planu zajęć', 0)
        self.bar.show()
        # session = self.db.get_scoped_session()
        # les_g, _ , feas = generate_lesson_graph(self.db, session)
        # bl_g = generate_block_graph(self.db, session)
        self.thread = ColoringThread(self.db)
        self.thread.update_bar.connect(self.update_bar)
        self.thread.update_bar_total.connect(self.bar.set_total)
        self.thread.increment_bar.connect(self.bar.next)
        # self.thread.next_generation.connect(self.update_bar)
        self.thread.finished.connect(self.show_solution)
        self.thread.start()


    def update_bar(self, label):
        self.bar.show()
        self.bar.set_label(label)




    def show_solution(self, c, best_scores, cutoffs): 
        self.db.blockSignals(False)
        for lesson, color in c.items():
            # print(lesson, color)
            block_id, classroom_id = color
            # print(block_id, classroom_id)
            # if lesson.block_locked:
            #     print('dupadupa')
            # if lesson.block == block:
            #     continue
            self.db.place_lesson_id_mode(lesson, block_id, classroom_id, lock=False)
        # self.view.draw()
        QApplication.restoreOverrideCursor()
        self.bar = None
        if settings.verbose:
            l1, = plt.plot(best_scores)
            l2, = plt.plot(cutoffs)
            plt.legend([l1, l2],['Najlepszy wynik', 'Wynik odcięcia'])
            plt.show()
        # QMessageBox.information(self, 'Gotowe', 'Eksport zakończony')
        



    def clear_blocks(self):
        self.db.clear_all_lesson_blocks()
        # self.view.draw()


    def load_data(self, db):
        self.db = db
        self.class_filter.load_data(db)
        self.view.load_data(db)
        self.class_filter.update_filter()
        # self.view.draw()
        # self.hidden_view.load

