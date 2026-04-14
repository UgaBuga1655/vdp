from PyQt5.QtCore import pyqtSignal, QThread, QObject


class Signaler(QObject):
    progress = pyqtSignal(list)
    finished = pyqtSignal()

class QueueListener(QThread):
    def __init__(self, queue, n_of_workers):
        super().__init__()
        self.queue = queue
        self.signals = Signaler()
        self.n_of_workers = n_of_workers

    def run(self):
        finished = 0
        while True:
            msg, data = self.queue.get()
            self.signals.progress.emit(data)
            if msg == 'done':
                finished += 1
                # print(f'job {finished} finished')
                if finished == self.n_of_workers:
                    self.signals.finished.emit()
                    break
