"""统一日志配置：输出到 data/logs/app.log 与控制台。"""
import logging
import sys

from backend.config import LOG_DIR, LOG_FILE


def setup_logging(
    level: int = logging.INFO,
    log_file: str | None = None,
) -> None:
    """配置根 logger：同时写文件与控制台。"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = log_file or str(LOG_FILE)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)

    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """获取模块用 logger，建议 name=__name__。"""
    return logging.getLogger(name)
