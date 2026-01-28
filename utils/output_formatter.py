"""
输出格式化模块
负责控制台输出的颜色和格式
"""
from typing import Dict, Any  # 添加这行导入
from config.settings import Colors

class OutputFormatter:
    """输出格式化器"""
    
    @staticmethod
    def print_header(text: str):
        """打印主标题"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    
    @staticmethod
    def print_section(text: str):
        """打印章节标题"""
        print(f"\n{Colors.BOLD}{Colors.GREEN}▶ {text}{Colors.ENDC}")
    
    @staticmethod
    def print_info(text: str):
        """打印普通信息"""
        print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {text}")
    
    @staticmethod
    def print_warning(text: str):
        """打印警告信息"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {text}")
    
    @staticmethod
    def print_error(text: str):
        """打印错误信息"""
        print(f"{Colors.RED}[ERROR]{Colors.ENDC} {text}")
    
    @staticmethod
    def print_success(text: str):
        """打印成功信息"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {text}")
    
    @staticmethod
    def print_step(step: int, total: int, text: str):
        """打印步骤进度信息"""
        print(f"[{step}/{total}] {text}")
    
    @staticmethod
    def format_table(data: Dict[str, Any], title: str = "扫描结果") -> str:
        """格式化表格输出 - 极简版（只有上下线，不带冒号）"""
        # 计算最大键长度
        max_key_len = max(len(key) for key in data.keys())
        
        # 计算最大值的字符串长度
        max_value_len = max(len(str(value)) for value in data.values())
        
        # 表格宽度 = 键部分 + 值部分 + 间距
        table_width = max_key_len + max_value_len + 6    # 6是间距
        
        lines = []
        lines.append(f"{Colors.BOLD}{title}:{Colors.ENDC}")
        
        # 上划线
        lines.append("  " + "─" * table_width)
        
        # 数据行
        for key, value in data.items():
            # 键部分：左对齐到最大键长度
            key_part = key.ljust(max_key_len)
            # 值部分：右对齐到最大值长度
            value_part = str(value).rjust(max_value_len)
            lines.append(f"  {key_part} {value_part}")
        
        # 下划线
        lines.append("  " + "─" * table_width)
        
        return "\n".join(lines)