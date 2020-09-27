from multiprocessing import Process, Queue
import time
import random
import os 

class RangeReceiver:
    def __init__(self, checkingInterval, expireTime):
        self.checkingInterval = checkingInterval
        self.expireTime = expireTime
        self.lastUpdated = time.time()
        self.checkingTime = time.time()

    def receive_mpg(self, mpgQueue, lastUpdatedQueue):
        pid = str(os.getpid())

        while True:
            msg = mpgQueue.get()

            if 'mpg' in msg:
                self.update_time()
                lastUpdatedQueue.put({'lastUpdated': self.lastUpdated})
                print('Process#' + pid + ' --> lastUpdatedQueue value was updated.')

    def update_time(self):
        self.lastUpdated = time.time()

    def check_alive(self, lastUpdatedQueue):
        pid = str(os.getpid())

        while True:
            time.sleep(self.checkingInterval)

            try:
                msg = lastUpdatedQueue.get(timeout=5)

                if 'lastUpdated' in msg:
                    self.lastUpdated = msg['lastUpdated']

            except Exception:
                FaultMonitor.log_failure('Process#' + pid + ' --> lastUpdatedQueue is not responding.')

            self.checkingTime = time.time()
            difference = self.checkingTime - self.lastUpdated

            if difference > self.expireTime:
                FaultMonitor.log_failure('Process#' + pid + ' --> Sender module is not responding.')
                FaultMonitor.log_failure('Process#' + pid + ' --> Last heartbeat was: ' + str(round(difference)) + ' seconds ago.')

class RangeSender:
    def __init__(self, interval, range, gasAmount):
        self.sendinterval = interval
        self.gasAmount = gasAmount
        self.range = range

    def heartbeat(self, mpgQueue):
        pid = str(os.getpid())

        while True:
            time.sleep(self.sendinterval)
            mpgQueue.put({'mpg':self.current_mpg()})
            print('Process#' + pid + ' --> mpgQueue value was updated.')

    def current_mpg(self):
        self.gasAmount = self.gasAmount - random.randrange(1,4)
        self.range = self.range - random.randrange(1,20)

        if self.gasAmount < 0:
            self.gasAmount = 0
        mpg = self.range / self.gasAmount

        return mpg

class FaultMonitor:
    @staticmethod
    def log_failure(message):
        print('Failure Monitor: ' + message)

if __name__ == '__main__':
    mpgQueue = Queue()
    lastUpdatedQueue = Queue()

    range_receiver = RangeReceiver(5, 20)
    range_sender = RangeSender(5, 200, 15)

    heartbeatProcess = Process(target= range_sender.heartbeat, args = (mpgQueue,))
    heartbeatProcess.start()

    checkAliveProcess = Process(target=range_receiver.check_alive, args = (lastUpdatedQueue,))
    checkAliveProcess.start()

    receiveMpgProcess = Process(target=range_receiver.receive_mpg, args=(mpgQueue, lastUpdatedQueue,))
    receiveMpgProcess.start()
    
    heartbeatProcess.join()
    checkAliveProcess.join()
    receiveMpgProcess.join()
