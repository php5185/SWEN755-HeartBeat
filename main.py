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
        self.recoveryMode = False

    def receive_mpg(self, mpg1Queue, mpg2Queue, lastUpdatedQueue, recoveryQueue):
        pid = str(os.getpid())

        while True:
            if self.recoveryMode:
                msg = mpg2Queue.get()
                print('recovery mpg' + str(msg['mpg']))
            else:
                try:
                    recovery = recoveryQueue.get()
                    if 'switch' in recovery:
                        if recovery['switch']:
                            print('queue initiates recovery')
                            self.recoveryMode = True
                            msg = mpg2Queue.get()
                        else:
                            msg = mpg1Queue.get()
                    else:
                        msg = mpg1Queue.get()
                except:
                    msg = mpg1Queue.get()
            try:
                print(str(mpg1Queue.get()['mpg']))
            except:
                continue
            if 'mpg' in msg:
                self.update_time()
                lastUpdatedQueue.put({'lastUpdated': self.lastUpdated})
                print('Process#' + pid + ' --> lastUpdatedQueue value was updated.')

    def update_time(self):
        self.lastUpdated = time.time()

    def check_alive(self, lastUpdatedQueue, recoveryQueue, faultMonitor):
        pid = str(os.getpid())
        while True:
            time.sleep(self.checkingInterval)
            try:
                msg = lastUpdatedQueue.get(timeout=10)

                if 'lastUpdated' in msg:
                    self.lastUpdated = msg['lastUpdated']

            except Exception:
                print('Process#' + pid + ' --> lastUpdatedQueue is not responding.')

            self.checkingTime = time.time()
            difference = self.checkingTime - self.lastUpdated

            if difference > self.expireTime:
                faultMonitor.log_failure('Process#' + pid + ' --> Sender module is not responding.',recoveryQueue)

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

    def recovery(self, recoveryQueue):
        print('putting recovery in')
        recoveryQueue.put({'switch': True})

    def log_failure(self, message, recoveryQueue):
        self.recovery(recoveryQueue)
        print('Failure Monitor: ' + message)

if __name__ == '__main__':
    mpg1Queue = Queue()
    mpg2Queue = Queue()
    lastUpdatedQueue = Queue()
    recoveryQueue = Queue()

    mpg_receiver = MPGReceiver(5, 20)
    mpg_sender1 = MPGSender(5, 200, 10)
    mpg_sender2 = MPGSender(5, 200, 100)
    faultMonitor = FaultMonitor()

    heartbeatProcess = Process(target= mpg_sender1.heartbeat, args = (mpg1Queue,))
    heartbeatProcess.start()

    heartbeatProcess2 = Process(target=mpg_sender2.heartbeat, args= (mpg2Queue,))
    heartbeatProcess2.start()

    checkAliveProcess = Process(target= mpg_receiver.check_alive, args = (lastUpdatedQueue,recoveryQueue, faultMonitor))
    checkAliveProcess.start()

    receiveMpgProcess = Process(target= mpg_receiver.receive_mpg, args=(mpg1Queue,mpg2Queue,lastUpdatedQueue,recoveryQueue))
    receiveMpgProcess.start()
    
    heartbeatProcess.join()
    checkAliveProcess.join()
    receiveMpgProcess.join()
