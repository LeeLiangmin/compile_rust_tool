#!/usr/bin/env python3
"""
Rust 跨平台编译工具
使用 Python 脚本管理多个 Rust crate 的跨平台编译
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 目标平台列表
TARGETS = [
    "x86_64-pc-windows-gnu",
    "x86_64-pc-windows-msvc",
    "aarch64-unknown-linux-gnu",
    "x86_64-unknown-linux-gnu",
]

# Windows 目标平台列表
WINDOWS_TARGETS = [
    "x86_64-pc-windows-gnu",
    "x86_64-pc-windows-msvc",
]

# 非 Windows 目标平台列表（Linux）
NON_WINDOWS_TARGETS = [
    "aarch64-unknown-linux-gnu",
    "x86_64-unknown-linux-gnu",
]

# 输出目录
DIST_DIR = "dist"

# 配置文件路径
TOOLS_CONFIG = "config/tools.toml"


def load_tools_config():
    """加载 tools.toml 配置文件"""
    try:
        # 尝试使用 Python 3.11+ 的 tomllib
        import tomllib
        with open(TOOLS_CONFIG, 'rb') as f:
            return tomllib.load(f)
    except ImportError:
        try:
            # 尝试使用 toml 包
            import toml
            with open(TOOLS_CONFIG, 'r', encoding='utf-8') as f:
                return toml.load(f)
        except ImportError:
            print("错误: 需要 tomllib (Python 3.11+) 或 toml 包")
            print("安装 toml 包: pip install toml")
            sys.exit(1)


def save_tools_config(config):
    """保存 tools.toml 配置文件"""
    try:
        import tomli_w
        with open(TOOLS_CONFIG, 'wb') as f:
            tomli_w.dump(config, f)
    except ImportError:
        try:
            import toml
            with open(TOOLS_CONFIG, 'w', encoding='utf-8') as f:
                toml.dump(config, f)
        except ImportError:
            print("错误: 需要 tomli_w 或 toml 包来保存配置")
            print("安装 toml 包: pip install toml")
            sys.exit(1)


def get_tools():
    """获取工具列表"""
    config = load_tools_config()
    return list(config.get('tools', {}).keys())


def get_tool_version(tool):
    """获取工具版本"""
    config = load_tools_config()
    return config.get('tools', {}).get(tool, {}).get('version', 'latest')


def tool_exists(tool):
    """检查工具是否在配置中"""
    return tool in get_tools()


def get_output_dir(tool, target):
    """获取输出目录路径"""
    return Path(DIST_DIR) / tool / target


def get_exe_ext(target):
    """获取二进制文件扩展名"""
    if target.startswith('x86_64-pc-windows') or target.startswith('aarch64-pc-windows'):
        return '.exe'
    return ''


def get_cargo_bin():
    """获取 cargo bin 目录"""
    cargo_home = os.environ.get('CARGO_HOME', os.path.expanduser('~/.cargo'))
    return Path(cargo_home) / 'bin'


def get_installed_binaries(tool, target):
    """获取 cargo install 安装的所有二进制文件"""
    cargo_bin = get_cargo_bin()
    exe_ext = get_exe_ext(target)
    
    # 可能的二进制文件名列表
    # 1. 工具名本身 (如 flamegraph)
    # 2. cargo-工具名 (如 cargo-flamegraph)
    possible_names = [
        f"{tool}{exe_ext}",
        f"cargo-{tool}{exe_ext}",
    ]
    
    # 查找所有存在的二进制文件
    installed_binaries = []
    for name in possible_names:
        binary_path = cargo_bin / name
        if binary_path.exists():
            installed_binaries.append(name)
    
    # 如果没找到预期的二进制文件，尝试列出 cargo bin 目录中所有文件
    # 查找所有以工具名开头的文件
    if not installed_binaries:
        if cargo_bin.exists():
            for file in cargo_bin.iterdir():
                if file.is_file() and not file.suffix == '.d' and not file.suffix == '.pdb':
                    file_name = file.name
                    # 检查是否以工具名开头（忽略扩展名）
                    file_base = file_name.replace(exe_ext, '')
                    if file_base == tool or file_base == f"cargo-{tool}":
                        installed_binaries.append(file_name)
    
    return installed_binaries


def get_installed_version(tool):
    """获取已安装工具的实际版本"""
    try:
        # 方法1: 使用 cargo install --list
        result = run_command("cargo install --list", check=False, capture_output=True)
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.split('\n'):
                line = line.strip()
                # cargo install --list 输出格式: "tool_name v0.1.0:" 或 "cargo-tool_name v0.1.0:"
                if line.startswith(f"{tool} ") or line.startswith(f"cargo-{tool} "):
                    # 提取版本号
                    parts = line.split()
                    if len(parts) >= 2:
                        version = parts[1].rstrip(':')
                        if not version.startswith('v'):
                            version = f"v{version}"
                        return version
        
        # 方法2: 尝试运行二进制文件的 --version（先尝试 Windows 格式，再尝试 Linux 格式）
        cargo_bin = get_cargo_bin()
        
        # 尝试不同的扩展名
        for exe_ext in ['.exe', '']:
            binary_name = f"{tool}{exe_ext}"
            binary_path = cargo_bin / binary_name
            
            if not binary_path.exists():
                binary_name = f"cargo-{tool}{exe_ext}"
                binary_path = cargo_bin / binary_name
            
            if binary_path.exists():
                try:
                    result = run_command(f'"{binary_path}" --version', check=False, capture_output=True)
                    if result.returncode == 0 and result.stdout:
                        # 版本输出格式通常是 "tool_name 0.1.0" 或 "tool_name v0.1.0"
                        output = result.stdout.strip()
                        parts = output.split()
                        if len(parts) >= 2:
                            version = parts[-1]
                            if not version.startswith('v'):
                                version = f"v{version}"
                            return version
                except Exception:
                    continue
        
        return "unknown"
    except Exception as e:
        print(f"  警告: 无法获取版本信息: {e}")
        return "unknown"


def run_command(cmd, check=True, capture_output=False):
    """运行命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print(f"错误: 命令执行失败: {cmd}")
            print(f"返回码: {e.returncode}")
            sys.exit(1)
        return e


def build_tool(tool, target):
    """编译单个工具到指定目标平台"""
    print(f"正在编译 {tool} 到 {target}...")
    
    # 检查工具是否存在
    if not tool_exists(tool):
        print(f"错误: 工具 '{tool}' 在 tools.toml 中不存在")
        sys.exit(1)
    
    # 检查目标平台是否有效
    if target not in TARGETS:
        print(f"错误: 无效的目标平台 '{target}'")
        sys.exit(1)
    
    # 确保目标工具链已安装
    print(f"  检查目标工具链 {target}...")
    run_command(f"rustup target add {target}", check=False)
    
    # 获取版本
    version = get_tool_version(tool)
    version_flag = f"--version {version}" if version != "latest" else ""
    
    # 创建输出目录
    output_dir = get_output_dir(tool, target)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 编译工具
    print(f"  使用 cargo install 编译...")
    if version_flag:
        cmd = f"cargo install --target {target} {version_flag} {tool} --force"
    else:
        cmd = f"cargo install --target {target} {tool} --force"
    
    run_command(cmd)
    
    # 获取所有安装的二进制文件
    cargo_bin = get_cargo_bin()
    installed_binaries = get_installed_binaries(tool, target)
    
    if not installed_binaries:
        print(f"  ✗ 错误: 找不到任何二进制文件")
        print(f"    检查目录: {cargo_bin}")
        sys.exit(1)
    
    # 复制所有二进制文件到输出目录
    copied_files = []
    for binary_name in installed_binaries:
        source_binary = cargo_bin / binary_name
        if source_binary.exists():
            shutil.copy2(source_binary, output_dir / binary_name)
            copied_files.append(binary_name)
            print(f"  ✓ 复制 {binary_name} -> {output_dir / binary_name}")
    
    if copied_files:
        print(f"  ✓ 成功编译 {tool} 到 {target}，共 {len(copied_files)} 个二进制文件")
        
        # 获取实际安装的版本并保存到工具目录
        actual_version = get_installed_version(tool)
        tool_dir = get_output_dir(tool, target).parent
        version_file = tool_dir / "version"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(actual_version)
        print(f"  ✓ 版本信息: {actual_version} -> {version_file}")
    else:
        print(f"  ✗ 错误: 无法复制任何二进制文件")
        sys.exit(1)


def build_all():
    """编译所有工具到所有目标平台"""
    tools = get_tools()
    for tool in tools:
        for target in TARGETS:
            try:
                build_tool(tool, target)
            except SystemExit:
                print(f"  跳过 {tool} 的 {target} 编译")
                continue
    print("所有编译任务完成!")


def build_windows():
    """编译所有工具到 Windows 目标平台"""
    print("开始编译 Windows 平台...")
    tools = get_tools()
    for tool in tools:
        for target in WINDOWS_TARGETS:
            try:
                build_tool(tool, target)
            except SystemExit:
                print(f"  跳过 {tool} 的 {target} 编译")
                continue
    print("所有 Windows 平台编译任务完成!")


def build_non_windows():
    """编译所有工具到非 Windows 目标平台（Linux）"""
    print("开始编译非 Windows 平台（Linux）...")
    tools = get_tools()
    for tool in tools:
        for target in NON_WINDOWS_TARGETS:
            try:
                build_tool(tool, target)
            except SystemExit:
                print(f"  跳过 {tool} 的 {target} 编译")
                continue
    print("所有非 Windows 平台编译任务完成!")


def build_tool_all_targets(tool):
    """编译指定工具到所有目标平台"""
    if not tool_exists(tool):
        print(f"错误: 工具 '{tool}' 在 tools.toml 中不存在")
        sys.exit(1)
    
    for target in TARGETS:
        try:
            build_tool(tool, target)
        except SystemExit:
            print(f"  跳过 {tool} 的 {target} 编译")
            continue
    print(f"工具 {tool} 的所有目标平台编译完成!")


def build_target_all_tools(target):
    """编译所有工具到指定目标平台"""
    if target not in TARGETS:
        print(f"错误: 无效的目标平台 '{target}'")
        sys.exit(1)
    
    tools = get_tools()
    for tool in tools:
        try:
            build_tool(tool, target)
        except SystemExit:
            print(f"  跳过 {tool} 的 {target} 编译")
            continue
    print(f"所有工具在 {target} 平台的编译完成!")


def list_tools_and_targets():
    """列出所有工具和目标平台"""
    print("可用工具:")
    tools = get_tools()
    for tool in tools:
        version = get_tool_version(tool)
        print(f"  - {tool} (version: {version})")
    
    print("\n可用目标平台:")
    for target in TARGETS:
        print(f"  - {target}")


def clean():
    """清理编译输出目录"""
    dist_path = Path(DIST_DIR)
    if dist_path.exists():
        print(f"正在清理 {DIST_DIR} 目录...")
        shutil.rmtree(dist_path)
        print("清理完成!")
    else:
        print(f"{DIST_DIR} 目录不存在，无需清理")


def add_tool(tool_name):
    """添加新工具到配置文件"""
    if not tool_name:
        print("错误: 需要提供工具名称")
        print("用法: python build.py add-tool <tool-name>")
        sys.exit(1)
    
    # 检查工具是否已存在
    if tool_exists(tool_name):
        print(f"工具 '{tool_name}' 已存在于 tools.toml 中")
        return
    
    # 加载配置
    config = load_tools_config()
    
    # 添加新工具
    if 'tools' not in config:
        config['tools'] = {}
    config['tools'][tool_name] = {'version': 'latest'}
    
    # 保存配置
    save_tools_config(config)
    print(f"已添加工具 '{tool_name}' 到 tools.toml")


def install_targets():
    """安装所有目标工具链"""
    print("正在安装所有目标工具链...")
    for target in TARGETS:
        print(f"  安装 {target}...")
        run_command(f"rustup target add {target}", check=False)
    print("所有目标工具链安装完成!")


def main():
    parser = argparse.ArgumentParser(
        description='Rust 跨平台编译工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python build.py build flamegraph x86_64-pc-windows-msvc
  python build.py build-tool flamegraph
  python build.py build-target x86_64-pc-windows-msvc
  python build.py build-all
  python build.py build-windows      # 只编译 Windows 平台
  python build.py build-non-windows   # 只编译 Linux 平台
  python build.py list
  python build.py add-tool ripgrep
  python build.py clean
  python build.py install-targets
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # build 命令
    build_parser = subparsers.add_parser('build', help='编译指定工具到指定目标')
    build_parser.add_argument('tool', help='工具名称')
    build_parser.add_argument('target', help='目标平台')
    
    # build-all 命令
    subparsers.add_parser('build-all', help='编译所有工具到所有目标平台')
    
    # build-windows 命令
    subparsers.add_parser('build-windows', help='编译所有工具到 Windows 目标平台')
    
    # build-non-windows 命令
    subparsers.add_parser('build-non-windows', help='编译所有工具到非 Windows 目标平台（Linux）')
    
    # build-tool 命令
    build_tool_parser = subparsers.add_parser('build-tool', help='编译指定工具到所有目标平台')
    build_tool_parser.add_argument('tool', help='工具名称')
    
    # build-target 命令
    build_target_parser = subparsers.add_parser('build-target', help='编译所有工具到指定目标平台')
    build_target_parser.add_argument('target', help='目标平台')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有工具和目标平台')
    
    # clean 命令
    subparsers.add_parser('clean', help='清理编译输出目录')
    
    # add-tool 命令
    add_tool_parser = subparsers.add_parser('add-tool', help='添加新工具到配置文件')
    add_tool_parser.add_argument('tool', help='工具名称')
    
    # install-targets 命令
    subparsers.add_parser('install-targets', help='安装所有目标工具链')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # 执行对应命令
    if args.command == 'build':
        build_tool(args.tool, args.target)
    elif args.command == 'build-all':
        build_all()
    elif args.command == 'build-windows':
        build_windows()
    elif args.command == 'build-non-windows':
        build_non_windows()
    elif args.command == 'build-tool':
        build_tool_all_targets(args.tool)
    elif args.command == 'build-target':
        build_target_all_tools(args.target)
    elif args.command == 'list':
        list_tools_and_targets()
    elif args.command == 'clean':
        clean()
    elif args.command == 'add-tool':
        add_tool(args.tool)
    elif args.command == 'install-targets':
        install_targets()


if __name__ == '__main__':
    main()


