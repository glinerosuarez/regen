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
    def get_console_logger(name: str) -> Logger:
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
            h_err.setLevel(logging.INFO)
            h_err.addFilter(StdErrFilter())

            # Create stdout handler.
            h_out: StreamHandler = StreamHandler(stdout)
            h_out.setLevel(logging.INFO)
            h_out.addFilter(StdOutFilter())

            # Create formatter.
            formatter: Formatter = Formatter("[%(asctime)s - %(name)s - %(levelname)s]: %(message)s")

            # add formatter to handlers
            h_err.setFormatter(formatter)
            h_out.setFormatter(formatter)

            # add handlers to logger
            logger.addHandler(h_err)
            logger.addHandler(h_out)

        return logger
