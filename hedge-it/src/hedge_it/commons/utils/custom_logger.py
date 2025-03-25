import functools
import logging
import os
import sys
from datetime import datetime
from typing import Optional

_root_package = __package__.split(".")[0] if __package__ else __name__.split(".")[0]


class ModulePathFilter(logging.Filter):
    def filter(self, record):
        if (
            record.pathname
            and f"{os.path.sep}{_root_package}{os.path.sep}" in record.pathname
        ):
            path_split = record.pathname.split(os.path.sep)
            record.module_path = ".".join(
                path_split[path_split.index(_root_package) : -1]
            )
        else:
            record.module_path = record.module
        return True


COLOR_RESET = "\033[0m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_GREEN = "\033[92m"
COLOR_CYAN = "\033[96m"

DEFAULT_LOG_NAME = "HEDGE_IT"


class CustomFormatter(logging.Formatter):
    COLORS = {
        "ERROR": COLOR_RED,
        "WARNING": COLOR_YELLOW,
        "INFO": COLOR_GREEN,
        "DEBUG": COLOR_CYAN,
    }

    def __init__(self, root_path, fmt, datefmt=None):
        super().__init__(fmt, datefmt)
        self.root_path = root_path

    def format(self, record):
        # Replace the full pathname with the relative path
        path_components = os.path.normpath(record.pathname).split(os.path.sep)
        root_package_index = 0
        if self.root_path in path_components:
            root_package_index = path_components.index(self.root_path)
        relative_components = path_components[root_package_index:-1]
        module_path = ".".join(relative_components)
        record.pathname = module_path
        message = super().format(record)
        levelname = record.levelname
        return f"{self.COLORS.get(levelname, '')}{message}{COLOR_RESET}"


def _init_logger(log_name: str, log_level: str):
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)

    formatter = CustomFormatter(
        _root_package,
        "%(asctime)s %(levelname)s |%(name)s| %(pathname)s:%(module)s:%(lineno)d:: %(message)s",
        datefmt="%y/%m/%d %H:%M:%S",
    )
    # logger.addFilter(ModulePathFilter())
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        f"{log_name}_run_{datetime.utcnow().strftime('%Y-%m-%d')}.log", mode="a"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    print(f"custom logger created:{logger.name} and level:{logger.getEffectiveLevel()}")
    return logger


class CustomLogger:
    _logger: Optional[logging.Logger] = None

    def __new__(
        cls, log_name: str = DEFAULT_LOG_NAME, log_level: str = "INFO"
    ) -> logging.Logger:
        if cls._logger is None:
            cls._logger = _init_logger(log_name, log_level)
        return cls._logger

    @classmethod
    def reinitialize(cls, log_name: str= DEFAULT_LOG_NAME, log_level: str = "INFO") -> logging.Logger:
        cls._logger = _init_logger(log_name, log_level)
        return cls._logger
    @classmethod
    def set_level(cls,log_level: str = "INFO") -> logging.Logger:
        cls._logger.setLevel(log_level)
        return cls._logger

    @classmethod
    def logger(cls) -> logging.Logger:
        if cls._logger is None:
            cls._logger = _init_logger(DEFAULT_LOG_NAME, "INFO")
        return cls._logger


get_logger = functools.partial(CustomLogger.logger)
