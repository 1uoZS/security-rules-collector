"""
安全设备规则文件收集工具 - 主程序入口
模块化版本，支持本地和Docker设备规则采集
"""
import os
import sys
import shutil

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config.settings import DOCKER_TEMP_DIR, OUTPUT_DIR
from core.collector import RulesCollector
from utils.output_formatter import OutputFormatter

def clear_cache():
    """清除所有缓存记录，强制下次全量扫描"""
    OutputFormatter.print_header("清除缓存")
    files_removed = 0
    
    cache_files = [
        os.path.join(OUTPUT_DIR, "file_hashes.json"),
        os.path.join(OUTPUT_DIR, "path_cache.json")
    ]
    
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            OutputFormatter.print_info(f"已删除: {cache_file}")
            files_removed += 1
    
    # 清理Docker临时目录
    if os.path.exists(DOCKER_TEMP_DIR):
        shutil.rmtree(DOCKER_TEMP_DIR)
        OutputFormatter.print_info(f"已删除: {DOCKER_TEMP_DIR}")
        files_removed += 1
    
    if files_removed == 0:
        OutputFormatter.print_warning("未找到缓存文件")
    else:
        OutputFormatter.print_success(f"成功删除 {files_removed} 个缓存文件和目录")

def show_help():
    """显示帮助信息"""
    OutputFormatter.print_header("安全设备规则文件收集工具 - 帮助")
    print(f"{OutputFormatter.Colors.BOLD}使用方法:{OutputFormatter.Colors.ENDC}")
    print("  python3 main.py [选项]")
    print(f"\n{OutputFormatter.Colors.BOLD}选项:{OutputFormatter.Colors.ENDC}")
    print("  --force        强制全量扫描，忽略缓存")
    print("  --clear-cache  清除所有缓存文件")
    print("  --help         显示此帮助信息")
    
    # 显示支持的设备
    collector = RulesCollector()
    devices = collector.device_manager.get_all_devices()
    print(f"\n{OutputFormatter.Colors.BOLD}支持的设备:{OutputFormatter.Colors.ENDC}")
    for device_name, device_config in devices.items():
        device_type = "Docker" if device_config.type == "docker" else "本地"
        if device_config.type == "docker":
            print(f"  • {device_name} ({device_type}: {device_config.container})")
        else:
            print(f"  • {device_name} ({device_type})")

def main():
    """主程序入口点"""
    if len(sys.argv) > 1:
        argument = sys.argv[1]
        
        if argument == "--force":
            collector = RulesCollector()
            collector.collect_rules(force_rescan=True)
        elif argument == "--clear-cache":
            clear_cache()
        elif argument == "--help":
            show_help()
        else:
            OutputFormatter.print_error(f"未知参数: {argument}")
            print("使用 --help 查看可用选项")
            sys.exit(1)
    else:
        # 默认运行模式：智能增量扫描
        collector = RulesCollector()
        collector.collect_rules(force_rescan=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "="*50)
        OutputFormatter.print_error("用户中断执行")
        print("="*50)
        sys.exit(1)
    except Exception as error:
        print("\n\n" + "="*50)
        OutputFormatter.print_error(f"程序执行出错: {error}")
        print("="*50)
        sys.exit(1)
    finally:
        # 无论是否出错，都清理临时目录
        if os.path.exists(DOCKER_TEMP_DIR):
            try:
                shutil.rmtree(DOCKER_TEMP_DIR)
                OutputFormatter.print_info("已清理临时目录")
            except Exception:
                pass