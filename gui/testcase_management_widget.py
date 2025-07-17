"""
テストケース管理ウィジェット
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
from core import scenario_db
from gui.common.utils import get_text_dialog, get_selected_rows_from_listwidget
import sqlite3

class TestCaseManagementWidget(QWidget):
    """
    テストケース管理用ウィジェット
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("テストケース管理画面"))

        # プロジェクト選択
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo)

        # 画面（シナリオ）選択
        self.screen_combo = QComboBox()
        self.screen_combo.currentIndexChanged.connect(self._on_screen_changed)
        layout.addWidget(self.screen_combo)

        # テストケース一覧
        self.case_list = QListWidget()
        # 複数選択を有効化
        self.case_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.case_list)

        # ボタン
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("テストケース追加")
        self.add_btn.clicked.connect(self._add_case)
        btn_layout.addWidget(self.add_btn)
        self.del_btn = QPushButton("テストケース削除")
        self.del_btn.clicked.connect(self._delete_case)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def _load_projects(self):
        self.project_combo.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM projects ORDER BY id")
            self._projects = cur.fetchall()
            for pid, name in self._projects:
                self.project_combo.addItem(name, pid)
        self._on_project_changed()

    def _on_project_changed(self):
        idx = self.project_combo.currentIndex()
        if idx < 0 or not hasattr(self, '_projects') or idx >= len(self._projects):
            self.screen_combo.clear()
            self.case_list.clear()
            return
        pid = self._projects[idx][0]
        self._load_screens(pid)

    def _load_screens(self, project_id):
        self.screen_combo.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM screens WHERE project_id=? ORDER BY id", (project_id,))
            self._screens = cur.fetchall()
            for sid, name in self._screens:
                self.screen_combo.addItem(name, sid)
        self._on_screen_changed()

    def _on_screen_changed(self):
        idx = self.screen_combo.currentIndex()
        if idx < 0 or not hasattr(self, '_screens') or idx >= len(self._screens):
            self.case_list.clear()
            return
        sid = self._screens[idx][0]
        self._load_cases(sid)

    def _load_cases(self, screen_id):
        self.case_list.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM test_cases WHERE screen_id=? ORDER BY id", (screen_id,))
            self._cases = cur.fetchall()
            for cid, name in self._cases:
                self.case_list.addItem(name)
        if self._cases:
            self.case_list.setCurrentRow(0)

    def _add_case(self):
        sidx = self.screen_combo.currentIndex()
        if sidx < 0 or not hasattr(self, '_screens') or sidx >= len(self._screens):
            QMessageBox.warning(self, "エラー", "画面（シナリオ）を選択してください")
            return
        sid = self._screens[sidx][0]
        name, ok = get_text_dialog(self, "新規テストケース名を入力してください")
        if ok and name:
            name = name.strip()
            if not name or len(name) > 100:
                QMessageBox.warning(self, "エラー", "テストケース名は1～100文字で入力してください")
                return
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO test_cases (screen_id, name) VALUES (?, ?)", (sid, name))
                    conn.commit()
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "エラー", "同名のテストケースが既に存在します")
            self._load_cases(sid)

    def _delete_case(self):
        sidx = self.screen_combo.currentIndex()
        if sidx < 0 or not hasattr(self, '_screens') or sidx >= len(self._screens):
            QMessageBox.warning(self, "エラー", "画面（シナリオ）を選択してください")
            return
        sid = self._screens[sidx][0]
        # 共通関数で選択データ取得
        delete_targets = get_selected_rows_from_listwidget(self.case_list, getattr(self, '_cases', []))
        if not delete_targets:
            QMessageBox.warning(self, "エラー", "削除するテストケースを選択してください")
            return
        names = ', '.join([name for _, name in delete_targets])
        reply = QMessageBox.question(
            self,
            "確認",
            f"選択したテストケース({names})を削除しますか？\n関連するテスト項目も全て削除されます。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                errors = []
                for cid, name in delete_targets:
                    try:
                        # テスト項目削除
                        cur.execute("DELETE FROM test_items WHERE test_case_id=?", (cid,))
                        # テストケース削除
                        cur.execute("DELETE FROM test_cases WHERE id=?", (cid,))
                    except Exception as e:
                        errors.append(f"{name}: {str(e)}")
                conn.commit()
                if errors:
                    QMessageBox.critical(self, "エラー", "\n".join(errors))
                else:
                    QMessageBox.information(self, "削除完了", f"選択したテストケースを削除しました")
            self._load_cases(sid)
