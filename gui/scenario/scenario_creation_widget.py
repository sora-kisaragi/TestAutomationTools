"""
シナリオ作成用ウィジェット
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QDateEdit, QListWidget, QMessageBox, QScrollArea, QDialog
from PyQt5.QtCore import QDate
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import scenario_db
from gui.common.constants import *
from gui.common.utils import get_text_dialog
from gui.common.import_result_dialog import ImportResultDialog

class ScenarioCreationWidget(QWidget):
    """
    シナリオ作成用ウィジェット（左：プロジェクトリスト、上部：画面名選択、下部：テストケース・テスト項目入力）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        scenario_db.init_db()
        self._init_ui()
        self._load_projects()
        self._load_master_data()

    def _init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        self._init_project_list(main_layout)
        self._init_right_area(main_layout)

    def _init_project_list(self, layout):
        """プロジェクトリスト部分の初期化"""
        vbox = QVBoxLayout()
        self.project_list = QListWidget()
        self.project_list.itemSelectionChanged.connect(self._on_project_selected)
        vbox.addWidget(self.project_list)
        # 削除ボタン追加
        self.delete_project_btn = QPushButton("選択プロジェクト削除")
        self.delete_project_btn.clicked.connect(self._delete_project)
        vbox.addWidget(self.delete_project_btn)
        container = QWidget()
        container.setLayout(vbox)
        layout.addWidget(container, 1)

    def _delete_project(self):
        """
        選択中プロジェクトを削除する
        """
        idx = self.project_list.currentRow()
        if idx < 0 or not hasattr(self, '_projects') or idx >= len(self._projects):
            QMessageBox.warning(self, "削除エラー", "削除するプロジェクトを選択してください")
            return
        pid, name = self._projects[idx]
        reply = QMessageBox.question(
            self, "確認", f"プロジェクト '{name}' を本当に削除しますか？\n(関連する画面・テストケース・テスト項目も全て削除されます)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                scenario_db.delete_project(pid)
                QMessageBox.information(self, "削除完了", f"プロジェクト '{name}' を削除しました")
                self._load_projects()
            except Exception as e:
                QMessageBox.critical(self, "削除失敗", f"削除中にエラーが発生しました: {str(e)}")

    def _init_right_area(self, layout):
        """右側（入力エリア）の初期化"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        layout.addWidget(right_widget, 3)
        self._init_header_area(right_layout)
        self._init_form_area(right_layout)
        self._init_button_area(right_layout)

    def _init_header_area(self, layout):
        """画面名選択・追加部分の初期化"""
        header_layout = QHBoxLayout()
        header_label = QLabel("画面名:")
        self.screen_combo = QComboBox()
        self.screen_combo.currentIndexChanged.connect(self._on_screen_changed)
        header_layout.addWidget(header_label)
        header_layout.addWidget(self.screen_combo)
        self.screen_add_btn = QPushButton("＋新規")
        self.screen_add_btn.clicked.connect(self._add_screen)
        header_layout.addWidget(self.screen_add_btn)
        layout.addLayout(header_layout)

    def _init_form_area(self, layout):
        """テストケース・テスト項目入力フォーム部分の初期化"""
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        layout.addWidget(form_widget)
        # テストケース名（小シナリオ）選択・追加
        self.case_combo = QComboBox()
        self.case_add_btn = QPushButton("＋新規")
        self.case_add_btn.clicked.connect(self._add_case)
        h_case = QHBoxLayout()
        h_case.addWidget(self.case_combo)
        h_case.addWidget(self.case_add_btn)
        self.form_layout.addRow("テストケース名:", self._wrap_widget(h_case))
        self.case_combo.currentIndexChanged.connect(self._on_case_changed)
        # テスト項目名
        self.test_item_edit = QLineEdit()
        self.form_layout.addRow("テスト項目名:", self.test_item_edit)
        # 入力データ
        self.input_data_edit = QTextEdit()
        self.input_data_edit.setMaximumHeight(60)
        self.form_layout.addRow("入力データ:", self.input_data_edit)
        # 操作手順
        self.operation_edit = QTextEdit()
        self.operation_edit.setMaximumHeight(60)
        self.form_layout.addRow("操作手順:", self.operation_edit)
        # 期待結果
        self.expected_edit = QTextEdit()
        self.expected_edit.setMaximumHeight(60)
        self.form_layout.addRow("期待結果:", self.expected_edit)
        # 優先度
        self.priority_combo = QComboBox()
        self.form_layout.addRow("優先度:", self.priority_combo)
        # 担当者
        self.tester_combo = QComboBox()
        self.form_layout.addRow("担当者:", self.tester_combo)
        # 実施日
        self.exec_date_edit = QDateEdit()
        self.exec_date_edit.setDate(QDate.currentDate())
        self.exec_date_edit.setCalendarPopup(True)
        self.form_layout.addRow("実施日:", self.exec_date_edit)
        # 結果
        self.result_combo = QComboBox()
        self.form_layout.addRow("結果:", self.result_combo)
        # 備考
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(60)
        self.form_layout.addRow("備考:", self.remarks_edit)

    def _init_button_area(self, layout):
        """ボタン類の初期化"""
        button_layout = QHBoxLayout()
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self._clear_form)
        button_layout.addWidget(self.clear_button)
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self._save_test_item)
        button_layout.addWidget(self.save_button)
        self.import_button = QPushButton("インポート")
        self.import_button.clicked.connect(self.show_import_dialog)
        button_layout.addWidget(self.import_button)
        self.excel_import_button = QPushButton("Excelインポート")
        self.excel_import_button.clicked.connect(self.show_excel_import_dialog)
        button_layout.addWidget(self.excel_import_button)
        self.csv_sample_button = QPushButton("CSVサンプル表示")
        self.csv_sample_button.clicked.connect(self.show_csv_sample)
        button_layout.addWidget(self.csv_sample_button)
        self.export_csv_button = QPushButton("CSVサンプル出力")
        self.export_csv_button.clicked.connect(self.export_csv_sample)
        button_layout.addWidget(self.export_csv_button)
        layout.addLayout(button_layout)

    def _wrap_widget(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def _load_projects(self):
        self.project_list.clear()
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM projects ORDER BY id")
            self._projects = cur.fetchall()
            for pid, name in self._projects:
                self.project_list.addItem(name)
        if self._projects:
            self.project_list.setCurrentRow(0)

    def _on_project_selected(self):
        idx = self.project_list.currentRow()
        if idx < 0 or not hasattr(self, '_projects') or idx >= len(self._projects):
            self.screen_combo.clear()
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
        if self._screens:
            self.screen_combo.setCurrentIndex(0)

    def _on_screen_changed(self):
        sid = self._get_current_screen_id()
        if sid is None:
            self.case_combo.clear()
            return
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM test_cases WHERE screen_id=? ORDER BY id", (sid,))
            self._cases = cur.fetchall()
            self.case_combo.clear()
            for cid, name in self._cases:
                self.case_combo.addItem(name, cid)
        self._on_case_changed()

    def _on_case_changed(self):
        # 今回は何もしない（将来拡張用）
        pass

    def _get_current_project_id(self):
        idx = self.project_list.currentRow()
        if idx < 0 or not hasattr(self, '_projects') or idx >= len(self._projects):
            return None
        return self._projects[idx][0]

    def _get_current_screen_id(self):
        idx = self.screen_combo.currentIndex()
        if idx < 0 or not hasattr(self, '_screens') or idx >= len(self._screens):
            return None
        return self._screens[idx][0]

    def _get_current_case_id(self):
        idx = self.case_combo.currentIndex()
        if idx < 0 or not hasattr(self, '_cases') or idx >= len(self._cases):
            return None
        return self._cases[idx][0]

    def _add_case(self):
        sid = self._get_current_screen_id()
        if sid is None:
            QMessageBox.warning(self, "エラー", "画面名を選択してください")
            return
        name, ok = get_text_dialog(self, "新規テストケース名を入力してください")
        if ok and name:
            name = name.strip()
            if not name or len(name) > 100:
                QMessageBox.warning(self, "エラー", "テストケース名は1～100文字で入力してください")
                return
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                self._get_or_create_case(conn.cursor(), sid, name)
                conn.commit()
            self._on_screen_changed()

    def _add_screen(self):
        """
        選択中プロジェクトに画面名を追加
        """
        pid = self._get_current_project_id()
        if pid is None:
            QMessageBox.warning(self, "エラー", "プロジェクトを選択してください")
            return
        name, ok = get_text_dialog(self, "新規画面名を入力してください")
        if ok and name:
            name = name.strip()
            if not name or len(name) > 100:
                QMessageBox.warning(self, "エラー", "画面名は1～100文字で入力してください")
                return
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                try:
                    self._get_or_create_screen(conn.cursor(), pid, name)
                    conn.commit()
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "エラー", "同名の画面が既に存在します")
            self._load_screens(pid)

    def _clear_form(self):
        self.test_item_edit.clear()
        self.input_data_edit.clear()
        self.operation_edit.clear()
        self.expected_edit.clear()
        self.remarks_edit.clear()
        self.exec_date_edit.setDate(QDate.currentDate())
        self.priority_combo.setCurrentIndex(0)
        self.tester_combo.setCurrentIndex(0)
        self.result_combo.setCurrentIndex(0)

    def _save_test_item(self):
        # 必須チェック
        case_id = self._get_current_case_id()
        if case_id is None:
            QMessageBox.warning(self, "エラー", "テストケースを選択してください")
            return
        name = self.test_item_edit.text().strip()
        if not name or len(name) > 100:
            QMessageBox.warning(self, "エラー", "テスト項目名は1～100文字で入力してください")
            return
        # データ取得
        data = {
            "test_case_id": case_id,
            "name": name,
            "input_data": self.input_data_edit.toPlainText().strip(),
            "operation": self.operation_edit.toPlainText().strip(),
            "expected": self.expected_edit.toPlainText().strip(),
            "priority": self.priority_combo.currentText().strip(),
            "tester": self.tester_combo.currentText().strip(),
            "exec_date": self.exec_date_edit.date().toString("yyyy-MM-dd"),
            "result": self.result_combo.currentText().strip(),
            "remarks": self.remarks_edit.toPlainText().strip()
        }
        # DB登録
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO test_items (
                    test_case_id, name, input_data, operation, expected, priority, tester, exec_date, result, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data["test_case_id"], data["name"], data["input_data"], data["operation"], data["expected"],
                data["priority"], data["tester"], data["exec_date"], data["result"], data["remarks"]
            ))
            conn.commit()
            item_id = cur.lastrowid
        QMessageBox.information(self, "保存完了", f"テスト項目ID: {item_id} を保存しました")
        self._clear_form()

    def _load_master_data(self):
        """
        優先度・担当者・結果などのマスターデータをコンボボックスにセット
        """
        self.priority_combo.clear()
        self.tester_combo.clear()
        self.result_combo.clear()
        priorities = scenario_db.get_master_data("master_priorities")
        testers = scenario_db.get_master_data("master_testers")
        results = scenario_db.get_master_data("master_results")
        self.priority_combo.addItems(priorities)
        self.tester_combo.addItems(testers)
        self.result_combo.addItems(results)

    def _get_or_create_project(self, cur, project_name):
        """プロジェクトがなければ作成し、IDを返す"""
        cur.execute("SELECT id FROM projects WHERE name=?", (project_name,))
        proj = cur.fetchone()
        if proj:
            return proj[0]
        cur.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
        return cur.lastrowid

    def _get_or_create_screen(self, cur, pid, screen_name):
        """画面がなければ作成し、IDを返す"""
        cur.execute("SELECT id FROM screens WHERE project_id=? AND name=?", (pid, screen_name))
        scr = cur.fetchone()
        if scr:
            return scr[0]
        cur.execute("INSERT INTO screens (project_id, name) VALUES (?, ?)", (pid, screen_name))
        return cur.lastrowid

    def _get_or_create_case(self, cur, sid, case_name):
        """テストケースがなければ作成し、IDを返す"""
        cur.execute("SELECT id FROM test_cases WHERE screen_id=? AND name=?", (sid, case_name))
        case = cur.fetchone()
        if case:
            return case[0]
        cur.execute("INSERT INTO test_cases (screen_id, name) VALUES (?, ?)", (sid, case_name))
        return cur.lastrowid

    def import_projects_from_csv(self, csv_path):
        """
        プロジェクト・画面・テストケースをCSVから一括登録する
        CSV例: プロジェクト名,画面名,テストケース名
        """
        import csv
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                with open(csv_path, encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) < 3:
                            continue
                        # 入力値のトリムとバリデーション
                        project_name = row[0].strip()
                        screen_name = row[1].strip()
                        case_name = row[2].strip()
                        if not project_name or not screen_name or not case_name:
                            continue
                        if len(project_name) > 100 or len(screen_name) > 100 or len(case_name) > 100:
                            continue
                        pid = self._get_or_create_project(cur, project_name)
                        sid = self._get_or_create_screen(cur, pid, screen_name)
                        self._get_or_create_case(cur, sid, case_name)
                conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "インポートエラー", f"CSVインポート中にエラーが発生しました:\n{str(e)}")
            return
        QMessageBox.information(self, "インポート完了", "CSVから一括登録が完了しました")
        self._load_projects()  # インポート後にプロジェクトリストを自動更新

    def import_projects_from_excel(self, excel_path):
        """
        Excelファイルからプロジェクト・画面・テストケース・テスト項目を一括登録
        画面名一覧を最初に列挙し、1回だけプロジェクト名を聞いて全画面をそのプロジェクトに登録
        """
        from core.scenario_loader import ScenarioLoader
        loader = ScenarioLoader(excel_path)
        all_data = loader.load_all_scenarios()
        if not all_data:
            QMessageBox.warning(self, "インポート失敗", "Excelからシナリオが見つかりませんでした")
            return
        # 画面名一覧を抽出
        screen_names = [page["screen_name"] for page in all_data]
        # 画面名一覧をダイアログで表示
        dlg = QDialog(self)
        dlg.setWindowTitle("インポート対象の画面一覧")
        dlg.setFixedSize(400, 350)
        vbox = QVBoxLayout(dlg)
        vbox.addWidget(QLabel("以下の画面がExcelから検出されました："))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        list_widget = QListWidget()
        for name in screen_names:
            list_widget.addItem(name)
        list_widget.setMinimumWidth(350)
        list_widget.setMaximumWidth(350)
        list_widget.setMinimumHeight(200)
        scroll.setWidget(list_widget)
        vbox.addWidget(scroll)
        btn = QPushButton("OK")
        btn.clicked.connect(dlg.accept)
        vbox.addWidget(btn)
        dlg.exec_()
        # プロジェクト名を1回だけ聞く
        project_name, ok = get_text_dialog(self, "これらの画面を登録するプロジェクト名を入力してください")
        if not ok or not project_name:
            return
        import_result = []
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                # プロジェクト（共通関数で取得・作成）
                pid = self._get_or_create_project(cur, project_name)
                for page in all_data:
                    screen_name = page["screen_name"].strip()
                    if not screen_name or len(screen_name) > 100:
                        continue
                    sid = self._get_or_create_screen(cur, pid, screen_name)
                    screen_result = {"screen": screen_name, "scenarios": []}
                    for scenario in page["scenarios"]:
                        scenario_name = scenario["name"].strip()
                        if not scenario_name or len(scenario_name) > 100:
                            continue
                        cid = self._get_or_create_case(cur, sid, scenario_name)
                        # テスト項目
                        for testcase in scenario.get("testitems", []):
                            name = testcase.get("テスト項目") or testcase.get("name")
                            if not name:
                                continue
                            name = str(name).strip()
                            if not name or len(name) > 100:
                                continue
                            cur.execute("""
                                INSERT INTO test_items (
                                    test_case_id, name, input_data, operation, expected, priority, tester, exec_date, result, remarks
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                cid,
                                name,
                                str(testcase.get("入力データ", "")).strip(),
                                str(testcase.get("操作手順", "")).strip(),
                                str(testcase.get("期待結果", "")).strip(),
                                str(testcase.get("優先度", "")).strip(),
                                str(testcase.get("担当者", "")).strip(),
                                str(testcase.get("実施日", "")).strip(),
                                str(testcase.get("結果", "")).strip(),
                                str(testcase.get("備考", "")).strip()
                            ))
                        screen_result["scenarios"].append({
                            "name": scenario_name,
                            "testcase_count": len(scenario.get("testitems", []))
                        })
                    import_result.append(screen_result)
                conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "インポートエラー", f"Excelインポート中にエラーが発生しました:\n{str(e)}")
            return
        self._load_projects()  # インポート後にプロジェクトリストを自動更新
        dlg = ImportResultDialog(import_result, self)
        dlg.exec_()

    def import_projects_from_excel_dialog(self, excel_path, project_mode, project_id, project_name, overwrite):
        """
        ImportExcelDialog用: Excelファイルからプロジェクト・画面・シナリオを一括登録
        project_mode: 'existing' or 'new'
        project_id: 既存プロジェクトID（existing時のみ）
        project_name: 新規プロジェクト名（new時のみ）
        overwrite: True=上書き, False=残す
        戻り値: [{screen, name, status, message}...]
        """
        from core.scenario_loader import ScenarioLoader
        import sqlite3
        result_list = []
        loader = ScenarioLoader(excel_path)
        all_data = loader.load_all_scenarios()
        if not all_data:
            return [{"screen": "-", "name": "-", "status": "失敗", "message": "Excelからシナリオが見つかりませんでした"}]
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                # プロジェクトID決定
                if project_mode == 'existing' and project_id:
                    pid = project_id
                else:
                    pid = self._get_or_create_project(cur, project_name)
                for page in all_data:
                    screen_name = page["screen_name"].strip()
                    if not screen_name or len(screen_name) > 100:
                        continue
                    sid = self._get_or_create_screen(cur, pid, screen_name)
                    for scenario in page["scenarios"]:
                        scenario_name = scenario["name"].strip()
                        if not scenario_name or len(scenario_name) > 100:
                            continue
                        # 上書き/残す判定
                        cur.execute("SELECT id FROM test_cases WHERE screen_id=? AND name=?", (sid, scenario_name))
                        row = cur.fetchone()
                        if row:
                            if overwrite:
                                cid = row[0]
                                cur.execute("DELETE FROM test_items WHERE test_case_id=?", (cid,))
                                cur.execute("DELETE FROM test_cases WHERE id=?", (cid,))
                                # 新規作成
                                cid = self._get_or_create_case(cur, sid, scenario_name)
                                status = "成功"
                                msg = "上書き登録"
                            else:
                                status = "成功"
                                msg = "既存シナリオを残しました"
                                result_list.append({"screen": screen_name, "name": scenario_name, "status": status, "message": msg})
                                continue
                        else:
                            cid = self._get_or_create_case(cur, sid, scenario_name)
                            status = "成功"
                            msg = "新規登録"
                        # テスト項目
                        for testcase in scenario.get("testitems", []):
                            name = testcase.get("テスト項目") or testcase.get("name")
                            if not name:
                                continue
                            name = str(name).strip()
                            if not name or len(name) > 100:
                                continue
                            cur.execute("""
                                INSERT INTO test_items (
                                    test_case_id, name, input_data, operation, expected, priority, tester, exec_date, result, remarks
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                cid,
                                name,
                                str(testcase.get("入力データ", "")).strip(),
                                str(testcase.get("操作手順", "")).strip(),
                                str(testcase.get("期待結果", "")).strip(),
                                str(testcase.get("優先度", "")).strip(),
                                str(testcase.get("担当者", "")).strip(),
                                str(testcase.get("実施日", "")).strip(),
                                str(testcase.get("結果", "")).strip(),
                                str(testcase.get("備考", "")).strip()
                            ))
                        result_list.append({"screen": screen_name, "name": scenario_name, "status": status, "message": msg})
                conn.commit()
        except Exception as e:
            return [{"screen": "-", "name": "-", "status": "失敗", "message": str(e)}]
        return result_list

    def show_import_dialog(self):
        """
        CSVファイル選択ダイアログを表示し、インポートを実行
        """
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "CSVファイルを選択", "", "CSV Files (*.csv)")
        if path:
            self.import_projects_from_csv(path)
            self._load_projects()

    def show_excel_import_dialog(self):
        """
        Excelファイル選択ダイアログを表示し、インポートを実行
        """
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Excelファイルを選択", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.import_projects_from_excel(path)
            self._load_projects()

    def show_csv_sample(self):
        """
        CSVサンプル内容をダイアログで表示
        """
        QMessageBox.information(self, "CSVサンプル", f"CSV例:\n\n{CSV_SAMPLE}\n(カンマ区切り・1行1レコード)")

    def export_csv_sample(self):
        """
        CSVサンプルファイルを出力
        """
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "CSVサンプルを書き出し", "sample.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(CSV_SAMPLE)
            QMessageBox.information(self, "出力完了", f"CSVサンプルを保存しました: {path}")

