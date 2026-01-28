"""
验证工具模块
提供各种验证功能
"""
def validate_file_path(file_path: str) -> bool:
    """验证文件路径是否存在"""
    import os
    return os.path.exists(file_path)

def validate_directory_path(directory_path: str) -> bool:
    """验证目录路径是否存在"""
    import os
    return os.path.exists(directory_path) and os.path.isdir(directory_path)