"""
プロジェクト管理ウィジェット（雛形）
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
from PyQt5.QtCore import pyqtSignal
from core import scenario_db
from gui.common.utils import get_text_dialog, get_selected_rows_from_listwidget

class ProjectManagementWidget(QWidget):
    """
    プロジェクト管理用ウィジェット
    """
    # プロジェクト変更通知用シグナル
    project_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("プロジェクト管理画面"))

        self.project_list = QListWidget()
        # 複数選択を有効化
        self.project_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.project_list)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("追加")
        self.add_btn.clicked.connect(self._add_project)
        btn_layout.addWidget(self.add_btn)
        self.del_btn = QPushButton("削除")
        self.del_btn.clicked.connect(self._delete_project)
        btn_layout.addWidget(self.del_btn)
        # Excel一括取込ボタンは不要のため削除
        layout.addLayout(btn_layout)

    def _load_projects(self):
        self.project_list.clear()
        import sqlite3
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM projects ORDER BY id")
            self._projects = cur.fetchall()
            for pid, name in self._projects:
                self.project_list.addItem(name)
        if self._projects:
            self.project_list.setCurrentRow(0)

    def _add_project(self):
        name, ok = get_text_dialog(self, "新規プロジェクト名を入力してください")
        if ok and name:
            name = name.strip()
            if not name or len(name) > 100:
                QMessageBox.warning(self, "エラー", "プロジェクト名は1～100文字で入力してください")
                return
            
            try:
                import sqlite3
                with sqlite3.connect(scenario_db.DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO projects (name) VALUES (?)", (name,))
                    conn.commit()
                    QMessageBox.information(self, "作成完了", f"プロジェクト '{name}' を作成しました")
                    self._load_projects()
                    # 他のタブに変更を通知
                    self.project_changed.emit()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "エラー", "同名のプロジェクトが既に存在します")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"プロジェクト作成中にエラーが発生しました:\n{str(e)}")

    def _delete_project(self):
        # 共通関数で選択データ取得
        delete_targets = get_selected_rows_from_listwidget(self.project_list, getattr(self, '_projects', []))
        if not delete_targets:
            QMessageBox.warning(self, "エラー", "削除するプロジェクトを選択してください")
            return
        names = ', '.join([name for _, name in delete_targets])
        reply = QMessageBox.question(
            self,
            "確認",
            f"選択したプロジェクト({names})を削除しますか？\n関連する画面・テストケース・テスト項目も全て削除されます。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                errors = []
                for pid, name in delete_targets:
                    try:
                        scenario_db.delete_project(pid)
                    except Exception as e:
                        errors.append(f"{name}: {str(e)}")
                
                if errors:
                    QMessageBox.critical(self, "削除エラー", "\n".join(errors))
                else:
                    QMessageBox.information(self, "削除完了", f"選択したプロジェクトを削除しました")
                    # 他のタブに変更を通知
                    self.project_changed.emit()
                
                self._load_projects()
                
            except Exception as e:
                QMessageBox.critical(self, "予期しないエラー", f"削除処理中に予期しないエラーが発生しました:\n{str(e)}")
                self._load_projects()
