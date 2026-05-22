from numpy import average
from .functions import mutate_batch
from PyQt5.QtCore import QThread, pyqtSignal
from networkx import Graph
from itertools import combinations
from data import Data, Class, LessonBlockDB, Subject, Lesson, Subclass, Classroom, Metadata, Results
from time import perf_counter
from .queue_listener import QueueListener
from .functions import random_coloring, mutate_batch, legalize_batch
from .scorer import scorer_factory, rank
import multiprocess as mp
import math


class ColoringThread(QThread):
    update_bar = pyqtSignal(str)
    # next_generation = pyqtSignal(int, int)
    update_bar_total = pyqtSignal(int)
    increment_bar = pyqtSignal(int)
    finished = pyqtSignal(dict, list)
    

    def __init__(self, db: Data):
        super().__init__()
        self.db = db
        self.session = self.db.get_scoped_session()
        self.processes = []



    def run(self): 
        self.settings = self.session.query(Metadata).first()
        self.bl_g, self.for_bl = None, None
        self.les_g, self.feas = None, None
        self.recent_pop = []
        self.all_params, self.best_params = None, None

        # pick up when we've finished
        if self.settings.preserve_population:
            last_result = self.session.query(Results).first()
            self.bl_g = last_result.bl_g
            self.for_bl = last_result.for_bl
            self.les_g = last_result.les_g
            self.feas = last_result.feas
            self.recent_pop = last_result.population
            self.all_params = [p[:-1] for p in last_result.all_params]
            self.best_params = [p[:-1] for p in last_result.best_params]

        # create from scratch if not loaded
        needs_legalisation = False
        if self.bl_g is None or self.for_bl is None:
            self.bl_g, self.for_bl = self.generate_block_graph()
            needs_legalisation = True
        if self.les_g is None or self.feas is None:
            self.les_g, _, self.feas = self.generate_lesson_graph(self.for_bl)
            needs_legalisation = True
        print(f'needs legalisation: {needs_legalisation}')
        self.scorer = scorer_factory(self.db, self.session, self.bl_g, self.les_g)
        self.population = []

        if not len(self.recent_pop):
            self.generate_random_pop()
        elif needs_legalisation:
            self.legalize()
        else:
            print('not legalising, use last results')
            self.population = self.recent_pop.copy()
            self.generate_random_pop()
            
    def legalize(self):
        self.recent_pop = self.recent_pop.copy()
        pop_size = len(self.recent_pop)


        if pop_size:
            self.update_bar.emit(f'Poprawianie początkowej populacji ({pop_size} rozwiązań)')
            self.update_bar_total.emit(pop_size)
        cores_count = mp.cpu_count()
        chunk_size = math.ceil(pop_size/cores_count)
        queue = mp.Queue()
        self.processes = []
        for _ in range(cores_count):
            if chunk_size < len(self.recent_pop):
                chunk = self.recent_pop[:chunk_size]
                self.recent_pop = self.recent_pop[chunk_size:]
            else:
                chunk = self.recent_pop
            p = mp.Process(
                target=legalize_batch,
                args = ((self.les_g, self.bl_g, self.feas, chunk), queue, self.scorer)
            )
            self.processes.append(p)
            p.start()
            pop_size -= chunk_size
        self.listener = QueueListener(queue, cores_count)
        self.listener.signals.progress.connect(self.add_to_population)
        self.listener.signals.finished.connect(self.generate_random_pop)
        self.listener.start()



    def generate_random_pop(self):
        print(len(self.population))
        for p in self.processes:
            p.join()
        self.pop_start_time = perf_counter()

        target_pop_size = int(self.settings.pop_size)
        remaining_pop_size = target_pop_size - len(self.population)
        print(f'remaining pop size: {remaining_pop_size}')
        if remaining_pop_size <= 0:
            self.population = self.population[:target_pop_size]
            print(len(self.population))
            self.finished_pop()
        else:
            self.update_bar.emit(f'Generowanie nowych rozwiązań ({remaining_pop_size})')
            self.update_bar_total.emit(remaining_pop_size)

            cores_count = mp.cpu_count()
            chunk_size = math.ceil(remaining_pop_size/cores_count)
            queue = mp.Queue()
            self.processes = []
            for _ in range(cores_count):
                p = mp.Process(
                    target=random_coloring,
                    args = ((self.les_g, self.bl_g, self.feas, min(remaining_pop_size,chunk_size)), queue, self.scorer)
                )
                self.processes.append(p)
                p.start()
                remaining_pop_size -= chunk_size
            self.listener = QueueListener(queue, cores_count)
            self.listener.signals.progress.connect(self.add_to_population)
            self.listener.signals.finished.connect(self.finished_pop)
            self.listener.start()
        

    def add_to_population(self, data):
        self.population.extend(data)
        self.increment_bar.emit(len(data))

    def add_to_population_without_incrementing_bar(self, data):
        # print(f'adding {len(data)} to data')
        self.population.extend(data)

    def finished_pop(self):
        for p in self.processes:
            p.join()
        duration = perf_counter() - self.pop_start_time
        avg = duration/self.settings.pop_size
        print(f'Wygenerowano populację w {duration}s ({avg} na osobnika)')
        self.pop_size = self.settings.pop_size
        self.generations = self.settings.generations
        self.cutoff = int(self.settings.cutoff*self.pop_size)
        if not self.all_params:
            self.all_params = [[] for _ in self.settings.scoring_weights]
        # print(len(self.population))
        rank(self.population, self.settings.scoring_weights, self.all_params)

        self.goats = [self.population[0]]
        if not self.best_params:
            self.best_params = [[p] for p in self.population[0][-1]]
        else:
            for old_params, new_param in zip(self.best_params, self.population[0][-1]):
                old_params.append(new_param)
        self.starting_gen = len(self.best_params[0])-1

        self.update_bar.emit(f'Pokolenie {self.starting_gen} {self.population[0][-1]}')
        self.update_bar_total.emit(self.generations)

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
            # print(f'chunk size: {len(chunk)}')
            p = mp.Process(
                target=mutate_batch,
                args= ((self.les_g, self.bl_g, self.feas, chunk), queue, self.scorer, self.pop_size, self.cutoff)
            )
            self.processes.append(p)
            p.start()
        self.queue_listener = QueueListener(queue, cores_count)
        self.queue_listener.signals.progress.connect(self.add_to_population_without_incrementing_bar)
        self.queue_listener.signals.finished.connect(self.finished_generation)
        self.queue_listener.start()

    def finished_generation(self):
        self.completed_generations += 1
        for process in self.processes:
            process.join()
        print(len(self.population))
        rank(self.population, self.settings.scoring_weights, self.all_params)
        # log the best results
        self.goats.append(self.population[0])
        for old_params, new_param in zip(self.best_params, self.population[0][-1]):
            old_params.append(new_param)
        # report stats
        end = perf_counter()
        duration = end - self.gen_start
        self.times.append(duration)
        print(f'Generation {self.completed_generations + self.starting_gen}: {duration:.2f}s')
        self.update_bar.emit(f'Pokolenie {self.completed_generations + self.starting_gen} {self.population[0][-1]}')
        self.increment_bar.emit(1)
        if self.completed_generations < self.settings.generations:
            self.do_next_generation()
        else:
            self.finish_everything()

    def finish_everything(self):
        rank(self.goats, self.settings.scoring_weights, self.all_params, note_results=False)
        coloring = self.goats[0][0][0]
        print(f'total time: {sum(self.times):.2f}s')
        print(f'avg: {average(self.times):.2f}s')
        self.session.close()
        # self.best_params = []
        # self.cutoffs = []
        self.finished.emit(coloring, [coloring, self.population, self.bl_g, self.for_bl, self.les_g, self.feas, self.best_params, self.all_params])





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
        print(f'Naniesiono przedmioty w {tick_2-tick_1:.2f}s')
        self.update_bar.emit('Generowanie grafu lekcji')
        lesson_count = self.session.query(Lesson).count()
        self.update_bar_total.emit(lesson_count)
        classrooms = self.session.query(Classroom).filter_by(allow_lessons=True).all()
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
                # if block.day in [les.block.day for les in subject.lessons if les.block]:
                #     continue
                
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
                graph.add_edge(l1, l2)
            # subject is no longer needed
            if subject in graph.nodes:
                graph.remove_node(subject)
        tick_3 = perf_counter()
        print(f'Naniesiono lekcje w {tick_3-tick_2}s')
        
        return graph, labels, feasible_blocks

    def generate_block_graph(self):
        graph = Graph()
        # blocks taking place in different days can't possibly colide
        for day in range(5):
            self.update_bar.emit(f'Generowanie grafu bloków (dzień {day+1})')
            blocks = self.session.query(LessonBlockDB).filter_by(day=day).all()
            for block in blocks:
                graph.add_node(block.id, day=block.day)
            x = len(blocks)
            total = x * (x-1) // 2
            self.update_bar_total.emit(total)

            for b1, b2 in combinations(blocks, 2):
                self.increment_bar.emit(1)
                # if one block starts after the second has ended...
                if b1.start+b1.length < b2.start \
                or b2.start+b2.length < b1.start:
                    # ...the blocks don't collide
                    continue
                graph.add_edge(b1.id, b2.id)
        classrooms = self.session.query(Classroom).all()
        # WHY ARE BLOCKS FORBIDDEN? - to make sure that two lessons are not taking place at the same time and space
        forbidden_blocks = {cl.id: set() for cl in classrooms}
        for lesson in self.session.query(Lesson).filter(Lesson.classroom_id!= None).all():
            block = lesson.block_id
            forbidden_blocks[lesson.classroom_id].add(block)
            forbidden_blocks[lesson.classroom_id].update(graph[block])
        print('Naniesiono bloki zajęciowe')
        return graph, forbidden_blocks



