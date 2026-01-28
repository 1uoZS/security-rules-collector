"""
缓存管理模块
负责哈希记录和路径缓存的管理
"""
import json
import os
from typing import Dict, Any, List
from pathlib import Path

from config.settings import HASH_RECORD_FILE, PATH_CACHE_FILE
from models.data_models import PathCacheItem
from utils.output_formatter import OutputFormatter
from utils.file_utils import FileUtils

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.hash_record: Dict[str, str] = {}
        self.path_cache: Dict[str, List[Dict[str, str]]] = {}
    
    def load_hash_record(self) -> Dict[str, str]:
        """从JSON文件加载之前的哈希记录"""
        if os.path.exists(HASH_RECORD_FILE):
            try:
                with open(HASH_RECORD_FILE, "r", encoding="utf-8") as file:
                    self.hash_record = json.load(file)
                    return self.hash_record
            except Exception as error:
                OutputFormatter.print_error(f"加载哈希记录失败: {error}")
        return {}
    
    def save_hash_record(self, hash_record: Dict[str, str]):
        """将哈希记录保存到JSON文件"""
        try:
            FileUtils.ensure_directory_exists(os.path.dirname(HASH_RECORD_FILE))
            with open(HASH_RECORD_FILE, "w", encoding="utf-8") as file:
                json.dump(hash_record, file, indent=2, ensure_ascii=False)
            OutputFormatter.print_success("哈希记录保存成功")
        except Exception as error:
            OutputFormatter.print_error(f"保存哈希记录失败: {error}")
    
    def load_path_cache(self) -> Dict[str, List[Dict[str, str]]]:
        """从JSON文件加载路径缓存"""
        if os.path.exists(PATH_CACHE_FILE):
            try:
                with open(PATH_CACHE_FILE, "r", encoding="utf-8") as file:
                    self.path_cache = json.load(file)
                    OutputFormatter.print_info(f"加载路径缓存成功，包含 {len(self.path_cache)} 个设备的缓存")
                    
                    for device, paths in self.path_cache.items():
                        OutputFormatter.print_info(f"  {device}: {len(paths)} 个路径")
                    return self.path_cache
            except Exception as error:
                OutputFormatter.print_error(f"加载路径缓存失败: {error}")
        else:
            OutputFormatter.print_info("未找到路径缓存文件")
        return {}
    
    def save_path_cache(self, path_cache: Dict[str, List[Dict[str, str]]]):
        """将路径缓存保存到JSON文件"""
        try:
            FileUtils.ensure_directory_exists(os.path.dirname(PATH_CACHE_FILE))
            with open(PATH_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(path_cache, file, indent=2, ensure_ascii=False)
            
            total_paths = sum(len(paths) for paths in path_cache.values())
            OutputFormatter.print_success(f"路径缓存已保存，包含 {len(path_cache)} 个设备的 {total_paths} 个路径")
        except Exception as error:
            OutputFormatter.print_error(f"保存路径缓存失败: {error}")
    
    def verify_cached_paths(self, path_cache: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
        """验证缓存的路径是否仍然有效"""
        valid_paths = {}
        total_checked = 0
        total_valid = 0
        
        for device, paths in path_cache.items():
            valid_paths[device] = []
            for path_info in paths:
                total_checked += 1
                path = path_info["path"]
                
                if os.path.exists(path):
                    valid_paths[device].append(path_info)
                    total_valid += 1
                else:
                    OutputFormatter.print_warning(f"缓存路径已失效: {path}")
        
        OutputFormatter.print_info(f"路径缓存验证完成: {total_valid}/{total_checked} 个路径有效")
        return valid_paths