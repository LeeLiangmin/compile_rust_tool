# Rust 跨平台编译工具

一个基于 Python 的编译工具，用于将 Rust crates.io 上的工具编译为多个目标平台。

## 功能特性

- 🚀 支持编译多个 Rust 工具到不同目标平台
- 📦 易于扩展：只需在配置文件中添加新工具
- 🎯 支持多个目标平台（Windows GNU/MSVC、Linux x86_64/aarch64）
- 🐍 使用 Python 脚本管理编译任务，简单高效

## 支持的工具

当前配置的工具：
- `flamegraph` - 性能分析工具
- `grov` - 代码搜索工具
- `cargo-fuzz` - 模糊测试工具
- `cargo-audit` - 安全审计工具

## 支持的目标平台

- `x86_64-pc-windows-gnu` - Windows (GNU工具链)
- `x86_64-pc-windows-msvc` - Windows (MSVC工具链)
- `aarch64-unknown-linux-gnu` - Linux ARM64
- `x86_64-unknown-linux-gnu` - Linux x86_64

## 前置要求

1. **Rust 工具链**
   ```bash
   # 安装 Rust (如果还没有安装)
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Python 3**
   - Python 3.11+ (内置 `tomllib`)
   - 或 Python 3.x + `toml` 包: `pip install toml`

3. **Rust 目标工具链**
   ```bash
   # 安装所有目标工具链
   python build.py install-targets
   
   # 或手动安装
   rustup target add x86_64-pc-windows-gnu
   rustup target add x86_64-pc-windows-msvc
   rustup target add aarch64-unknown-linux-gnu
   rustup target add x86_64-unknown-linux-gnu
   ```

4. **交叉编译链接器（必需）**
   
   为了进行交叉编译，需要安装相应的链接器工具链：
   
   **Linux (Ubuntu/Debian):**
   ```bash
   # 用于编译 aarch64-unknown-linux-gnu
   sudo apt-get install gcc-aarch64-linux-gnu
   
   # 用于编译 x86_64-pc-windows-gnu
   sudo apt-get install mingw-w64
   ```
   
   **Linux (RHEL/CentOS/Fedora):**
   ```bash
   # 用于编译 aarch64-unknown-linux-gnu
   sudo yum install gcc-aarch64-linux-gnu
   # 或
   sudo dnf install gcc-aarch64-linux-gnu
   
   # 用于编译 x86_64-pc-windows-gnu
   sudo yum install mingw64-gcc
   # 或
   sudo dnf install mingw64-gcc
   ```
   
   **注意:** 
   - `x86_64-unknown-linux-gnu` 目标使用系统默认的 gcc，无需额外安装
   - `x86_64-pc-windows-msvc` 目标需要在 Windows 系统上编译，或使用 wine + msvc 工具链

5. **Python 依赖（可选）**
   ```bash
   # 如果使用 Python < 3.11，需要安装 toml 包
   pip install toml
   ```

## 使用方法

### 查看可用命令

```bash
python build.py --help
```

### 编译单个工具到指定目标

```bash
python build.py build <tool-name> <target>
```

示例：
```bash
python build.py build flamegraph x86_64-pc-windows-msvc
python build.py build cargo-audit x86_64-unknown-linux-gnu
```

### 编译指定工具到所有目标平台

```bash
python build.py build-tool <tool-name>
```

示例：
```bash
python build.py build-tool flamegraph
```

### 编译所有工具到指定目标平台

```bash
python build.py build-target <target>
```

示例：
```bash
python build.py build-target x86_64-pc-windows-msvc
```

### 编译所有工具到所有目标平台

```bash
python build.py build-all
```

### 编译所有工具到 Windows 平台

```bash
python build.py build-windows
```

此命令只编译 Windows 目标平台（`x86_64-pc-windows-gnu` 和 `x86_64-pc-windows-msvc`），适合在 Windows 平台上使用，避免交叉编译 Linux 目标时可能遇到的问题。

### 编译所有工具到非 Windows 平台（Linux）

```bash
python build.py build-non-windows
```

此命令只编译 Linux 目标平台（`aarch64-unknown-linux-gnu` 和 `x86_64-unknown-linux-gnu`），适合在 Linux 平台上使用，避免交叉编译 Windows 目标时可能遇到的问题。

### 列出所有工具和目标平台

```bash
python build.py list
```

### 清理编译输出

```bash
python build.py clean
```

## 添加新工具

### 方法 1：使用命令行（推荐）

```bash
python build.py add-tool <tool-name>
```

示例：
```bash
python build.py add-tool ripgrep
```

### 方法 2：手动编辑配置文件

编辑 `config/tools.toml` 文件，在 `[tools]` 部分添加新工具：

```toml
[tools]
flamegraph = { version = "latest" }
grov = { version = "latest" }
cargo-fuzz = { version = "latest" }
cargo-audit = { version = "latest" }
# 添加新工具
ripgrep = { version = "latest" }
```

或者指定特定版本：

```toml
ripgrep = { version = "13.0.0" }
```

添加后，新工具会自动被所有编译命令识别。

## 输出目录结构

编译后的二进制文件会输出到以下目录结构：

```
dist/
├── flamegraph/
│   ├── x86_64-pc-windows-gnu/
│   │   └── flamegraph.exe
│   ├── x86_64-pc-windows-msvc/
│   │   └── flamegraph.exe
│   ├── aarch64-unknown-linux-gnu/
│   │   └── flamegraph
│   └── x86_64-unknown-linux-gnu/
│       └── flamegraph
├── grov/
│   └── ...
└── ...
```

## 常见问题

### Q: 编译失败，提示找不到工具链

A: 确保已安装相应的目标工具链：
```bash
python build.py install-targets
```

### Q: Python 报错找不到 tomllib

A: 如果使用 Python < 3.11，需要安装 `toml` 包：
```bash
pip install toml
```

### Q: 如何指定工具的特定版本？

A: 编辑 `config/tools.toml` 文件，修改对应工具的版本：
```toml
flamegraph = { version = "0.4.1" }
```

### Q: 编译后的二进制文件在哪里？

A: 默认在 `dist/{tool-name}/{target-triple}/` 目录下。Windows 平台的二进制文件会有 `.exe` 扩展名。

**注意**: 某些工具（如 `flamegraph`）会安装多个二进制文件。例如 `cargo install flamegraph` 会安装 `flamegraph` 和 `cargo-flamegraph` 两个二进制文件，脚本会自动检测并复制所有相关的二进制文件。

### Q: 如何只编译特定平台？

A: 有几种方式：
1. 使用 `python build.py build-target <target>` 编译所有工具到指定目标平台：
   ```bash
   python build.py build-target x86_64-pc-windows-msvc
   ```

2. 使用 `python build.py build-windows` 编译所有工具到所有 Windows 平台：
   ```bash
   python build.py build-windows
   ```

3. 使用 `python build.py build-non-windows` 编译所有工具到所有 Linux 平台：
   ```bash
   python build.py build-non-windows
   ```

### Q: 为什么需要分别构建 Windows 和非 Windows 平台？

A: 在 Windows 平台上交叉编译 Linux 目标（或反之）可能会遇到工具链配置问题。使用 `build-windows` 和 `build-non-windows` 命令可以：
- 在 Windows 平台上只编译 Windows 目标，避免 Linux 交叉编译的复杂性
- 在 Linux 平台上只编译 Linux 目标，避免 Windows 交叉编译的复杂性
- 提高编译成功率，减少配置问题

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

