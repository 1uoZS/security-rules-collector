"""
主收集器模块
协调各个模块完成规则收集任务
"""
import os
import time
import datetime
from typing import Dict, List

from config.settings import SCAN_ORDER_PRIORITY, OUTPUT_DIR, DOCKER_TEMP_DIR
from config.device_config import DeviceConfigManager
from config.data_models import DeviceConfig  # 从新的数据模型导入
from models.data_models import FileTarget, CollectionResult
from utils.output_formatter import OutputFormatter
from utils.file_utils import FileUtils
from .cache_manager import CacheManager
from .file_operations import FileOperations
from .docker_operations import DockerOperations

class RulesCollector:
    """规则收集器主类"""
    
    def __init__(self):
        self.device_manager = DeviceConfigManager()
        self.cache_manager = CacheManager()
        self.output_formatter = OutputFormatter()
    
    def collect_rules(self, force_rescan: bool = False) -> CollectionResult:
        """收集规则文件的主函数"""
        start_time = time.time()
        
        # 打印启动信息
        self._print_startup_info(force_rescan)
        
        # 确保输出目录存在
        FileUtils.ensure_directory_exists(OUTPUT_DIR)
        FileUtils.ensure_directory_exists(DOCKER_TEMP_DIR)
        
        # 阶段1: 加载缓存数据
        old_hash_record, path_cache = self._load_cache_data()
        
        # 阶段2: 缓存验证和路径扫描决策
        use_cache, verified_cache = self._decide_scan_strategy(force_rescan, path_cache)
        
        # 阶段3: 扫描规则文件
        all_targets = self._scan_rule_files(use_cache, verified_cache)
        
        if not all_targets:
            OutputFormatter.print_warning("未找到匹配文件。")
            return CollectionResult()
        
        # 阶段4: 统计信息
        stats = self._calculate_statistics(all_targets)
        self._print_discovery_stats(stats)
        
        # 阶段5: 哈希计算和变化检测
        new_hash_record, changed_files, unchanged_count = FileOperations.calculate_file_hashes(
            all_targets, old_hash_record
        )
        
        # 阶段6: 复制变化的文件
        copied_files = FileOperations.copy_changed_files(changed_files)
        
        # 阶段7: 保存缓存和生成报告
        self._save_cache_data(new_hash_record)
        
        # 阶段8: 生成最终结果
        result = self._generate_final_result(
            start_time, stats, len(all_targets), unchanged_count, 
            len(changed_files), copied_files
        )
        
        self._print_final_report(result)
        return result
    
    def _print_startup_info(self, force_rescan: bool):
        """打印启动信息"""
        OutputFormatter.print_header("安全设备规则文件采集工具")
        OutputFormatter.print_info(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        OutputFormatter.print_info(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
        OutputFormatter.print_info(f"扫描模式: {'强制全量扫描' if force_rescan else '智能增量扫描'}")
    
    def _load_cache_data(self) -> tuple:
        """加载缓存数据"""
        OutputFormatter.print_section("加载缓存数据")
        old_hash_record = self.cache_manager.load_hash_record()
        path_cache = self.cache_manager.load_path_cache()
        return old_hash_record, path_cache
    
    def _decide_scan_strategy(self, force_rescan: bool, path_cache: dict) -> tuple:
        """决定扫描策略"""
        use_cache = not force_rescan and path_cache
        
        if use_cache:
            OutputFormatter.print_section("验证缓存路径")
            verified_cache = self.cache_manager.verify_cached_paths(path_cache)
            
            has_valid_cache = any(len(paths) > 0 for paths in verified_cache.values())
            if has_valid_cache:
                OutputFormatter.print_info("使用验证后的缓存路径")
                return True, verified_cache
            else:
                OutputFormatter.print_warning("无有效缓存路径，执行全量扫描")
        
        return False, {}
    
    def _scan_rule_files(self, use_cache: bool, verified_cache: dict) -> List[FileTarget]:
        """扫描规则文件"""
        OutputFormatter.print_section("扫描规则文件")
        
        all_targets = []
        new_path_cache = {}
        devices = self.device_manager.get_all_devices()
        
        for device_index, (device_name, device_config) in enumerate(devices.items(), 1):
            OutputFormatter.print_step(device_index, len(devices), f"处理设备: {device_name}")
            new_path_cache[device_name] = []
            
            if device_config.type == "docker":
                # Docker设备处理
                docker_files = DockerOperations.collect_from_docker_container(
                    device_config.container,
                    device_config.path,
                    device_name,
                    device_config.file_type
                )
                all_targets.extend(docker_files)
            else:
                # 本地设备处理
                device_targets = self._process_local_device(
                    device_name, device_config, use_cache, verified_cache, new_path_cache
                )
                all_targets.extend(device_targets)
        
        # 保存新的路径缓存
        self.cache_manager.save_path_cache(new_path_cache)
        
        # 去重处理
        return self._deduplicate_targets(all_targets)
    
    def _process_local_device(
        self, 
        device_name: str, 
        device_config: DeviceConfig,
        use_cache: bool,
        verified_cache: dict,
        new_path_cache: dict
    ) -> List[FileTarget]:
        """处理本地设备"""
        targets = []
        cached_targets = []
        
        # 策略1: 使用缓存路径
        if use_cache and device_name in verified_cache and verified_cache[device_name]:
            OutputFormatter.print_info(f"  使用缓存路径进行快速扫描...")
            cached_targets = self._process_cached_paths(
                device_name, verified_cache[device_name], new_path_cache
            )
        
        # 策略2: 完整路径搜索
        if (not use_cache or device_name not in verified_cache or not verified_cache[device_name]):
            found_items = self._search_device_paths(device_config)
            new_targets = FileOperations.process_found_items(
                found_items, device_name, device_config.file_type
            )
            targets.extend(new_targets)
            
            # 更新路径缓存
            for target in new_targets:
                new_path_cache[device_name].append({
                    "path": target.src,
                    "dest_rel": target.dest_rel
                })
        
        return cached_targets + targets
    
    def _process_cached_paths(self, device_name: str, cached_paths: list, new_path_cache: dict) -> List[FileTarget]:
        """处理缓存路径"""
        cached_targets = []
        
        for path_info in cached_paths:
            source_path = path_info["path"]
            destination_relative = path_info["dest_rel"]
            
            if os.path.exists(source_path):
                cached_targets.append(FileTarget(
                    src=source_path,
                    device=device_name,
                    dest_rel=destination_relative,
                    cached=True,
                    from_docker=False
                ))
                new_path_cache[device_name].append({
                    "path": source_path,
                    "dest_rel": destination_relative
                })
        
        return cached_targets
    
    def _search_device_paths(self, device_config: DeviceConfig) -> List[str]:
        """搜索设备路径"""
        found_items = []
        
        for description, search_paths in SCAN_ORDER_PRIORITY:
            OutputFormatter.print_info(f"    扫描{description} ...")
            matched_items = FileOperations.search_rule_files(
                device_config.relative_path, search_paths
            )
            
            if matched_items:
                found_items.extend(matched_items)
                OutputFormatter.print_info(f"    在{description}找到 {len(matched_items)} 个项目")
                break
        
        # 如果常见路径没找到，尝试全盘扫描
        if not found_items:
            OutputFormatter.print_warning(f"  未在常见路径找到 {device_config.name}，全盘扫描中...")
            matched_items = FileOperations.search_rule_files(device_config.relative_path, ["/"])
            
            if matched_items:
                found_items.extend(matched_items)
                OutputFormatter.print_info(f"  全盘扫描找到 {len(matched_items)} 个项目")
        
        return found_items
    
    def _deduplicate_targets(self, targets: List[FileTarget]) -> List[FileTarget]:
        """目标文件去重"""
        seen_source_paths = set()
        unique_targets = []
        
        for target in targets:
            if target.src not in seen_source_paths:
                unique_targets.append(target)
                seen_source_paths.add(target.src)
        
        return unique_targets
    
    def _calculate_statistics(self, targets: List[FileTarget]) -> dict:
        """计算统计信息"""
        docker_files_count = sum(1 for target in targets if target.from_docker)
        local_files_count = len(targets) - docker_files_count
        cached_targets_count = sum(1 for target in targets if target.cached)
        new_targets_count = len(targets) - cached_targets_count
        
        return {
            "docker_files": docker_files_count,
            "local_files": local_files_count,
            "cached_targets": cached_targets_count,
            "new_targets": new_targets_count
        }
    
    def _print_discovery_stats(self, stats: dict):
        """打印发现统计"""
        OutputFormatter.print_success(
            f"找到 {stats['local_files'] + stats['docker_files']} 个唯一文件 "
            f"(本地: {stats['local_files']}, Docker: {stats['docker_files']}, "
            f"缓存: {stats['cached_targets']}, 新增: {stats['new_targets']})"
        )
    
    def _save_cache_data(self, new_hash_record: dict):
        """保存缓存数据"""
        OutputFormatter.print_section("保存缓存数据")
        self.cache_manager.save_hash_record(new_hash_record)
    
    def _generate_final_result(
        self, 
        start_time: float, 
        stats: dict, 
        total_files: int,
        unchanged_count: int,
        changed_count: int,
        copied_files: List[str]
    ) -> CollectionResult:
        """生成最终结果"""
        end_time = time.time()
        execution_time = end_time - start_time
        
        return CollectionResult(
            total=total_files,
            copied=copied_files,
            unchanged=unchanged_count,
            changed=changed_count,
            local_files=stats["local_files"],
            docker_files=stats["docker_files"],
            cached_paths_used=stats["cached_targets"],
            new_paths_found=stats["new_targets"],
            execution_time=execution_time,
            timestamp=datetime.datetime.now().isoformat()
        )
    
    def _print_final_report(self, result: CollectionResult):
        """打印最终报告"""
        OutputFormatter.print_section("扫描完成统计")
        
        table_data = {
            "总文件数": result.total,
            "本地文件": result.local_files,
            "Docker文件": result.docker_files,
            "使用缓存路径": result.cached_paths_used,
            "新发现路径": result.new_paths_found,
            "变化文件": result.changed,
            "未变文件": result.unchanged,
            "成功复制": len(result.copied),
            "执行时间": f"{result.execution_time:.2f} 秒"
        }
        
        print(OutputFormatter.format_table(table_data))
        OutputFormatter.print_info(f"结束时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        OutputFormatter.print_success("规则文件收集完成！")