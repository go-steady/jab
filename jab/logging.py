import logging
from typing import Any

from typing_extensions import Protocol


class Logger(Protocol):
    def debug(self, msg: Any) -> None:
        pass  # pragma: no cover

    def info(self, msg: Any) -> None:
        pass  # pragma: no cover

    def warning(self, msg: Any) -> None:
        pass  # pragma: no cover

    def error(self, msg: Any) -> None:
        pass  # pragma: no cover

    def critical(self, msg: Any) -> None:
        pass  # pragma: no cover


class DefaultJabLogger:
    def __init__(self) -> None:
        self._log = logging.getLogger(__name__)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s] - %(levelname)s - %(message)s")  # pragma: no mutate
        ch.setFormatter(formatter)
        self._log.addHandler(ch)

    def debug(self, msg: Any) -> None:
        self._log.debug(msg)

    def info(self, msg: Any) -> None:
        self._log.info(msg)

    def warning(self, msg: Any) -> None:
        self._log.warning(msg)

    def error(self, msg: Any) -> None:
        self._log.error(msg)

    def critical(self, msg: Any) -> None:
        self._log.critical(msg)
