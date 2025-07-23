from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QListWidget, QMessageBox, QLineEdit
from PyQt5.QtCore import Qt
import sqlite3
from core import scenario_db
from gui.common.utils import get_text_dialog

class ProjectCreationWidget(QWidget):
    """プロジェクト追加専用ウィジェット（削除は不可）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        scenario_db.init_db()
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("プロジェクト作成"))

        self.project_list = QListWidget()
        layout.addWidget(self.project_list)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("追加")
        self.add_btn.clicked.connect(self._add_project)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_projects(self):
        self.project_list.clear()
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM projects ORDER BY id")
                self._projects = cur.fetchall()
                for pid, name in self._projects:
                    self.project_list.addItem(name)
        except Exception:
            pass

    def _add_project(self):
        name, ok = get_text_dialog(self, "新規プロジェクト名を入力してください")
        if ok and name:
            name = name.strip()
            if not name or len(name) > 100:
                QMessageBox.warning(self, "エラー", "プロジェクト名は1～100文字で入力してください")
                return
            try:
                with sqlite3.connect(scenario_db.DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO projects (name) VALUES (?)", (name,))
                    conn.commit()
                self._load_projects()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "エラー", "同名のプロジェクトが既に存在します") 