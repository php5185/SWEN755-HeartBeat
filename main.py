from multiprocessing import Process, Queue
import time
import random
import os 

class MPGReceiver:
    def __init__(self, checkingInterval, expireTime):
        self.checkingInterval = checkingInterval
        self.expireTime = expireTime
        self.lastUpdated = time.time()
        self.checkingTime = time.time()

    def receive_mpg(self, mpgQueue, recoveryMpgQueue, lastUpdatedQueue):
        pid = str(os.getpid())

        while True:
            msg = {}

            try:
                msg = mpgQueue.get(timeout=7)
            except Exception:
                print('Process#' + pid + ' --> Primary Mpg Sender Module is not responding. Switching to Recovery module.')

            if not msg:
                try:
                    msg = recoveryMpgQueue.get(timeout=7)
                except Exception:
                    print('Process#' + pid + ' --> Recovery Mpg sender module is not responding.')

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
                FaultMonitor.log_failure('Process#' + pid + ' --> Sender module(s) are not responding.')
                FaultMonitor.log_failure('Process#' + pid + ' --> Last heartbeat was: ' + str(round(difference)) + ' seconds ago.')

class MPGSender:
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
    recoveryMpgQueue = Queue()
    lastUpdatedQueue = Queue()

    mpg_receiver = MPGReceiver(5, 20)
    mpg_sender = MPGSender(5, 200, 15)
    mpg_sender_recovery = MPGSender(5, 200, 200)

    heartbeatProcess = Process(target= mpg_sender.heartbeat, args = (mpgQueue,))
    heartbeatProcess.start()

    recoveryHeartbeatProcess = Process(target= mpg_sender_recovery.heartbeat, args = (recoveryMpgQueue,))
    recoveryHeartbeatProcess.start()

    checkAliveProcess = Process(target= mpg_receiver.check_alive, args = (lastUpdatedQueue,))
    checkAliveProcess.start()

    receiveMpgProcess = Process(target= mpg_receiver.receive_mpg, args=(mpgQueue, recoveryMpgQueue, lastUpdatedQueue,))
    receiveMpgProcess.start()
    
    heartbeatProcess.join()
    recoveryHeartbeatProcess.join()
    checkAliveProcess.join()
    receiveMpgProcess.join()
