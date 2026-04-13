from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject, QThread
from .functions import crazy
from time import perf_counter

class Signaler(QObject):
    new_chromosomes = pyqtSignal(list)
    finished = pyqtSignal()

def random_coloring(params, queue):
    lg, bg, feas, chunk_size = params
    data = []
    for _ in range(chunk_size):
        coloring = crazy(lg, bg, feas)
        cost = sum([len(les.subject.students) for les, block in coloring.items() if block is None])
        data.append((coloring, cost))

    queue.put(data)

class QueueListener(QThread):
    def __init__(self, queue, n_of_workers):
        super().__init__()
        self.queue = queue
        self.signals = Signaler()
        self.n_of_workers = n_of_workers

    def run(self):
        finished = 0
        while True:
            data = self.queue.get()
            self.signals.new_chromosomes.emit(data)

            finished += 1
            if finished == self.n_of_workers:
                self.signals.finished.emit()
                break



