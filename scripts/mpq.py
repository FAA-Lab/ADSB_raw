import glob
import logging
from logging.handlers import QueueHandler, QueueListener
import multiprocessing

from scripts.qc import qc


target_year = "2022"

csv_path = "/data3/storage/ADSB/merged"
file_list = glob.glob(f"{csv_path}/{target_year}*.txt")
# file_list = [x.split('/')[-1][:-4] for x in csv_list]

log_path = "../log"
num_core = 36


def worker_init(q):
    qh = QueueHandler(q)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(qh)


def logger_init():
    q = multiprocessing.Queue()
    handler = logging.FileHandler(f"{log_path}/{target_year}_calculated_wind_QC.log", mode="a")
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
    logging.info(f'Start QC for calculated wind')
    pool = multiprocessing.Pool(num_core, worker_init, [q])
    for result in pool.map(qc, file_list):
        pass
    pool.close()
    pool.join()
    q_listener.stop()

if __name__ == '__main__':
    main()
