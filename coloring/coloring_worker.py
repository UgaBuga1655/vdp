from numpy import add, average

from .functions import crazy, mutate
from PyQt5.QtCore import QThread, pyqtSignal, QThreadPool, pyqtSlot
from db_config import settings
from networkx import Graph
import math
from itertools import combinations
from data import Data, Class, LessonBlockDB, Subject, Lesson, Subclass
from time import perf_counter
from .pop_worker import Birther, random_coloring, QueueListener
import multiprocessing as mp

class ColoringThread(QThread):
    update_bar = pyqtSignal(str)
    next_generation = pyqtSignal(int, int)
    update_bar_total = pyqtSignal(int)
    increment_bar = pyqtSignal(int)
    finished = pyqtSignal(dict, list, list)
    

    def __init__(self, db: Data):
        super().__init__()
        self.db = db
        # self.feas = feas
        self.session = self.db.get_scoped_session()

    

    def add_to_population(self, data):
        for specimen in data:
            self.population.append(specimen)
        self.increment_bar.emit(len(data))
        
            # self.foo() 

    def finished_pop(self):
        for p in self.processes:
            p.join()
        duration = perf_counter() - self.pop_start_time
        avg = duration/settings.pop_size
        print(f'Wygenerowano populację w {duration}s ({avg} na osobnika)')

    def run(self): 
        # create graphs
        self.les_g, _, self.feas = self.generate_lesson_graph()
        self.bl_g = self.generate_block_graph()
        # les_g, bl_g, feas = self.les_g, self.bl_g, self.feas
        
        self.pop_start_time = perf_counter()
        
        # genetic loop
        pop_size = settings.pop_size
        self.population = []
        self.update_bar.emit('Generowanie początkowej populacji')
        self.update_bar_total.emit(pop_size)
        self.pop_times = []
        cores_count = mp.cpu_count()
        chunk_size = math.ceil(pop_size/cores_count)
        queue = mp.Queue()
        self.processes = []
        # pool = QThreadPool.globalInstance()
        for _ in range(cores_count):
            p = mp.Process(
                target=random_coloring,
                args = ((self.les_g, self.bl_g, self.feas, min(pop_size,chunk_size)), queue)
            )
            self.processes.append(p)
            p.start()
        #     birther = Birther(min(chunk_size, pop_size), self.les_g, self.bl_g, self.feas)
        #     birther.signals.new_chromosome.connect(self.add_to_population)
            pop_size -= chunk_size
            # print(pop_size)
        self.listener = QueueListener(queue, settings.pop_size, cores_count)
        self.listener.signals.new_chromosomes.connect(self.add_to_population)
        self.listener.signals.finished.connect(self.finished_pop)
        self.listener.start()

        #     pool.start(birther)
            # print(f'Rozwiązanie {i+1}: {duration}ns')

    def foo(self):
        pop_size = settings.pop_size
        generations = settings.generations
        cutoff = int(settings.cutoff*pop_size)
        num_of_children = int(pop_size/cutoff)
    
        # for _ in range(1,pop_size):
            # population.append(mutate(les_g, bl_g, feas, coloring))
        self.population.sort(key= lambda x: x[1])
        best_scores = [self.population[0][1]]
        cutoffs = [self.population[cutoff][1]]
        goat = (self.population[0])
        self.update_bar.emit(f'Pokolenie {0}, ({self.population[0][1]})')
        self.update_bar_total.emit(generations)
        # self.increment_bar.emit()
        times = []
        for i in range(generations):
            start = perf_counter()
            self.new_pop = []
            for col in self.population[:cutoff]:
                # new_pop.append(col)
                for _ in range(num_of_children):
                    self.new_pop.append(mutate(self.les_g, self.bl_g, self.feas, col[0]))
            self.new_pop.sort(key=lambda x: x[1])
            self.population = self.new_pop
            bs = self.population[0][1]
            if bs < goat[1]:
                goat = self.population[0]
            best_scores.append(bs)
            cutoffs.append(self.population[cutoff][1])
            end = perf_counter()
            duration = end - start
            times.append(duration)
            print(f'Generation {i+1}: {duration}s')
            self.update_bar.emit(f'Pokolenie {i+1}, ({self.population[0][1]})')
            self.increment_bar.emit()
            # self.next_generation.emit(i+1, population[0][1])

    
        coloring = goat[0]
        print(f'total time: {sum(times)}s')
        print(f'avg: {average(times)}s')
        self.finished.emit(coloring, best_scores, cutoffs)





    def generate_lesson_graph(self):
        graph = Graph()
        labels = {}

        # session = db.get_scoped_session()
        self.update_bar.emit('Generowanie grafu przedmiotów')
        subclass_count = self.session.query(Subclass).count()
        self.update_bar_total.emit(subclass_count)
        # i = 0

        # create subject graph
        for class_ in self.db.all_classes(self.session):
            # find all subjects in class and subclasses
            total_subjects = []
            total_subjects.extend(class_.subjects)
            for subclass in class_.subclasses:
                self.increment_bar.emit(1)
                total_subjects.extend(subclass.subjects)

            graph.add_nodes_from(total_subjects)
            for pair in combinations(total_subjects, 2):
                for student in pair[0].students:
                    if student in pair[1].students:
                        graph.add_edge(*pair)
                        break
        for pair in combinations(graph.nodes, 2):
            if pair[0].teacher == pair[1].teacher and pair[0].teacher is not None:
                graph.add_edge(*pair)
                continue
        
        feasible_blocks = {}
        self.update_bar.emit('Generowanie grafu przedmiotów')
        lesson_count = self.session.query(Lesson).count()
        self.update_bar_total.emit(lesson_count)
        for subject in self.session.query(Subject).all():
            for lesson in subject.lessons:
                feasible_blocks[lesson] = []
                for block in self.session.query(LessonBlockDB).all():
                    # wrong length
                    if block.length*5 != lesson.length:
                        continue
                    # teacher doesn't work at that time
                    if not self.db.is_teacher_available(lesson.subject.teacher, block):
                        continue
                    # block is in the wrong class
                    possible_sub_classes = [block.parent()]
                    if isinstance(possible_sub_classes[0], Class):
                        possible_sub_classes.extend(block.parent().subclasses)
                    if lesson.subject.parent() not in possible_sub_classes:
                        continue
                    #
                    if len(self.db.get_collisions_for_students_at_block(subject.students, block, self.session)):
                        continue
                    if len(self.db.get_lesson_collisions_for_teacher_at_block(subject.teacher, block, self.session)):
                        continue
                    if block.day in [les.block.day for les in subject.lessons if les.block]:
                        continue
                    # else block is feasible
                    feasible_blocks[lesson].append(block)
                # if there is no possible blocks dont put it in graph
                if len(feasible_blocks[lesson]) == 0:
                    continue
                if lesson.block_locked:
                    continue
                # add lesson to graph with the same neigbours as subject
                graph.add_node(lesson, weight=len(subject.students))
                labels[lesson] = f'{subject.get_name()} ({lesson.length})'
                for neighbour in graph[subject]:
                    graph.add_edge(lesson, neighbour)
                self.increment_bar.emit(1)
            # lessons of the same subject are obviously connected
            for pair in combinations(subject.lessons, 2):
                graph.add_edge(*pair)
            # subject is no longer needed
            if subject in graph.nodes:
                graph.remove_node(subject)
        to_remove = []
        for lesson in graph.nodes:
            if len(feasible_blocks[lesson]) == 0 \
            or lesson.block_locked:
                to_remove.append(lesson)
        graph.remove_nodes_from(to_remove)
                
        return graph, labels, feasible_blocks

    def generate_block_graph(self):
        # session = db.get_scoped_session()
        graph = Graph()
        # blocks taking place in different days can't possibly colide
        for day in range(5):
            self.update_bar.emit(f'Generowanie grafu bloków (dzień {day+1})')
            blocks = self.session.query(LessonBlockDB).filter_by(day=day).all()
            graph.add_nodes_from(blocks)
            x = len(blocks)
            self.update_bar_total.emit(x * (x-1) // 2)

            for b1, b2 in combinations(blocks, 2):
                self.increment_bar.emit(1)
                # if one block starts after the second has ended...
                if b1.start+b1.length < b2.start \
                or b2.start+b2.length < b1.start:
                    # ...the blocks don't collide
                    continue
                graph.add_edge(b1, b2)
        # print(len(graph))
        return graph



