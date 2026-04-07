from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QToolTip, QGraphicsTextItem, QGraphicsRectItem
from PyQt5.QtGui import QPen, QColor, QBrush, QTransform
from PyQt5.QtCore import QPoint, Qt, QRectF, QEvent
from networkx import Graph
import gcol
from .lesson_block import LessonBlock
from .custom_block import CustomBlock
from .block import BasicBlock
from .stats import Statistic, StudentDensityStat
from functions import snap_position, display_hour, contrast_ratio
from data import Data, Class, Subclass, LessonBlockDB
from db_config import settings
from matplotlib.pyplot import get_cmap
from matplotlib.colors import to_hex
from numpy import linspace

class MyView(QGraphicsView):

    def __init__(self,parent, size=None):
        super().__init__(parent)
        if size:
            self.resize(*size)
        self.setScene(QGraphicsScene())
        self.db: Data = parent.db
        self.classes = []
        self.blocks = {}
        self.mode = 'normal'
        self.widths = [0]
        self.block_start = -1
        self.new_block = False
        self.setMouseTracking(True)
        self.ready = False
        self.stat = Statistic(self.db)

        self.top_bar_h = 75
        self.left_bar_w = 50
        self.update_size_params()
        def filter(l):
            return True
        self.filter_func = filter

        # self.db.update_block.connect(self.redraw_block)

    def uncheck_all_modes(self):
        self.parent().uncheck_all_modes()
        self.set_mode('normal')
    

    def set_classes(self, classes):
        self.widths = [0]
        self.classes = classes
        if not len(classes):
            self.class_names = []
            self.update_column_sizes()
            return
        last_cls = classes[0].get_class()
        for cls in classes:
            if cls.get_class() != last_cls:
                self.widths.append(0)
                last_cls = cls.get_class()
            self.widths[-1]+=1
        self.class_names = [c.full_name() for c in classes]
        self.update_column_sizes()
            

    def update_column_sizes(self):
        self.l = len(self.classes) + isinstance(self.stat, StudentDensityStat) # extra column if any stats active
        self.block_w = self.day_w/self.l if self.l>0 else self.day_w
        self.boundries = [0]
        for width in self.widths:
            self.boundries.append(self.block_w*width+self.boundries[-1])

    def update_size_params(self):
        self.scene_width = self.geometry().width()-10
        self.scene_height = self.geometry().height()-10
        self.hour_h = (self.scene_height-self.top_bar_h)/8
        self.five_min_h = self.hour_h/12
        self.day_w = (self.scene_width-self.left_bar_w)/5
        self.update_column_sizes()

    def set_ready(self):
        self.ready = True
        self.draw()


    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        if not self.ready:
            return
        self.update_size_params()
        self.draw()

    def set_mode(self, mode: str):
        self.mode = mode
        for block in self.scene().items():
            if isinstance(block, BasicBlock):
                block.set_movable(mode=='move', self.five_min_h, self.top_bar_h)
                block.set_selectable(mode not in ('new', 'new_custom'))
        if mode in ['new', 'new_custom']:
            self.viewport().setCursor(Qt.CrossCursor)
        else:
            self.viewport().setCursor(Qt.ArrowCursor)

    def set_stat(self, stat: Statistic):
        self.stat = stat
        self.stat.load_stat()
        self.update_size_params()
        self.draw()

    # def viewportEvent(self, event):
    #     if event.type() == QEvent.ToolTip:
    #         # Find the item under the cursor
    #         pos = event.pos()
    #         items = [item for item in self.items(pos) if isinstance(item, QGraphicsRectItem)]

    #         if len(items):
    #             item = items[0]
    #             text = item.toolTip()
    #             if text:
    #                 # Show tooltip immediately
    #                 QToolTip.showText(event.globalPos(), text)
    #                 return True  # stop default delayed tooltip

    #         # If no item or no tooltip, hide
    #         QToolTip.hideText()
    #         return True

    #     return super().viewportEvent(event) 
    
    def mousePressEvent(self, event):
        if self.mode in ('new', 'new_custom'):
            if event.button() == Qt.MouseButton.LeftButton:
                l = len(self.class_names)
                if l == 0:
                    return 
                self.block_start = self.how_many_5_min_blocks(event)
                self.new_block_top = snap_position(self.mapToScene(event.pos()).y(), self.five_min_h, self.top_bar_h)
                self.new_block_left = snap_position(self.mapToScene(event.pos()).x(), self.block_w, self.left_bar_w)
                # don't draw anything on stats column
                i = ((self.new_block_left-self.left_bar_w + self.block_w/2)//self.block_w)%self.l
                if i >= l:
                    return
                self.new_block = BasicBlock(self.new_block_left, self.new_block_top, self.block_w, self.five_min_h, self.scene(), self.db, self.classes)
                # if self.mode == 'new':
                #     self.new_block = LessonBlock(self.new_block_left, self.new_block_top, self.block_w, self.five_min_h, self.scene(), self.db, self.classes)
                # elif self.mode == 'new_custom':
                #     self.new_block = CustomBlock(self.new_block_left, self.new_block_top, self.block_w, self.five_min_h, self.scene(), self.db, self.classes)
                self.new_block.bring_forward()
                # self.new_block.setBrush(QBrush(QColor('#c0c0c0')))
                
                self.scene().addItem(self.new_block)
            elif event.button() == Qt.MouseButton.RightButton:
                self.drop_new_block()
        
        if event.button() == Qt.MouseButton.LeftButton and self.mode!='move':
            item = self.itemAt(event.pos())
            if isinstance(item, (BasicBlock, QGraphicsTextItem)):
                item.bring_back()
                item.setSelected(False)
            item = self.itemAt(event.pos())
            if isinstance(item, (BasicBlock, QGraphicsTextItem)):
                item.bring_forward()
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, (QGraphicsTextItem, LessonBlock, CustomBlock)):
            item.contextMenuEvent(event)


    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.new_block:
            # drop block if it has no length:
            if self.new_block.boundingRect().height() < self.five_min_h:
                self.new_block.delete()
                self.new_block = ''
                return
            # add new block to db
            # find day
            x = self.new_block.boundingRect().x() - self.left_bar_w + 1
            day = int(x // self.day_w)
            y = self.new_block.boundingRect().y() - self.top_bar_h + 1
            start = int(y // self.five_min_h)
            length = int(self.new_block.boundingRect().height() // self.five_min_h)
            # find (sub)class
            i = x // self.block_w
            i = int(i%self.l)

            if self.mode == 'new':
                my_class = self.classes[i]
                # find if block spans entire class
                # either is wide
                if self.new_block.boundingRect().width() -1 > self.block_w:
                    my_class = my_class.get_class()
                # ... or is the only subclass
                if len(my_class.get_class().subclasses)==1:
                    my_class = my_class.get_class()

                block = self.db.create_block(day, start, length, my_class)

            elif self.mode =='new_custom':
                n_of_classes = int(self.new_block.boundingRect().width()//self.block_w)
                classes = self.classes[i:i+n_of_classes]
                subclasses = [s.subclasses[0] if isinstance(s, Class) else s for s in classes]
                block: CustomBlock = self.db.create_custom_block(day, start, length, subclasses)

            self.scene().removeItem(self.new_block)
            self.draw_block(block)

            self.blocks[block].bring_forward()
        self.block_start = -1
        self.new_block = False


    
    def how_many_5_min_blocks(self, event):
        y = self.mapToScene(event.pos()).y() - self.top_bar_h
        mins = y//self.five_min_h
        return mins

    def drop_new_block(self):
        if self.new_block:
            self.scene().removeItem(self.new_block)
        self.new_block = False
        self.block_start = -1
        QToolTip.showText(QPoint(), '')

    def mouseMoveEvent(self, event):
        # show tooltip
        item = self.itemAt(event.pos())
        if not item or self.new_block:
            now = self.how_many_5_min_blocks(event)
            times = [now, self.block_start] if self.block_start >=0 else [now]
            times.sort()
            msg = '-'.join([display_hour(t) for t in times])
            if self.block_start>=0:
                msg += f' ({int(abs(now-self.block_start)*5)})'
            QToolTip.showText(event.globalPos(), msg)
        else:
            QToolTip.showText(event.globalPos(), '')


        super().mouseMoveEvent(event)
        if self.mode in ('new', 'new_custom'):
            # stop if moved out of bounds:
            if (event.y() < self.top_bar_h or event.x() < self.left_bar_w):
                self.drop_new_block()
                return
            
            # update block
            if self.new_block:
                self.new_block.bring_forward()
                cursor_x = snap_position(self.mapToScene(event.pos()).x(), self.block_w, self.left_bar_w)
                x, width = self.calculate_x_w(cursor_x)
                
                new_block_bottom = snap_position(self.mapToScene(event.pos()).y(), self.five_min_h, self.top_bar_h)
                height = abs(new_block_bottom - self.new_block_top)
                y = min(new_block_bottom, self.new_block_top)
                self.new_block.setRect(x, y, width, height)


    def calculate_x_w(self, cursor_x):
        # if in the same subclass block dont stretch
        if self.new_block_left==cursor_x:
            return self.new_block_left, self.block_w

        if self.mode == 'new':
            # get the bottom boundry
            x1 = (self.new_block_left - self.left_bar_w)%self.day_w + 2
            for boundry in self.boundries:
                if x1>=boundry:
                    bottom = boundry
            
            day_start = snap_position(self.new_block_left, self.day_w, self.left_bar_w)
            x = bottom+day_start
            top = self.boundries[self.boundries.index(bottom)+1]
            w = top-bottom

        elif self.mode == 'new_custom':
            left, right = sorted([self.new_block_left, cursor_x])
            day_start = snap_position(self.new_block_left, self.day_w, self.left_bar_w)
            day_end = day_start + self.day_w
            left = max(day_start, left)
            right = min(day_end, right+self.block_w) 
            x = left
            w = right - left
        return x,w

    def draw_frame(self):
        scene = self.scene()
        wide_pen = QPen()
        wide_pen.setWidth(3)
        line = scene.addLine(0, self.top_bar_h, self.scene_width, self.top_bar_h, wide_pen)
        line.setZValue(1_000_000)
        line = scene.addLine(0, 0, self.scene_width, 0, wide_pen)
        line.setZValue(1_000_000)
        line = scene.addLine(0, 0, 0, self.scene_height, wide_pen)
        line.setZValue(1_000_000)
        line = scene.addLine(0, self.scene_height, self.scene_width, self.scene_height, wide_pen)
        line.setZValue(1_000_000)
        line = scene.addLine(self.left_bar_w, 0, self.left_bar_w, self.scene_height, wide_pen)
        line.setZValue(1_000_000)

        for hour in range(8,16):
            pos = self.top_bar_h+(hour - 7)*self.hour_h
            text = scene.addSimpleText(f'{hour}-{hour+1}')

            # center text
            text_x = (self.left_bar_w-text.boundingRect().width())/2
            text_y = pos-(self.hour_h+text.boundingRect().height())/2
            text.setPos(text_x, text_y)

            scene.addLine(0, pos, self.left_bar_w, pos)

        # self.l = len(self.classes)
        days = 'Poniedziałek Wtorek Środa Czwartek Piątek'.split()
        for day in range(5):
            pos = self.day_w*(day+1)+self.left_bar_w
            line = scene.addLine(pos, 0, pos, self.scene_height)
            line.setZValue(1_000_000)
            line.setPen(wide_pen)
            
            text = scene.addSimpleText(days[day])
            text_x = pos - (self.day_w + text.boundingRect().width())/2
            text_y = (self.top_bar_h/2 - text.boundingRect().height()/2)\
                /(2 if not settings.draw_blocks_full_width else 1)
            text.setPos(text_x, text_y)
        self.draw_headers = self.l>0 and not settings.draw_blocks_full_width
        if self.draw_headers:
            
            scene.addLine(self.left_bar_w, self.top_bar_h/2, self.scene_width, self.top_bar_h/2)
            self.block_w = self.day_w/self.l
            for i in range(5):
                for n, class_name in enumerate(self.class_names):
                    pos = self.block_w*(n+i*self.l+1)+self.left_bar_w
                    text = scene.addSimpleText(class_name)
                    text_x = pos - (text.boundingRect().width()+self.block_w)/2
                    text_y = self.top_bar_h/2 + (self.top_bar_h/2 - text.boundingRect().height())/2
                    text.setPos(text_x, text_y)
                    scene.addLine(pos, self.top_bar_h/2, pos, self.scene_height)

    
    def draw_stats(self, only_day = None):
        for day in range(5) if not only_day else [only_day]:
            # print(day)
            # print(self.stat.rects)
            for rect in self.stat.rects[day][::-1]:
                self.scene().removeItem(rect)
            self.stat.rects[day] = []
        def add_rect():
            rect = scene.addRect(left+0.5, top, self.block_w-1, h)
            i = 255-int(last/student_count*255)
            # print(i)
            rect.setBrush(QColor(hex_colors[i]))
            rect.setPen(QPen(Qt.NoPen))
            rect.setToolTip(str(last))
            # if last:
            #     text = scene.addSimpleText(str(last))
            #     text.setPos(rect.boundingRect().center())

        student_count = self.db.student_count()
        stats = self.stat.get_stats(only_day)
        cmap = get_cmap('bwr')
        hex_colors = [to_hex(cmap(i)) for i in linspace(0, 1, 256)]
        if stats is None:
            return
        compiled = [[] for _ in range(5)]
        scene = self.scene()
        for n, day in enumerate(stats):
            if only_day:
                n = only_day
            left = self.left_bar_w + (n+1)*self.day_w - self.block_w
            last = day[0]
            length = 1
            top = self.top_bar_h
            for five_min_cell in day[1:]:
                if five_min_cell == last:
                    length +=1
                else:
                    h = length*self.five_min_h
                    add_rect()
                    last = five_min_cell
                    length = 1
                    top+=h
            h = length*self.five_min_h
            add_rect()





    def place_block(self, block):
        if settings.draw_blocks_full_width:
            n = 0
            width_multiplier = len(self.classes)
        elif isinstance(block, LessonBlockDB):
            # find subclass
            if block.subclass in self.classes:
                n = self.classes.index(block.subclass)
            # find first subclass
            elif block.my_class:
                n = -1
                for subclass in block.my_class.subclasses:
                    if subclass in self.classes:
                        n = self.classes.index(subclass)
                        break
                # if none are found don't draw the block
                if n < 0:
                    return
            else:
                return

            # stretch the width if needed
            if block.my_class:
                mask = [1 if cl.get_class().id == block.class_id else 0 for cl in self.classes]
                width_multiplier = sum(mask)
            else:
                width_multiplier = 1
            

        else:
            ns = []
            width_multiplier = 0
            for subclass in block.subclasses:
                if subclass in self.classes:
                    ns.append(self.classes.index(subclass))
                    width_multiplier += 1
            if len(ns) == 0:
                return
            
            n = min(ns)

        x = self.left_bar_w + self.day_w*block.day + n*self.block_w
        y = self.five_min_h*block.start+ self.top_bar_h
        width = self.block_w*width_multiplier
        height = self.five_min_h * block.length

        if isinstance(block, LessonBlockDB):
            block = LessonBlock(x, y, width, height, self.scene(), self.db, self.classes)
            block.signal.block_moved.connect(block.move_and_check_collisions)
        else:
            # if not settings.draw_custom_blocks:
            #     return
            block = CustomBlock(x, y, width, height, self.scene(), self.db, self.classes)
        block.signal.block_moved.connect(self.move_block)
        block.signal.block_updated.connect(self.redraw_block)
        return block
                

    def draw_blocks(self, blocks):
        for z, block in enumerate(blocks): 
            self.draw_block(block, z)
        for block in blocks:
            self.update_collisions_around(block)

    def draw_block(self, block, z=0):
        new_block = self.place_block(block)
        self.blocks[block] = new_block
        if not new_block:
            return
        new_block.block = block
        new_block.start = block.start
        if isinstance(new_block, LessonBlock): 
            new_block.setZValue(z+5000)
        else:
            new_block.setZValue(z+2000)
        new_block.set_filter(self.filter_func)
        new_block.draw_contents()
        new_block.set_movable(self.mode=='move', self.five_min_h, self.top_bar_h)
        new_block.set_selectable(True)
        self.scene().addItem(new_block)

    def narrow_overlapping_blocks(self):
        # for each day
        for day in range(5):

            # get blocks in every day
            x = self.left_bar_w + self.day_w*day + 10
            y = self.top_bar_h
            width = self.day_w -30
            height = self.scene_height - self.top_bar_h
            day_rect = QRectF(x, y, width, height)
            blocks = [bl for bl in self.scene().items(day_rect) if isinstance(bl, LessonBlock)]
            if not len(blocks):
                continue

            # generate graph
            graph = Graph()
            for block in blocks:
                graph.add_node(block.block.id)
            for block in blocks:
                for col_block in block.overlapping_lesson_blocks():
                    if graph.has_edge(block.block.id, col_block.block.id):
                        continue
                    graph.add_edge(block.block.id, col_block.block.id)

            # color graph
            colored = gcol.node_coloring(graph)
            num_of_colors = max(list(colored.values()))+1

            for block in blocks:
                if not len(block.overlapping_lesson_blocks()):
                    continue
                color = colored[block.block.id]
                
                dx = (color+day)*self.day_w+self.left_bar_w
                transform = QTransform()
                transform.scale(1/num_of_colors, 1)
                transform.translate(dx, 0)
                block.setTransform(transform, combine=True)
                block.write()



    def update_filters(self, classes, filter):
        self.set_classes(classes)
        self.filter_func = filter
        self.draw()

    def redraw_block(self, block: LessonBlockDB | CustomBlock):
        if not block:
            return
        # to_update = self.blocks[block]
        self.update_collisions_around(block)
        # to_update.draw_contents()
        # print(len(self.blocks))

    def move_block(self, block, start):
        # remove lessons from stats
        if hasattr(block, 'lessons'):
            for lesson in block.lessons:
                self.stat.remove_lesson(lesson)
        # move block in db
        no_longer_overlapping = self.db.update_block_start(block, start)
        # update collisions
        for bl in no_longer_overlapping:
            self.blocks[bl].remove_collisions_with(block)
            self.blocks[block].remove_collisions_with(bl)
        self.update_collisions_around(block)
        # add lessons back to stats
        if hasattr(block, 'lessons'):
            for lesson in block.lessons:
                self.stat.add_lesson(lesson)
        # print(self.stat.get_stats(block.day))
        self.draw_stats(block.day)

    def update_collisions_around(self, block):
        if not self.blocks[block]:
            return
        collisions = self.db.block_collisions(block)
        for bl, cols in collisions.items():
            my_tooltip = '\n'.join([c[0] for c in cols])
            self.blocks[block].add_collision(bl, my_tooltip)
            self.blocks[block].draw_contents()
            if bl and self.blocks[bl]:
                their_tooltip = '\n'.join([c[1] for c in cols])
                self.blocks[bl].add_collision(block, their_tooltip)


    def draw(self):
        scene = self.scene()
        scene.clear()
        scene.setSceneRect(0,0, self.scene_width, self.scene_height)
        self.draw_frame()
        self.draw_stats()
        # self.blocks: dict[LessonBlockDB, LessonBlock] = {}
        if len(self.classes):
            self.draw_blocks(self.db.all_blocks())

            # self.draw_blocks(self.db.all_lesson_blocks())
            # self.draw_blocks(self.db.all_custom_blocks())

    def load_data(self, db):
        self.db = db

