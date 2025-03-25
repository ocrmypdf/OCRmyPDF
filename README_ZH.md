# OCRmyPDF 中文说明

我将为您创建一个中文版的 README.md 文件。以下是基于原始英文版本的中文翻译：

```markdown:/Users/huapai/PycharmProjects/OCRmyPDF/README.md
<!-- SPDX-FileCopyrightText: 2014 Julien Pfefferkorn -->
<!-- SPDX-FileCopyrightText: 2015 James R. Barlow -->
<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->

<img src="docs/images/logo.svg" width="240" alt="OCRmyPDF">

[![构建状态](https://github.com/ocrmypdf/OCRmyPDF/actions/workflows/build.yml/badge.svg)](https://github.com/ocrmypdf/OCRmyPDF/actions/workflows/build.yml) [![PyPI 版本][pypi]](https://pypi.org/project/ocrmypdf/) ![Homebrew 版本][homebrew] ![ReadTheDocs][docs] ![Python 版本][pyversions]

[pypi]: https://img.shields.io/pypi/v/ocrmypdf.svg "PyPI 版本"
[homebrew]: https://img.shields.io/homebrew/v/ocrmypdf.svg "Homebrew 版本"
[docs]: https://readthedocs.org/projects/ocrmypdf/badge/?version=latest "RTD"
[pyversions]: https://img.shields.io/pypi/pyversions/ocrmypdf "支持的 Python 版本"

OCRmyPDF 为扫描的 PDF 文件添加 OCR 文本层，使其可以被搜索或复制粘贴。

```bash
ocrmypdf                      # 这是一个可脚本化的命令行程序
   -l eng+fra                 # 支持多种语言
   --rotate-pages             # 可以修正旋转错误的页面
   --deskew                   # 可以校正倾斜的 PDF！
   --title "My PDF"           # 可以更改输出元数据
   --jobs 4                   # 默认使用多核心处理
   --output-type pdfa         # 默认生成 PDF/A 格式
   input_scanned.pdf          # 接受 PDF 输入（或图像）
   output_searchable.pdf      # 生成经过验证的 PDF 输出
```

[查看发布说明了解最新变更的详情](https://ocrmypdf.readthedocs.io/en/latest/release_notes.html)。

## 主要特点

- 从普通 PDF 生成可搜索的 [PDF/A](https://en.wikipedia.org/?title=PDF/A) 文件
- 准确地将 OCR 文本放置在图像下方，便于复制/粘贴
- 保持原始嵌入图像的精确分辨率
- 在可能的情况下，以"无损"操作方式插入 OCR 信息，不破坏任何其他内容
- 优化 PDF 图像，通常生成比输入文件更小的文件
- 如果需要，在执行 OCR 前对图像进行校正和/或清理
- 验证输入和输出文件
- 在所有可用的 CPU 核心上分配工作
- 使用 [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) 引擎识别超过 [100 种语言](https://github.com/tesseract-ocr/tessdata)
- 保护您的私人数据安全
- 适当扩展以处理包含数千页的文件
- 在数百万 PDF 上经过实战测试

<img src="misc/screencast/demo.svg" alt="终端会话中的 OCRmyPDF 演示">

详情请参阅[文档](https://ocrmypdf.readthedocs.io/en/latest/)。

## 开发动机

我在网上搜索免费的命令行工具来对 PDF 文件进行 OCR：我找到了很多，但没有一个真正令人满意：

- 要么它们生成的 PDF 文件中文本位置错误（使复制/粘贴变得不可能）
- 要么它们不处理重音和多语言字符
- 要么它们改变了嵌入图像的分辨率
- 要么它们生成了体积巨大的 PDF 文件
- 要么它们在尝试 OCR 时崩溃
- 要么它们不生成有效的 PDF 文件
- 最重要的是，它们都不生成 PDF/A 文件（专为长期存储设计的格式）

...所以我决定开发自己的工具。

## 安装

支持 Linux、Windows、macOS 和 FreeBSD。Docker 镜像也可用，同时支持 x64 和 ARM。

| 操作系统                     | 安装命令                      |
| --------------------------- | ----------------------------- |
| Debian, Ubuntu              | ``apt install ocrmypdf``      |
| Windows Subsystem for Linux | ``apt install ocrmypdf``      |
| Fedora                      | ``dnf install ocrmypdf``      |
| macOS (Homebrew)            | ``brew install ocrmypdf``     |
| macOS (MacPorts)            | ``port install ocrmypdf``     |
| macOS (nix)                 | ``nix-env -i ocrmypdf``       |
| LinuxBrew                   | ``brew install ocrmypdf``     |
| FreeBSD                     | ``pkg install py-ocrmypdf``   |
| Ubuntu Snap                 | ``snap install ocrmypdf``     |

对于其他用户，[请参阅我们的文档](https://ocrmypdf.readthedocs.io/en/latest/installation.html)了解安装步骤。

## 语言

OCRmyPDF 使用 Tesseract 进行 OCR，并依赖其语言包。对于 Linux 用户，您通常可以找到提供语言包的软件包：

```bash
# 显示所有 Tesseract 语言包的列表
apt-cache search tesseract-ocr

# Debian/Ubuntu 用户
apt-get install tesseract-ocr-chi-sim  # 示例：安装中文简体语言包

# Arch Linux 用户
pacman -S tesseract-data-eng tesseract-data-deu # 示例：安装英语和德语语言包

# brew macOS 用户
brew install tesseract-lang
```

然后，您可以向 OCRmyPDF 传递 `-l LANG` 参数，提示它应该搜索哪些语言。可以请求多种语言。

OCRmyPDF 支持 Tesseract 4.1.1+。它会自动使用在 `PATH` 环境变量中首先找到的版本。在 Windows 上，如果 `PATH` 不提供 Tesseract 二进制文件，我们会根据 Windows 注册表使用已安装的最高版本号。

## 文档和支持

安装 OCRmyPDF 后，可以通过以下方式访问内置帮助，解释命令语法和选项：

```bash
ocrmypdf --help
```

我们的[文档托管在 Read the Docs 上](https://ocrmypdf.readthedocs.io/en/latest/index.html)。

请在我们的 [GitHub issues](https://github.com/ocrmypdf/OCRmyPDF/issues) 页面上报告问题，并遵循问题模板以获得快速响应。

## 功能演示

```bash
# 添加 OCR 层并转换为 PDF/A
ocrmypdf input.pdf output.pdf

# 将图像转换为单页 PDF
ocrmypdf input.jpg output.pdf

# 就地为文件添加 OCR（仅在成功时修改文件）
ocrmypdf myfile.pdf myfile.pdf

# 使用非英语语言进行 OCR（查找您语言的 ISO 639-3 代码）
ocrmypdf -l fra LeParisien.pdf LeParisien.pdf

# OCR 多语言文档
ocrmypdf -l eng+fra Bilingual-English-French.pdf Bilingual-English-French.pdf

# 校正（矫正倾斜的页面）
ocrmypdf --deskew input.pdf output.pdf
```

更多功能，请参阅[文档](https://ocrmypdf.readthedocs.io/en/latest/index.html)。

## 要求

除了所需的 Python 版本外，OCRmyPDF 还需要外部程序安装 Ghostscript 和 Tesseract OCR。OCRmyPDF 是纯 Python 编写的，几乎可以在所有平台上运行：Linux、macOS、Windows 和 FreeBSD。

## 媒体报道

- [使用 OCRmyPDF 实现无纸化](https://medium.com/@ikirichenko/going-paperless-with-ocrmypdf-e2f36143f46a)
- [将扫描文档转换为带有编辑的压缩可搜索 PDF](https://medium.com/@treyharris/converting-a-scanned-document-into-a-compressed-searchable-pdf-with-redactions-63f61c34fe4c)
- [c't 1-2014, 第 59 页](https://heise.de/-2279695)：在德国领先的 IT 杂志 c't 中详细介绍 OCRmyPDF v1.0
- [heise Open Source, 09/2014: 使用 OCRmyPDF 进行文本识别](https://heise.de/-2356670)
- [heise 使用 OCRmyPDF 创建可搜索的 PDF 文档](https://www.heise.de/ratgeber/Durchsuchbare-PDF-Dokumente-mit-OCRmyPDF-erstellen-4607592.html)
- [优秀实用工具：OCRmyPDF](https://www.linuxlinks.com/excellent-utilities-ocrmypdf-add-ocr-text-layer-scanned-pdfs/)
- [LinuxUser 使用 OCRmyPDF 和 Scanbd 自动化文本识别](https://www.linux-community.de/ausgaben/linuxuser/2021/06/texterkennung-mit-ocrmypdf-und-scanbd-automatisieren/)
- [Y Combinator 讨论](https://news.ycombinator.com/item?id=32028752)

## 商业咨询

如果没有公司和用户选择为功能开发和咨询提供支持，OCRmyPDF 就不会成为今天的软件。我们很乐意讨论所有咨询，无论是扩展现有功能集，还是将 OCRmyPDF 集成到更大的系统中。

## 许可证

OCRmyPDF 软件根据 Mozilla 公共许可证 2.0 (MPL-2.0) 授权。此许可证允许将 OCRmyPDF 与其他代码集成，包括商业和闭源代码，但要求您发布对 OCRmyPDF 所做的源代码级修改。

OCRmyPDF 的某些组件有其他许可证，如标准 SPDX 许可证标识符或 DEP5 版权和许可信息文件所示。一般来说，非核心代码根据 MIT 许可，文档和测试文件根据 Creative Commons ShareAlike 4.0 (CC-BY-SA 4.0) 许可。

## 免责声明

本软件按"原样"分发，不提供任何明示或暗示的保证或条件。

这份中文版 README.md 保留了原始文档的所有重要信息，包括功能介绍、安装说明、语言支持、使用示例等内容，同时保持了原始格式和结构。