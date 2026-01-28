"""
Docker操作模块
负责与Docker容器的交互操作
"""
import os
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any  # 添加类型导入
from dataclasses import dataclass

from config.settings import DOCKER_TEMP_DIR
from models.data_models import FileTarget, DockerContainerInfo
from utils.output_formatter import OutputFormatter
from utils.file_utils import FileUtils

class DockerOperations:
    """Docker容器操作类"""
    
    @staticmethod
    def run_docker_command(command: List[str], capture: bool = False) -> Tuple[int, str, str]:
        """执行Docker命令并返回结果"""
        try:
            process = subprocess.run(
                command, 
                stdout=subprocess.PIPE if capture else None,
                stderr=subprocess.PIPE if capture else None,
                text=True, 
                shell=False
            )
            stdout = process.stdout if capture else ""
            stderr = process.stderr if capture else ""
            return process.returncode, stdout, stderr
        except Exception as error:
            OutputFormatter.print_error(f"执行Docker命令失败: {error}")
            return -1, "", str(error)
    
    @staticmethod
    def resolve_container_id(container_identifier: str) -> Optional[str]:
        """解析容器ID或名称"""
        # 首先尝试直接inspect
        returncode, stdout, _ = DockerOperations.run_docker_command(
            ["docker", "inspect", "--format={{.Id}}", container_identifier], 
            capture=True
        )
        if returncode == 0 and stdout.strip():
            return stdout.strip()
        
        # 尝试通过名称过滤
        returncode, stdout, _ = DockerOperations.run_docker_command(
            ["docker", "ps", "-aq", "--filter", f"name={container_identifier}"], 
            capture=True
        )
        if returncode == 0 and stdout.strip():
            lines = stdout.strip().splitlines()
            if lines:
                return lines[0].strip()
        
        return None
    
    @staticmethod
    def get_container_info(container_identifier: str) -> Optional[DockerContainerInfo]:
        """获取容器信息"""
        resolved_id = DockerOperations.resolve_container_id(container_identifier)
        if not resolved_id:
            return None
        
        # 检查容器状态
        returncode, stdout, _ = DockerOperations.run_docker_command(
            ["docker", "inspect", "--format={{.State.Status}}", resolved_id], 
            capture=True
        )
        is_running = returncode == 0 and stdout.strip() == "running"
        
        return DockerContainerInfo(
            container_id=container_identifier,
            is_running=is_running,
            resolved_id=resolved_id
        )
    
    @staticmethod
    def path_exists_in_container(container: str, path: str) -> bool:
        """检查容器内路径是否存在"""
        returncode, _, _ = DockerOperations.run_docker_command(
            ["docker", "exec", container, "test", "-e", path], 
            capture=True
        )
        return returncode == 0
    
    @staticmethod
    def copy_directory_from_container(container: str, source_path: str, destination_path: str) -> bool:
        """从容器复制目录到本地"""
        try:
            FileUtils.ensure_directory_exists(destination_path)
            
            OutputFormatter.print_info(f"复制目录: {container}:{source_path} -> {destination_path}")
            returncode, _, stderr = DockerOperations.run_docker_command(
                ["docker", "cp", f"{container}:{source_path}/.", destination_path], 
                capture=True
            )
            
            if returncode != 0:
                OutputFormatter.print_error(f"docker cp 目录失败: {stderr.strip()}")
                return False
                
            # 检查是否真的复制了文件
            if not any(Path(destination_path).iterdir()):
                OutputFormatter.print_warning("目录复制后为空，可能源目录不存在或为空")
                return False
                
            return True
        except Exception as error:
            OutputFormatter.print_error(f"docker cp 目录异常: {error}")
            return False
    
    @staticmethod
    def extract_directory_using_tar(container: str, source_path: str, destination_path: str) -> bool:
        """使用tar流从容器提取目录"""
        try:
            FileUtils.ensure_directory_exists(destination_path)
            OutputFormatter.print_info(f"使用tar流复制: {container}:{source_path} -> {destination_path}")
            
            # 构建tar命令
            command = [
                "docker", "exec", container, "tar", "czf", "-", 
                "-C", os.path.dirname(source_path) if source_path != '/' else '/', 
                os.path.basename(source_path) if source_path != '/' else '.'
            ]
            
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                try:
                    with tarfile.open(fileobj=process.stdout, mode='r|gz') as tar:
                        tar.extractall(path=destination_path)
                except tarfile.ReadError as error:
                    OutputFormatter.print_error(f"tar解压错误: {error}")
                    process.terminate()
                    return False
                
                _, stderr = process.communicate(timeout=30)
                if process.returncode != 0:
                    stderr_text = stderr.decode('utf-8', errors='ignore') if isinstance(stderr, bytes) else str(stderr)
                    OutputFormatter.print_error(f"tar流复制失败: {stderr_text}")
                    return False
                    
            return True
        except subprocess.TimeoutExpired:
            OutputFormatter.print_error("tar流复制超时")
            process.terminate()
            return False
        except Exception as error:
            OutputFormatter.print_error(f"tar流复制异常: {error}")
            return False
    
    @staticmethod
    def collect_from_docker_container(
        container_identifier: str, 
        source_path: str, 
        device_name: str, 
        file_extension: str = ""
    ) -> List[FileTarget]:
        """从Docker容器采集规则文件"""
        # 解析容器信息
        container_info = DockerOperations.get_container_info(container_identifier)
        if not container_info:
            OutputFormatter.print_error(f"未找到容器: {container_identifier}")
            return []
        
        OutputFormatter.print_info(f"容器解析为 ID: {container_info.resolved_id}")
        
        # 检查容器状态
        if not container_info.is_running:
            OutputFormatter.print_error(f"容器未运行: {container_info.resolved_id}")
            return []
        
        # 检查源路径是否存在
        if not DockerOperations.path_exists_in_container(container_info.resolved_id, source_path):
            OutputFormatter.print_error(f"容器内路径不存在: {source_path}")
            return []
        
        # 准备目标路径
        short_id = container_info.resolved_id[:12]
        temp_destination = os.path.join(DOCKER_TEMP_DIR, device_name, short_id)
        
        # 确保目标目录干净
        if os.path.exists(temp_destination):
            shutil.rmtree(temp_destination)
        FileUtils.ensure_directory_exists(temp_destination)
        
        # 尝试多种复制方法
        methods = [
            ("docker cp 目录", lambda: DockerOperations.copy_directory_from_container(
                container_info.resolved_id, source_path, temp_destination)),
            ("tar 流复制", lambda: DockerOperations.extract_directory_using_tar(
                container_info.resolved_id, source_path, temp_destination)),
        ]
        
        success = False
        last_error = ""
        
        for method_name, method_function in methods:
            OutputFormatter.print_info(f"尝试方法: {method_name}")
            if method_function():
                success = True
                break
            else:
                last_error = f"{method_name} 失败"
                OutputFormatter.print_warning(last_error)
        
        if not success:
            OutputFormatter.print_error(f"所有复制方法均失败: {last_error}")
            return []
        
        # 验证复制结果
        if not any(Path(temp_destination).iterdir()):
            OutputFormatter.print_error(f"复制后目标目录为空: {temp_destination}")
            return []
        
        OutputFormatter.print_success(f"Docker规则已采集到临时目录: {temp_destination}")
        
        # 枚举采集到的文件
        collected_files = []
        for root, dirs, files in os.walk(temp_destination):
            for file in files:
                # 文件类型过滤
                if file_extension and not file.lower().endswith(f".{file_extension.lower()}"):
                    continue
                    
                source_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(source_file_path, temp_destination)
                
                collected_files.append(FileTarget(
                    src=source_file_path,
                    device=device_name,
                    dest_rel=relative_path,
                    cached=False,
                    from_docker=True
                ))
        
        return collected_files