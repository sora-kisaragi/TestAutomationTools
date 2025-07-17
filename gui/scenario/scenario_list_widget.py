"""
シナリオ一覧表示ウィジェット
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import scenario_db
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout, QLineEdit, QLabel, QComboBox
from PyQt5.QtCore import Qt

class ScenarioListWidget(QWidget):
    """
    シナリオ一覧表示ウィジェット
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_projects()
        
    def _init_ui(self):
        """UI要素の初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # プロジェクト選択＋現在のプロジェクト名表示
        proj_layout = QHBoxLayout()
        self.project_label = QLabel("プロジェクト:")
        self.project_combo = QComboBox()
        self.project_combo.setEditable(True)
        self.project_combo.setInsertPolicy(QComboBox.NoInsert)
        self.project_combo.setPlaceholderText("プロジェクト名を検索または選択")
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setMaxVisibleItems(15)
        self.project_combo.lineEdit().editingFinished.connect(self._on_project_search)
        self.project_combo.currentIndexChanged.connect(self._on_project_selected)
        self.current_project = QLabel("現在: -")
        proj_layout.addWidget(self.project_label)
        proj_layout.addWidget(self.project_combo)
        proj_layout.addWidget(self.current_project)
        proj_layout.addStretch()
        layout.addLayout(proj_layout)

        # 上部ボタンエリア
        btn_area = QHBoxLayout()
        self.btn_new = QPushButton("新規作成")
        self.btn_import = QPushButton("Excelインポート")
        self.btn_import.clicked.connect(self._on_excel_import)
        self.btn_export = QPushButton("Excelエクスポート")
        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self._on_refresh)
        btn_area.addWidget(self.btn_new)
        btn_area.addWidget(self.btn_import)
        btn_area.addWidget(self.btn_export)
        btn_area.addWidget(self.refresh_button)
        btn_area.addStretch()
        layout.addLayout(btn_area)

        # 検索欄
        search_layout = QHBoxLayout()
        search_label = QLabel("検索キーワード:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("シナリオ名・画面名・担当者など")
        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self._on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "No", "シナリオ名", "ステータス", "最終実行日", "実行結果", "プロジェクト", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        layout.addWidget(self.table)
    
    def _on_search(self):
        """検索ボタン押下時の処理"""
        keyword = self.search_edit.text().strip()
        self._load_scenarios(keyword)
    
    def _load_projects(self):
        """DBからプロジェクト一覧を取得しコンボボックスにセット"""
        import sqlite3
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self._project_list = []
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM projects ORDER BY id")
                for pid, name in cur.fetchall():
                    self.project_combo.addItem(name, pid)
                    self._project_list.append((pid, name))
        except Exception as e:
            self.project_combo.addItem("(DBエラー)")
        self.project_combo.blockSignals(False)
        if self._project_list:
            self.project_combo.setCurrentIndex(0)
            self.current_project.setText(f"現在: {self._project_list[0][1]}")
        else:
            self.current_project.setText("現在: -")

    def _on_project_selected(self, idx: int):
        """プロジェクト選択時の処理"""
        if hasattr(self, '_project_list') and 0 <= idx < len(self._project_list):
            pid, name = self._project_list[idx]
            self.current_project.setText(f"現在: {name}")
            self._load_scenarios(project_id=pid)
        else:
            self.current_project.setText("現在: -")
            self._load_scenarios()

    def _on_project_search(self):
        """プロジェクト名検索時の処理（エディットボックスでEnter/フォーカスアウト時）"""
        text = self.project_combo.currentText().strip()
        if not text or not hasattr(self, '_project_list'):
            return
        # 完全一致優先、部分一致で最も近いものを選択
        idx = -1
        for i, (pid, name) in enumerate(self._project_list):
            if name == text:
                idx = i
                break
        if idx == -1:
            # 部分一致（前方一致→部分一致）
            for i, (pid, name) in enumerate(self._project_list):
                if name.startswith(text):
                    idx = i
                    break
        if idx == -1:
            for i, (pid, name) in enumerate(self._project_list):
                if text in name:
                    idx = i
                    break
        if idx >= 0:
            self.project_combo.setCurrentIndex(idx)
        else:
            # 一致なし
            self.current_project.setText("現在: - (該当なし)")
            self._load_scenarios()

    def _load_scenarios(self, keyword: str = "", project_id: int = None):
        """シナリオ一覧を取得してテーブルに表示（キーワード・プロジェクト対応）"""
        import sqlite3
        scenarios = []
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                if project_id:
                    cur.execute("""
                        SELECT id, scenario_name, status, last_run, result, project_id
                        FROM scenarios WHERE project_id=?
                        ORDER BY id
                    """, (project_id,))
                else:
                    cur.execute("""
                        SELECT id, scenario_name, status, last_run, result, project_id
                        FROM scenarios ORDER BY id
                    """)
                for row in cur.fetchall():
                    scenarios.append({
                        'id': row[0],
                        'scenario_name': row[1],
                        'status': row[2],
                        'last_run': row[3],
                        'result': row[4],
                        'project': self._get_project_name(row[5])
                    })
        except Exception as e:
            print(f"DBエラー: {e}")
        if keyword:
            keyword_lower = keyword.lower()
            scenarios = [s for s in scenarios if
                keyword_lower in str(s['scenario_name']).lower() or
                keyword_lower in str(s['project']).lower()
            ]
        self.table.setRowCount(len(scenarios))
        for row, scenario in enumerate(scenarios):
            self.table.setItem(row, 0, QTableWidgetItem(str(row+1)))
            self.table.setItem(row, 1, QTableWidgetItem(scenario['scenario_name']))
            # ステータス色分け
            status_item = QTableWidgetItem(scenario.get('status', '-'))
            if scenario.get('status') == '合格':
                status_item.setForeground(Qt.green)
            elif scenario.get('status') == '不合格':
                status_item.setForeground(Qt.red)
            self.table.setItem(row, 2, status_item)
            self.table.setItem(row, 3, QTableWidgetItem(scenario.get('last_run', '-')))
            # 実行結果色分け
            result_item = QTableWidgetItem(scenario.get('result', '-'))
            if scenario.get('result') == '合格':
                result_item.setForeground(Qt.green)
            elif scenario.get('result') == '不合格':
                result_item.setForeground(Qt.red)
            self.table.setItem(row, 4, result_item)
            self.table.setItem(row, 5, QTableWidgetItem(scenario.get('project', '-')))
            # 操作ボタン
            op_widget = QWidget()
            op_layout = QHBoxLayout(op_widget)
            btn_detail = QPushButton("詳細")
            btn_edit = QPushButton("編集")
            btn_exec = QPushButton("実行")
            op_layout.addWidget(btn_detail)
            op_layout.addWidget(btn_edit)
            op_layout.addWidget(btn_exec)
            op_layout.setContentsMargins(0,0,0,0)
            op_layout.addStretch()
            self.table.setCellWidget(row, 6, op_widget)

    def _get_project_name(self, project_id):
        if not hasattr(self, '_project_list'):
            return "-"
        for pid, name in self._project_list:
            if pid == project_id:
                return name
        return "-"

    def _on_excel_import(self):
        """
        Excelインポートダイアログを表示（インポート処理はダイアログ内で完結）
        ダイアログ終了後に一覧を必ず再読み込み
        """
        from gui.common.import_excel_dialog import ImportExcelDialog
        dialog = ImportExcelDialog(self._project_list, self)
        dialog.exec_()
        # ダイアログ終了後に必ず一覧を再読み込み
        self._load_projects()
        self._load_scenarios()

    def _on_refresh(self):
        """
        更新ボタン押下時の処理（プロジェクト・シナリオ一覧を再読み込み）
        """
        self._load_projects()
        self._load_scenarios()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_projects()
        self._load_scenarios()
