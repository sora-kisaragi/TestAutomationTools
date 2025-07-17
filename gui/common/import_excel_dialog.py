"""
Excelシナリオインポートダイアログ
設計・ワイヤーフレーム準拠
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QComboBox, QLineEdit, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QButtonGroup, QGroupBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
import os

class ImportExcelDialog(QDialog):
    def __init__(self, project_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Excelシナリオインポート")
        self.resize(600, 500)
        self.project_list = project_list
        self.selected_file = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # インポート先プロジェクト
        group = QGroupBox("インポート先プロジェクト:")
        group_layout = QHBoxLayout()
        self.radio_existing = QRadioButton("既存プロジェクトに追加")
        self.radio_new = QRadioButton("新規プロジェクトとして作成")
        self.radio_existing.setChecked(True)
        self.combo_project = QComboBox()
        for pid, name in self.project_list:
            self.combo_project.addItem(name, pid)
        self.edit_new_project = QLineEdit()
        self.edit_new_project.setPlaceholderText("新規プロジェクト名")
        self.edit_new_project.setEnabled(False)
        self.radio_existing.toggled.connect(self._on_radio_toggle)
        group_layout.addWidget(self.radio_existing)
        group_layout.addWidget(self.combo_project)
        group_layout.addWidget(self.radio_new)
        group_layout.addWidget(self.edit_new_project)
        group.setLayout(group_layout)
        layout.addWidget(group)

        # ファイル選択
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.btn_file = QPushButton("ファイルを選択")
        self.btn_file.clicked.connect(self._on_select_file)
        file_layout.addWidget(QLabel("ファイル選択:"))
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(self.btn_file)
        layout.addLayout(file_layout)
        layout.addWidget(QLabel("またはドラッグ＆ドロップでExcelファイルを追加"))
        self.setAcceptDrops(True)

        # インポートオプション
        opt_layout = QHBoxLayout()
        self.radio_overwrite = QRadioButton("既存シナリオを上書き")
        self.radio_keep = QRadioButton("既存シナリオを残す")
        self.radio_overwrite.setChecked(True)
        opt_layout.addWidget(QLabel("インポートオプション:"))
        opt_layout.addWidget(self.radio_overwrite)
        opt_layout.addWidget(self.radio_keep)
        layout.addLayout(opt_layout)

        # 実行ボタン
        btn_layout = QHBoxLayout()
        self.btn_import = QPushButton("インポート開始")
        self.btn_cancel = QPushButton("キャンセル")
        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # インポート結果
        self.result_table = QTableWidget(0, 4)
        self.result_table.setHorizontalHeaderLabels(["No", "画面名", "シナリオ名", "ステータス", "メッセージ"])
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(QLabel("インポート結果:"))
        layout.addWidget(self.result_table)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_import.clicked.connect(self._on_import_clicked)

    def _on_radio_toggle(self):
        self.combo_project.setEnabled(self.radio_existing.isChecked())
        self.edit_new_project.setEnabled(self.radio_new.isChecked())

    def _on_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Excelファイルを選択", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.selected_file = path
            self.file_edit.setText(os.path.basename(path))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.xlsx', '.xls')):
                self.selected_file = path
                self.file_edit.setText(os.path.basename(path))
                break

    def set_result(self, result_list):
        """インポート結果をテーブルに反映 result_list: List[dict] (各dictに 'screen' キーがあれば画面名も表示)"""
        self.result_table.setRowCount(len(result_list))
        for i, row in enumerate(result_list):
            self.result_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.result_table.setItem(i, 1, QTableWidgetItem(row.get('screen', '-')))
            self.result_table.setItem(i, 2, QTableWidgetItem(row.get('name', '-')))
            status_item = QTableWidgetItem(row.get('status', '-'))
            if row.get('status') == '成功':
                status_item.setForeground(Qt.darkGreen)
            elif row.get('status') == '失敗':
                status_item.setForeground(Qt.red)
            self.result_table.setItem(i, 3, status_item)
            self.result_table.setItem(i, 4, QTableWidgetItem(row.get('message', '-')))

    def _on_import_clicked(self):
        """
        インポート開始ボタン押下時の処理（ダイアログを閉じず、インポート処理・結果反映）
        """
        from gui.scenario.scenario_creation_widget import ScenarioCreationWidget
        from PyQt5.QtWidgets import QMessageBox
        import os
        # 入力内容取得
        if self.radio_existing.isChecked():
            project_mode = 'existing'
            project_id = self.combo_project.currentData()
            project_name = self.combo_project.currentText()
        else:
            project_mode = 'new'
            project_id = None
            project_name = self.edit_new_project.text().strip()
        excel_path = self.selected_file
        overwrite = self.radio_overwrite.isChecked()
        # バリデーション
        if not excel_path or not os.path.exists(excel_path):
            QMessageBox.warning(self, "ファイル未選択", "Excelファイルを選択してください")
            return
        if project_mode == 'new' and not project_name:
            QMessageBox.warning(self, "プロジェクト名未入力", "新規プロジェクト名を入力してください")
            return
        # インポート処理
        widget = ScenarioCreationWidget()
        try:
            result_list = widget.import_projects_from_excel_dialog(
                excel_path=excel_path,
                project_mode=project_mode,
                project_id=project_id,
                project_name=project_name,
                overwrite=overwrite
            )
            self.set_result(result_list)
            QMessageBox.information(self, "インポート完了", "Excelからのインポートが完了しました。結果を確認してください。")
        except Exception as e:
            QMessageBox.critical(self, "インポートエラー", f"Excelインポート中にエラーが発生しました:\n{str(e)}")
        # ダイアログは閉じない
