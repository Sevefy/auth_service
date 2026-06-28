import logging
import sys

from colorlog import ColoredFormatter


def config_logging() -> None:
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(asctime)s%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # 3. Pass the custom handler into basicConfig
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])