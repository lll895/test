"""
企业知识库 RAG 问答系统 - 统一日志系统
======================================
功能：
- 彩色控制台日志输出
- 文件日志（按天轮转）
- 通过 LOG_LEVEL 环境变量控制日志级别
- 每个模块独立日志器，自动追踪调用来源
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler

# 日志级别映射
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# ---------- 彩色日志格式 ----------
COLOR_MAP = {
    'DEBUG': '\033[36m',      # 青色
    'INFO': '\033[32m',       # 绿色
    'WARNING': '\033[33m',    # 黄色
    'ERROR': '\033[31m',      # 红色
    'CRITICAL': '\033[35m',   # 紫色
    'RESET': '\033[0m',       # 重置
}


class ColoredFormatter(logging.Formatter):
    """支持终端彩色输出的日志格式化器"""

    def format(self, record):
        levelname = record.levelname
        color = COLOR_MAP.get(levelname, COLOR_MAP['RESET'])
        reset = COLOR_MAP['RESET']

        # 为级别名添加颜色
        record.levelname = f"{color}{levelname}{reset}"
        record.msg = f"{record.msg}"

        # 格式化时间
        record.asctime = self.formatTime(record, self.datefmt or '%Y-%m-%d %H:%M:%S')

        return f"{record.asctime} | {record.levelname:20s} | {record.name:30s} | {record.msg}"


# ---------- 日志器工厂 ----------

_loggers = {}  # 已创建的日志器缓存


def get_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    获取或创建日志器

    Args:
        name: 模块名称（通常传入 __name__）
        log_file: 日志文件路径，None 表示使用默认路径

    Returns:
        配置好的 Logger 实例
    """
    if name in _loggers:
        return _loggers[name]

    # 获取日志级别
    level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    level = LOG_LEVELS.get(level_name, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # 避免重复添加

    # ---- 控制台 Handler（彩色输出） ----
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-20s | %(name)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # ---- 文件 Handler（保留最近 5 个文件，每个 10MB） ----
    try:
        log_dir = os.environ.get('LOG_DIR', './logs')
        os.makedirs(log_dir, exist_ok=True)

        file_path = log_file or os.path.join(log_dir, 'enterprise_oa.log')
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-30s | %(pathname)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # 日志系统初始化失败不应影响主流程
        logger.warning(f"无法创建文件日志处理器: {e}")

    _loggers[name] = logger
    return logger


def init_logging():
    """初始化日志系统（应用启动时调用）"""
    logger = get_logger('system')
    level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logger.info(f"日志系统已初始化，日志级别: {level}")
    log_dir = os.environ.get('LOG_DIR', './logs')
    logger.info(f"日志文件目录: {log_dir}")
    return logger
