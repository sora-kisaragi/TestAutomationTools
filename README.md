# テスト自動化支援ツール

WebシステムのE2Eテスト業務の効率化を目的としたデスクトップアプリケーションです。

## 📋 プロジェクト概要

本ツールは、Excelで記述されたテストシナリオをGUIで管理・確認し、テストの実行（自動・手動）および結果記録・Excel出力を行うツールです。「テスト管理システム」と「テスト自動実行システム」の2つの役割を持ちます。

### 対象ユーザー
- テスト担当者
- QAエンジニア
- Webサービス開発チームのメンバー

### 対応ブラウザ（マルチブラウザ対応）
- Google Chrome
- Microsoft Edge
- Mozilla Firefox
- Apple Safari（macOS限定／将来対応予定）

## 🎯 現在の実装状況

このプロジェクトは現在**テスト管理システム**として機能しており、以下の機能が実装されています：

✅ **実装済み機能**
- PyQt5によるGUIインターフェース
- SQLiteデータベースによるデータ管理
- Excelファイルの読み込み（openpyxl）
- プロジェクト・画面・テストケース・不具合管理
- テストシナリオの作成・一覧表示
- マスタデータ管理
- BUG-ID自動採番システム

🚧 **未実装機能（将来予定）**
- Seleniumによる自動テスト実行
- WebDriverを使ったブラウザ操作
- スクリーンショット取得

## 📋 必要な環境

- **Python**: 3.9以上（推奨: 3.12+）
- **OS**: Windows 10/11, macOS, Linux
- **メモリ**: 最低2GB以上

## 🚀 クイックスタート

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd TestAutomationTools
```

### 2. 仮想環境の作成とアクティベート

**Windows (PowerShell)**:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (コマンドプロンプト)**:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 必要パッケージのインストール

**最小構成（現在動作に必要なもののみ）**:
```bash
pip install -r requirements-minimal.txt
```

**フル構成（将来機能含む）**:
```bash
pip install -r requirements.txt
```

### 4. アプリケーションの起動
```bash
python main.py
```

## 📦 パッケージ構成

### 現在必要な最小パッケージ
```
PyQt5==5.15.11          # GUIフレームワーク
openpyxl==3.1.5          # Excel読み込み
pandas==2.2.3            # データ処理
python-dateutil==2.9.0.post0  # 日時処理
```

### 将来機能用パッケージ（現在は不要）
```
selenium==4.32.0         # ブラウザ自動化（未実装）
webdriver-manager==4.0.2 # WebDriver管理（未実装）
```

## 🗂️ プロジェクト構造

```
TestAutomationTools/
├── main.py                    # アプリケーションエントリポイント
├── app.py                     # PyQt5アプリケーションメイン
├── requirements.txt           # 全依存関係（将来機能含む）
├── requirements-minimal.txt   # 最小構成
├── core/                      # コアロジック
│   ├── scenario_db.py         # データベース操作
│   └── scenario_loader.py     # シナリオ読み込み
├── gui/                       # GUIコンポーネント
│   ├── main_window.py         # メインウィンドウ
│   ├── scenario/              # シナリオ管理画面
│   ├── test/                  # テスト関連画面
│   ├── bug/                   # 不具合管理画面
│   └── common/                # 共通コンポーネント
├── data/                      # データファイル
│   └── scenarios.db           # SQLiteデータベース
└── docs/                      # ドキュメント
```

## 🔧 開発環境のセットアップ

### 1. 必要なツールのインストール
```bash
# 開発用追加パッケージ
pip install rich pytest black flake8
```

### 2. データベースの初期化
初回起動時にSQLiteデータベースが自動的に作成されます。

### 3. 設定ファイル
`.env`ファイルで環境変数を設定できます（オプション）。

## 📚 使用方法

### 基本的な使い方
1. アプリケーションを起動
2. 「プロジェクト管理」でプロジェクトを作成
3. 「画面管理」でテスト対象画面を登録
4. 「シナリオ管理」でテストシナリオを作成
5. 「テスト管理」で手動テストを実行・記録

### Excelインポート
- 既存のExcelテスト仕様書を読み込み可能
- 複数シナリオが含まれる場合は自動分割

## 🛠️ トラブルシューティング

### PyQt5のインストールエラー
```bash
# Windowsでエラーが発生する場合
pip install --upgrade pip setuptools wheel
pip install PyQt5
```

### データベースエラー
```bash
# データベースを初期化する場合
rm data/scenarios.db
python main.py  # 再起動で自動再作成
```

## 🚀 将来のロードマップ

- [ ] Seleniumによる自動テスト実行機能
- [ ] マルチブラウザ対応（Chrome, Edge, Firefox）
- [ ] スクリーンショット自動取得
- [ ] CI/CD連携
- [ ] レポート機能強化

## 📄 ライセンス

[ライセンス情報を記載]

## 🤝 コントリビューション

[コントリビューション方法を記載]

---

**注意**: Seleniumとwebdriver-managerは将来の自動テスト機能のために`requirements.txt`に含まれていますが、現在のバージョンでは使用されていません。最小構成でのセットアップをお勧めします。