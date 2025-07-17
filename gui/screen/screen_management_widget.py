"""
画面（シナリオ）管理ウィジェット
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
from core import scenario_db
from gui.common.utils import get_text_dialog, get_selected_rows_from_listwidget
import sqlite3

class ScreenManagementWidget(QWidget):
    """
    画面（シナリオ）管理用ウィジェット
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("画面（シナリオ）管理画面"))

        # プロジェクト選択
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo)

        # 画面一覧
        self.screen_list = QListWidget()
        # 複数選択を有効化
        self.screen_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.screen_list)

        # ボタン
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("画面追加")
        self.add_btn.clicked.connect(self._add_screen)
        btn_layout.addWidget(self.add_btn)
        self.del_btn = QPushButton("画面削除")
        self.del_btn.clicked.connect(self._delete_screen)
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
            self.screen_list.clear()
            return
        pid = self._projects[idx][0]
        self._load_screens(pid)

    def _load_screens(self, project_id):
        self.screen_list.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM screens WHERE project_id=? ORDER BY id", (project_id,))
            self._screens = cur.fetchall()
            for sid, name in self._screens:
                self.screen_list.addItem(name)
        if self._screens:
            self.screen_list.setCurrentRow(0)

    def _add_screen(self):
        idx = self.project_combo.currentIndex()
        if idx < 0 or not hasattr(self, '_projects') or idx >= len(self._projects):
            QMessageBox.warning(self, "エラー", "プロジェクトを選択してください")
            return
        pid = self._projects[idx][0]
        name, ok = get_text_dialog(self, "新規画面名を入力してください")
        if ok and name:
            name = name.strip()
            if not name or len(name) > 100:
                QMessageBox.warning(self, "エラー", "画面名は1～100文字で入力してください")
                return
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO screens (project_id, name) VALUES (?, ?)", (pid, name))
                    conn.commit()
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "エラー", "同名の画面が既に存在します")
            self._load_screens(pid)

    def _delete_screen(self):
        pidx = self.project_combo.currentIndex()
        if pidx < 0 or not hasattr(self, '_projects') or pidx >= len(self._projects):
            QMessageBox.warning(self, "エラー", "プロジェクトを選択してください")
            return
        pid = self._projects[pidx][0]
        # 共通関数で選択データ取得
        delete_targets = get_selected_rows_from_listwidget(self.screen_list, getattr(self, '_screens', []))
        if not delete_targets:
            QMessageBox.warning(self, "エラー", "削除する画面を選択してください")
            return
        names = ', '.join([name for _, name in delete_targets])
        reply = QMessageBox.question(
            self,
            "確認",
            f"選択した画面({names})を削除しますか？\n関連するテストケース・テスト項目も全て削除されます。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                errors = []
                for sid, name in delete_targets:
                    try:
                        # テストケースID取得
                        cur.execute("SELECT id FROM test_cases WHERE screen_id=?", (sid,))
                        case_ids = [row[0] for row in cur.fetchall()]
                        # テスト項目削除
                        if case_ids:
                            cur.executemany("DELETE FROM test_items WHERE test_case_id=?", [(cid,) for cid in case_ids])
                        # テストケース削除
                        cur.execute("DELETE FROM test_cases WHERE screen_id=?", (sid,))
                        # 画面削除
                        cur.execute("DELETE FROM screens WHERE id=?", (sid,))
                    except Exception as e:
                        errors.append(f"{name}: {str(e)}")
                conn.commit()
                if errors:
                    QMessageBox.critical(self, "エラー", "\n".join(errors))
                else:
                    QMessageBox.information(self, "削除完了", f"選択した画面を削除しました")
            self._load_screens(pid)
