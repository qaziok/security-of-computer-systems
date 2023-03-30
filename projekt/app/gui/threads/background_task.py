from PyQt6.QtCore import QThread, pyqtSignal


class BackgroundTask(QThread):
    task_completed = pyqtSignal()

    def __init__(self, *, sleep_time=0, loop=False):
        self.sleep_time = sleep_time
        self.loop = loop
        super().__init__()

    def run(self):
        while self.loop:
            self.task_completed.emit()
            self.msleep(self.sleep_time)
