import glob
import logging
from logging.handlers import QueueHandler, QueueListener
import multiprocessing

from scripts.edr import edr2, jerk


csv_path = "/data3/storage/ADSB/QCdone"
file_list = glob.glob(f"{csv_path}/*.csv")
# file_list = [x.split('/')[-1][:-4] for x in csv_list]
type_edr = "EDR2"
# type_edr = "jerk_EDR"

log_path = "../log"
num_core = 36


def worker_init(q):
    qh = QueueHandler(q)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(qh)


def logger_init():
    q = multiprocessing.Queue()
    handler = logging.FileHandler(f"{log_path}/calculate_{type_edr}.log", mode="a")
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
    logging.info(f'Start calculating {type_edr}')
    pool = multiprocessing.Pool(num_core, worker_init, [q])
    for result in pool.map(edr2, file_list):
        pass
    pool.close()
    pool.join()
    q_listener.stop()

if __name__ == '__main__':
    main()
