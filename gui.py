import sys
import os
import subprocess
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit, QMessageBox,
    QCheckBox, QComboBox, QSpinBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import QThread, pyqtSignal, QUrl, Qt
from PyQt6.QtGui import QFontMetrics, QDesktopServices

# 获取虚拟环境的 Python 解释器路径
VENV_PYTHON = os.path.join('.venv', 'bin', 'python')
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = os.path.join('.venv', 'Scripts', 'python.exe')
    if not os.path.exists(VENV_PYTHON):
        print("警告：无法找到虚拟环境中的 Python 解释器，将尝试使用当前解释器。")
        VENV_PYTHON = sys.executable

# Dictionary mapping display names to Tesseract language codes (Expanded)
LANGUAGES = {
    "English": "eng",
    "简体中文": "chi_sim",
    "繁體中文": "chi_tra",
    "Français": "fra",
    "Deutsch": "deu",
    "Español": "spa",
    "日本語": "jpn",
    "한국어": "kor",
    "Русский": "rus",
    "Italiano": "ita",
    "Português": "por",
    "Nederlands": "nld",
    "Deutsch (Fraktur)": "deu_frak",
    "Uzbek (Cyrillic)": "uzb_cyrl",
    "Uzbek (Latin)": "uzb",
}

class WorkerThread(QThread):
    """后台运行 OCRmyPDF 的工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str, str)  # 新增：传递错误类型

    def __init__(self, input_file, output_file, options):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.options = options
        self.is_running = True

    def run(self):
        """执行 OCRmyPDF 命令"""
        command = [
            VENV_PYTHON,
            "-m",
            "ocrmypdf",
            self.input_file,
            self.output_file
        ]
        insert_pos = 3

        # Handle combined language string
        if self.options.get('language'):
            command.insert(insert_pos, '-l')
            command.insert(insert_pos + 1, self.options['language'])

        # Other options...
        if self.options.get('rotate'): command.insert(insert_pos, '-r')
        if self.options.get('deskew'): command.insert(insert_pos, '-d')
        if self.options.get('clean'): command.insert(insert_pos, '-c')
        if self.options.get('force_ocr'): command.insert(insert_pos, '-f')
        if self.options.get('skip_text'): command.insert(insert_pos, '-s')
        if self.options.get('output_type'):
            command.insert(insert_pos, '--output-type')
            command.insert(insert_pos + 1, self.options['output_type'])
        if self.options.get('optimize') is not None:
             optimize_level_text = self.options['optimize']
             optimize_level = '1'
             if "0" in optimize_level_text: optimize_level = '0'
             elif "2" in optimize_level_text: optimize_level = '2'
             elif "3" in optimize_level_text: optimize_level = '3'
             command.insert(insert_pos, '-O')
             command.insert(insert_pos + 1, optimize_level)

        self.progress.emit(f"正在处理 {os.path.basename(self.input_file)}...")
        self.progress.emit(f"命令: {' '.join(command)}\n")

        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')
            stdout_output = process.stdout
            stderr_output = process.stderr
            return_code = process.returncode

            output_message = "--- OCRmyPDF 输出 ---\n" + stdout_output
            output_message += "\n--- OCRmyPDF 错误 (如果有) ---\n" + stderr_output

            if return_code == 0:
                output_message += f"\n\n处理完成！输出文件保存在: {self.output_file}"
                self.finished.emit(output_message, self.output_file)
            else:
                output_message += f"\n\n处理失败，返回码: {return_code}"
                # 检测是否是语言包缺失错误
                if "does not have language data" in stderr_output:
                    missing_lang = self.extract_missing_language(stderr_output)
                    self.error.emit("missing_language", f"{output_message}\n\n缺失的语言包: {missing_lang}")
                else:
                    self.error.emit("other_error", output_message)
        except FileNotFoundError:
            self.error.emit("command_not_found", 
                f"错误：找不到命令 '{VENV_PYTHON}' 或 'ocrmypdf' 模块。\n请确保虚拟环境已正确激活，并且 ocrmypdf 已安装在其中。")
        except Exception as e:
            self.error.emit("unexpected_error", f"运行 OCRmyPDF 时发生意外错误: {e}")

    def extract_missing_language(self, error_text):
        """从错误信息中提取缺失的语言"""
        lines = error_text.split('\n')
        for line in lines:
            if "does not have language data" in line:
                return line.split(':')[-1].strip()
        return "未知语言"

    def install_language_package(self, language_code):
        """自动安装缺失的语言包"""
        import platform
        system = platform.system()
        
        # 标准化语言代码格式 (chi_sim -> chi-sim)
        install_lang = language_code.replace('_', '-')
        
        if system == "Darwin":  # macOS
            # 确保使用系统PATH查找brew
            cmd = f"PATH=$PATH:/usr/local/bin brew install tesseract-lang"
        elif system == "Linux":
            if os.path.exists("/etc/debian_version"):  # Debian/Ubuntu
                cmd = f"sudo apt-get install -y tesseract-ocr-{install_lang}"
            else:  # 其他Linux发行版
                cmd = f"sudo dnf install -y tesseract-langpack-{install_lang} || " \
                      f"sudo yum install -y tesseract-langpack-{install_lang} || " \
                      f"sudo zypper install -y tesseract-ocr-{install_lang}"
        elif system == "Windows":
            # 尝试使用winget安装
            cmd = f"winget install -e --id Tesseract-OCR.Tesseract --silent && " \
                  f"curl -L https://github.com/tesseract-ocr/tessdata/raw/main/{language_code}.traineddata " \
                  f"-o \"%ProgramFiles%\\Tesseract-OCR\\tessdata\\{language_code}.traineddata\""
        else:
            return False, "不支持的操作系统"

        try:
            self.progress.emit(f"正在安装语言包: {language_code}...")
            result = subprocess.run(cmd, shell=True, check=True, 
                                  capture_output=True, text=True)
            self.progress.emit(result.stdout)
            
            # 验证安装是否成功
            verify_cmd = f"tesseract --list-langs"
            verify_result = subprocess.run(verify_cmd, shell=True, 
                                         capture_output=True, text=True)
            if language_code in verify_result.stdout:
                return True, f"成功安装语言包: {language_code}"
            else:
                return False, f"安装后未检测到语言包: {language_code}"
        except subprocess.CalledProcessError as e:
            return False, f"安装失败: {e.stderr}"

    def stop(self):
        self.is_running = False

class OCRmyPDFApp(QWidget):
    def __init__(self):
        super().__init__()
        self.language_map = LANGUAGES
        self.setWindowTitle("OCRmyPDF 图形界面 (PyQt)")
        self.setGeometry(100, 100, 700, 600)  # 增加高度以容纳新按钮
        self.worker_thread = None
        self.init_ui()

    def init_ui(self):
        # [之前的UI代码保持不变...]
        # 在init_ui方法末尾添加帮助按钮
        help_button = QPushButton("安装语言包帮助")
        help_button.clicked.connect(self.show_language_help)
        layout.addWidget(help_button)

    def show_language_help(self):
        """显示语言包安装帮助"""
        help_text = """
        <h3>如何安装Tesseract语言包</h3>
        <p>根据你的操作系统选择安装方法:</p>
        <ul>
            <li><b>macOS (Homebrew):</b><br>
                <code>brew install tesseract-lang</code></li>
            <li><b>Ubuntu/Debian:</b><br>
                <code>sudo apt-get install tesseract-ocr-chi-sim</code></li>
            <li><b>Windows:</b><br>
                1. 下载语言包(.traineddata)从:<br>
                <a href='https://github.com/tesseract-ocr/tessdata'>https://github.com/tesseract-ocr/tessdata</a><br>
                2. 放入Tesseract安装目录的tessdata文件夹</li>
        </ul>
        <p>安装完成后请重启本程序。</p>
        """
        msg = QMessageBox()
        msg.setWindowTitle("语言包安装帮助")
        msg.setTextFormat(Qt.TextFormat.RichText)  # 设置为富文本格式
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def on_processing_error(self, error_type, error_message):
        """处理错误信息"""
        self.update_status(error_message)
        self.run_button.setEnabled(True)
        
        if error_type == "missing_language":
            # 提取语言代码
            lang_code = self.worker_thread.extract_missing_language(error_message)
            
            # 创建自定义对话框
            dialog = QMessageBox(self)
            dialog.setWindowTitle("语言包缺失")
            dialog.setText(f"缺少Tesseract语言包: {lang_code}")
            dialog.setInformativeText("是否尝试自动安装?")
            
            # 添加按钮
            install_button = dialog.addButton("自动安装", QMessageBox.ButtonRole.ActionRole)
            help_button = dialog.addButton("查看帮助", QMessageBox.ButtonRole.ActionRole)
            dialog.addButton(QMessageBox.StandardButton.Cancel)
            
            result = dialog.exec()
            
            if dialog.clickedButton() == install_button:
                # 创建安装线程
                self.install_thread = WorkerThread(None, None, None)
                self.install_thread.progress.connect(self.update_status)
                self.install_thread.finished.connect(lambda: QMessageBox.information(
                    self, "完成", "语言包安装完成，请重新运行OCR"))
                
                # 在lambda中捕获lang_code
                self.install_thread.run = lambda: self.install_thread.install_language_package(lang_code)
                self.install_thread.start()
                
            elif dialog.clickedButton() == help_button:
                self.show_language_help()
        else:
            QMessageBox.critical(self, "错误", "OCRmyPDF 处理失败。\n查看状态区域获取详细信息。")
        
        self.worker_thread = None

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # 输入文件选择
        input_layout = QHBoxLayout()
        self.input_label = QLabel("输入PDF文件:")
        self.input_path = QLineEdit()
        self.input_button = QPushButton("浏览...")
        self.input_button.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(self.input_button)
        layout.addLayout(input_layout)

        # 输出文件选择
        output_layout = QHBoxLayout()
        self.output_label = QLabel("输出PDF文件:")
        self.output_path = QLineEdit()
        self.output_button = QPushButton("浏览...")
        self.output_button.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_button)
        layout.addLayout(output_layout)

        # 选项区域
        options_layout = QGridLayout()
        
        # 语言选择
        self.language_label = QLabel("OCR语言:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(self.language_map.keys())
        options_layout.addWidget(self.language_label, 0, 0)
        options_layout.addWidget(self.language_combo, 0, 1)

        # 其他选项
        self.rotate_check = QCheckBox("自动旋转")
        self.deskew_check = QCheckBox("自动纠偏")
        self.clean_check = QCheckBox("清理图像")
        self.force_ocr_check = QCheckBox("强制OCR")
        self.skip_text_check = QCheckBox("跳过已有文本")
        
        self.output_type_combo = QComboBox()
        self.output_type_combo.addItems(["pdf", "pdfa", "pdfa-1", "pdfa-2", "pdfa-3"])
        self.output_type_label = QLabel("输出类型:")
        
        self.optimize_combo = QComboBox()
        self.optimize_combo.addItems(["不优化", "优化级别1", "优化级别2", "优化级别3"])
        self.optimize_label = QLabel("优化级别:")
        
        options_layout.addWidget(self.rotate_check, 1, 0)
        options_layout.addWidget(self.deskew_check, 1, 1)
        options_layout.addWidget(self.clean_check, 2, 0)
        options_layout.addWidget(self.force_ocr_check, 2, 1)
        options_layout.addWidget(self.skip_text_check, 3, 0)
        options_layout.addWidget(self.output_type_label, 4, 0)
        options_layout.addWidget(self.output_type_combo, 4, 1)
        options_layout.addWidget(self.optimize_label, 5, 0)
        options_layout.addWidget(self.optimize_combo, 5, 1)
        
        layout.addLayout(options_layout)

        # 状态显示
        self.status_area = QTextEdit()
        self.status_area.setReadOnly(True)
        layout.addWidget(self.status_area)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("开始处理")
        self.run_button.clicked.connect(self.run_ocrmypdf)
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_processing)
        
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # 帮助按钮
        help_button = QPushButton("安装语言包帮助")
        help_button.clicked.connect(self.show_language_help)
        layout.addWidget(help_button)

        self.setLayout(layout)

    def select_input_file(self):
        """选择输入PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择PDF文件", "", "PDF文件 (*.pdf)")
        if file_path:
            self.input_path.setText(file_path)
            # 自动设置输出文件名
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(os.path.dirname(file_path), f"{base_name}_ocr.pdf")
            self.output_path.setText(output_path)

    def select_output_file(self):
        """选择输出PDF文件"""
        file_path, _ = QFileDialog.getSaveFileName(self, "保存PDF文件", "", "PDF文件 (*.pdf)")
        if file_path:
            self.output_path.setText(file_path)

    def run_ocrmypdf(self):
        """启动OCR处理"""
        input_file = self.input_path.text()
        output_file = self.output_path.text()
        
        if not input_file or not output_file:
            QMessageBox.warning(self, "警告", "请选择输入和输出文件")
            return
            
        options = {
            'language': self.language_map[self.language_combo.currentText()],
            'rotate': self.rotate_check.isChecked(),
            'deskew': self.deskew_check.isChecked(),
            'clean': self.clean_check.isChecked(),
            'force_ocr': self.force_ocr_check.isChecked(),
            'skip_text': self.skip_text_check.isChecked(),
            'output_type': self.output_type_combo.currentText(),
            'optimize': self.optimize_combo.currentText()
        }
        
        self.worker_thread = WorkerThread(input_file, output_file, options)
        self.worker_thread.progress.connect(self.update_status)
        self.worker_thread.finished.connect(self.on_processing_finished)
        self.worker_thread.error.connect(self.on_processing_error)
        
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.worker_thread.start()

    def stop_processing(self):
        """停止当前处理"""
        if self.worker_thread:
            self.worker_thread.stop()
            self.update_status("处理已停止")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def update_status(self, message):
        """更新状态区域"""
        self.status_area.append(message)

    def on_processing_finished(self, message, output_file):
        """处理完成时的回调"""
        self.update_status(message)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker_thread = None

    def on_processing_error(self, error_type, error_message):
        """处理错误信息"""
        self.update_status(error_message)
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if error_type == "missing_language":
            dialog = QMessageBox(self)
            dialog.setWindowTitle("语言包缺失")
            dialog.setText("缺少必要的Tesseract语言包")
            dialog.setInformativeText("请安装所需的语言包后重试。")
            dialog.setDetailedText(error_message)
            
            help_button = dialog.addButton("查看安装帮助", QMessageBox.ButtonRole.ActionRole)
            dialog.addButton(QMessageBox.StandardButton.Ok)
            
            result = dialog.exec()
            if dialog.clickedButton() == help_button:
                self.show_language_help()
        else:
            QMessageBox.critical(self, "错误", "OCRmyPDF 处理失败。\n查看状态区域获取详细信息。")
        
        self.worker_thread = None

    def show_language_help(self):
        """显示语言包安装帮助"""
        help_text = """
        <h3>如何安装Tesseract语言包</h3>
        <p>根据你的操作系统选择安装方法:</p>
        <ul>
            <li><b>macOS (Homebrew):</b><br>
                <code>brew install tesseract-lang</code></li>
            <li><b>Ubuntu/Debian:</b><br>
                <code>sudo apt-get install tesseract-ocr-chi-sim</code></li>
            <li><b>Windows:</b><br>
                1. 下载语言包(.traineddata)从:<br>
                <a href='https://github.com/tesseract-ocr/tessdata'>https://github.com/tesseract-ocr/tessdata</a><br>
                2. 放入Tesseract安装目录的tessdata文件夹</li>
        </ul>
        <p>安装完成后请重启本程序。</p>
        """
        msg = QMessageBox()
        msg.setWindowTitle("语言包安装帮助")
        msg.setTextFormat(Qt.TextFormat.RichText)  # 设置为富文本格式
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OCRmyPDFApp()
    window.show()
    sys.exit(app.exec())
