from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QComboBox,
    QLineEdit, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QGroupBox, QAbstractItemView, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from typing import Optional
import os
import sqlite3
import logging

from core import scenario_db
from gui.scenario.scenario_creation_widget import ScenarioCreationWidget

class ImportExcelTab(QWidget):
    """シナリオ一覧タブ内に埋め込む Excel インポート用タブ"""

    import_completed = pyqtSignal()  # インポート完了後に一覧を更新してもらうためのシグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        scenario_db.init_db()
        self.selected_file: Optional[str] = None
        self._load_projects()
        self._init_ui()

    # ------------------------------ UI ------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 取り込み先は既存プロジェクトのみ
        proj_layout = QHBoxLayout()
        proj_layout.addWidget(QLabel("取り込み先プロジェクト:"))
        self.combo_project = QComboBox()
        for pid, name in self._project_list:
            self.combo_project.addItem(name, pid)
        proj_layout.addWidget(self.combo_project)
        layout.addLayout(proj_layout)

        # --- ファイル選択 ---
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.btn_file = QPushButton("ファイルを選択")
        self.btn_file.clicked.connect(self._on_select_file)
        file_layout.addWidget(QLabel("ファイル選択:"))
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(self.btn_file)
        layout.addLayout(file_layout)
        layout.addWidget(QLabel("またはドラッグ＆ドロップでExcelファイルを追加"))
        self.setAcceptDrops(True)

        # --- インポートオプション ---
        opt_layout = QHBoxLayout()
        self.radio_overwrite = QRadioButton("既存シナリオを上書き")
        self.radio_keep = QRadioButton("既存シナリオを残す")
        self.radio_overwrite.setChecked(True)
        opt_layout.addWidget(QLabel("インポートオプション:"))
        opt_layout.addWidget(self.radio_overwrite)
        opt_layout.addWidget(self.radio_keep)
        layout.addLayout(opt_layout)

        # --- 実行ボタン ---
        btn_layout = QHBoxLayout()
        self.btn_import = QPushButton("インポート開始")
        self.btn_import.clicked.connect(self._on_import_clicked)
        btn_layout.addWidget(self.btn_import)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- インポート結果テーブル ---
        self.result_table = QTableWidget(0, 5)
        self.result_table.setHorizontalHeaderLabels(["No", "画面名", "シナリオ名", "ステータス", "メッセージ"])
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(QLabel("インポート結果:"))
        layout.addWidget(self.result_table)

    # ------------------------------ Drag & Drop ------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        try:
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                # パス検証
                if not self._is_safe_file_path(path):
                    QMessageBox.warning(self, "ファイルエラー", "不正なファイルパスです")
                    continue
                    
                if path.lower().endswith((".xlsx", ".xls")):
                    # ファイル存在確認
                    if not os.path.exists(path) or not os.access(path, os.R_OK):
                        QMessageBox.warning(self, "ファイルエラー", "ファイルが存在しないか読み取り権限がありません")
                        continue
                        
                    self.selected_file = path
                    self.file_edit.setText(os.path.basename(path))
                    break
        except Exception as e:
            logging.exception("ドロップ処理エラー")
            QMessageBox.critical(self, "エラー", f"ファイル処理中にエラーが発生しました: {str(e)}")

    # ------------------------------ Slots ------------------------------
    def _on_select_file(self):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Excelファイルを選択", "", "Excel Files (*.xlsx *.xls)")
            if path:
                # パス検証
                if not self._is_safe_file_path(path):
                    QMessageBox.warning(self, "ファイルエラー", "不正なファイルパスです")
                    return
                    
                # ファイル存在確認
                if not os.path.exists(path) or not os.access(path, os.R_OK):
                    QMessageBox.warning(self, "ファイルエラー", "ファイルが存在しないか読み取り権限がありません")
                    return
                    
                self.selected_file = path
                self.file_edit.setText(os.path.basename(path))
        except Exception as e:
            logging.exception("ファイル選択エラー")
            QMessageBox.critical(self, "エラー", f"ファイル選択中にエラーが発生しました: {str(e)}")

    def _on_import_clicked(self):
        # 入力内容取得
        project_mode = "existing"
        project_id = self.combo_project.currentData()
        project_name = self.combo_project.currentText()

        excel_path = self.selected_file
        overwrite = self.radio_overwrite.isChecked()

        # バリデーション
        if not excel_path or not os.path.exists(excel_path):
            QMessageBox.warning(self, "ファイル未選択", "Excelファイルを選択してください")
            return
        # プロジェクト未選択チェック
        if project_id is None:
            QMessageBox.warning(self, "プロジェクト未選択", "取り込み先プロジェクトを選択してください")
            return

        # インポート処理
        widget = ScenarioCreationWidget()
        result_list = []
        try:
            # 既存プロジェクトへのインポートのみ
            result_list = widget.import_projects_from_excel_dialog(
                 excel_path=excel_path,
                 project_mode="existing",
                 project_id=project_id,
                 project_name=project_name,
                 overwrite=overwrite,
             )
            self._set_result(result_list)
            QMessageBox.information(self, "インポート完了", "Excelからのインポートが完了しました。結果を確認してください。")
            # 完了通知
            self.import_completed.emit()
        except Exception as e:
            QMessageBox.critical(self, "インポートエラー", f"Excelインポート中にエラーが発生しました:\n{str(e)}")

    # ------------------------------ Helpers ------------------------------
    def _set_result(self, result_list):
        self.result_table.setRowCount(len(result_list))
        for i, row in enumerate(result_list):
            self.result_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.result_table.setItem(i, 1, QTableWidgetItem(row.get("screen", "-")))
            self.result_table.setItem(i, 2, QTableWidgetItem(row.get("name", "-")))
            status_item = QTableWidgetItem(row.get("status", "-"))
            if row.get("status") == "成功":
                status_item.setForeground(QColor('darkgreen'))
            elif row.get("status") == "失敗":
                status_item.setForeground(QColor('red'))
            self.result_table.setItem(i, 3, status_item)
            self.result_table.setItem(i, 4, QTableWidgetItem(row.get("message", "-")))

    def _is_safe_file_path(self, path: str) -> bool:
        try:
            normalized_path = os.path.normpath(os.path.abspath(path))
            
            if '..' in path or path.startswith('/') and not os.name == 'nt':
                return False
            
            if not path.lower().endswith(('.xlsx', '.xls')):
                return False
                
            return True
        except Exception:
            return False

    def _load_projects(self):
        """DB からプロジェクト一覧を取得し保持"""
        self._project_list = []
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM projects ORDER BY id")
                self._project_list = cur.fetchall()
        except Exception as e:
            logging.exception("プロジェクト一覧取得エラー") 