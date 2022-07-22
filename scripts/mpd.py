import glob
import logging
from logging.handlers import QueueHandler, QueueListener
import multiprocessing

from scripts.decode import decode

log_path = "../log"
file_path = "/data3/storage/ADSB/raw/DF"
num_core = 36
file_list = glob.glob(f"{file_path}/**/*.txt")


def worker_init(q):
    qh = QueueHandler(q)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(qh)


def logger_init():
    q = multiprocessing.Queue()
    handler = logging.FileHandler(f"{log_path}/decode.log", mode="a")
    handler.setFormatter(
        logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    )

    ql = QueueListener(q, handler)
    ql.start()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return ql, q


def main():
    q_listener, q = logger_init()
    logging.info(f"Decode start, all files")
    pool = multiprocessing.Pool(num_core, worker_init, [q])
    for result in pool.map(decode, file_list):
        pass
    pool.close()
    pool.join()
    q_listener.stop()

if __name__ == '__main__':
    main()
