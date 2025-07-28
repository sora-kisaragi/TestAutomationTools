from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
import sqlite3
from core import scenario_db
from typing import Optional, List

class ScenarioDeleteWidget(QWidget):
    """既存シナリオを複数選択して削除するウィジェット"""
    # 削除完了時のシグナル
    deletion_completed = pyqtSignal()
    
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
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        filter_layout.addWidget(QLabel("プロジェクト:"))
        filter_layout.addWidget(self.project_combo)

        self.screen_combo = QComboBox()
        self.screen_combo.currentIndexChanged.connect(self._on_screen_changed)
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
        self.delete_btn = QPushButton("選択シナリオを削除")
        self.delete_btn.setEnabled(False)  # Initially disabled
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)
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
        self.table.itemChanged.connect(self._on_item_changed)
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
        self._on_project_changed()

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

        # 取得
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
            # 選択画面IDがNoneでない場合のみ条件追加（"(すべて)"はNone）
            if screen_id is not None:
                sql += "AND s.id=? "
                params.append(screen_id)
            sql += "ORDER BY tc.id"
            cur.execute(sql, params)
            all_rows = cur.fetchall()

        # フィルタリング
        rows_to_show = [r for r in all_rows if not keyword or keyword in r[2].lower()]

        # 一度に行数を設定
        self.table.setRowCount(len(rows_to_show))

        for row_idx, (cid, screen_name, scenario_name, status, last_run, result) in enumerate(rows_to_show):
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
        
        # テーブル更新後は削除ボタンを無効化（選択状態がリセットされるため）
        self.delete_btn.setEnabled(False)

    # -------------------- Slots --------------------
    def _on_project_changed(self):
        """プロジェクト変更時の処理"""
        project_id = self.project_combo.currentData()
        self._load_screens(project_id)
        self._load_table()
    
    def _on_screen_changed(self):
        """画面変更時の処理"""
        self._load_table()
    
    def _on_filter_changed(self):
        """検索ボタン押下時の処理"""
        self._load_table()

    def _select_all(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(state)
        self._update_delete_button_state()

    def _on_item_changed(self, item):
        """テーブルアイテム変更時の処理（チェックボックス状態変更を監視）"""
        if item.column() == 0:  # チェックボックス列のみ
            self._update_delete_button_state()

    def _update_delete_button_state(self):
        """削除ボタンの有効/無効状態を更新"""
        has_checked = False
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                has_checked = True
                break
        self.delete_btn.setEnabled(has_checked)

    def _check_related_bugs(self, test_case_ids: List[int]) -> int:
        """指定したテストケースID群に関連付くバグ件数を返す"""
        if not isinstance(test_case_ids, list) or not all(isinstance(i, int) for i in test_case_ids):
            raise ValueError("test_case_ids は整数IDのリストである必要があります")
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            placeholders = ','.join('?' * len(test_case_ids))
            cur.execute(f"""
                SELECT COUNT(DISTINCT b.id) 
                FROM bugs b 
                JOIN test_items ti ON b.test_item_id = ti.id 
                WHERE ti.test_case_id IN ({placeholders})
            """, test_case_ids)
            result = cur.fetchone()
            return result[0] if result else 0

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
        
        # 削除前に関連バグ情報を確認
        related_bugs_count = self._check_related_bugs(cids)
        confirmation_msg = f"選択した {len(cids)} 件のシナリオを削除しますか？"
        if related_bugs_count > 0:
            confirmation_msg += f"\n\n⚠️ 注意: {related_bugs_count} 件の関連バグ情報があります。\nシナリオ削除後、これらのバグ情報からテスト項目への参照は解除されます。"
        
        reply = QMessageBox.question(
            self, "確認", confirmation_msg, QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                # sqlite3 のコンテキストマネージャ内では自動でトランザクション開始されるため明示的BEGINは不要
                
                for cid in cids:
                    # データ整合性を保つための適切な削除順序
                    # 1. bugsテーブルのtest_item_id参照を解除
                    cur.execute("""
                        UPDATE bugs SET test_item_id = NULL 
                        WHERE test_item_id IN (
                            SELECT id FROM test_items WHERE test_case_id = ?
                        )
                    """, (cid,))
                    
                    # 2. test_itemsテーブルのbug_id参照を解除（念のため）
                    cur.execute("UPDATE test_items SET bug_id = NULL WHERE test_case_id = ?", (cid,))
                    
                    # 3. test_itemsを削除
                    cur.execute("DELETE FROM test_items WHERE test_case_id=?", (cid,))
                    
                    # 4. 最後にtest_casesを削除
                    cur.execute("DELETE FROM test_cases WHERE id=?", (cid,))
                
                # 全ての処理が成功した場合のみコミット
                conn.commit()
                
                # 削除完了メッセージ
                completion_msg = f"{len(cids)} 件のシナリオを削除しました"
                if related_bugs_count > 0:
                    completion_msg += f"\n{related_bugs_count} 件のバグ情報の参照も更新されました"
                QMessageBox.information(self, "削除完了", completion_msg)
                
                # テーブル更新と削除ボタン状態リセット
                self._load_table()
                self.delete_btn.setEnabled(False)  # 削除後はボタンを無効化
                # 他の画面にも削除完了を通知
                self.deletion_completed.emit()
                
        except sqlite3.Error as e:
            # データベースエラーの場合
            QMessageBox.critical(
                self, 
                "削除エラー", 
                f"データベース操作中にエラーが発生しました:\n{str(e)}\n\n削除処理は中止されました。"
            )
        except Exception as e:
            # その他の予期しないエラー
            QMessageBox.critical(
                self, 
                "予期しないエラー", 
                f"削除中に予期しないエラーが発生しました:\n{str(e)}\n\n削除処理は中止されました。"
            ) 