"""
设备配置管理模块
负责设备规则的配置管理和验证
"""
from typing import Dict
from .data_models import DeviceConfig  # 从新的数据模型导入

class DeviceConfigManager:
    """设备配置管理器"""
    
    def __init__(self):
        self._devices: Dict[str, DeviceConfig] = self._load_default_config()
    
    def _load_default_config(self) -> Dict[str, DeviceConfig]:
        """加载默认设备配置"""
        return {
            "suricata": DeviceConfig(
                name="suricata",
                type="local",
                relative_path=["**/suricata/rules/"],
                file_type="rules"
            ),
            "snort": DeviceConfig(
                name="snort",
                type="local",
                relative_path=["**/snort/rules/", "**/scripts/policy", "**/scripts/site"],
                file_type="rules"
            ),
            "ModSecurity": DeviceConfig(
                name="ModSecurity",
                type="local",
                relative_path=["**/crs4/rules"],
                file_type="conf"
            ),
            "zeek": DeviceConfig(
                name="zeek",
                type="local",
                relative_path=[
                    "**/zeek/share/zeek/policy/protocols/ftp/detect-bruteforcing.zeek",
                    "**/zeek/share/zeek/policy/protocols/http/detect-sqli.zeek",
                    "**/zeek/share/zeek/policy/protocols/http/detect-webapps.zeek",
                    "**/zeek/share/zeek/policy/protocols/ssh/detect-bruteforcing.zeek",
                    "**/zeek/share/zeek/policy/protocols/ssl/heartbleed.zeek",
                    "**/zeek/share/zeek/policy/protocols/ssl/weak-keys.zeek",
                    "**/zeek/share/zeek/policy/protocols/smtp/blocklists.zeek",
                    "**/zeek/share/zeek/policy/protocols/smtp/detect-suspicious-orig.zeek",
                    "**/zeek/share/zeek/policy/frameworks/files/detect-MHR.zeek",
                    "**/zeek/share/zeek/policy/frameworks/software/vulnerable.zeek",
                ],
                file_type="zeek"
            ),
            "nuclei": DeviceConfig(
                name="nuclei",
                type="local",
                relative_path=["**/nuclei-templates/"],
                file_type="yaml"
            ),
            "堡塔云waf": DeviceConfig(
                name="堡塔云waf",
                type="docker",
                relative_path=[],
                file_type="json",
                container="86e4e41a871c",
                path="/etc/nginx/waf/rule"
            ),
            "南墙uuwaf": DeviceConfig(
                name="南墙uuwaf",
                type="docker",
                relative_path=[],
                file_type="w",
                container="ca466ab891e4",
                path="/uuwaf/waf/plugins/"
            ),
            
        }
    
    def get_device(self, device_name: str) -> DeviceConfig:
        """获取设备配置"""
        if device_name not in self._devices:
            raise KeyError(f"未知设备: {device_name}")
        return self._devices[device_name]
    
    def get_all_devices(self) -> Dict[str, DeviceConfig]:
        """获取所有设备配置"""
        return self._devices.copy()
    
    def add_device(self, config: DeviceConfig):
        """添加新设备配置"""
        self._devices[config.name] = config
    
    def remove_device(self, device_name: str):
        """移除设备配置"""
        if device_name in self._devices:
            del self._devices[device_name]