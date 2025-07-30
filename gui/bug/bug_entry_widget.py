"""
不具合入力用ウィジェット
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit, QScrollArea, QPushButton, QHBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import QDate
import sqlite3
import sys
import os
if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from core import scenario_db
from gui.common.constants import *

class BugEntryWidget(QWidget):
    """
    不具合入力用ウィジェット
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_projects()
        self._load_master_data()

    def _init_ui(self):
        """UI要素の初期化（各部品ごとに分割）"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # フォームレイアウト用のウィジェット
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)

        # スクロールエリア設定
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area)

        # 各部品ごとに初期化
        self._init_project_area()
        self._init_bug_info_area()
        self._init_master_area()
        self._init_date_area()
        self._init_remarks_area()
        self._init_button_area(layout)

    def _init_project_area(self):
        """プロジェクト・画面名エリアの初期化"""
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        self.form_layout.addRow("プロジェクト:", self.project_combo)

        self.screen_name_combo = QComboBox()
        self.form_layout.addRow("画面名:", self.screen_name_combo)

    def _init_bug_info_area(self):
        """不具合ID・発生シナリオ・概要・詳細エリアの初期化"""
        self.bug_id_edit = QLineEdit()
        self.bug_id_edit.setPlaceholderText("BUG-xxxx（自動採番）")
        self.bug_id_edit.setReadOnly(True)
        self.form_layout.addRow("不具合ID:", self.bug_id_edit)

        self.scenario_name_edit = QLineEdit()
        self.form_layout.addRow("発生シナリオ:", self.scenario_name_edit)

        self.summary_edit = QLineEdit()
        self.form_layout.addRow("概要:", self.summary_edit)

        self.details_edit = QTextEdit()
        self.details_edit.setMaximumHeight(100)
        self.form_layout.addRow("詳細:", self.details_edit)

    def _init_master_area(self):
        """原因カテゴリ・重要度・再現性・状態・対応者エリアの初期化"""
        self.cause_category_combo = QComboBox()
        self.form_layout.addRow("原因カテゴリ:", self.cause_category_combo)

        self.severity_combo = QComboBox()
        self.form_layout.addRow("重要度:", self.severity_combo)

        self.reproducibility_combo = QComboBox()
        self.form_layout.addRow("再現性:", self.reproducibility_combo)

        self.status_combo = QComboBox()
        self.form_layout.addRow("状態:", self.status_combo)

        self.assignee_combo = QComboBox()
        self.form_layout.addRow("対応者:", self.assignee_combo)

    def _init_date_area(self):
        """発生日・修正日エリアの初期化"""
        self.reported_date_edit = QDateEdit()
        self.reported_date_edit.setDate(QDate.currentDate())
        self.reported_date_edit.setCalendarPopup(True)
        self.form_layout.addRow("発生日:", self.reported_date_edit)

        self.fix_date_edit = QDateEdit()
        self.fix_date_edit.setDate(QDate.currentDate())
        self.fix_date_edit.setCalendarPopup(True)
        self.form_layout.addRow("修正日:", self.fix_date_edit)

    def _init_remarks_area(self):
        """備考エリアの初期化"""
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(100)
        self.form_layout.addRow("備考:", self.remarks_edit)

    def _init_button_area(self, layout):
        """ボタンエリアの初期化"""
        button_layout = QHBoxLayout()
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self._clear_form)
        button_layout.addWidget(self.clear_button)
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self._save_bug)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def _load_projects(self):
        """プロジェクト一覧をロードし、画面名も連動更新"""
        self.project_combo.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM projects ORDER BY id")
            self._projects = cur.fetchall()
            for pid, name in self._projects:
                self.project_combo.addItem(name, pid)
        self._on_project_changed()

    def _on_project_changed(self):
        """プロジェクト選択時に画面名を更新"""
        self.screen_name_combo.clear()
        idx = self.project_combo.currentIndex()
        if idx < 0 or not hasattr(self, '_projects') or idx >= len(self._projects):
            return
        pid = self._projects[idx][0]
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM screens WHERE project_id=? ORDER BY id", (pid,))
            screens = cur.fetchall()
            for sid, name in screens:
                self.screen_name_combo.addItem(name, sid)

    def _load_master_data(self):
        """マスターデータをコンボボックスにロード（画面名は除外）"""
        # 原因カテゴリ
        cause_categories = scenario_db.get_master_data("master_cause_categories")
        self.cause_category_combo.addItems(cause_categories)
        # 重要度
        severities = scenario_db.get_master_data("master_severities")
        self.severity_combo.addItems(severities)
        # 再現性
        reproducibilities = scenario_db.get_master_data("master_reproducibilities")
        self.reproducibility_combo.addItems(reproducibilities)
        # 状態
        statuses = scenario_db.get_master_data("master_statuses")
        self.status_combo.addItems(statuses)
        # 対応者
        testers = scenario_db.get_master_data("master_testers")
        self.assignee_combo.addItems(testers)

    def _get_form_data(self):
        """フォームデータを辞書型で取得"""
        reported_date = self.reported_date_edit.date().toString("yyyy-MM-dd")
        fix_date = self.fix_date_edit.date().toString("yyyy-MM-dd")
        # project_id取得
        idx = self.project_combo.currentIndex()
        project_id = self.project_combo.itemData(idx) if idx >= 0 else None
        return {
            "project_id": project_id,
            "reported_date": reported_date,
            "screen_name": self.screen_name_combo.currentText(),
            "scenario_name": self.scenario_name_edit.text(),
            "summary": self.summary_edit.text(),
            "details": self.details_edit.toPlainText(),
            "cause_category": self.cause_category_combo.currentText(),
            "severity": self.severity_combo.currentText(),
            "reproducibility": self.reproducibility_combo.currentText(),
            "status": self.status_combo.currentText(),
            "assignee": self.assignee_combo.currentText(),
            "fix_date": fix_date,
            "remarks": self.remarks_edit.toPlainText()
        }

    def _clear_form(self):
        """フォームをクリア"""
        self.bug_id_edit.clear()
        self.scenario_name_edit.clear()
        self.summary_edit.clear()
        self.details_edit.clear()
        self.remarks_edit.clear()
        self.reported_date_edit.setDate(QDate.currentDate())
        self.fix_date_edit.setDate(QDate.currentDate())

    def _save_bug(self):
        """不具合情報を保存"""
        data = self._get_form_data()
        # 必須項目の検証
        if not data["project_id"]:
            QMessageBox.warning(self, "入力エラー", "プロジェクト選択は必須です")
            return
        if not data["summary"]:
            QMessageBox.warning(self, "入力エラー", "概要は必須です")
            return
        # DB保存
        try:
            bug_id_disp = scenario_db.insert_bug(data)
            self.bug_id_edit.setText(bug_id_disp)
            QMessageBox.information(
                self, "保存完了", 
                f"不具合ID: {bug_id_disp} を保存しました"
            )
            self._clear_form()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存に失敗しました: {str(e)}")
