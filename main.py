from multiprocessing import Process, Queue
import time
import random
class RangeReceiver:
    def __init__(self, checkingInterval, expireTime):
        self.checkingInterval = checkingInterval
        self.expireTime = expireTime
        self.lastUpdated = time.time()
        self.checkingTime = time.time()
    def receive_mpg(self, q, q2):
        while True:
            msg = q.get()
            print('received message')
            if 'mpg' in msg:
                self.update_time()
                print('new time ' + str(self.lastUpdated))
                q2.put({'lastUpdated': self.lastUpdated})
    def update_time(self):
        self.lastUpdated = time.time()
    def check_alive(self, q2):
        while True:
            try:
                msg = q2.get(timeout=5)
                if 'lastUpdated' in msg:
                    self.lastUpdated = msg['lastUpdated']
                    print('updating last updated')
            except Exception as error:
                print('queue stopped responding')
            time.sleep(self.checkingInterval)
            self.checkingTime = time.time()
            print('current time ' + str(self.checkingTime) + 'last Updated' + str(self.lastUpdated) + 'expire time' + str(self.expireTime))
            # print('type ' + str(type(self.checkingTime)))
            difference = self.checkingTime - self.lastUpdated
            print('the difference is ' + str(difference))
            if difference > self.expireTime:
                # print('calling fault monitor')
                FaultMonitor.failure_detected()

class RangeSender:
    def __init__(self, interval, range, gasAmount):
        self.sendinterval = interval
        self.gasAmount = gasAmount
        self.range = range
    def heartbeat(self, q):
        while True:
            # print('Im sleeping')
            time.sleep(self.sendinterval)
            print('getting mpg')
            q.put({'mpg':self.current_mpg()})
    def current_mpg(self):
        self.gasAmount = self.gasAmount - random.randrange(1,4)
        self.range = self.range - random.randrange(1,20)
        print(self.gasAmount)
        if self.gasAmount < 0:
            self.gasAmount = 0
        mpg = self.range / self.gasAmount
        print('mpg is '+ str(mpg))
        return mpg


class FaultMonitor:
    @staticmethod
    def failure_detected():
        print('The core process has failed')



if __name__ == '__main__':
    q = Queue()
    q2 = Queue()
    range_receiver = RangeReceiver(5, 20)
    range_sender = RangeSender(5, 200, 15)
    fault_monitor = FaultMonitor()
    p = Process(target= range_sender.heartbeat, args = (q,))
    p.start()
    p2 = Process(target=range_receiver.check_alive, args = (q2,))
    p2.start()
    p3 = Process(target=range_receiver.receive_mpg, args=(q, q2,))
    p3.start()
    p.join()
    p2.join()
    p3.join()
