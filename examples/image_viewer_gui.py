"""PyQt5を使用したgRPC画像ビューアー。"""

import argparse
import sys
import threading

from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from image_server.server_grpc import ImageStreamClient


class StreamWorker(QObject):
    frame_received = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, client, topic):
        QObject.__init__(self)
        self._client = client
        self._topic = topic
        self._stop = threading.Event()

    def run(self):
        try:
            self._client.start_stream()
            for _payload, frame in self._client.iter_frames(self._topic):
                if self._stop.is_set():
                    break
                self.frame_received.emit(frame)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            try:
                self._client.stop_stream()
            except Exception:
                pass
            self.finished.emit()

    def stop(self):
        self._stop.set()


class ImageViewerWindow(QMainWindow):
    def __init__(self, server_ip, port, topic):
        QMainWindow.__init__(self)
        self.setWindowTitle("grpc_frame Image Viewer")
        self.resize(960, 720)
        self._worker = None
        self._thread = None
        self._client = None

        self._ip = QLineEdit(server_ip)
        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(port)
        self._topic = QLineEdit(topic)
        self._connect_button = QPushButton("Connect / Start")
        self._stop_button = QPushButton("Stop")
        self._status = QLabel("Disconnected")
        self._image = QLabel("No image")
        self._image.setAlignment(Qt.AlignCenter)
        self._image.setMinimumSize(640, 480)

        top = QHBoxLayout()
        top.addWidget(QLabel("IP"))
        top.addWidget(self._ip)
        top.addWidget(QLabel("Port"))
        top.addWidget(self._port)
        top.addWidget(QLabel("Topic"))
        top.addWidget(self._topic)
        top.addWidget(self._connect_button)
        top.addWidget(self._stop_button)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self._status)
        layout.addWidget(self._image, 1)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._connect_button.clicked.connect(self.start_stream)
        self._stop_button.clicked.connect(self.stop_stream)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_status)
        self._timer.start(1000)

    def start_stream(self):
        self.stop_stream()
        self._client = ImageStreamClient(
            self._ip.text().strip(),
            self._port.value(),
            5.0,
        )
        self._worker = StreamWorker(
            self._client,
            self._topic.text().strip(),
        )
        self._worker.frame_received.connect(self.display_frame)
        self._worker.error.connect(self.show_error)
        self._thread = threading.Thread(target=self._worker.run)
        self._thread.daemon = True
        self._thread.start()
        self._status.setText("Streaming")

    def stop_stream(self):
        if self._worker is not None:
            self._worker.stop()
        if self._client is not None:
            try:
                self._client.stop_stream()
            except Exception:
                pass
            close = getattr(self._client, "close", None)
            if callable(close):
                close()
        self._worker = None
        self._thread = None
        self._client = None
        self._status.setText("Stopped")

    def display_frame(self, frame):
        rgb = frame[:, :, ::-1].copy()
        height, width, channels = rgb.shape
        image = QImage(
            rgb.data,
            width,
            height,
            channels * width,
            QImage.Format_RGB888,
        ).copy()
        pixmap = QPixmap.fromImage(image)
        self._image.setPixmap(
            pixmap.scaled(
                self._image.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def refresh_status(self):
        if self._client is None:
            return
        try:
            status = self._client.get_status()
            self._status.setText(
                "stream={} camera={} frame={} errors={}".format(
                    status.get("stream_running"),
                    status.get("camera_id"),
                    status.get("frame_id"),
                    status.get("read_error_count"),
                )
            )
        except Exception as exc:
            self._status.setText(str(exc))

    def show_error(self, message):
        self._status.setText("Error: {}".format(message))

    def closeEvent(self, event):
        self.stop_stream()
        event.accept()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--topic", default="camera.frame")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = ImageViewerWindow(
        args.server_ip,
        args.port,
        args.topic,
    )
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
