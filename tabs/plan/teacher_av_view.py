from PyQt5.QtWidgets import QGraphicsView, QGraphicsRectItem, QGraphicsTextItem, QGraphicsScene
from PyQt5.QtGui import QPen, QFont, QBrush, QColor
from data import Data, Teacher, TeacherDuty, Lesson

DAY_NAMES = 'Poniedziałek Wtorek Środa Czwartek Piątek'.split()

class TeacherView(QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent)
        self.db: Data = parent.db
        self.resize(4200, 2970)
        self.setScene(QGraphicsScene())

        self.left_bar_w = 50
        self.top_bar_h = 50
        self.name_bar_h = 0
        self.DAYS = [[] for _ in range(5)]
        self.col_count = 0
        self.wide_col_widths = [0] * 5

    def load(self):
        self.scene().clear()
        self.DAYS = [[] for _ in range(5)]
        self.col_count = 0
        for teacher in self.db.all_teachers():

            days = [[] for _ in range(5)]
            for lesson in teacher.lessons:
                if not lesson.block:
                    continue
                days[lesson.block.day].append(lesson)
            for duty in teacher.duties:
                days[duty.block.day].append(duty)

            for day, events in enumerate(days):
                if not len(events):
                    continue
                self.col_count += 1
                self.wide_col_widths[day] += 1
                self.DAYS[day].append((teacher, events))
        self.draw_frame()
        self.draw_rects()

    def draw_frame(self):
        H = self.geometry().height()
        W = self.geometry().width()
        self.col_width = (W-self.left_bar_w) / self.col_count
        wide_pen = QPen()
        wide_pen.setWidth(5)
        self.scene().addLine(self.left_bar_w, 0, self.left_bar_w, H, wide_pen)
        self.scene().addLine(self.left_bar_w, self.top_bar_h, W, self.top_bar_h, wide_pen)
        self.scene().addLine(self.left_bar_w, 0, W, 0, wide_pen)
        self.scene().addLine(0, H, W, H, wide_pen)
        left_margin = self.left_bar_w
        teacher_font = QFont()
        teacher_font.setPixelSize(int(self.col_width//2))
        day_font = QFont()
        day_font.setPixelSize(self.top_bar_h - 15)
        for teachers, day_name in zip(self.DAYS, DAY_NAMES):
            day_w = len(teachers) * self.col_width
            self.scene().addLine(left_margin+day_w, 0, left_margin+day_w, H, wide_pen)
            text = self.scene().addSimpleText(day_name, day_font)
            text_x = left_margin + (day_w - text.boundingRect().width())/2
            text_y = (self.top_bar_h - text.boundingRect().height())/2
            text.setPos(text_x, text_y)
            for teacher, events in teachers:
                name = self.scene().addSimpleText(teacher.name, teacher_font)
                w = name.boundingRect().width()
                if w > self.name_bar_h:
                    self.name_bar_h = w
                h = name.boundingRect().height()
                name_x = left_margin+(self.col_width + h)/2
                name.setPos(name_x, self.top_bar_h+10)
                name.setRotation(90)
                left_margin += self.col_width
                self.scene().addLine(left_margin, self.top_bar_h, left_margin, H)
        self.name_bar_h += 20
        self.scene().addLine(0, self.top_bar_h+self.name_bar_h, 0, H, wide_pen)
        y = self.name_bar_h + self.top_bar_h
        self.hour_h = (H - self.top_bar_h - self.name_bar_h)/8
        self.small_y = self.hour_h / 12
        for hour in range(8):
            self.scene().addLine(0, y, W, y, wide_pen)
            text = self.scene().addSimpleText(f'{hour+8}-{hour+9}')
            text_x = (self.left_bar_w - text.boundingRect().width())/2
            text_y = y + (self.hour_h - text.boundingRect().height())/2
            text.setPos(text_x, text_y)
            for i in range(12):
                self.scene().addLine(self.left_bar_w, y+i*self.small_y, W, y+i*self.small_y)
            y += self.hour_h

    def draw_rects(self):
        x = self.left_bar_w
        y = self.top_bar_h + self.name_bar_h
        font = QFont()
        font.setBold(True)
        for day in self.DAYS:
            for teacher, events in day:
                for event in events:
                    block = event.block
                    top = y + block.start*self.small_y
                    h = block.length*self.small_y
                    brush = QBrush(QColor('yellow' if event.type=='lesson' else 'green'))
                    rect = self.scene().addRect(x, top, self.col_width, h, QPen(), brush)
                    rect.setZValue(-1)
                    if event.type=='lesson':
                        continue
                    text = self.scene().addSimpleText(event.classroom.name)
                    text.setBrush(QBrush(QColor("white")))  # text fill
                    text.setFont(font)
                    # white_pen = QPen(QColor('white'))
                    # white_pen.setWidth(2)
                    # text.setPen(white_pen)      # text outline

                    if text.boundingRect().width() > self.col_width:
                        text_x =  x + (self.col_width + text.boundingRect().height())/2
                        text_y = top + (h - text.boundingRect().width())/2
                        text.setRotation(90)
                    else:
                        text_x = x + (self.col_width-text.boundingRect().width())/2
                        text_y = top + (h-text.boundingRect().height())/2
                    text.setPos(text_x, text_y)
                x += self.col_width
