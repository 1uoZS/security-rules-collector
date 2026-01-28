"""
数据模型定义模块
定义应用程序中使用的核心数据类
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class FileTarget:
    """文件目标数据类"""
    src: str                    # 源文件路径
    device: str                 # 设备名称
    dest_rel: str              # 目标相对路径
    cached: bool = False       # 是否来自缓存
    from_docker: bool = False  # 是否来自Docker
    
    @property
    def source_path(self) -> Path:
        """获取源路径的Path对象"""
        return Path(self.src)

@dataclass
class CollectionResult:
    """收集结果数据类"""
    total: int = 0                     # 总文件数
    copied: List[str] = field(default_factory=list)  # 已复制文件
    unchanged: int = 0                 # 未变化文件数
    changed: int = 0                   # 变化文件数
    local_files: int = 0               # 本地文件数
    docker_files: int = 0              # Docker文件数
    cached_paths_used: int = 0         # 使用的缓存路径数
    new_paths_found: int = 0           # 新发现路径数
    execution_time: float = 0.0        # 执行时间
    timestamp: str = ""                # 时间戳

@dataclass
class PathCacheItem:
    """路径缓存项数据类"""
    path: str              # 路径
    dest_rel: str          # 目标相对路径
    device: str = ""       # 设备名称（可选）

@dataclass
class DockerContainerInfo:
    """Docker容器信息数据类"""
    container_id: str      # 容器ID
    is_running: bool       # 是否运行中
    resolved_id: str       # 解析后的ID