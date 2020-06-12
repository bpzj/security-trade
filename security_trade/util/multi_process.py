from multiprocessing import Process, Queue
import time


def producer(queue: Queue):
    while True:
        queue.put('a')
        time.sleep(1)


def consumer(queue: Queue):
    i=1
    while True:
        data = queue.get()
        print(i,"次循环")
        print(data)
        i=i+1


if __name__ == "__main__":
    queue = Queue()
    my_producer = Process(target=producer, args=(queue,))
    my_consumer = Process(target=consumer, args=(queue,))
    my_producer.start()
    my_consumer.start()
    my_producer.join()
    my_consumer.join()

