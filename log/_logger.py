import logging
from sys import stderr, stdout
from logging import Logger, StreamHandler, Formatter, LogRecord, Filter


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
            logger.setLevel(logging.DEBUG)

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
    def get_file_logger(name: str, filename: str = "logs") -> Logger:
        # Create logger.
        logger: Logger = logging.getLogger(name)

        if logger.hasHandlers():
            # Logger already set up.
            return logger
        else:
            # Set severity level.
            logger.setLevel(logging.DEBUG)

            # Create file stderr handler.
            err_handler = logging.FileHandler("output/logs/" + filename + "_stderr.log")
            err_handler.setLevel(logging.DEBUG)
            err_handler.addFilter(StdErrFilter())

            # Create stdout handler.
            out_handler = logging.FileHandler("output/logs/" + filename + "_stdout.log")
            out_handler.setLevel(logging.DEBUG)
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
