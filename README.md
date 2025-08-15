# VidDown

VidDownは、YouTubeなどの動画サイトから動画や音声を簡単にダウンロードできるWindows向けGUIアプリケーションです。  
直感的な操作で複数動画の一括ダウンロードや画質・保存形式の選択が可能です。

## ダウンロード
[こちら](https://github.com/Hallkun19/VidDown/releases/latest) から最新リリースをダウンロードできます。

## 主な機能

- 動画/再生リストのURLを入力してキューに追加
- ダウンロードキュー管理（追加・削除・全クリア）
- 保存先フォルダ・ファイル名テンプレートの指定
- 保存形式（mp4, webm, mkv, mp3, m4a, wav, flac）選択
- 画質（最高画質～最低画質、8K/4K/2K/1080pなど）選択
- ダウンロード進捗表示・ステータス管理
- ダーク/ライトテーマ切り替え
- 設定保存（テーマ等）

## 使い方

1. **URL入力**  
	ダウンロードしたい動画または再生リストのURLを入力し、「貼り付け」ボタンでクリップボードからも貼り付け可能です。

2. **キューに追加**  
	「キューに追加」ボタンでダウンロードキューに登録します。

3. **オプション設定**  
	- 保存先フォルダを指定
	- ファイル名テンプレートを編集（例: `%(title)s [%(id)s]`）
	- 保存形式・画質を選択

4. **ダウンロード開始**  
	「ダウンロード開始」ボタンでキュー内の動画を一括ダウンロードします。進捗バーとステータスで状況を確認できます。

5. **キュー管理**  
	- 選択した項目の削除
	- キュー全体のクリア

6. **テーマ・バージョン情報**  
	右上の設定ボタンからテーマ切り替えやバージョン情報の確認ができます。

## 必要なライブラリ

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [sv-ttk](https://github.com/rdbende/Sun-Valley-ttk-theme)
- [pywinstyles](https://github.com/rossy/pywinstyles)
- [Pillow](https://python-pillow.org/)
- [pyglet](https://pyglet.readthedocs.io/)

インストール例:
```sh
pip install -r requirements.txt
```

## 実行方法

1. 必要なライブラリをインストール
2. `main.py`を実行
	```sh
	python main.py
	```

## ライセンス・作者

- 作者: はるくん / harukun19
- フォント: BIZ UDPGothic（fontsフォルダ）
- アイコン: Material Symbols & Icons （iconsフォルダ）
