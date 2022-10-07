import logging
from pathlib import Path
from sys import stderr, stdout
from logging import Logger, StreamHandler, Formatter, LogRecord, Filter
from typing import Union, Optional


class StdErrFilter(Filter):
    def filter(self, record: LogRecord) -> bool:
        return record.levelno >= logging.ERROR


class StdOutFilter(Filter):
    def filter(self, record: LogRecord) -> bool:
        return record.levelno < logging.ERROR


class LoggerFactory:
    """Factory to create logger objects."""

    @staticmethod
    def get_formatter() -> Formatter:
        return Formatter("[%(asctime)s - %(name)s - %(levelname)s]: %(message)s")

    @staticmethod
    def get_console_logger(name: str, level: int = logging.INFO) -> Logger:
        """Get a logger that prints INFO or more severe logs to the console"""

        # Create logger.
        logger: Logger = logging.getLogger(name)

        if logger.hasHandlers():
            # Logger already set up.
            return logger
        else:
            # Set severity level.
            logger.setLevel(logging.WARNING)

            # Create stderr handler.
            h_err: StreamHandler = StreamHandler(stderr)
            h_err.setLevel(level)
            h_err.addFilter(StdErrFilter())

            # Create stdout handler.
            h_out: StreamHandler = StreamHandler(stdout)
            h_out.setLevel(level)
            h_out.addFilter(StdOutFilter())

            # Create formatter.
            formatter = LoggerFactory.get_formatter()

            # add formatter to handlers
            h_err.setFormatter(formatter)
            h_out.setFormatter(formatter)

            # add handlers to logger
            logger.addHandler(h_err)
            logger.addHandler(h_out)

        return logger

    @staticmethod
    def get_file_logger(name: str, file_dir: Path = Path()/"logs", preffix: Optional[str] = None) -> Logger:
        # Create logger.
        logger: Logger = logging.getLogger(name)

        if logger.hasHandlers():
            # Logger already set up.
            return logger
        else:
            # Set severity level.
            logger.setLevel(logging.WARNING)

            # Create file stderr handler.
            stderr_filename = file_dir / f"{'' if preffix is None else preffix + '_'}stderr.log"
            if not stderr_filename.is_file():
                stderr_filename.parent.mkdir(parents=True, exist_ok=True)
                stderr_filename.touch()  # Create file if it does not exist
            err_handler = logging.FileHandler(str(stderr_filename.absolute()))
            err_handler.setLevel(logging.WARNING)
            err_handler.addFilter(StdErrFilter())

            # Create stdout handler.
            stdout_filename = file_dir / f"{'' if preffix is None else preffix + '_'}stdout.log"
            if not stdout_filename.is_file():
                stdout_filename.parent.mkdir(parents=True, exist_ok=True)
                stdout_filename.touch()  # Create file if it does not exist
            out_handler = logging.FileHandler(str(stdout_filename.absolute()))
            out_handler.setLevel(logging.WARNING)
            out_handler.addFilter(StdOutFilter())

            # Create formatter.
            formatter = LoggerFactory.get_formatter()

            # add formatter to handlers
            err_handler.setFormatter(formatter)
            out_handler.setFormatter(formatter)

            # add handlers to logger
            logger.addHandler(err_handler)
            logger.addHandler(out_handler)

        return logger
