"""
テスト管理ウィジェット
画面名・テストケース・操作手順・期待結果・優先度・結果 を一覧し、
詳細ボタンで担当者・実施日・備考を表示する。
個別実行（一つのテストケース単位）と一括実行の導線だけ用意する。
"""
from typing import Optional, List, Dict
import sqlite3

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtGui import QColor

from core import scenario_db
from gui.test.test_execution_window import TestExecutionWindow
from gui.test.test_scenario_select_window import TestScenarioSelectWindow
from gui.test.test_runner import TestRunnerThread


class TestManagementWidget(QWidget):
    """テスト管理一覧ウィジェット"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # DB初期化（未作成時）
        scenario_db.init_db()
        self._init_ui()
        self._load_projects()

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------
    def _init_ui(self) -> None:
        root_layout = QVBoxLayout()
        self.setLayout(root_layout)

        # --- 上部フィルタ＆操作バー --------------------------------------
        top_layout = QHBoxLayout()

        # プロジェクト選択
        top_layout.addWidget(QLabel("プロジェクト:"))
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(180)
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        top_layout.addWidget(self.project_combo)

        # キーワード検索
        top_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("画面名・テストケース名・操作手順など")
        self.search_edit.returnPressed.connect(self._reload_table)
        top_layout.addWidget(self.search_edit)
        search_btn = QPushButton("検索")
        search_btn.clicked.connect(self._reload_table)
        top_layout.addWidget(search_btn)

        # Stretch
        top_layout.addStretch()

        # 一括実行ボタンのみ
        self.bulk_exec_btn = QPushButton("一括実行")
        self.bulk_exec_btn.clicked.connect(self._exec_bulk)
        top_layout.addWidget(self.bulk_exec_btn)

        root_layout.addLayout(top_layout)

        # --- テーブル ----------------------------------------------------
        self.table = QTableWidget()
        self.table.setColumnCount(8)  # 6列 + 詳細 + 実行ボタン
        self.table.setHorizontalHeaderLabels([
            "画面名",
            "テストケース",
            "操作手順",
            "期待結果",
            "優先度",
            "結果",
            "詳細",
            "実行",
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # 優先度・結果列は内容に合わせて縮小
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        # 1行表示で高さが変わらないように設定
        self.table.setWordWrap(False)
        self.table.verticalHeader().setDefaultSectionSize(24)

        root_layout.addWidget(self.table)

    # ----- ユーティリティ -------------------------------------------------
    def _shorten(self, text: str, max_len: int = 40) -> str:
        """セル表示用に文字列を切り詰め。max_len 以上なら末尾に…を付加"""
        if text and len(text) > max_len:
            return text[:max_len] + "…"
        return text

    # ---------------------------------------------------------------------
    # Data Loading
    # ---------------------------------------------------------------------
    def _load_projects(self) -> None:
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self._project_list: List[tuple] = []
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM projects ORDER BY id")
                for pid, name in cur.fetchall():
                    self.project_combo.addItem(name, pid)
                    self._project_list.append((pid, name))
        except Exception as e:
            # DB error – show placeholder
            self.project_combo.addItem("(DBエラー)")
        self.project_combo.blockSignals(False)
        if self._project_list:
            self.project_combo.setCurrentIndex(0)
        # 初期データ読み込み
        self._reload_table()

    def _on_project_changed(self):
        self._reload_table()

    def _reload_table(self):
        keyword = self.search_edit.text().strip()
        proj_idx = self.project_combo.currentIndex()
        project_id = None
        if 0 <= proj_idx < len(self._project_list):
            project_id = self._project_list[proj_idx][0]
        self._load_tests(keyword, project_id)

    def _load_tests(self, keyword: str = "", project_id: Optional[int] = None) -> None:
        self.table.clearContents()
        self.table.setRowCount(0)
        self._data: List[Dict] = []

        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                base_sql = """
                    SELECT
                        ti.id,
                        s.name AS screen_name,
                        tc.name AS test_case_name,
                        COALESCE(ti.operation, '') AS operation,
                        COALESCE(ti.expected, '') AS expected,
                        COALESCE(ti.priority, '') AS priority,
                        COALESCE(ti.result, '未実施') AS result,
                        COALESCE(ti.tester, '') AS tester,
                        COALESCE(ti.exec_date, '') AS exec_date,
                        COALESCE(ti.remarks, '') AS remarks,
                        tc.id AS test_case_id
                    FROM test_items ti
                    JOIN test_cases tc ON ti.test_case_id = tc.id
                    JOIN screens s ON tc.screen_id = s.id
                """
                params: List = []
                if project_id is not None:
                    base_sql += " WHERE s.project_id = ?"
                    params.append(project_id)
                base_sql += " ORDER BY s.name, tc.id, ti.id"
                cur.execute(base_sql, params)
                rows = cur.fetchall()
                for r in rows:
                    self._data.append({
                        "item_id": r[0],
                        "screen_name": r[1],
                        "test_case_name": r[2],
                        "operation": r[3],
                        "expected": r[4],
                        "priority": r[5],
                        "result": r[6],
                        "tester": r[7],
                        "exec_date": r[8],
                        "remarks": r[9],
                        "test_case_id": r[10],
                    })
        except Exception as e:
            print(f"DB読み込みエラー: {e}")

        # キーワードフィルタ
        if keyword:
            kw = keyword.lower()
            self._data = [d for d in self._data if any(kw in str(v).lower() for v in (
                d["screen_name"], d["test_case_name"], d["operation"], d["expected"], d["priority"], d["result"]))]

        # テーブルに反映
        self.table.setRowCount(len(self._data))
        for row, d in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(d["screen_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(d["test_case_name"]))
            op_item = QTableWidgetItem(self._shorten(d["operation"]))
            op_item.setToolTip(d["operation"])
            self.table.setItem(row, 2, op_item)

            exp_item = QTableWidgetItem(self._shorten(d["expected"]))
            exp_item.setToolTip(d["expected"])
            self.table.setItem(row, 3, exp_item)
            # priority colouring
            pr_item = QTableWidgetItem(d["priority"])
            if d["priority"] == "高":
                pr_item.setForeground(QColor("red"))
            elif d["priority"] == "中":
                pr_item.setForeground(QColor("orange"))
            elif d["priority"] == "低":
                pr_item.setForeground(QColor("blue"))
            self.table.setItem(row, 4, pr_item)
            # result colouring
            res_item = QTableWidgetItem(d["result"])
            if d["result"] == "成功":
                res_item.setForeground(QColor("green"))
            elif d["result"] == "失敗":
                res_item.setForeground(QColor("red"))
            elif d["result"] == "要確認":
                res_item.setForeground(QColor("orange"))
            self.table.setItem(row, 5, res_item)

            # 詳細ボタン
            detail_btn = QPushButton("詳細")
            detail_btn.setFixedWidth(50)
            detail_btn.clicked.connect(lambda _=False, r=row: self._show_detail(r))
            self.table.setCellWidget(row, 6, detail_btn)

            # 実行ボタン
            exec_btn = QPushButton("実行")
            exec_btn.setFixedWidth(50)
            exec_btn.clicked.connect(lambda _=False, r=row: self._exec_row(r))
            self.table.setCellWidget(row, 7, exec_btn)

        # 行高は固定なので再計算不要

        # 行ヘッダー非表示
        vh = self.table.verticalHeader()
        if vh:
            vh.setVisible(False)

    # ------------------------------------------------------------------
    # Detail Dialog
    # ------------------------------------------------------------------
    def _show_detail(self, row: int):
        if not (0 <= row < len(self._data)):
            return
        d = self._data[row]
        msg = (
            "操作手順:\n" + (d["operation"] or "-") + "\n\n"
            "期待結果:\n" + (d["expected"] or "-") + "\n\n"
            f"優先度: {d['priority'] or '-'}\n"
            f"担当者: {d['tester'] or '-'}\n"
            f"実施日: {d['exec_date'] or '-'}\n"
            f"備考  : {d['remarks'] or '-'}"
        )
        QMessageBox.information(self, "詳細", msg)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def _exec_bulk(self):
        # 既存のシナリオ選択ウィンドウを再利用
        select_win = TestScenarioSelectWindow(self)
        select_win.show()

    def _open_execution(self, test_case_id: int):
        exec_win = TestExecutionWindow(test_case_id, self)
        exec_win.show()

    def _exec_row(self, row: int):
        """テーブル行単位の実行ボタン処理"""
        if not (0 <= row < len(self._data)):
            return
        self._run_auto(self._data[row]["test_case_id"])

    # ---------------- 自動実行 -----------------
    def _run_auto(self, test_case_id: int):
        thread = TestRunnerThread(test_case_id, self)
        thread.finished_signal.connect(self._on_run_finished)
        thread.start()
        # UI を一時的に無効化
        self._set_running_state(True)
        # Keep reference to avoid GC
        if not hasattr(self, "_threads"):
            self._threads = []
        self._threads.append(thread)

    def _on_run_finished(self, test_case_id: int, success: bool, log_text: str):
        # Clean finished threads
        self._threads = [t for t in getattr(self, "_threads", []) if t.isRunning()]
        # すべてのスレッドが終了したら UI を再有効化
        if not self._threads:
            self._set_running_state(False)
        status = "成功" if success else "失敗"
        QMessageBox.information(self, "自動実行完了", f"TestCase {test_case_id}: {status}\n----\n{log_text}")
        # Reload to reflect DB updates
        self._reload_table()

    def _set_running_state(self, running: bool):
        """実行ボタン群とテーブルの有効/無効を切り替え"""
        self.bulk_exec_btn.setEnabled(not running)
        self.table.setEnabled(not running) 