#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QClipboard, QPixmap, QImage
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QSpinBox,
    QComboBox,
    QSlider,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QGroupBox,
    QFormLayout,
)

from img2ascii import (
    image_to_ascii,
    image_to_colored,
    DEFAULT_RAMP,
    CHAT_RAMP_BLOCKS,
    CHAT_RAMP_CLASSIC,
    CHAT_RAMP_SAFE,
    apply_gamma,
)

PRESETS = {
    "iMessage":         (33, 18),
    "WhatsApp":         (36, 20),
    "Telegram":         (55, 28),
    "Discord (mobile)": (42, 22),
    "Discord (desktop)":(80, 40),
    "SMS":              (32, 15),
    "Twitter / X":      (40, 22),
}


class ASCIIArtConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_image: Optional[Image.Image] = None
        self._plain_ascii: str = ""
        self.setWindowTitle("Image to ASCII Art Converter")
        self.setMinimumSize(1200, 700)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Splitter for resizable columns
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left column: Image preview
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setText("No image loaded")
        self.image_label.setStyleSheet("border: 1px solid #666; background-color: #2b2b2b; color: #aaa;")
        left_layout.addWidget(self.image_label)

        self.upload_btn = QPushButton("Upload Image")
        self.upload_btn.clicked.connect(self.upload_image)
        left_layout.addWidget(self.upload_btn)

        splitter.addWidget(left_widget)

        # Right column: Controls and ASCII output
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # Controls group
        controls_group = QGroupBox("Conversion Settings")
        controls_layout = QFormLayout()
        controls_layout.setSpacing(10)

        # Preset dropdown
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Custom")
        for name in PRESETS:
            self.preset_combo.addItem(name)
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        controls_layout.addRow("Preset:", self.preset_combo)

        # Max Width
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(10, 500)
        self.max_width_spin.setValue(70)
        self.max_width_spin.valueChanged.connect(lambda: self.preset_combo.setCurrentIndex(0))
        self.max_width_spin.valueChanged.connect(self.on_setting_changed)
        controls_layout.addRow("Max Width:", self.max_width_spin)

        # Max Height
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(10, 500)
        self.max_height_spin.setValue(35)
        self.max_height_spin.valueChanged.connect(lambda: self.preset_combo.setCurrentIndex(0))
        self.max_height_spin.valueChanged.connect(self.on_setting_changed)
        controls_layout.addRow("Max Height:", self.max_height_spin)

        # Ramp dropdown
        self.ramp_combo = QComboBox()
        self.ramp_combo.addItem("Blocks (█▓▒░ )", CHAT_RAMP_BLOCKS)
        self.ramp_combo.addItem("Classic (@#S%?*+;:,. )", CHAT_RAMP_CLASSIC)
        self.ramp_combo.addItem("Detailed", DEFAULT_RAMP)
        self.ramp_combo.addItem("Chat safe (no markdown)", CHAT_RAMP_SAFE)
        self.ramp_combo.currentIndexChanged.connect(self.on_setting_changed)
        controls_layout.addRow("Ramp:", self.ramp_combo)

        # Contrast slider
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(100, 300)  # 1.0 to 3.0 (scaled by 100)
        self.contrast_slider.setValue(160)  # 1.6
        self.contrast_slider.valueChanged.connect(self.on_setting_changed)
        self.contrast_label = QLabel("1.6")
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_label)
        self.contrast_slider.valueChanged.connect(
            lambda v: self.contrast_label.setText(f"{v / 100:.2f}")
        )
        controls_layout.addRow("Contrast:", contrast_layout)

        # Gamma slider
        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setRange(40, 140)  # 0.4 to 1.4 (scaled by 100)
        self.gamma_slider.setValue(75)  # 0.75
        self.gamma_slider.valueChanged.connect(self.on_setting_changed)
        self.gamma_label = QLabel("0.75")
        gamma_layout = QHBoxLayout()
        gamma_layout.addWidget(self.gamma_slider)
        gamma_layout.addWidget(self.gamma_label)
        self.gamma_slider.valueChanged.connect(
            lambda v: self.gamma_label.setText(f"{v / 100:.2f}")
        )
        controls_layout.addRow("Gamma:", gamma_layout)

        # Checkboxes
        self.dither_check = QCheckBox()
        self.dither_check.toggled.connect(self.on_setting_changed)
        controls_layout.addRow("Dither:", self.dither_check)

        self.invert_check = QCheckBox()
        self.invert_check.toggled.connect(self.on_setting_changed)
        controls_layout.addRow("Invert:", self.invert_check)

        self.double_width_check = QCheckBox()
        self.double_width_check.toggled.connect(self.on_setting_changed)
        controls_layout.addRow("Double Width:", self.double_width_check)

        self.color_check = QCheckBox()
        self.color_check.toggled.connect(self.on_setting_changed)
        controls_layout.addRow("Color:", self.color_check)

        self.wrap_code_block_check = QCheckBox()
        controls_layout.addRow("Wrap in code block:", self.wrap_code_block_check)

        controls_group.setLayout(controls_layout)
        right_layout.addWidget(controls_group)

        # Action buttons
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.clicked.connect(self.convert_image)
        self.convert_btn.setEnabled(False)
        button_layout.addWidget(self.convert_btn)

        self.copy_btn = QPushButton("Copy ASCII")
        self.copy_btn.clicked.connect(self.copy_ascii)
        self.copy_btn.setEnabled(False)
        button_layout.addWidget(self.copy_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()

        right_layout.addLayout(button_layout)

        # ASCII output area
        ascii_label = QLabel("Terminal Output:")
        ascii_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(ascii_label)

        self.ascii_text = QTextEdit()
        self.ascii_text.setReadOnly(True)
        self.ascii_text.setFontFamily("Courier New")
        self.ascii_text.setFontPointSize(9)
        self.ascii_text.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #666;"
        )
        self.ascii_text.setLineWrapMode(QTextEdit.NoWrap)
        right_layout.addWidget(self.ascii_text)

        splitter.addWidget(right_widget)

        # Set splitter proportions (40% left, 60% right)
        splitter.setSizes([400, 800])

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*)",
        )
        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.display_image_preview()
                self.convert_btn.setEnabled(True)
                self.convert_image()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {e}")

    def display_image_preview(self):
        if not self.current_image:
            return

        # Convert PIL Image to QImage
        img_rgb = self.current_image.convert("RGB")
        img_bytes = img_rgb.tobytes("raw", "RGB")
        q_image = QImage(
            img_bytes,
            img_rgb.width,
            img_rgb.height,
            img_rgb.width * 3,  # bytesPerLine — must be explicit or Qt misaligns rows
            QImage.Format.Format_RGB888,
        )

        # Convert to QPixmap and scale to fit label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.display_image_preview()

    def on_preset_changed(self, name: str):
        if name not in PRESETS:
            return
        w, h = PRESETS[name]
        self.max_width_spin.blockSignals(True)
        self.max_height_spin.blockSignals(True)
        self.max_width_spin.setValue(w)
        self.max_height_spin.setValue(h)
        self.max_width_spin.blockSignals(False)
        self.max_height_spin.blockSignals(False)
        if self.current_image:
            self.convert_image()

    def on_setting_changed(self):
        if self.current_image:
            self.convert_image()

    def convert_image(self):
        if not self.current_image:
            return

        try:
            max_width = self.max_width_spin.value()
            max_height = self.max_height_spin.value()
            ramp = self.ramp_combo.currentData()
            contrast = self.contrast_slider.value() / 100.0
            gamma = self.gamma_slider.value() / 100.0
            dither = self.dither_check.isChecked()
            double = self.double_width_check.isChecked()
            invert = self.invert_check.isChecked()
            color = self.color_check.isChecked()

            img = self.current_image.copy()

            if color:
                plain, colored_html = image_to_colored(
                    img=img,
                    max_width=max_width,
                    max_height=max_height,
                    ramp=ramp,
                    aspect=0.55,
                    contrast=contrast,
                    gamma=gamma,
                    autocontrast_cutoff=1,
                    dither=dither,
                    double=double,
                    invert=invert,
                )
                self._plain_ascii = plain
                html_doc = (
                    '<pre style="font-family:\'Courier New\',monospace;'
                    ' font-size:9pt; margin:0; padding:0;">'
                    + colored_html
                    + "</pre>"
                )
                self.ascii_text.setHtml(html_doc)
            else:
                if invert:
                    img = ImageOps.invert(img.convert("L"))
                ascii_art = image_to_ascii(
                    img=img,
                    max_width=max_width,
                    max_height=max_height,
                    ramp=ramp,
                    aspect=0.55,
                    contrast=contrast,
                    gamma=gamma,
                    autocontrast_cutoff=1,
                    dither=dither,
                    double=double,
                )
                self._plain_ascii = ascii_art
                self.ascii_text.setPlainText(ascii_art)

            self.copy_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"Failed to convert image: {e}")

    def copy_ascii(self):
        text = self._plain_ascii
        if not text:
            return

        clipboard = QApplication.clipboard()
        if self.wrap_code_block_check.isChecked():
            clipboard.setText(f"```\n{text}\n```")
        else:
            clipboard.setText(text)

        self.status_label.setText("Copied!")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")  # Modern look

        window = ASCIIArtConverter()
        window.show()

        sys.exit(app.exec())
    except ImportError:
        print("PySide6 not available, falling back to Tkinter...")
        # Fallback to Tkinter
        import img2ascii_gui_tk
        img2ascii_gui_tk.main()


if __name__ == "__main__":
    main()
