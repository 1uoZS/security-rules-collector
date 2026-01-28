"""
文件操作模块
负责文件搜索、处理和复制操作
"""
import os
from typing import List, Tuple, Dict  # 添加类型导入
from tqdm import tqdm

from config.settings import OUTPUT_DIR
from models.data_models import FileTarget
from utils.output_formatter import OutputFormatter
from utils.file_utils import FileUtils

class FileOperations:
    """文件操作类"""
    
    @staticmethod
    def search_rule_files(patterns: List[str], base_paths: List[str]) -> List[str]:
        """搜索规则文件"""
        found_paths = FileUtils.search_files(patterns, base_paths)
        
        if found_paths:
            OutputFormatter.print_info(f"找到 {len(found_paths)} 个匹配项")
        
        return found_paths
    
    @staticmethod
    def process_found_items(
        found_items: List[str], 
        device_name: str, 
        file_extension: str
    ) -> List[FileTarget]:
        """处理找到的项目并转换为文件目标，并精确计算相对路径"""
        targets = []
        
        # 定义 Zeek 策略的根路径模式（用于计算相对路径的锚点）
        # 确保与设备配置中使用的路径模式一致。这里我们假设要从 'policy/' 之后开始计算相对路径
        # 注意：使用 lower() 避免大小写问题，但 Zeek 路径通常是小写
        # 使用 policy/ 来定位起始点，而不是 /zeek/share/zeek/policy/
        ANCHOR_PATTERN = "policy"
        
        for item in found_items:
            files = []
            
            if os.path.isfile(item) and item.lower().endswith(f".{file_extension.lower()}"):
                # --- 模式1: 处理精确文件路径 (如 Zeek) ---
                
                # 寻找目标文件在路径中的位置
                # 找到 "policy/" 在路径中的索引
                try:
                    anchor_index = item.lower().find(ANCHOR_PATTERN.lower())
                    
                    if anchor_index != -1:
                        # 相对路径 = 'policy/' 结束后的所有字符
                        # + 1 是为了跳过 'y'
                        # + 1 是为了跳过路径分隔符 '/' 或 '\'
                        policy_end_index = anchor_index + len(ANCHOR_PATTERN) + 1 
                        destination_relative = item[policy_end_index:]
                        
                        # 确保路径被规范化 (例如，Windows路径转为 /)
                        destination_relative = destination_relative.replace(os.sep, '/')
                        
                        if destination_relative:
                             files.append((item, destination_relative))
                        else:
                            OutputFormatter.print_error(f"无法计算文件 {item} 的有效相对目标路径。")
                    else:
                        OutputFormatter.print_warning(f"警告: 文件 {item} 未包含预期锚点 '{ANCHOR_PATTERN}'，将其视为根文件。")
                        files.append((item, os.path.basename(item))) # 备选方案
                except Exception as e:
                    OutputFormatter.print_error(f"处理精确文件路径时出错: {e}")


            elif os.path.isdir(item):
                # --- 模式2: 处理目录路径 (如 Suricata, Snort) ---
                # 沿用原有的递归遍历目录逻辑
                try:
                    files = FileUtils.enumerate_directory_files(item, file_extension)
                except Exception as e:
                    OutputFormatter.print_error(f"遍历目录 {item} 时出错: {e}")
            
            else:
                # 跳过不匹配文件类型或不存在的文件/目录
                continue
            
            for source_path, destination_relative in files:
                # 检查是否已存在相同源路径的目标 (保持不变)
                if any(target.src == source_path for target in targets):
                    continue
                    
                targets.append(FileTarget(
                    src=source_path,
                    device=device_name,
                    dest_rel=destination_relative,
                    cached=False,
                    from_docker=False
                ))
                
        return targets
    
    @staticmethod
    def calculate_file_hashes(targets: List[FileTarget], old_hash_record: Dict[str, str]) -> Tuple[Dict[str, str], List[FileTarget], int]:
        """计算文件哈希并检测变化"""
        new_hash_record = {}
        changed_files = []
        unchanged_count = 0
        
        hash_progress = tqdm(
            total=len(targets), 
            desc="计算文件哈希", 
            unit="文件", 
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
        )
        
        for target in targets:
            source_path = target.src
            file_hash = FileUtils.calculate_file_hash(source_path)
            
            if file_hash:
                new_hash_record[source_path] = file_hash
                
                if (source_path in old_hash_record and 
                    old_hash_record[source_path] == file_hash):
                    unchanged_count += 1
                else:
                    changed_files.append(target)
            
            hash_progress.update(1)
        
        hash_progress.close()
        
        return new_hash_record, changed_files, unchanged_count
    
    @staticmethod
    def copy_changed_files(changed_files: List[FileTarget]) -> List[str]:
        """复制变化的文件到目标目录"""
        copied_files = []
        
        if not changed_files:
            OutputFormatter.print_info("所有文件均未发生变化，无需复制。")
            return copied_files
        
        copy_progress = tqdm(
            total=len(changed_files), 
            desc="复制文件", 
            unit="文件",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
        )
        
        for target in changed_files:
            source_path = target.src
            device_name = target.device
            destination_relative = target.dest_rel
            
            copy_progress.set_postfix({
                "device": device_name[:10], 
                "file": (os.path.basename(source_path)[:20] + '...' 
                        if len(os.path.basename(source_path)) > 20 
                        else os.path.basename(source_path))
            })
            
            destination_base = os.path.join(OUTPUT_DIR, device_name)
            destination_path = os.path.join(destination_base, destination_relative)
            FileUtils.ensure_directory_exists(os.path.dirname(destination_path))
            
            if FileUtils.safe_copy(source_path, destination_path):
                copied_files.append(destination_path)
            
            copy_progress.update(1)
        
        copy_progress.close()
        return copied_files