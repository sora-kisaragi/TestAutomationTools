"""
テスト実行専用ウインドウ
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
import sqlite3
from core import scenario_db

class TestExecutionWindow(QWidget):
    """
    テスト実行専用ウインドウ
    """
    def __init__(self, test_case_id: int, parent=None):
        super().__init__(parent)
        self.test_case_id = test_case_id
        self.setWindowTitle("テスト実行ウインドウ")
        self.setGeometry(200, 200, 1000, 600)
        self._init_ui()
        self._load_test_items()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel("テスト項目一覧（テスト実施・記録）")
        layout.addWidget(self.label)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "No", "テスト項目", "入力データ", "操作手順", "期待結果", "優先度", "担当者", "実施日", "結果", "不具合ID", "備考"
        ])
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)
        layout.addWidget(self.table)

        # ボタン
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("結果保存")
        self.save_btn.clicked.connect(self._save_results)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _load_test_items(self):
        # DBからテスト項目を取得
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, input_data, operation, expected, priority, assignee, exec_date, result, bug_id, remarks
                FROM test_items WHERE test_case_id=? ORDER BY id
            """, (self.test_case_id,))
            items = cur.fetchall()
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            for col, value in enumerate(item):
                # bug_idは整数型。表示時はBUG-0001形式に変換
                if col == 9 and value is not None and str(value).isdigit():
                    cell = QTableWidgetItem(f"BUG-{int(value):04d}")
                else:
                    cell = QTableWidgetItem(str(value) if value is not None else "")
                if col == 0:
                    cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Noは編集不可
                self.table.setItem(row, col, cell)

    def _save_results(self):
        # テーブルの内容をDBに保存
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            for row in range(self.table.rowCount()):
                item_id = self.table.item(row, 0).text()
                values = []
                for col in range(1, 11):
                    val = self.table.item(row, col).text() if self.table.item(row, col) else None
                    # bug_id欄（col==9）はBUG-0001形式→整数に変換
                    if col == 9 and val and val.startswith("BUG-"):
                        try:
                            val = int(val.replace("BUG-", ""))
                        except Exception:
                            val = None
                    values.append(val)
                cur.execute("""
                    UPDATE test_items SET
                        name=?, input_data=?, operation=?, expected=?, priority=?, assignee=?, exec_date=?, result=?, bug_id=?, remarks=?
                    WHERE id=?
                """, (*values, item_id))
            conn.commit()
        QMessageBox.information(self, "保存完了", "テスト結果を保存しました")
