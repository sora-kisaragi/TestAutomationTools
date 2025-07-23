from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QListWidget, QMessageBox, QAbstractItemView
import sqlite3
from core import scenario_db
from gui.common.utils import get_selected_rows_from_listwidget

class ProjectDeleteWidget(QWidget):
    """プロジェクト削除専用ウィジェット（追加は不可）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        scenario_db.init_db()
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("プロジェクト削除"))
        self.project_list = QListWidget()
        self.project_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.project_list)
        btn_layout = QHBoxLayout()
        self.del_btn = QPushButton("削除")
        self.del_btn.clicked.connect(self._delete_project)
        btn_layout.addWidget(self.del_btn)
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

    def _delete_project(self):
        delete_targets = get_selected_rows_from_listwidget(self.project_list, getattr(self, '_projects', []))
        if not delete_targets:
            QMessageBox.warning(self, "エラー", "削除するプロジェクトを選択してください")
            return
        names = ', '.join([name for _, name in delete_targets])
        reply = QMessageBox.question(
            self,
            "確認",
            f"選択したプロジェクト({names})を削除しますか？\n関連する画面・テストケース・テスト項目も全て削除されます。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            errors = []
            for pid, name in delete_targets:
                try:
                    scenario_db.delete_project(pid)
                except Exception as e:
                    errors.append(f"{name}: {str(e)}")
            if errors:
                QMessageBox.critical(self, "エラー", "\n".join(errors))
            else:
                QMessageBox.information(self, "削除完了", "選択したプロジェクトを削除しました")
            self._load_projects() 