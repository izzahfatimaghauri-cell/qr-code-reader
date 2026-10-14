"""
QR Code Reader - Professional Edition
A clean, modern QR code scanner with support for images and live camera scanning.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
import webbrowser
import os
from datetime import datetime


# ============================================================
# COLOR PALETTE & STYLING
# ============================================================
class Theme:
    BG_PRIMARY = "#1e1e2e"       # Main background
    BG_SECONDARY = "#282838"     # Card background
    BG_TERTIARY = "#313145"      # Hover / input background
    ACCENT = "#89b4fa"           # Primary accent (blue)
    ACCENT_HOVER = "#74a8f7"
    SUCCESS = "#a6e3a1"          # Success green
    WARNING = "#f9e2af"          # Warning yellow
    ERROR = "#f38ba8"            # Error red
    TEXT_PRIMARY = "#cdd6f4"     # Main text
    TEXT_SECONDARY = "#9399b2"   # Muted text
    BORDER = "#45475a"


# ============================================================
# MAIN APPLICATION
# ============================================================
class QRCodeReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Reader")
        self.root.geometry("900x680")
        self.root.minsize(780, 600)
        self.root.configure(bg=Theme.BG_PRIMARY)

        # State
        self.camera_active = False
        self.cap = None
        self.current_frame = None
        self.last_result = ""
        self.scan_history = []

        # Setup
        self._setup_styles()
        self._build_ui()
        self._center_window()

        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # --------------------------------------------------------
    # Window helpers
    # --------------------------------------------------------
    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Accent.TButton",
            background=Theme.ACCENT,
            foreground="#1e1e2e",
            borderwidth=0,
            focuscolor=Theme.ACCENT,
            padding=(16, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", Theme.ACCENT_HOVER), ("pressed", Theme.ACCENT_HOVER)],
        )

        style.configure(
            "Secondary.TButton",
            background=Theme.BG_TERTIARY,
            foreground=Theme.TEXT_PRIMARY,
            borderwidth=0,
            focuscolor=Theme.BG_TERTIARY,
            padding=(16, 10),
            font=("Segoe UI", 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", Theme.BORDER), ("pressed", Theme.BORDER)],
        )

        style.configure(
            "Danger.TButton",
            background=Theme.ERROR,
            foreground="#1e1e2e",
            borderwidth=0,
            focuscolor=Theme.ERROR,
            padding=(16, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#e17b96"), ("pressed", "#e17b96")],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=Theme.BG_TERTIARY,
            troughcolor=Theme.BG_SECONDARY,
            bordercolor=Theme.BG_SECONDARY,
            arrowcolor=Theme.TEXT_SECONDARY,
        )

    # --------------------------------------------------------
    # UI Construction
    # --------------------------------------------------------
    def _build_ui(self):
        # ---- Header ----
        header = tk.Frame(self.root, bg=Theme.BG_PRIMARY, height=80)
        header.pack(fill="x", padx=24, pady=(20, 10))
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="QR Code Reader",
            font=("Segoe UI", 22, "bold"),
            bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_PRIMARY,
        )
        title.pack(side="left", anchor="w")

        subtitle = tk.Label(
            header,
            text="Scan from image or live camera",
            font=("Segoe UI", 10),
            bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_SECONDARY,
        )
        subtitle.pack(side="left", anchor="w", padx=(12, 0), pady=(8, 0))

        # ---- Main body: left (display) + right (history) ----
        body = tk.Frame(self.root, bg=Theme.BG_PRIMARY)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Left column
        left = tk.Frame(body, bg=Theme.BG_PRIMARY)
        left.pack(side="left", fill="both", expand=True)

        # Display card
        self.display_card = tk.Frame(
            left, bg=Theme.BG_SECONDARY, highlightthickness=1,
            highlightbackground=Theme.BORDER
        )
        self.display_card.pack(fill="both", expand=True)

        # Display area
        self.display_label = tk.Label(
            self.display_card,
            text="📷\n\nNo image loaded\n\nClick 'Open Image' or 'Start Camera' to begin",
            font=("Segoe UI", 12),
            bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT_SECONDARY,
            justify="center",
        )
        self.display_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Result card
        result_frame = tk.Frame(
            left, bg=Theme.BG_SECONDARY, highlightthickness=1,
            highlightbackground=Theme.BORDER
        )
        result_frame.pack(fill="x", pady=(12, 0))

        result_header = tk.Frame(result_frame, bg=Theme.BG_SECONDARY)
        result_header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            result_header, text="Decoded Result",
            font=("Segoe UI", 10, "bold"),
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_SECONDARY,
        ).pack(side="left")

        self.status_label = tk.Label(
            result_header, text="●  Ready",
            font=("Segoe UI", 9),
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_SECONDARY,
        )
        self.status_label.pack(side="right")

        self.result_text = tk.Text(
            result_frame,
            height=4,
            bg=Theme.BG_TERTIARY,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            font=("Consolas", 10),
            wrap="word",
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=10,
        )
        self.result_text.pack(fill="x", padx=16, pady=(0, 12))

        # Action buttons
        buttons = tk.Frame(left, bg=Theme.BG_PRIMARY)
        buttons.pack(fill="x", pady=(12, 0))

        self.open_btn = ttk.Button(
            buttons, text="🖼  Open Image",
            style="Accent.TButton", command=self.open_image
        )
        self.open_btn.pack(side="left", padx=(0, 8))

        self.camera_btn = ttk.Button(
            buttons, text="📹  Start Camera",
            style="Secondary.TButton", command=self.toggle_camera
        )
        self.camera_btn.pack(side="left", padx=(0, 8))

        self.copy_btn = ttk.Button(
            buttons, text="📋  Copy",
            style="Secondary.TButton", command=self.copy_result
        )
        self.copy_btn.pack(side="left", padx=(0, 8))

        self.open_link_btn = ttk.Button(
            buttons, text="🔗  Open Link",
            style="Secondary.TButton", command=self.open_link
        )
        self.open_link_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = ttk.Button(
            buttons, text="🗑  Clear",
            style="Secondary.TButton", command=self.clear_all
        )
        self.clear_btn.pack(side="left")

        # Right column - history
        right = tk.Frame(
            body, bg=Theme.BG_SECONDARY,
            highlightthickness=1, highlightbackground=Theme.BORDER,
            width=260
        )
        right.pack(side="right", fill="y", padx=(16, 0))
        right.pack_propagate(False)

        history_header = tk.Frame(right, bg=Theme.BG_SECONDARY)
        history_header.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            history_header, text="Scan History",
            font=("Segoe UI", 11, "bold"),
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        clear_hist_btn = tk.Label(
            history_header, text="Clear", cursor="hand2",
            font=("Segoe UI", 9, "underline"),
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_SECONDARY,
        )
        clear_hist_btn.pack(side="right")
        clear_hist_btn.bind("<Button-1>", lambda e: self.clear_history())

        # History list
        list_frame = tk.Frame(right, bg=Theme.BG_SECONDARY)
        list_frame.pack(fill="both", expand=True, padx=(8, 0), pady=(0, 12))

        self.history_listbox = tk.Listbox(
            list_frame,
            bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT_PRIMARY,
            selectbackground=Theme.BG_TERTIARY,
            selectforeground=Theme.ACCENT,
            font=("Segoe UI", 9),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
        )
        self.history_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical",
            command=self.history_listbox.yview,
            style="Vertical.TScrollbar",
        )
        scrollbar.pack(side="right", fill="y")
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        self.history_listbox.bind("<Double-Button-1>", self._on_history_select)

        # ---- Footer / status bar ----
        footer = tk.Frame(self.root, bg=Theme.BG_PRIMARY, height=28)
        footer.pack(fill="x", side="bottom", padx=24, pady=(0, 10))
        footer.pack_propagate(False)

        self.footer_label = tk.Label(
            footer, text="Tip: Double-click a history item to view it again.",
            font=("Segoe UI", 9),
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_SECONDARY,
        )
        self.footer_label.pack(side="left")

        self.count_label = tk.Label(
            footer, text="Scans: 0",
            font=("Segoe UI", 9),
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_SECONDARY,
        )
        self.count_label.pack(side="right")

    # --------------------------------------------------------
    # Status updates
    # --------------------------------------------------------
    def _set_status(self, text, color):
        self.status_label.config(text=f"●  {text}", fg=color)

    def _show_result(self, text, status="Success", color=Theme.SUCCESS):
        self.result_text.delete("1.0", "end")
        if text:
            self.result_text.insert("1.0", text)
        self._set_status(status, color)

    # --------------------------------------------------------
    # Image opening
    # --------------------------------------------------------
    def open_image(self):
        if self.camera_active:
            self.toggle_camera()

        path = filedialog.askopenfilename(
            title="Select an image containing a QR code",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            img = Image.open(path)
            self._display_pil(img)

            # Decode
            results = decode(img)
            if results:
                data = results[0].data.decode("utf-8", errors="replace")
                qr_type = results[0].type
                self._handle_success(data, source="Image", qr_type=qr_type)
            else:
                self._show_result(
                    "No QR code detected in the selected image.",
                    status="Not found", color=Theme.WARNING,
                )
                self.footer_label.config(text=f"Loaded: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open image:\n{e}")

    def _display_pil(self, pil_img):
        """Fit PIL image into display label while preserving aspect ratio."""
        self.root.update_idletasks()
        target_w = max(self.display_label.winfo_width(), 300) - 20
        target_h = max(self.display_label.winfo_height(), 200) - 20

        img = pil_img.copy()
        img.thumbnail((target_w, target_h), Image.LANCZOS)
        self._tk_img = ImageTk.PhotoImage(img)
        self.display_label.config(image=self._tk_img, text="")

    # --------------------------------------------------------
    # Camera handling
    # --------------------------------------------------------
    def toggle_camera(self):
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror(
                "Camera Error",
                "Could not access the camera.\n"
                "Please make sure a webcam is connected and not in use."
            )
            self.cap = None
            return

        self.camera_active = True
        self.camera_btn.config(text="⏹  Stop Camera", style="Danger.TButton")
        self.open_btn.config(state="disabled")
        self._set_status("Camera running…", Theme.ACCENT)
        self.footer_label.config(text="Point the camera at a QR code.")

        self._update_camera()

    def stop_camera(self):
        self.camera_active = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.camera_btn.config(text="📹  Start Camera", style="Secondary.TButton")
        self.open_btn.config(state="normal")
        self._set_status("Ready", Theme.TEXT_SECONDARY)
        self.footer_label.config(text="Camera stopped.")

    def _update_camera(self):
        if not self.camera_active or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_camera()
            messagebox.showerror("Camera Error", "Lost connection to camera.")
            return

        # Convert & decode
        frame = cv2.flip(frame, 1)  # mirror for user comfort
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        results = decode(pil_img)

        if results:
            data = results[0].data.decode("utf-8", errors="replace")
            # Draw bounding boxes on frame
            frame_annotated = frame.copy()
            for r in results:
                pts = r.polygon
                if len(pts) == 4:
                    import numpy as np
                    pts_arr = [(p.x, p.y) for p in pts]
                    cv2.polylines(
                        frame_annotated, [np.array(pts_arr, dtype="int32")],
                        True, (166, 227, 161), 3
                    )
            rgb = cv2.cvtColor(frame_annotated, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)

            self._handle_success(data, source="Camera", qr_type=results[0].type)
            self._display_camera_frame(pil_img)
            # Stop after successful scan for stability
            self.root.after(400, self.stop_camera)
            return

        self._display_camera_frame(pil_img)
        self.root.after(30, self._update_camera)

    def _display_camera_frame(self, pil_img):
        self.root.update_idletasks()
        target_w = max(self.display_label.winfo_width(), 300) - 20
        target_h = max(self.display_label.winfo_height(), 200) - 20

        img = pil_img.copy()
        img.thumbnail((target_w, target_h), Image.LANCZOS)
        self._tk_img = ImageTk.PhotoImage(img)
        self.display_label.config(image=self._tk_img, text="")

    # --------------------------------------------------------
    # Success handler
    # --------------------------------------------------------
    def _handle_success(self, data, source="Image", qr_type="QRCODE"):
        self.last_result = data
        self._show_result(data, status="Detected", color=Theme.SUCCESS)
        self.footer_label.config(text=f"Scanned from {source} • Type: {qr_type}")

        timestamp = datetime.now().strftime("%H:%M:%S")
        preview = data.strip().replace("\n", " ")
        if len(preview) > 40:
            preview = preview[:37] + "…"
        entry = f"[{timestamp}]  {preview}"
        self.scan_history.append((entry, data))
        self.history_listbox.insert("end", entry)
        self.history_listbox.see("end")
        self.count_label.config(text=f"Scans: {len(self.scan_history)}")

    # --------------------------------------------------------
    # Result actions
    # --------------------------------------------------------
    def copy_result(self):
        text = self.result_text.get("1.0", "end").strip()
        if not text or text.startswith("No QR code"):
            self._flash_status("Nothing to copy", Theme.WARNING)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._flash_status("Copied to clipboard", Theme.SUCCESS)

    def open_link(self):
        text = self.result_text.get("1.0", "end").strip()
        if not text:
            self._flash_status("No link to open", Theme.WARNING)
            return
        if not (text.startswith("http://") or text.startswith("https://")):
            self._flash_status("Not a valid URL", Theme.WARNING)
            return

        try:
            # Try Chrome first, fall back to default browser
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            ]
            opened = False
            for chrome in chrome_paths:
                if os.path.exists(chrome):
                    webbrowser.register(
                        "chrome", None,
                        webbrowser.BackgroundBrowser(chrome)
                    )
                    webbrowser.get("chrome").open(text)
                    opened = True
                    break

            if not opened:
                webbrowser.open(text)  # fallback to default browser

            self._flash_status("Opened in browser", Theme.SUCCESS)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open link:\n{e}")

    def _flash_status(self, msg, color):
        self._set_status(msg, color)
        self.root.after(1600, lambda: self._set_status("Ready", Theme.TEXT_SECONDARY))

    # --------------------------------------------------------
    # History
    # --------------------------------------------------------
    def _on_history_select(self, event):
        sel = self.history_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.scan_history):
            _, data = self.scan_history[idx]
            self.last_result = data
            self._show_result(data, status="From history", color=Theme.ACCENT)
            self.footer_label.config(text="Loaded from scan history.")

    def clear_history(self):
        if not self.scan_history:
            return
        if messagebox.askyesno("Clear history", "Delete all scan history?"):
            self.scan_history.clear()
            self.history_listbox.delete(0, "end")
            self.count_label.config(text="Scans: 0")

    # --------------------------------------------------------
    # Clear everything
    # --------------------------------------------------------
    def clear_all(self):
        if self.camera_active:
            self.toggle_camera()
        self.result_text.delete("1.0", "end")
        self.display_label.config(image="", text="📷\n\nNo image loaded\n\nClick 'Open Image' or 'Start Camera' to begin")
        self._tk_img = None
        self._set_status("Ready", Theme.TEXT_SECONDARY)
        self.footer_label.config(text="Cleared. Ready for a new scan.")

    # --------------------------------------------------------
    # Window close
    # --------------------------------------------------------
    def _on_close(self):
        if self.camera_active:
            self.stop_camera()
        self.root.destroy()


# ============================================================
# ENTRY POINT
# ============================================================
def main():
    root = tk.Tk()
    app = QRCodeReaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()