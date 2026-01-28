"""
配置数据模型模块
定义配置相关的数据类，避免循环导入
"""
from dataclasses import dataclass
from typing import List

@dataclass
class DeviceConfig:
    """设备配置数据类"""
    name: str
    type: str  # "local" 或 "docker"
    relative_path: List[str]
    file_type: str = ""
    container: str = ""  # 仅Docker类型需要
    path: str = ""  # 仅Docker类型需要
    
    def __post_init__(self):
        """初始化后验证配置"""
        self._validate()
    
    def _validate(self):
        """验证配置有效性"""
        if self.type not in ["local", "docker"]:
            raise ValueError(f"设备类型必须为 'local' 或 'docker'，当前为: {self.type}")
        
        if self.type == "docker":
            if not self.container:
                raise ValueError("Docker设备必须指定容器ID")
            if not self.path:
                raise ValueError("Docker设备必须指定路径")
        
        if self.type == "local" and not self.relative_path:
            raise ValueError("本地设备必须指定相对路径")