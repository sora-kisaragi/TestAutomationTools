from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
import sqlite3
from core import scenario_db

class ScenarioDeleteWidget(QWidget):
    """既存シナリオを複数選択して削除するウィジェット"""
    def __init__(self, parent=None):
        super().__init__(parent)
        scenario_db.init_db()
        self._init_ui()
        self._load_projects()

    # -------------------- UI --------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)

        # フィルタバー
        filter_layout = QHBoxLayout()
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("プロジェクト:"))
        filter_layout.addWidget(self.project_combo)

        self.screen_combo = QComboBox()
        self.screen_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("画面:"))
        filter_layout.addWidget(self.screen_combo)

        self.keyword_edit = QLineEdit()
        filter_layout.addWidget(QLabel("検索:"))
        filter_layout.addWidget(self.keyword_edit)
        search_btn = QPushButton("検索")
        search_btn.clicked.connect(self._on_filter_changed)
        filter_layout.addWidget(search_btn)
        layout.addLayout(filter_layout)

        # 操作ボタン
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("すべて選択")
        select_all_btn.clicked.connect(lambda: self._select_all(True))
        btn_layout.addWidget(select_all_btn)
        deselect_btn = QPushButton("選択解除")
        deselect_btn.clicked.connect(lambda: self._select_all(False))
        btn_layout.addWidget(deselect_btn)
        delete_btn = QPushButton("選択シナリオを削除")
        delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "", "画面名", "シナリオ名", "ステータス", "最終実行日", "実行結果"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

    # -------------------- Data Load --------------------
    def _load_projects(self):
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self._projects = []
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM projects ORDER BY id")
            self._projects = cur.fetchall()
            for pid, name in self._projects:
                self.project_combo.addItem(name, pid)
        self.project_combo.blockSignals(False)
        self._on_filter_changed()

    def _load_screens(self, project_id):
        self.screen_combo.blockSignals(True)
        self.screen_combo.clear()
        self._screens = []
        if project_id is None:
            self.screen_combo.blockSignals(False)
            return
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM screens WHERE project_id=? ORDER BY id", (project_id,))
            self._screens = cur.fetchall()
            self.screen_combo.addItem("(すべて)", None)
            for sid, name in self._screens:
                self.screen_combo.addItem(name, sid)
        self.screen_combo.blockSignals(False)

    def _load_table(self):
        project_id = self.project_combo.currentData()
        screen_id = self.screen_combo.currentData()
        keyword = self.keyword_edit.text().strip().lower()

        self.table.setRowCount(0)
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            sql = (
                "SELECT tc.id, s.name, tc.name, tc.status, tc.last_run, tc.result "
                "FROM test_cases tc JOIN screens s ON tc.screen_id=s.id "
                "WHERE 1=1 "
            )
            params = []
            if project_id:
                sql += "AND s.project_id=? "
                params.append(project_id)
            if screen_id:
                sql += "AND s.id=? "
                params.append(screen_id)
            sql += "ORDER BY tc.id"
            cur.execute(sql, params)
            rows = cur.fetchall()

        for row_idx, (cid, screen_name, scenario_name, status, last_run, result) in enumerate(rows):
            if keyword and keyword not in scenario_name.lower():
                continue
            self.table.insertRow(self.table.rowCount())
            # チェックボックス
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Unchecked)
            chk_item.setData(Qt.UserRole, cid)
            self.table.setItem(row_idx, 0, chk_item)
            # 他の列
            self.table.setItem(row_idx, 1, QTableWidgetItem(screen_name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(scenario_name))
            self.table.setItem(row_idx, 3, QTableWidgetItem(status or '-'))
            self.table.setItem(row_idx, 4, QTableWidgetItem(last_run or '-'))
            self.table.setItem(row_idx, 5, QTableWidgetItem(result or '-'))

    # -------------------- Slots --------------------
    def _on_filter_changed(self):
        project_id = self.project_combo.currentData()
        self._load_screens(project_id)
        self._load_table()

    def _select_all(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(state)

    def _delete_selected(self):
        cids = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                cid = item.data(Qt.UserRole)
                cids.append(cid)
        if not cids:
            QMessageBox.information(self, "確認", "削除するシナリオを選択してください")
            return
        reply = QMessageBox.question(
            self, "確認", f"選択した {len(cids)} 件のシナリオを削除しますか？", QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            for cid in cids:
                cur.execute("DELETE FROM test_items WHERE test_case_id=?", (cid,))
                cur.execute("DELETE FROM test_cases WHERE id=?", (cid,))
            conn.commit()
        QMessageBox.information(self, "削除完了", f"{len(cids)} 件のシナリオを削除しました")
        self._load_table() 