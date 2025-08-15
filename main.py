import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import json
import os
import sys
import re
from pathlib import Path

# 外部ライブラリのインポート
try:
    import yt_dlp
    import sv_ttk
    import pywinstyles
    from PIL import Image, ImageTk
    import pyglet
except ImportError:
    messagebox.showerror(
        "依存関係エラー",
        "必要なライブラリがインストールされていません。"
    )
    sys.exit(1)

# --- アプリケーションの基本情報 ---
APP_NAME = "VidDown"
APP_VERSION = "1.0.0" 
APP_AUTHOR = "Made by Halkun19"
ICON_SIZE = (18, 18)


def load_fonts():
    font_dir = resource_path("fonts")
    if not os.path.isdir(font_dir):
        print(f"警告: フォントディレクトリが見つかりません: {font_dir}")
        return
    font_files = {"regular": "BIZUDPGothic-Regular.ttf", "bold": "BIZUDPGothic-Bold.ttf"}
    for font_type, filename in font_files.items():
        font_path = os.path.join(font_dir, filename)
        if os.path.exists(font_path):
            try:
                pyglet.font.add_file(str(font_path))
                print(f"フォントをロードしました: {filename}")
            except Exception as e:
                print(f"フォント '{filename}' の読み込みに失敗: {e}")
        else:
            print(f"警告: フォントファイルが見つかりません: {font_path}")

def resource_path(relative_path):
    """ 実行ファイル内の一時パス、または開発中の相対パスを取得する """
    try:
        # PyInstallerが作成する一時フォルダ
        base_path = sys._MEIPASS
    except Exception:
        # 開発中の通常のパス
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- メインアプリケーションクラス ---
class App(tk.Tk):
    def __init__(self): 
        load_fonts()
        super().__init__()
        self.title(APP_NAME)

        self.iconbitmap(resource_path(os.path.join("icons", "icon.ico")))

        self.geometry("1000x600")
        self.minsize(800, 500)

        self.icons = {}

        # --- グローバルフォント設定 ---
        self.font_family = "BIZ UDPGothic"
        self.font_family_bold = "BIZ UDPGothic"
        self.font_size = 10
        self.default_font = (self.font_family, self.font_size)
        self.default_font_bold = (self.font_family_bold, self.font_size, "bold")

        self.option_add("*Font", self.default_font)

        # スタイルの設定
        self.style = ttk.Style()
        self.style.configure(".", font=self.default_font)
        self.style.configure("Treeview.Heading", font=self.default_font_bold)
        self.style.configure("Accent.TButton", font=self.default_font_bold)
        self.style.configure("TLabelFrame.Label", font=self.default_font)
        self.style.configure("Toolbutton", padding=5)

        # --- 変数初期化 ---
        self.download_queue = []
        self.is_downloading = False
        self.download_thread = None
        self.current_download_item_id = None
        self.comm_queue = queue.Queue()

        # --- UIの作成 ---
        self._create_widgets()

        # --- テーマの適用 ---
        self.current_theme = self.load_setting("theme", "dark")
        self.set_theme(self.current_theme)

        # --- 定期的なキューのチェック ---
        self.after(100, self.process_comm_queue)

    # def _is_valid_url(self, url):
    #     if not url:
    #         return False
    #     regex = re.compile(
    #         r"^(?:http|ftp)s?://"
    #         r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
    #         r"localhost|"
    #         r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    #         r"(?::\d+)?"
    #         r"(?:/?|[/?]\S+)$",
    #         re.IGNORECASE,
    #     )
    #     return re.match(regex, url) is not None

    def _load_icons(self):
        base_icon_theme = "white" if self.current_theme == "dark" else "black"
        icon_names = [
            "paste",
            "add",
            "settings",
            "delete",
            "clear",
            "folder",
            "download",
        ]
        accent_buttons = ["add", "download"]
        for name in icon_names:
            current_icon_theme = base_icon_theme
            if name in accent_buttons:
                current_icon_theme = "black" if base_icon_theme == "white" else "white"
            try:
                path = resource_path(os.path.join("icons", current_icon_theme, f"{name}.png"))
                if not os.path.exists(path):
                    print(f"警告: アイコンファイルが見つかりません: {path}")
                    self.icons[name] = None
                    continue
                image = Image.open(path)
                image = image.resize(ICON_SIZE, Image.Resampling.LANCZOS)
                self.icons[name] = ImageTk.PhotoImage(image)
            except Exception as e:
                print(f"アイコン '{name}' の読み込みに失敗: {e}")
                self.icons[name] = None

    def _update_button_icons(self):
        self.paste_button.config(image=self.icons.get("paste"))
        self.add_queue_button.config(image=self.icons.get("add"))
        self.settings_button.config(image=self.icons.get("settings"))
        self.remove_button.config(image=self.icons.get("delete"))
        self.clear_button.config(image=self.icons.get("clear"))
        self.browse_button.config(image=self.icons.get("folder"))
        self.download_button.config(image=self.icons.get("download"))

    def _create_widgets(self):
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill=tk.X)
        ttk.Label(top_frame, text="動画/再生リストのURL:").pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.url_entry = ttk.Entry(top_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.paste_button = ttk.Button(
            top_frame,
            text="貼り付け",
            command=self.paste_from_clipboard,
            compound="left",
        )
        self.paste_button.pack(side=tk.LEFT, padx=5)
        self.add_queue_button = ttk.Button(
            top_frame,
            text="キューに追加",
            style="Accent.TButton",
            command=self.add_to_queue,
            compound="left",
        )
        self.add_queue_button.pack(side=tk.LEFT)
        self.settings_button = ttk.Button(
            top_frame,
            text="",
            style="Toolbutton",
            command=self.open_settings,
            compound="left",
        )
        self.settings_button.pack(side=tk.RIGHT, padx=(10, 0))
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        queue_frame = ttk.LabelFrame(
            main_paned_window, text="ダウンロードキュー", padding=10
        )
        main_paned_window.add(queue_frame, weight=2)
        cols = ("#", "タイトル", "ステータス")
        self.queue_tree = ttk.Treeview(
            queue_frame, columns=cols, show="headings", selectmode="browse"
        )
        self.queue_tree.column("#", width=40, anchor=tk.CENTER)
        self.queue_tree.column("タイトル", width=350)
        self.queue_tree.column("ステータス", width=100, anchor=tk.CENTER)
        for col in cols:
            self.queue_tree.heading(col, text=col)
        vsb = ttk.Scrollbar(
            queue_frame, orient="vertical", command=self.queue_tree.yview
        )
        hsb = ttk.Scrollbar(
            queue_frame, orient="horizontal", command=self.queue_tree.xview
        )
        self.queue_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.queue_tree.pack(fill=tk.BOTH, expand=True)
        queue_button_frame = ttk.Frame(queue_frame)
        queue_button_frame.pack(fill=tk.X, pady=(5, 0))
        self.remove_button = ttk.Button(
            queue_button_frame,
            text="キューを削除",
            command=self.remove_selected_item,
            compound="left",
        )
        self.remove_button.pack(side=tk.LEFT)
        self.clear_button = ttk.Button(
            queue_button_frame,
            text="キューを全て削除",
            command=self.clear_queue,
            compound="left",
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        options_frame = ttk.LabelFrame(main_paned_window, text="オプション", padding=10)
        main_paned_window.add(options_frame, weight=1)
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, pady=5)
        ttk.Label(path_frame, text="保存先:").pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.browse_button = ttk.Button(
            path_frame,
            text="",
            style="Toolbutton",
            command=self.select_path,
            compound="left",
        )
        self.browse_button.pack(side=tk.LEFT)

        ttk.Label(options_frame, text="保存ファイル名:").pack(
            fill=tk.X, pady=(10, 2)
        )
        self.filename_template_var = tk.StringVar(value="%(title)s [%(id)s]")
        filename_template_entry = ttk.Entry(
            options_frame, textvariable=self.filename_template_var
        )
        filename_template_entry.pack(fill=tk.X)
        ttk.Label(
            options_frame,
            text="%(title)sなどのテンプレートが使用できます",
            foreground="grey",
        ).pack(anchor="w")

        ttk.Label(options_frame, text="保存形式:").pack(fill=tk.X, pady=(10, 2))
        self.format_var = tk.StringVar(value="mp4")
        self.format_combo = ttk.Combobox(
            options_frame,
            textvariable=self.format_var,
            state="readonly",
            values=["mp4", "webm", "mkv", "mp3", "m4a", "wav", "flac"],
        )
        self.format_combo.pack(fill=tk.X)
        ttk.Label(options_frame, text="画質:").pack(fill=tk.X, pady=(10, 2))
        self.quality_var = tk.StringVar(value="1080p")
        self.quality_combo = ttk.Combobox(
            options_frame,
            textvariable=self.quality_var,
            state="readonly",
            values=[
                "最高画質",
                "4320p (8K)",
                "2160p (4K)",
                "1440p (2K)",
                "1080p",
                "720p",
                "480p",
                "360p",
                "最低画質",
            ],
        )
        self.quality_combo.pack(fill=tk.X)

        bottom_frame = ttk.Frame(self, padding=10)
        bottom_frame.pack(fill=tk.X)
        self.status_label = ttk.Label(bottom_frame, text="準備完了")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_bar = ttk.Progressbar(
            bottom_frame, orient="horizontal", mode="determinate"
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.download_button = ttk.Button(
            bottom_frame,
            text="ダウンロード開始",
            style="Accent.TButton",
            command=self.start_download,
            compound="left",
        )
        self.download_button.pack(side=tk.LEFT)

    def set_theme(self, theme):
        sv_ttk.set_theme(theme)
        self.current_theme = theme
        self.save_setting("theme", theme)
        self.apply_fonts()
        self._load_icons()
        self._update_button_icons()
        if sys.platform == "win32":
            try:
                if theme == "dark":
                    pywinstyles.apply_style(self, "dark")
                else:
                    pywinstyles.apply_style(self, "light")
            except Exception as e:
                print(f"タイトルバーのテーマ変更に失敗: {e}")

    def apply_fonts(self):
        self.option_add("*Font", self.default_font)
        self.style.configure(".", font=self.default_font)
        self.style.configure("TLabel", font=self.default_font)
        self.style.configure("TButton", font=self.default_font)
        self.style.configure("TRadiobutton", font=self.default_font)
        self.style.configure("Accent.TButton", font=self.default_font_bold)
        self.style.configure("TEntry", font=self.default_font)
        self.style.configure("TCombobox", font=self.default_font)
        self.style.configure("TMenubutton", font=self.default_font)
        self.style.configure("Treeview", font=self.default_font)
        self.style.configure("Treeview.Heading", font=self.default_font_bold)
        self.style.configure("TLabelframe.Label", font=self.default_font)

    def paste_from_clipboard(self):
        try:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.clipboard_get())
        except tk.TclError:
            self.update_status("クリップボードが空です", error=True)

    def select_path(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)

    def add_to_queue(self):
        url = self.url_entry.get().strip()
        # if not self._is_valid_url(url):
        #     messagebox.showwarning(
        #         "無効なURL",
        #         "有効なURL形式ではありません。\nURLを正しく入力または貼り付けしてください。",
        #     )
        #     return
        self.update_status(f"情報を取得中: {url}")
        self.add_queue_button.config(state="disabled")
        thread = threading.Thread(target=self._get_video_info_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def _get_video_info_thread(self, url):
        try:
            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "noplaylist": True,
                "ignoreerrors": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                raise yt_dlp.utils.DownloadError(
                    "動画情報の解析に失敗しました。返された情報がありません。"
                )
            if "entries" in info:
                for entry in info.get("entries") or []:
                    if entry:
                        item = {
                            "url": entry["url"],
                            "title": entry.get("title", "タイトル不明"),
                            "status": "待機中",
                        }
                        self.comm_queue.put(("add_item", item))
            else:
                item = {
                    "url": url,
                    "title": info.get("title", "タイトル不明"),
                    "status": "待機中",
                }
                self.comm_queue.put(("add_item", item))
            self.comm_queue.put(("info_fetch_success", None))
        except Exception as e:
            clean_message = re.sub(r"\x1b\[[0-9;]*m", "", str(e))
            error_details = {
                "title": "情報取得エラー",
                "message": f"動画情報の取得に失敗しました。\nURLが正しいか、動画が公開されているか確認してください。\n\n詳細: {clean_message}",
            }
            self.comm_queue.put(("error", error_details))
        finally:
            self.comm_queue.put(("enable_add_button", None))

    def remove_selected_item(self):
        selected = self.queue_tree.selection()
        if not selected:
            return
        item_id = selected[0]
        index = self.queue_tree.index(item_id)
        if (
            self.is_downloading
            and self.queue_tree.item(item_id, "values")[2] == "ダウンロード中"
        ):
            self.update_status("ダウンロード中の項目は削除できません", error=True)
            return
        del self.download_queue[index]
        self.queue_tree.delete(item_id)
        self.update_status("選択項目を削除しました")

    def clear_queue(self):
        if self.is_downloading:
            self.update_status("ダウンロード中はキューをクリアできません", error=True)
            return
        self.download_queue.clear()
        for i in self.queue_tree.get_children():
            self.queue_tree.delete(i)
        self.update_status("キューをクリアしました")

    def start_download(self):
        if self.is_downloading:
            self.update_status("既にダウンロード処理が実行中です", error=True)
            return
        if not self.download_queue:
            self.update_status("キューが空です", error=True)
            return
        self.is_downloading = True
        self.download_button.config(text="ダウンロード中...", state="disabled")
        self.progress_bar["value"] = 0
        self.download_thread = threading.Thread(target=self._download_worker)
        self.download_thread.daemon = True
        self.download_thread.start()

    def _download_worker(self):
        for index, item in enumerate(self.download_queue):
            item_id = self.queue_tree.get_children()[index]
            self.current_download_item_id = item_id
            self.comm_queue.put(
                (
                    "update_status_text",
                    f"{index + 1}/{len(self.download_queue)}: {item['title']}",
                )
            )
            self.comm_queue.put(("update_item_status", (item_id, "ダウンロード中")))
            try:
                self._process_single_download(item)
                self.comm_queue.put(("update_item_status", (item_id, "完了")))
            except Exception as e:
                self.comm_queue.put(("update_item_status", (item_id, "エラー")))
                clean_message = re.sub(r"\x1b\[[0-9;]*m", "", str(e))
                error_details = {
                    "title": "ダウンロードエラー",
                    "message": f"「{item['title']}」のダウンロード中にエラーが発生しました。\n\n詳細: {clean_message}",
                }
                self.comm_queue.put(("error", error_details))
        self.comm_queue.put(("download_finished", None))

    def _process_single_download(self, item):
        save_path = self.path_var.get()
        os.makedirs(save_path, exist_ok=True)
        quality_map = {
            "最高画質": "bestvideo+bestaudio/best",
            "4320p (8K)": "bestvideo[height<=4320]+bestaudio/best[height<=4320]",
            "2160p (4K)": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
            "1440p (2K)": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "最低画質": "worstvideo+worstaudio/worst",
        }

        filename_template = self.filename_template_var.get()
        if not filename_template.strip():
            filename_template = "%(title)s [%(id)s]"

        output_template = os.path.join(save_path, f"{filename_template}.%(ext)s")

        ydl_opts = {
            "outtmpl": output_template,
            "progress_hooks": [self.progress_hook],
            "noplaylist": True,
            "ignoreerrors": True,
            'ffmpeg_location': resource_path(os.path.join('ffmpeg', 'ffmpeg.exe'))
        }

        format_type = self.format_var.get()
        is_audio_only = format_type in ["mp3", "m4a", "wav", "flac"]
        if is_audio_only:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": format_type}
            ]
        else:
            ydl_opts["format"] = quality_map.get(
                self.quality_var.get(), "bestvideo+bestaudio/best"
            )
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegVideoConvertor", "preferedformat": format_type}
            ]
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([item["url"]])

    def progress_hook(self, d):
        if d["status"] == "downloading":
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total_bytes:
                percent = (d.get("downloaded_bytes") / total_bytes) * 100
                self.comm_queue.put(("progress", percent))
        elif d["status"] == "finished":
            self.comm_queue.put(("progress", 100))

    def process_comm_queue(self):
        try:
            while True:
                message_type, data = self.comm_queue.get_nowait()
                if message_type == "add_item":
                    self.download_queue.append(data)
                    values = (len(self.download_queue), data["title"], data["status"])
                    self.queue_tree.insert("", tk.END, values=values)
                elif message_type == "info_fetch_success":
                    self.update_status(
                        "情報の取得が完了しました。キューに追加されました。"
                    )
                    self.url_entry.delete(0, tk.END)
                elif message_type == "enable_add_button":
                    self.add_queue_button.config(state="normal")
                elif message_type == "update_status_text":
                    self.status_label.config(text=data)
                elif message_type == "update_item_status":
                    item_id, status = data
                    current_values = list(self.queue_tree.item(item_id, "values"))
                    current_values[2] = status
                    self.queue_tree.item(item_id, values=tuple(current_values))
                elif message_type == "progress":
                    self.progress_bar["value"] = data
                elif message_type == "download_finished":
                    self.is_downloading = False
                    self.download_button.config(text="ダウンロード開始", state="normal")
                    self.update_status("すべてのダウンロードが完了しました。")
                    self.progress_bar["value"] = 0
                elif message_type == "error":
                    messagebox.showerror(data["title"], data["message"])
                    self.update_status(f"エラー: {data['title']}", error=True)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_comm_queue)

    def update_status(self, message, error=False):
        self.status_label.config(text=message)
        if error:
            print(f"ERROR: {message}")

    def get_settings_path(self):
        home = Path.home()
        config_dir = home / ".config" / APP_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "settings.json"

    def save_setting(self, key, value):
        settings_path = self.get_settings_path()
        settings = {}
        if settings_path.exists():
            with open(settings_path, "r") as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError:
                    pass
        settings[key] = value
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=4)

    def load_setting(self, key, default=None):
        settings_path = self.get_settings_path()
        if not settings_path.exists():
            return default
        with open(settings_path, "r") as f:
            try:
                settings = json.load(f)
                return settings.get(key, default)
            except json.JSONDecodeError:
                return default

    def open_settings(self):
        SettingsWindow(self)

    def show_about(self):
        messagebox.showinfo(
            "バージョン情報",
            f"{APP_NAME} - Version {APP_VERSION}\n\n作成者: {APP_AUTHOR}\n\nこのアプリケーションにはpythonとyt-dlpを使用しています。",
        )


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("設定")
        self.geometry("350x250")
        self.transient(parent)
        self.grab_set()
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="テーマ:").pack(pady=5, anchor=tk.W)
        self.theme_var = tk.StringVar(value=parent.current_theme)
        light_radio = ttk.Radiobutton(
            frame,
            text="ライト",
            variable=self.theme_var,
            value="light",
            command=self.apply_theme,
        )
        light_radio.pack(anchor=tk.W, padx=10)
        dark_radio = ttk.Radiobutton(
            frame,
            text="ダーク",
            variable=self.theme_var,
            value="dark",
            command=self.apply_theme,
        )
        dark_radio.pack(anchor=tk.W, padx=10)
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=15)
        about_button = ttk.Button(
            frame, text="バージョン情報", command=self.show_about_info
        )
        about_button.pack(pady=5)

    def apply_theme(self):
        self.parent.set_theme(self.theme_var.get())
        if sys.platform == "win32":
            try:
                if self.theme_var.get() == "dark":
                    pywinstyles.apply_style(self, "dark")
                else:
                    pywinstyles.apply_style(self, "light")
            except Exception as e:
                print(f"設定ウィンドウのテーマ変更に失敗: {e}")

    def show_about_info(self):
        self.parent.show_about()


if __name__ == "__main__":
    app = App()
    app.mainloop()
