"""
シナリオ一覧表示ウィジェット
"""
import sys
import os
if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from core import scenario_db
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout, QLineEdit, QLabel, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import Optional

class ScenarioListWidget(QWidget):
    """
    シナリオ一覧表示ウィジェット
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # データベースの初期化を確実に行う
        scenario_db.init_db()
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
        line_edit = self.project_combo.lineEdit()
        if line_edit:
            line_edit.editingFinished.connect(self._on_project_search)
        self.project_combo.currentIndexChanged.connect(self._on_project_selected)
        self.current_project = QLabel("現在: -")
        proj_layout.addWidget(self.project_label)
        proj_layout.addWidget(self.project_combo)
        proj_layout.addWidget(self.current_project)
        proj_layout.addStretch()
        layout.addLayout(proj_layout)

        # 検索欄
        search_layout = QHBoxLayout()
        search_label = QLabel("検索キーワード:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("テスト項目名・テストケース名・画面名・担当者など")
        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self._on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # テーブルを作成してから初期化
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # テーブルの初期化を確実に行う
        self._init_table()
        
        # 初期状態ではデータを読み込まない（showEventで読み込む）
    
    def _init_table(self):
        """テーブルの初期化"""
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "画面名", "テストケース", "テスト項目名", "優先度", "担当者", "結果", "操作"
        ])
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.Stretch)
            # 水平ヘッダー（列ヘッダー）を表示
            header.setVisible(True)
            # ソート機能を有効化
            header.setSortIndicatorShown(True)
            # ヘッダークリック時のカスタムソートは不要のためメソッド削除
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        # ソート機能を有効化
        self.table.setSortingEnabled(True)
        # 垂直ヘッダー（行番号）のみ非表示
        vheader = self.table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        # 初期状態では行を0に設定し、内容をクリア
        self.table.setRowCount(0)
        self.table.clearContents()
        # ヘッダーの表示を確実にする
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
    
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
        if hasattr(self, '_project_list') and idx is not None and 0 <= idx < len(self._project_list):
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

    def _load_scenarios(self, keyword: str = "", project_id: Optional[int] = None):
        """テスト項目一覧を取得してテーブルに表示（キーワード・プロジェクト対応）"""
        import sqlite3
        # データ読み込み前にテーブルをクリア
        self.table.clearContents()
        self.table.setRowCount(0)
        test_items = []
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                # テスト項目テーブルから詳細情報を取得
                if project_id:
                    cur.execute("""
                        SELECT 
                            p.name as project_name,
                            s.name as screen_name,
                            tc.name as testcase_name,
                            ti.name as testitem_name,
                            ti.priority,
                            ti.tester,
                            ti.result
                        FROM test_items ti
                        JOIN test_cases tc ON ti.test_case_id = tc.id
                        JOIN screens s ON tc.screen_id = s.id
                        JOIN projects p ON s.project_id = p.id
                        WHERE p.id = ?
                        ORDER BY p.name, s.name, tc.name, ti.id
                    """, (project_id,))
                else:
                    cur.execute("""
                        SELECT 
                            p.name as project_name,
                            s.name as screen_name,
                            tc.name as testcase_name,
                            ti.name as testitem_name,
                            ti.priority,
                            ti.tester,
                            ti.result
                        FROM test_items ti
                        JOIN test_cases tc ON ti.test_case_id = tc.id
                        JOIN screens s ON tc.screen_id = s.id
                        JOIN projects p ON s.project_id = p.id
                        ORDER BY p.name, s.name, tc.name, ti.id
                    """)
                for row in cur.fetchall():
                    test_items.append({
                        'project_name': row[0],
                        'screen_name': row[1],
                        'testcase_name': row[2],
                        'testitem_name': row[3],
                        'priority': row[4] or '-',
                        'tester': row[5] or '-',
                        'result': row[6] or '未実施'
                    })
        except Exception as e:
            print(f"DBエラー: {e}")
            print(f"詳細: {str(e)}")
        if keyword:
            keyword_lower = keyword.lower()
            test_items = [item for item in test_items if
                keyword_lower in str(item['testcase_name']).lower() or
                keyword_lower in str(item['testitem_name']).lower() or
                keyword_lower in str(item['screen_name']).lower() or
                keyword_lower in str(item['project_name']).lower() or
                keyword_lower in str(item['tester']).lower()
            ]
        # データがない場合は空のテーブルを表示
        if not test_items:
            self.table.setRowCount(0)
            return
            
        # 既存のセルウィジェットをクリア
        self.table.clearContents()
        self.table.setRowCount(len(test_items))
        
        for row, item in enumerate(test_items):
            # データ行のみにアイテムを設定（プロジェクト列は削除）
            self.table.setItem(row, 0, QTableWidgetItem(item['screen_name']))
            self.table.setItem(row, 1, QTableWidgetItem(item['testcase_name']))
            self.table.setItem(row, 2, QTableWidgetItem(item['testitem_name']))
            
            # 優先度色分け
            priority_item = QTableWidgetItem(item['priority'])
            if item['priority'] == '高':
                priority_item.setForeground(QColor('red'))
            elif item['priority'] == '中':
                priority_item.setForeground(QColor('orange'))
            elif item['priority'] == '低':
                priority_item.setForeground(QColor('blue'))
            self.table.setItem(row, 3, priority_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(item['tester']))
            
            # 実行結果色分け
            result_item = QTableWidgetItem(item['result'])
            if item['result'] == '成功':
                result_item.setForeground(QColor('green'))
            elif item['result'] == '失敗':
                result_item.setForeground(QColor('red'))
            elif item['result'] == '要確認':
                result_item.setForeground(QColor('orange'))
            self.table.setItem(row, 5, result_item)
            
            # 操作ボタンは未実装のため現在は表示しない
            self.table.setItem(row, 6, QTableWidgetItem("-"))

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
        result = dialog.exec_()
        # ダイアログ終了後に必ず一覧を再読み込み
        # データベースの変更を確実に反映するため、少し待機してから再読み込み
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._force_refresh)
    
    def _force_refresh(self):
        """強制的にプロジェクトとシナリオ一覧を再読み込み"""
        current_index = self.project_combo.currentIndex()
        self._load_projects()
        # 現在選択されているプロジェクトのデータのみ表示
        if hasattr(self, '_project_list') and self._project_list and 0 <= current_index < len(self._project_list):
            selected_project_id = self._project_list[current_index][0]
            self._load_scenarios(project_id=selected_project_id)
        else:
            self._load_scenarios()
        print("Excelインポート後の一覧更新完了")

    def _on_refresh(self):
        """
        更新ボタン押下時の処理（プロジェクト・シナリオ一覧を再読み込み）
        """
        current_index = self.project_combo.currentIndex()
        self._load_projects()
        # 現在選択されているプロジェクトのデータのみ表示
        if hasattr(self, '_project_list') and self._project_list and 0 <= current_index < len(self._project_list):
            selected_project_id = self._project_list[current_index][0]
            self._load_scenarios(project_id=selected_project_id)
        else:
            self._load_scenarios()

    def showEvent(self, event):
        super().showEvent(event)
        # 初回表示時のみデータを読み込む
        if not hasattr(self, '_initialized'):
            self._load_projects()
            # 初期化時は選択されたプロジェクトのデータのみ表示
            if hasattr(self, '_project_list') and self._project_list:
                selected_project_id = self._project_list[0][0]  # 最初のプロジェクトのID
                self._load_scenarios(project_id=selected_project_id)
            else:
                self._load_scenarios()
            self._initialized = True
