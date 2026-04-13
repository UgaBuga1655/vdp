from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject, QThread
from .functions import crazy
from time import perf_counter

class Signaler(QObject):
    new_chromosome = pyqtSignal(dict, int)
    new_chromosomes = pyqtSignal(list)
    finished = pyqtSignal()

def random_coloring(data, queue):
    lg, bg, feas, chunk_size = data
    i = 0
    data = []
    update_size = chunk_size
    for _ in range(chunk_size):
        coloring = crazy(lg, bg, feas)
        cost = sum([len(les.subject.students) for les, block in coloring.items() if block is None])
        # print(cost)
        data.append((coloring, cost))
        # i+=1
        # if  i == update_size:
        #     queue.put(('progress', data))
        #     data = []
        #     i = 0    
    # queue.put(('progress', data))
    queue.put(data)

class QueueListener(QThread):
    def __init__(self, queue, pop_size, n_of_workers):
        super().__init__()
        self.queue = queue
        self.signals = Signaler()
        self.pop_size = pop_size
        self.n_of_workers = n_of_workers

    def run(self):

        finished = 0
        while True:
            # print('foo')
            data = self.queue.get()
            
            # print(data)
            
            self.signals.new_chromosomes.emit(data)

            finished += 1
            if finished == self.n_of_workers:
                self.signals.finished.emit()
                break




class Birther(QRunnable):
    def __init__(self, chunksize, lg, bg, feas):
        self.chunksize = chunksize
        self.lg = lg
        self.bg = bg
        self.feas = feas
        self.signals = Signaler()
        super().__init__()

    def run(self):
        for _ in range(self.chunksize):
            start = perf_counter()
            coloring = crazy(self.lg, self.bg, self.feas)
            cost = sum([len(les.subject.students) for les, block in coloring.items() if block is None])
            end = perf_counter()
            self.signals.new_chromosome.emit(coloring, cost, end-start)