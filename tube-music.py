#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
import re
import speedtest

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QProgressBar,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


# downloader worker
class DownloadWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, is_audio, output_dir):
        super().__init__()
        self.url = url
        self.is_audio = is_audio
        self.output_dir = output_dir

    def run(self):
        try:
            output_template = str(Path(self.output_dir) / "%(title)s.%(ext)s")

            if self.is_audio:
                cmd = [
                    "yt-dlp",
                    "-x",
                    "--audio-format",
                    "mp3",
                    "-o",
                    output_template,
                    self.url,
                ]
                mode = "audio"
            else:
                cmd = [
                    "yt-dlp",
                    "-f",
                    "bv*+ba/b",
                    "--merge-output-format",
                    "mp4",
                    "-o",
                    output_template,
                    self.url,
                ]
                mode = "video"

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            for line in process.stdout:
                line = line.strip()
                percent = self.parse_progress(line)
                if percent is not None:
                    self.progress.emit(percent, f"Downloading {mode}… {percent}%")

            process.wait()

            if process.returncode == 0:
                self.progress.emit(100, "Finalizing file…")
                self.finished.emit(True, "Download completed")
            else:
                self.finished.emit(False, "Download failed")

        except Exception as e:
            self.finished.emit(False, str(e))

    def parse_progress(self, line):
        match = re.search(r"\[download\]\s+(\d+(?:\.\d+)?)%", line)
        if match:
            return int(float(match.group(1)))
        return None


# internet speed worker
class SpeedTestWorker(QThread):
    finished = pyqtSignal(float, float, float, str)

    def run(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download = st.download(threads=1) / 1_000_000
            upload = st.upload(threads=1) / 1_000_000
            ping = st.results.ping

            rating = self.rate_speed(download)
            self.finished.emit(download, upload, ping, rating)

        except Exception:
            self.finished.emit(0, 0, 0, "Failed")

    def rate_speed(self, download):
        if download >= 25:
            return "Good"
        elif download >= 5:
            return "OK"
        return "Poor"


# main user interface
class YTDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tube Music Downloader")
        self.setFixedSize(520, 400)

        self.output_dir = None
        self.worker = None

        main = QVBoxLayout(self)

        title = QLabel("▶︎ •၊၊||၊|။|||||\nYT Downloader")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("TitleLabel")
        main.addWidget(title)

        main.addWidget(QLabel("YouTube URL"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here")
        main.addWidget(self.url_input)

        mode = QHBoxLayout()
        self.audio_radio = QRadioButton("MP3 (Audio)")
        self.video_radio = QRadioButton("MP4 (Video)")
        self.audio_radio.setChecked(True)
        mode.addWidget(self.audio_radio)
        mode.addWidget(self.video_radio)
        main.addLayout(mode)

        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("📁 No folder selected")
        self.folder_btn = QPushButton("Select Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_btn)
        main.addLayout(folder_layout)

        buttons = QHBoxLayout()
        self.download_btn = QPushButton("Download")
        self.clear_btn = QPushButton("Clear")
        self.download_btn.clicked.connect(self.start_download)
        self.clear_btn.clicked.connect(self.clear_all)
        buttons.addWidget(self.download_btn)
        buttons.addWidget(self.clear_btn)
        main.addLayout(buttons)

        self.speed_btn = QPushButton("Test Internet Speed")
        self.speed_btn.clicked.connect(self.start_speed_test)
        main.addWidget(self.speed_btn)

        self.speed_label = QLabel("🌐 Speed: Not tested")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.speed_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        main.addWidget(self.progress)

        self.status = QLabel("Ready")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size:14pt; font-weight:bold; color:#00e5ff")
        main.addWidget(self.status)

        self.setStyleSheet(self.style())

    def style(self):
        return """
        QWidget {
            background:#0b0f14;
            color:#e6e6e6;
            font-family: Segoe UI;
        }
        #TitleLabel {
            font-size:22pt;
            font-weight:bold;
            color:#00e5ff;
        }
        QPushButton {
            padding:8px;
            font-weight:bold;
        }
        QProgressBar::chunk {
            background:#00e5ff;
        }
        """

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir = folder
            self.folder_label.setText(folder)

    def update_progress(self, value, text):
        self.progress.setValue(value)
        self.status.setText(text)

    def start_download(self):
        url = self.url_input.text().strip()

        if not url:
            QMessageBox.critical(self, "Error", "Enter a YouTube URL")
            return
        if not self.output_dir:
            QMessageBox.critical(self, "Error", "Select output folder")
            return

        self.download_btn.setDisabled(True)
        self.clear_btn.setDisabled(True)
        self.progress.setValue(0)
        self.status.setText("Starting download…")

        self.worker = DownloadWorker(url, self.audio_radio.isChecked(), self.output_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.start()

    def download_finished(self, success, message):
        self.status.setText(message)
        self.download_btn.setDisabled(False)
        self.clear_btn.setDisabled(False)

        if not success:
            QMessageBox.critical(self, "Download Failed", message)

    def start_speed_test(self):
        self.speed_btn.setDisabled(True)
        self.speed_label.setText("Testing internet speed…")

        self.speed_worker = SpeedTestWorker()
        self.speed_worker.finished.connect(self.speed_test_finished)
        self.speed_worker.start()

    def speed_test_finished(self, down, up, ping, rating):
        if rating == "Failed":
            self.speed_label.setText("Speed test failed")
        else:
            self.speed_label.setText(
                f"Ping {ping:.0f} ms | Down {down:.1f} Mbps | Up {up:.1f} Mbps | {rating}"
            )
        self.speed_btn.setDisabled(False)

    def clear_all(self):
        self.url_input.clear()
        self.progress.setValue(0)
        self.status.setText("Idle")


# entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = YTDownloader()
    win.show()
    sys.exit(app.exec())
