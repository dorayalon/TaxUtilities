import logging
import os.path
import sys


class MyLogger:
    LOGS_FOLDER = f"/var/tmp/log/{os.path.basename(os.path.dirname(os.path.dirname(__file__)))}"

    def __init__(self):
        if not os.path.exists(self.LOGS_FOLDER):
            os.makedirs(self.LOGS_FOLDER, exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Create a formatter and add it to the handler
        formatter = logging.Formatter("%(asctime)s %(module)s.%(funcName)s -> %(lineno)d-%(levelname)s: %(message)s")

        # Create & add a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Create & add a file handler
        file_handler = logging.FileHandler(f"{self.LOGS_FOLDER}/{os.path.basename(sys.argv[0])}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)


logger = MyLogger().logger
