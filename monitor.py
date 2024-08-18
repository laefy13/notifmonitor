import logging
import os
from tqdm import tqdm
from time import sleep
import psutil

logging.basicConfig(
    filename="performance.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def process_memory():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss


def process_cpu():
    process = psutil.Process(os.getpid())
    return process.cpu_percent(interval=0.1)


def profiler(func):
    def wrapper(*args, **kwargs):

        mem_before = process_memory()
        cpu_before = process_cpu()

        result = func(*args, **kwargs)

        mem_after = process_memory()
        cpu_after = process_cpu()

        print(
            "{}: consumed memory: {:,} bytes, CPU: {}%".format(
                func.__name__, mem_after - mem_before, cpu_after - cpu_before
            )
        )
        logging.info(
            "{}: consumed memory: {:,} bytes, CPU: {}%".format(
                func.__name__, mem_after - mem_before, cpu_after - cpu_before
            )
        )

        return result

    return wrapper
