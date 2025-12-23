# Rust 跨平台构建工具

一个基于 Python 的构建工具，用于将 Rust crates.io 上的工具编译为多个目标平台，并支持自动压缩打包。

## 功能特性

- 🚀 支持编译多个 Rust 工具到不同目标平台
- 📦 易于扩展：只需在配置文件中添加新工具
- 🎯 支持多个目标平台（Windows GNU/MSVC、Linux x86_64/aarch64）
- 🗜️ 灵活的压缩配置：支持多种压缩格式（zip、7z、tar.gz、tar.xz、tar.bz2）
- 📥 支持从 GitHub releases 下载预编译文件
- 🐍 使用 Python 脚本管理构建任务，简单高效
- 📋 自动生成清单文件（manifest.json）

## 支持的工具

当前配置的工具：
- `flamegraph` - 性能分析工具
- `grcov` - 代码覆盖率工具
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
   
   # 如果需要创建 7z 压缩文件，需要安装 py7zr 包
   pip install py7zr
   ```

## 使用方法

### 完整工作流程

典型的构建流程包括以下步骤：

1. **安装目标工具链**
   ```bash
   python build.py install-targets
   ```

2. **编译工具**
   ```bash
   # 编译所有工具到所有平台
   python build.py build-all
   
   # 或只编译 Windows 平台
   python build.py build-windows
   
   # 或只编译 Linux 平台
   python build.py build-non-windows
   ```

3. **后处理（压缩打包）**
   ```bash
   python post.py
   ```

4. **下载预编译文件（可选）**
   ```bash
   python download.py
   ```

### 编译命令

#### 查看可用命令

```bash
python build.py --help
```

#### 编译单个工具到指定目标

```bash
python build.py build <tool-name> <target>
```

示例：
```bash
python build.py build flamegraph x86_64-pc-windows-msvc
python build.py build cargo-audit x86_64-unknown-linux-gnu
```

#### 编译指定工具到所有目标平台

```bash
python build.py build-tool <tool-name>
```

示例：
```bash
python build.py build-tool flamegraph
```

#### 编译所有工具到指定目标平台

```bash
python build.py build-target <target>
```

示例：
```bash
python build.py build-target x86_64-pc-windows-msvc
```

#### 编译所有工具到所有目标平台

```bash
python build.py build-all
```

#### 编译所有工具到 Windows 平台

```bash
python build.py build-windows
```

此命令只编译 Windows 目标平台（`x86_64-pc-windows-gnu` 和 `x86_64-pc-windows-msvc`），适合在 Windows 平台上使用，避免交叉编译 Linux 目标时可能遇到的问题。

#### 编译所有工具到非 Windows 平台（Linux）

```bash
python build.py build-non-windows
```

此命令只编译 Linux 目标平台（`aarch64-unknown-linux-gnu` 和 `x86_64-unknown-linux-gnu`），适合在 Linux 平台上使用，避免交叉编译 Windows 目标时可能遇到的问题。

#### 列出所有工具和目标平台

```bash
python build.py list
```

#### 清理编译输出

```bash
python build.py clean
```

### 后处理脚本

`post.py` 脚本用于处理编译后的二进制文件，根据 `config/tools.toml` 中的配置决定是否压缩以及使用什么压缩格式。

```bash
python post.py
```

脚本会：
- 读取 `config/tools.toml` 中的压缩配置
- 根据配置为每个工具创建压缩文件
- 生成 `manifest.json` 清单文件，包含所有工具和文件的元数据

### 下载脚本

`download.py` 脚本用于从 GitHub releases 下载预编译文件。

```bash
# 下载所有配置项
python download.py

# 下载指定项
python download.py rust-analyzer

# 列出所有配置项
python download.py --list
```

下载配置在 `config/download.toml` 中定义。

## 配置文件

### tools.toml - 工具编译配置

`config/tools.toml` 文件定义了要编译的工具及其配置：

```toml
[tools]
# 性能分析工具（启用压缩）
flamegraph = { version = "latest", compress = true, windows_format = "zip", non_windows_format = "tar.xz" }

# 代码覆盖率工具（不压缩）
grcov = { version = "latest" }

# 模糊测试工具（不压缩）
cargo-fuzz = { version = "latest" }

# 安全审计工具（启用压缩）
cargo-audit = { version = "latest", compress = true, windows_format = "zip", non_windows_format = "tar.xz" }
```

#### 压缩配置选项

- `compress` (布尔值，默认 `false`): 是否压缩工具文件
  - `true`: 启用压缩
  - `false`: 不压缩（默认）

- `windows_format` (字符串，默认 `"zip"`): Windows 相关 target 的压缩格式
  - `"zip"`: ZIP 格式（默认）
  - `"7z"`: 7Z 格式（需要 `py7zr` 库）

- `non_windows_format` (字符串，默认 `"tar.gz"`): 非 Windows 相关 target 的压缩格式
  - `"tar.gz"`: gzip 压缩的 tar 文件（默认）
  - `"tar.xz"`: xz 压缩的 tar 文件
  - `"tar.bz2"`: bzip2 压缩的 tar 文件

#### 示例配置

```toml
# 不压缩
tool1 = { version = "latest" }

# 压缩，使用默认格式（Windows: zip, Linux: tar.gz）
tool2 = { version = "latest", compress = true }

# 压缩，自定义格式
tool3 = { 
    version = "latest", 
    compress = true, 
    windows_format = "7z", 
    non_windows_format = "tar.xz" 
}

# 指定版本
tool4 = { version = "1.2.3", compress = true }
```

### download.toml - 下载配置

`config/download.toml` 文件定义了要从 GitHub releases 下载的文件：

```toml
[downloads.rust-analyzer]
repo = "rust-lang/rust-analyzer"
file = "rust-analyzer-win32-x64.vsix"
output_dir = "rust-analyzer"
method = "date"  # date, tag, 或 latest
date = "2025-12-15"
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
grcov = { version = "latest" }
cargo-fuzz = { version = "latest" }
cargo-audit = { version = "latest" }
# 添加新工具
ripgrep = { version = "latest" }
```

或者指定特定版本和压缩配置：

```toml
ripgrep = { 
    version = "13.0.0", 
    compress = true, 
    windows_format = "zip", 
    non_windows_format = "tar.gz" 
}
```

添加后，新工具会自动被所有编译命令识别。

## 输出目录结构

编译后的文件会输出到以下目录结构：

```
dist/
├── flamegraph/
│   ├── x86_64-pc-windows-gnu/
│   │   ├── flamegraph.exe
│   │   ├── cargo-flamegraph.exe
│   │   └── flamegraph.zip          # 如果启用了压缩
│   ├── x86_64-pc-windows-msvc/
│   │   ├── flamegraph.exe
│   │   ├── cargo-flamegraph.exe
│   │   └── flamegraph.zip
│   ├── aarch64-unknown-linux-gnu/
│   │   ├── flamegraph
│   │   ├── cargo-flamegraph
│   │   └── flamegraph.tar.xz       # 如果启用了压缩
│   └── x86_64-unknown-linux-gnu/
│       ├── flamegraph
│       ├── cargo-flamegraph
│       └── flamegraph.tar.xz
├── grcov/
│   └── ...
├── cargo-fuzz/
│   └── ...
├── cargo-audit/
│   └── ...
└── manifest.json                   # 自动生成的清单文件
```

**注意**: 
- 某些工具（如 `flamegraph`）会安装多个二进制文件。例如 `cargo install flamegraph` 会安装 `flamegraph` 和 `cargo-flamegraph` 两个二进制文件，脚本会自动检测并复制所有相关的二进制文件。
- 如果工具配置了 `compress = true`，`post.py` 脚本会自动创建压缩文件。
- Windows 平台的二进制文件会有 `.exe` 扩展名。

## 使用 Justfile（可选）

如果安装了 `just` 命令运行器，可以使用以下快捷命令：

```bash
# 安装工具链
just iat          # 安装所有工具链
just iwt          # 安装 Windows 工具链
just inwt         # 安装非 Windows 工具链

# 编译
just ba           # 编译所有
just bw           # 编译 Windows
just bnw          # 编译非 Windows

# 后处理
just post         # 运行后处理脚本

# 下载
just download     # 下载预编译文件

# 清理
just clean        # 清理 dist 目录
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

### Q: 如何配置压缩？

A: 在 `config/tools.toml` 中为工具添加压缩配置：
```toml
# 启用压缩，使用默认格式
tool = { version = "latest", compress = true }

# 自定义压缩格式
tool = { 
    version = "latest", 
    compress = true, 
    windows_format = "7z", 
    non_windows_format = "tar.xz" 
}
```

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

### Q: 如何创建 7z 格式的压缩文件？

A: 需要安装 `py7zr` 库：
```bash
pip install py7zr
```

然后在配置中指定 `windows_format = "7z"`。如果未安装 `py7zr`，脚本会自动回退到 zip 格式。

### Q: manifest.json 是什么？

A: `manifest.json` 是 `post.py` 脚本自动生成的清单文件，包含所有工具、版本、目标平台和文件列表的元数据。可以用于：
- 追踪构建的版本和文件
- 自动化部署和分发
- 生成下载页面或文档

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！
