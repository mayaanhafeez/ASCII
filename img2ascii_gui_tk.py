#!/usr/bin/env python3
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Optional
from io import BytesIO

from PIL import Image, ImageOps, ImageTk

from img2ascii import (
    image_to_ascii,
    DEFAULT_RAMP,
    CHAT_RAMP_BLOCKS,
    CHAT_RAMP_CLASSIC,
)


class ASCIIArtConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to ASCII Art Converter")
        self.root.geometry("1200x700")
        self.root.minsize(800, 600)

        self.current_image: Optional[Image.Image] = None
        self.ascii_text_content = ""

        # Main container with paned window for resizable columns
        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left frame: Image preview
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        left_inner = ttk.Frame(left_frame)
        left_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.image_label = tk.Label(
            left_inner,
            text="No image loaded",
            bg="#2b2b2b",
            fg="#aaa",
            relief=tk.SOLID,
            borderwidth=1,
        )
        self.image_label.pack(fill=tk.BOTH, expand=True)

        self.upload_btn = ttk.Button(left_inner, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(pady=5)

        # Right frame: Controls and ASCII output
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        right_inner = ttk.Frame(right_frame)
        right_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controls frame
        controls_frame = ttk.LabelFrame(right_inner, text="Conversion Settings", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Max Width
        ttk.Label(controls_frame, text="Max Width:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.max_width_var = tk.IntVar(value=70)
        max_width_spin = ttk.Spinbox(
            controls_frame, from_=10, to=500, textvariable=self.max_width_var, width=10
        )
        max_width_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.max_width_var.trace("w", lambda *args: self.on_setting_changed())

        # Max Height
        ttk.Label(controls_frame, text="Max Height:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_height_var = tk.IntVar(value=35)
        max_height_spin = ttk.Spinbox(
            controls_frame, from_=10, to=500, textvariable=self.max_height_var, width=10
        )
        max_height_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.max_height_var.trace("w", lambda *args: self.on_setting_changed())

        # Ramp dropdown
        ttk.Label(controls_frame, text="Ramp:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ramp_var = tk.StringVar(value="Blocks")
        ramp_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.ramp_var,
            values=["Blocks", "Classic", "Detailed"],
            state="readonly",
            width=20,
        )
        ramp_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        ramp_combo.bind("<<ComboboxSelected>>", lambda e: self.on_setting_changed())

        # Contrast slider
        ttk.Label(controls_frame, text="Contrast:").grid(row=3, column=0, sticky=tk.W, pady=2)
        contrast_frame = ttk.Frame(controls_frame)
        contrast_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        self.contrast_var = tk.DoubleVar(value=1.6)
        contrast_slider = ttk.Scale(
            contrast_frame, from_=1.0, to=3.0, variable=self.contrast_var, orient=tk.HORIZONTAL, length=150
        )
        contrast_slider.pack(side=tk.LEFT)
        self.contrast_label = ttk.Label(contrast_frame, text="1.60")
        self.contrast_label.pack(side=tk.LEFT, padx=5)
        self.contrast_var.trace("w", lambda *args: (self.update_contrast_label(), self.on_setting_changed()))

        # Gamma slider
        ttk.Label(controls_frame, text="Gamma:").grid(row=4, column=0, sticky=tk.W, pady=2)
        gamma_frame = ttk.Frame(controls_frame)
        gamma_frame.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        self.gamma_var = tk.DoubleVar(value=0.75)
        gamma_slider = ttk.Scale(
            gamma_frame, from_=0.4, to=1.4, variable=self.gamma_var, orient=tk.HORIZONTAL, length=150
        )
        gamma_slider.pack(side=tk.LEFT)
        self.gamma_label = ttk.Label(gamma_frame, text="0.75")
        self.gamma_label.pack(side=tk.LEFT, padx=5)
        self.gamma_var.trace("w", lambda *args: (self.update_gamma_label(), self.on_setting_changed()))

        # Checkboxes
        self.dither_var = tk.BooleanVar()
        dither_check = ttk.Checkbutton(controls_frame, text="Dither", variable=self.dither_var)
        dither_check.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.dither_var.trace("w", lambda *args: self.on_setting_changed())

        self.invert_var = tk.BooleanVar()
        invert_check = ttk.Checkbutton(controls_frame, text="Invert", variable=self.invert_var)
        invert_check.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.invert_var.trace("w", lambda *args: self.on_setting_changed())

        self.double_width_var = tk.BooleanVar()
        double_check = ttk.Checkbutton(controls_frame, text="Double Width", variable=self.double_width_var)
        double_check.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.double_width_var.trace("w", lambda *args: self.on_setting_changed())

        self.wrap_code_block_var = tk.BooleanVar()
        wrap_check = ttk.Checkbutton(controls_frame, text="Wrap in code block", variable=self.wrap_code_block_var)
        wrap_check.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Action buttons
        button_frame = ttk.Frame(right_inner)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        self.convert_btn = ttk.Button(button_frame, text="Convert", command=self.convert_image, state=tk.DISABLED)
        self.convert_btn.pack(side=tk.LEFT, padx=5)

        self.copy_btn = ttk.Button(button_frame, text="Copy ASCII", command=self.copy_ascii, state=tk.DISABLED)
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(button_frame, text="", foreground="green", font=("", 9, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=10)

        # ASCII output area
        ttk.Label(right_inner, text="Terminal Output:", font=("", 9, "bold")).pack(anchor=tk.W)

        ascii_frame = ttk.Frame(right_inner)
        ascii_frame.pack(fill=tk.BOTH, expand=True)

        self.ascii_text = tk.Text(
            ascii_frame,
            wrap=tk.NONE,
            font=("Courier New", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
            relief=tk.SOLID,
            borderwidth=1,
        )
        scrollbar_v = ttk.Scrollbar(ascii_frame, orient=tk.VERTICAL, command=self.ascii_text.yview)
        scrollbar_h = ttk.Scrollbar(ascii_frame, orient=tk.HORIZONTAL, command=self.ascii_text.xview)
        self.ascii_text.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        self.ascii_text.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar_v.grid(row=0, column=1, sticky=tk.NS)
        scrollbar_h.grid(row=1, column=0, sticky=tk.EW)
        ascii_frame.grid_rowconfigure(0, weight=1)
        ascii_frame.grid_columnconfigure(0, weight=1)

        # Update image preview on resize
        self.image_label.bind("<Configure>", lambda e: self.display_image_preview())

    def update_contrast_label(self):
        self.contrast_label.config(text=f"{self.contrast_var.get():.2f}")

    def update_gamma_label(self):
        self.gamma_label.config(text=f"{self.gamma_var.get():.2f}")

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All Files", "*.*"),
            ],
        )
        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.display_image_preview()
                self.convert_btn.config(state=tk.NORMAL)
                self.convert_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def display_image_preview(self):
        if not self.current_image:
            return

        # Get label size
        self.root.update_idletasks()
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()

        if label_width <= 1 or label_height <= 1:
            # Label not yet sized, use a default
            label_width, label_height = 400, 300

        # Scale image to fit while maintaining aspect ratio
        img = self.current_image.copy()
        img.thumbnail((label_width, label_height), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo  # Keep a reference

    def on_setting_changed(self):
        if self.current_image:
            self.convert_image()

    def convert_image(self):
        if not self.current_image:
            return

        try:
            # Get current settings
            max_width = self.max_width_var.get()
            max_height = self.max_height_var.get()

            ramp_map = {
                "Blocks": CHAT_RAMP_BLOCKS,
                "Classic": CHAT_RAMP_CLASSIC,
                "Detailed": DEFAULT_RAMP,
            }
            ramp = ramp_map[self.ramp_var.get()]

            contrast = self.contrast_var.get()
            gamma = self.gamma_var.get()
            dither = self.dither_var.get()
            double = self.double_width_var.get()

            # Handle invert
            img = self.current_image.copy()
            if self.invert_var.get():
                img = ImageOps.invert(img.convert("L"))

            # Convert to ASCII
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

            # Display in text area
            self.ascii_text.delete("1.0", tk.END)
            self.ascii_text.insert("1.0", ascii_art)
            self.ascii_text_content = ascii_art
            self.copy_btn.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to convert image: {e}")

    def copy_ascii(self):
        if not self.ascii_text_content:
            return

        text_to_copy = self.ascii_text_content
        if self.wrap_code_block_var.get():
            text_to_copy = f"```txt\n{text_to_copy}\n```"

        self.root.clipboard_clear()
        self.root.clipboard_append(text_to_copy)

        # Show status message
        self.status_label.config(text="Copied!")
        self.root.after(2000, lambda: self.status_label.config(text=""))


def main():
    root = tk.Tk()
    app = ASCIIArtConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
