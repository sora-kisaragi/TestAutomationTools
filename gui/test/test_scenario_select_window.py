"""
テスト実行シナリオ選択ウインドウ
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
import sqlite3
from core import scenario_db
from .test_execution_window import TestExecutionWindow

class TestScenarioSelectWindow(QWidget):
    """
    プロジェクト・画面・シナリオ選択→テスト実行ウインドウ呼び出し
    未入力（未実施）シナリオが上に来るように並べ替え
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("テスト実行シナリオ選択")
        self.setGeometry(250, 250, 600, 400)
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("プロジェクト選択"))
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        layout.addWidget(self.project_combo)
        layout.addWidget(QLabel("画面選択"))
        self.screen_combo = QComboBox()
        self.screen_combo.currentIndexChanged.connect(self._on_screen_changed)
        layout.addWidget(self.screen_combo)
        layout.addWidget(QLabel("シナリオ一覧（未入力優先）"))
        self.scenario_list = QListWidget()
        layout.addWidget(self.scenario_list)
        btn_layout = QHBoxLayout()
        self.exec_btn = QPushButton("テスト実行")
        self.exec_btn.clicked.connect(self._open_test_execution)
        btn_layout.addWidget(self.exec_btn)
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
            self.scenario_list.clear()
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
            self.scenario_list.clear()
            return
        sid = self._screens[idx][0]
        self._load_scenarios(sid)

    def _load_scenarios(self, screen_id):
        self.scenario_list.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT tc.id, tc.name, MIN(ti.result) as min_result
                FROM test_cases tc
                LEFT JOIN test_items ti ON tc.id = ti.test_case_id
                WHERE tc.screen_id=?
                GROUP BY tc.id, tc.name
                ORDER BY CASE WHEN min_result IS NULL OR min_result='' OR min_result='未実施' THEN 0 ELSE 1 END, tc.id
            """, (screen_id,))
            self._scenarios = cur.fetchall()
            for cid, name, _ in self._scenarios:
                self.scenario_list.addItem(name)
        if self._scenarios:
            self.scenario_list.setCurrentRow(0)

    def _open_test_execution(self):
        idx = self.scenario_list.currentRow()
        if idx < 0 or not hasattr(self, '_scenarios') or idx >= len(self._scenarios):
            QMessageBox.warning(self, "エラー", "シナリオを選択してください")
            return
        case_id = self._scenarios[idx][0]
        self.exec_window = TestExecutionWindow(case_id)
        self.exec_window.show()
