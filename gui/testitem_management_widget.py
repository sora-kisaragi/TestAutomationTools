"""
テスト項目管理ウィジェット
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
from core import scenario_db
from gui.common.utils import get_text_dialog, get_selected_rows_from_listwidget
import sqlite3

class TestItemManagementWidget(QWidget):
    """
    テスト項目管理用ウィジェット
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("テスト項目管理画面"))

        # プロジェクト選択
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo)

        # 画面（シナリオ）選択
        self.screen_combo = QComboBox()
        self.screen_combo.currentIndexChanged.connect(self._on_screen_changed)
        layout.addWidget(self.screen_combo)

        # テストケース選択
        self.case_combo = QComboBox()
        self.case_combo.currentIndexChanged.connect(self._on_case_changed)
        layout.addWidget(self.case_combo)

        # テスト項目一覧
        self.item_list = QListWidget()
        # 複数選択を有効化
        self.item_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.item_list)

        # ボタン
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("テスト項目追加")
        self.add_btn.clicked.connect(self._add_item)
        btn_layout.addWidget(self.add_btn)
        self.del_btn = QPushButton("テスト項目削除")
        self.del_btn.clicked.connect(self._delete_item)
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
            self.case_combo.clear()
            self.item_list.clear()
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
            self.case_combo.clear()
            self.item_list.clear()
            return
        sid = self._screens[idx][0]
        self._load_cases(sid)

    def _load_cases(self, screen_id):
        self.case_combo.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM test_cases WHERE screen_id=? ORDER BY id", (screen_id,))
            self._cases = cur.fetchall()
            for cid, name in self._cases:
                self.case_combo.addItem(name, cid)
        self._on_case_changed()

    def _on_case_changed(self):
        idx = self.case_combo.currentIndex()
        if idx < 0 or not hasattr(self, '_cases') or idx >= len(self._cases):
            self.item_list.clear()
            return
        cid = self._cases[idx][0]
        self._load_items(cid)

    def _load_items(self, case_id):
        self.item_list.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM test_items WHERE test_case_id=? ORDER BY id", (case_id,))
            self._items = cur.fetchall()
            for iid, name in self._items:
                self.item_list.addItem(name)
        if self._items:
            self.item_list.setCurrentRow(0)

    def _add_item(self):
        cidx = self.case_combo.currentIndex()
        if cidx < 0 or not hasattr(self, '_cases') or cidx >= len(self._cases):
            QMessageBox.warning(self, "エラー", "テストケースを選択してください")
            return
        cid = self._cases[cidx][0]
        name, ok = get_text_dialog(self, "新規テスト項目名を入力してください")
        if ok and name:
            name = name.strip()
            if not name or len(name) > 100:
                QMessageBox.warning(self, "エラー", "テスト項目名は1～100文字で入力してください")
                return
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO test_items (test_case_id, name) VALUES (?, ?)", (cid, name))
                    conn.commit()
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "エラー", "同名のテスト項目が既に存在します")
            self._load_items(cid)

    def _delete_item(self):
        cidx = self.case_combo.currentIndex()
        if cidx < 0 or not hasattr(self, '_cases') or cidx >= len(self._cases):
            QMessageBox.warning(self, "エラー", "テストケースを選択してください")
            return
        cid = self._cases[cidx][0]
        # 共通関数で選択データ取得
        delete_targets = get_selected_rows_from_listwidget(self.item_list, getattr(self, '_items', []))
        if not delete_targets:
            QMessageBox.warning(self, "エラー", "削除するテスト項目を選択してください")
            return
        names = ', '.join([name for _, name in delete_targets])
        reply = QMessageBox.question(
            self,
            "確認",
            f"選択したテスト項目({names})を削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                errors = []
                for iid, name in delete_targets:
                    try:
                        cur.execute("DELETE FROM test_items WHERE id=?", (iid,))
                    except Exception as e:
                        errors.append(f"{name}: {str(e)}")
                conn.commit()
                if errors:
                    QMessageBox.critical(self, "エラー", "\n".join(errors))
                else:
                    QMessageBox.information(self, "削除完了", f"選択したテスト項目を削除しました")
            self._load_items(cid)
