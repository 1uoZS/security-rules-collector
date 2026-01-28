"""
配置常量定义模块
集中管理所有配置常量，便于维护和修改
"""
import os
from pathlib import Path
from typing import Dict, Any, List

# 输出目录和缓存文件配置
OUTPUT_DIR = "collected_rules"
HASH_RECORD_FILE = os.path.join(OUTPUT_DIR, "file_hashes.json")
PATH_CACHE_FILE = os.path.join(OUTPUT_DIR, "path_cache.json")
DOCKER_TEMP_DIR = os.path.join(OUTPUT_DIR, "docker_temp")

# 常见搜索路径
COMMON_PATHS = ["/etc", "/opt", "/usr/local", "/usr/share", "/var/lib", "/var"]
PROGRAM_PATHS = ["/usr/share", "/usr/local/share", "/var/lib", "/opt"]

# 终端颜色代码
class Colors:
    """终端颜色常量类"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# 扫描优先级配置
SCAN_ORDER_PRIORITY = [
    ("常见路径", COMMON_PATHS),
    ("用户主目录", [os.path.expanduser("~")]),
    ("程序安装目录", PROGRAM_PATHS),
]