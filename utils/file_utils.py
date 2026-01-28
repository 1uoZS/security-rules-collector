"""
文件工具模块
提供文件操作相关的工具函数
"""
import os
import glob
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any  # 确保导入所有需要的类型

class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> Optional[str]:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as error:
            from utils.output_formatter import OutputFormatter
            OutputFormatter.print_error(f"计算文件哈希失败: {file_path}: {error}")
            return None
    
    @staticmethod
    def search_files(patterns: List[str], base_paths: List[str]) -> List[str]:
        """在指定基础路径中搜索匹配模式的文件或目录"""
        found_paths = []
        for base_path in base_paths:
            for pattern in patterns:
                full_pattern = os.path.join(base_path, pattern.lstrip("/"))
                try:
                    matches = glob.glob(full_pattern, recursive=True)
                except Exception as error:
                    from utils.output_formatter import OutputFormatter
                    OutputFormatter.print_error(f"搜索模式失败 {full_pattern}: {error}")
                    matches = []
                
                for match in matches:
                    if os.path.exists(match):
                        abs_path = os.path.abspath(match)
                        if abs_path not in found_paths:
                            found_paths.append(abs_path)
        
        return found_paths
    
    @staticmethod
    def enumerate_directory_files(directory_path: str, file_extension: str = "") -> List[Tuple[str, str]]:
        """枚举目录中的所有文件"""
        result = []
        
        # 处理单个文件
        if os.path.isfile(directory_path):
            filename = os.path.basename(directory_path)
            if not file_extension or filename.lower().endswith("." + file_extension.lower()):
                result.append((os.path.abspath(directory_path), filename))
            return result
        
        # 处理目录，递归遍历所有文件
        for root_dir, _, files in os.walk(directory_path):
            relative_root = os.path.relpath(root_dir, directory_path)
            
            for filename in files:
                if file_extension and not filename.lower().endswith("." + file_extension.lower()):
                    continue
                
                source_path = os.path.join(root_dir, filename)
                
                if relative_root == ".":
                    destination_relative = filename
                else:
                    destination_relative = os.path.join(relative_root, filename)
                
                result.append((os.path.abspath(source_path), destination_relative))
        
        return result
    
    @staticmethod
    def ensure_directory_exists(directory_path: str):
        """确保目录存在，如果不存在则创建"""
        os.makedirs(directory_path, exist_ok=True)
    
    @staticmethod
    def safe_copy(source: str, destination: str) -> bool:
        """安全复制文件，使用临时文件避免损坏"""
        temp_path = destination + ".tmp"
        try:
            import shutil
            shutil.copy2(source, temp_path)
            os.replace(temp_path, destination)
            return True
        except Exception as error:
            from utils.output_formatter import OutputFormatter
            OutputFormatter.print_error(f"复制失败: {source} -> {destination}: {error}")
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            return False