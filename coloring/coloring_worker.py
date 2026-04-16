from numpy import average
from .functions import mutate_batch
from PyQt5.QtCore import QThread, pyqtSignal
from db_config import settings
from networkx import Graph
from itertools import combinations
from data import Data, Class, LessonBlockDB, Subject, Lesson, Subclass, Classroom
from time import perf_counter
from .queue_listener import QueueListener
from .functions import random_coloring, mutate_batch
from .scorer import scorer_factory, rank, default_weights
import multiprocessing as mp
import math


class ColoringThread(QThread):
    update_bar = pyqtSignal(str)
    # next_generation = pyqtSignal(int, int)
    update_bar_total = pyqtSignal(int)
    increment_bar = pyqtSignal(int)
    finished = pyqtSignal(dict, list, list)
    

    def __init__(self, db: Data):
        super().__init__()
        self.db = db
        self.session = self.db.get_scoped_session()



    def run(self): 
        # create graphs
        self.bl_g, for_bl = self.generate_block_graph()
        self.les_g, _, self.feas = self.generate_lesson_graph(for_bl)
        self.scorer = scorer_factory(self.db, self.session, self.bl_g, self.les_g)

        self.pop_start_time = perf_counter()
        
        # genetic loop
        pop_size = settings.pop_size
        self.population = []
        self.update_bar.emit('Generowanie początkowej populacji')
        self.update_bar_total.emit(pop_size)

        cores_count = mp.cpu_count()
        chunk_size = math.ceil(pop_size/cores_count)
        queue = mp.Queue()
        self.processes = []
        for _ in range(cores_count):
            p = mp.Process(
                target=random_coloring,
                args = ((self.les_g, self.bl_g, self.feas, min(pop_size,chunk_size)), queue, self.scorer)
            )
            self.processes.append(p)
            p.start()
            pop_size -= chunk_size
        self.listener = QueueListener(queue, cores_count)
        self.listener.signals.progress.connect(self.add_to_population)
        self.listener.signals.finished.connect(self.finished_pop)
        self.listener.start()
    

    def add_to_population(self, data):
        self.population.extend(data)
        self.increment_bar.emit(len(data))

    # def add_children(self, data):
    #     for child in data:
    #         self.population.append()
        

    def finished_pop(self):
        for p in self.processes:
            p.join()
        duration = perf_counter() - self.pop_start_time
        avg = duration/settings.pop_size
        print(f'Wygenerowano populację w {duration}s ({avg} na osobnika)')
        pop_size = settings.pop_size
        generations = settings.generations
        self.cutoff = int(settings.cutoff*pop_size)
        num_of_children = int(pop_size/self.cutoff)
        rank(self.population, default_weights)
        # self.population.sort(key= lambda x: rank(x, default_weights))
        self.best_scores = [self.population[0][-1]]
        self.cutoffs = [self.population[self.cutoff][-1]]
        self.goat = (self.population[0])

        self.update_bar.emit(f'Pokolenie {0}, ({self.population[0][-1]})')
        self.update_bar_total.emit(generations)

        self.times = []
        self.completed_generations = 0
        self.do_next_generation()
    


    def do_next_generation(self):
        self.gen_start = perf_counter()
        self.new_pop = []
        survivors = self.population[:self.cutoff]
        self.population = []

        cores_count = mp.cpu_count()
        chunk_size = math.ceil(self.cutoff/cores_count)
        self.processes = []
        queue = mp.Queue()
        for _ in range(cores_count):
            if chunk_size < len(survivors):
                chunk = survivors[:chunk_size]
                survivors = survivors[chunk_size:]
            else:
                chunk = survivors
            p = mp.Process(
                target=mutate_batch,
                args= ((self.les_g, self.bl_g, self.feas, chunk), queue, self.scorer)
            )
            self.processes.append(p)
            p.start()
        self.queue_listener = QueueListener(queue, cores_count)
        self.queue_listener.signals.progress.connect(self.population.extend)
        self.queue_listener.signals.finished.connect(self.finished_generation)
        self.queue_listener.start()

    def finished_generation(self):
        self.completed_generations += 1
        for process in self.processes:
            process.join()
        rank(self.population, default_weights)
        # self.population.sort(key= lambda x: rank(x, default_weights))
        # self.population.sort(key=lambda x: x[-1])
        best_score = self.population[0][-1][0]
        if best_score < self.goat[-1][0]:
            self.goat = self.population[0]
        self.best_scores.append(best_score)
        self.cutoffs.append(self.population[self.cutoff][-1][0])
        end = perf_counter()
        duration = end - self.gen_start
        self.times.append(duration)
        print(f'Generation {self.completed_generations}: {duration}s')
        self.update_bar.emit(f'Pokolenie {self.completed_generations} ({self.population[0][-1]})')
        self.increment_bar.emit(1)
        if self.completed_generations < settings.generations:
            self.do_next_generation()
        else:
            self.finish_everything()

    def finish_everything(self):
        coloring = self.goat[0]
        print(f'total time: {sum(self.times)}s')
        print(f'avg: {average(self.times)}s')
        self.session.close()
        self.best_scores = []
        self.cutoffs = []
        self.finished.emit(coloring[0], self.best_scores, self.cutoffs)





    def generate_lesson_graph(self, forbidden_blocks):
        graph = Graph()
        labels = {}

        # session = db.get_scoped_session()
        self.update_bar.emit('Generowanie grafu przedmiotów')
        subclass_count = self.session.query(Subclass).count()
        self.update_bar_total.emit(subclass_count)
        # i = 0

        tick_1 = perf_counter()
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
        tick_2 = perf_counter()
        print(f'Naniesiono przedmioty w {tick_2-tick_1}s')
        self.update_bar.emit('Generowanie grafu lekcji')
        lesson_count = self.session.query(Lesson).count()
        self.update_bar_total.emit(lesson_count)
        classrooms = self.session.query(Classroom).all()
        blocks = self.session.query(LessonBlockDB).all()
        for subject in self.session.query(Subject).all():
            feasible_classrooms = [
                cr.id 
                for cr in classrooms 
                if cr.capacity >= len(subject.students)
            ] if not subject.classroom_id else [subject.classroom_id]
            unpinned_lessons = []
            for lesson in subject.lessons:
                feasible_blocks[lesson.id] = []
            for block in blocks:
                # teacher not available
                if not self.db.is_teacher_available(subject.teacher, block):
                    continue

                # block is in the wrong class
                possible_sub_classes = [block.parent()]
                if isinstance(possible_sub_classes[0], Class):
                    possible_sub_classes.extend(block.parent().subclasses)
                if subject.parent() not in possible_sub_classes:
                    continue

                # teacher is busy
                if len(self.db.get_lesson_collisions_for_teacher_at_block(subject.teacher, block, self.session)):
                    continue

                # students are busy
                if len(self.db.get_collisions_for_students_at_block(subject.students, block, self.session)):
                    continue

                # lesson happening this day
                if block.day in [les.block.day for les in subject.lessons if les.block]:
                    continue
                
                many_blocks = [(block.id, cl_id) for cl_id in feasible_classrooms]
                # differing for lessons
                for lesson in subject.lessons:
                    if lesson.block_locked:
                        continue
                    # wrong length
                    if block.length*5 != lesson.length:
                        continue
                    # else block is feasible
                    for bl, cl in many_blocks:
                        if bl not in forbidden_blocks[cl]:
                            feasible_blocks[lesson.id].append((bl, cl))
            for lesson in subject.lessons:
                # if there is no possible blocks dont put it in graph
                if len(feasible_blocks[lesson.id]) == 0:
                    continue
                # add lesson to graph with the same neigbours as subject
                graph.add_node(lesson.id, weight=len(subject.students), subject=subject.id)
                unpinned_lessons.append(lesson.id)
                labels[lesson] = f'{subject.get_name()} ({lesson.length})'
                for neighbour in graph[subject]:
                    graph.add_edge(lesson.id, neighbour)
            self.increment_bar.emit(len(subject.lessons))
            # lessons of the same subject are obviously connected
        
            for l1, l2 in combinations(unpinned_lessons, 2):
                # if l1.block_locked or l2.block_locked:
                    # continue
                graph.add_edge(l1, l2)
            # subject is no longer needed
            if subject in graph.nodes:
                graph.remove_node(subject)
        tick_3 = perf_counter()
        print(f'Naniesiono lekcje w {tick_3-tick_2}s')
        # to_remove = []
        # for lesson in graph.nodes:
        #     if len(feasible_blocks[lesson]) == 0 \
        #     or lesson.block_locked:
        #         to_remove.append(lesson)
        # graph.remove_nodes_from(to_remove)
        
        return graph, labels, feasible_blocks

    def generate_block_graph(self):
        # session = db.get_scoped_session()
        graph = Graph()
        # blocks taking place in different days can't possibly colide
        for day in range(5):
            self.update_bar.emit(f'Generowanie grafu bloków (dzień {day+1})')
            blocks = self.session.query(LessonBlockDB).filter_by(day=day).all()
            for block in blocks:
                graph.add_node(block.id, day=block.day)
            x = len(blocks)
            self.update_bar_total.emit(x * (x-1) // 2)

            for b1, b2 in combinations(blocks, 2):
                self.increment_bar.emit(1)
                # if one block starts after the second has ended...
                if b1.start+b1.length < b2.start \
                or b2.start+b2.length < b1.start:
                    # ...the blocks don't collide
                    continue
                graph.add_edge(b1.id, b2.id)
        classrooms = self.session.query(Classroom).all()
        forbidden_blocks = {cl.id: set() for cl in classrooms}
        for lesson in self.session.query(Lesson).filter(Lesson.classroom_id!= None).all():
            block = lesson.block_id
            forbidden_blocks[lesson.classroom_id].add(block)
            forbidden_blocks[lesson.classroom_id].update(graph[block])
        return graph, forbidden_blocks



