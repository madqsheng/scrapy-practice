"""每次爬取自动把日志写入 logs/<BOT_NAME>/<spider>_<时间>.log。

- 路径规则与 settings.py 里的 resource 保存保持一致：仓库根(含 .git) / logs / <BOT_NAME> /
- 同时保留控制台输出（不劫持 scrapy 默认的 stderr 日志）
- 每个 spider 每次运行单独一个文件，方便按时间定位某次爬取的日志
"""
import logging
import os
from datetime import datetime

from scrapy import signals


def _repo_root():
    # 本文件位于 <repo>/<project>/<project>/logging_ext.py
    # 向上三级即仓库根，与 settings.py 中 _REPO_ROOT 的计算一致
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SpiderLogFileExtension:
    """监听 spider_opened / spider_closed，为每个 spider 运行单独开一个日志文件。"""

    def __init__(self, settings):
        self.settings = settings
        self._handler = None
        self._log_path = None

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler.settings)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def spider_opened(self, spider):
        bot_name = self.settings.get("BOT_NAME") or "scrapy"
        log_dir = os.path.join(_repo_root(), "logs", bot_name)
        os.makedirs(log_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_path = os.path.join(log_dir, f"{spider.name}_{ts}.log")

        handler = logging.FileHandler(self._log_path, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        root = logging.getLogger()
        # 确保根日志器不高于文件级别，否则记录可能在到达本 handler 前被过滤
        if root.level in (logging.WARNING, logging.NOTSET, 0):
            root.setLevel(logging.DEBUG)
        root.addHandler(handler)
        self._handler = handler

        logging.getLogger(__name__).info("本次日志已开启，写入: %s", self._log_path)

    def spider_closed(self, spider):
        if self._handler is not None:
            root = logging.getLogger()
            root.removeHandler(self._handler)
            try:
                self._handler.flush()
            finally:
                self._handler.close()
            self._handler = None
