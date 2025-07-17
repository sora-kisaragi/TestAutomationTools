"""
メインウィンドウモジュール
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import scenario_db
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget, QTabWidget, QPushButton, QVBoxLayout, QLabel
)
from gui.scenario.scenario_creation_widget import ScenarioCreationWidget
from gui.bug.bug_entry_widget import BugEntryWidget
from gui.scenario.scenario_list_widget import ScenarioListWidget
from gui.project.project_management_widget import ProjectManagementWidget
from gui.screen.screen_management_widget import ScreenManagementWidget
from gui.testcase_management_widget import TestCaseManagementWidget
from gui.testitem_management_widget import TestItemManagementWidget
from gui.test.test_execution_window import TestExecutionWindow
from gui.test.test_scenario_select_window import TestScenarioSelectWindow

class MainWindow(QMainWindow):
    """
    メインウィンドウ
    サイドバー＋メインビュー方式でカテゴリごとに画面を切り替える
    管理カテゴリはサブタブでまとめる
    各画面のUIパーツは導線を意識して配置すること
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("テスト自動化支援ツール")
        self.setGeometry(100, 100, 1200, 600)

        # メインレイアウト
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # サイドバー（カテゴリ選択）
        self.sidebar = QListWidget()
        self.sidebar.addItems([
            "シナリオ管理",   # 0
            "テスト管理",     # 1
            "不具合管理",     # 2
            "運用管理",       # 3
            "システム管理",   # 4
            "マスタ管理"      # 5
        ])
        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        main_layout.addWidget(self.sidebar, 1)

        # メイン表示エリア
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 4)

        # --- 各カテゴリ画面 ---
        # シナリオ管理（サブタブ：一覧・作成・インポート・エクスポート）
        self.scenario_tab = QTabWidget()

        # --- 一覧タブ ---
        scenario_list_tab = QWidget()
        vbox = QVBoxLayout(scenario_list_tab)
        # 上部ボタンエリア
        btn_area = QHBoxLayout()
        btn_new = QPushButton("新規作成")
        btn_import = QPushButton("Excelインポート")
        btn_export = QPushButton("Excelエクスポート")
        btn_area.addWidget(btn_new)
        btn_area.addWidget(btn_import)
        btn_area.addWidget(btn_export)
        btn_area.addStretch()
        vbox.addLayout(btn_area)
        self.scenario_list_widget = ScenarioListWidget()
        vbox.addWidget(self.scenario_list_widget)
        self.scenario_tab.addTab(scenario_list_tab, "一覧")

        # --- 作成タブ ---
        scenario_create_tab = QWidget()
        vbox_create = QVBoxLayout(scenario_create_tab)
        self.scenario_creation_widget = ScenarioCreationWidget()
        vbox_create.addWidget(self.scenario_creation_widget)
        btn_to_list = QPushButton("一覧へ")
        vbox_create.addWidget(btn_to_list)
        self.scenario_tab.addTab(scenario_create_tab, "作成")

        # --- インポート・エクスポートタブ（プレースホルダー）---
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        import_layout.addWidget(QLabel("Excelインポート画面（今後拡張予定）"))
        self.scenario_tab.addTab(import_tab, "インポート")

        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.addWidget(QLabel("Excelエクスポート画面（今後拡張予定）"))
        self.scenario_tab.addTab(export_tab, "エクスポート")

        self.stack.addWidget(self.scenario_tab)

        # ボタンの画面遷移ロジック
        def goto_create():
            self.scenario_tab.setCurrentIndex(1)
        def goto_list():
            self.scenario_tab.setCurrentIndex(0)
        btn_new.clicked.connect(goto_create)
        btn_to_list.clicked.connect(goto_list)

        # テスト管理（サブタブ：一覧・実行・結果記録・エクスポート）
        self.test_tab = QTabWidget()
        # --- 一覧タブ（プレースホルダー）---
        test_list_tab = QWidget()
        vbox_test_list = QVBoxLayout(test_list_tab)
        # 上部ボタンエリア
        btn_area_test = QHBoxLayout()
        btn_test_exec = QPushButton("実行")
        btn_test_result = QPushButton("結果記録")
        btn_test_export = QPushButton("Excelエクスポート")
        btn_area_test.addWidget(btn_test_exec)
        btn_area_test.addWidget(btn_test_result)
        btn_area_test.addWidget(btn_test_export)
        btn_area_test.addStretch()
        vbox_test_list.addLayout(btn_area_test)
        vbox_test_list.addWidget(QLabel("テスト一覧画面（今後拡張予定）"))
        self.test_tab.addTab(test_list_tab, "一覧")

        # --- 実行タブ ---
        self.test_scenario_select_tab = TestScenarioSelectWindow()
        self.test_tab.addTab(self.test_scenario_select_tab, "実行")

        # --- 結果記録タブ（プレースホルダー）---
        test_result_tab = QWidget()
        vbox_result = QVBoxLayout(test_result_tab)
        vbox_result.addWidget(QLabel("テスト結果記録画面（今後拡張予定）"))
        self.test_tab.addTab(test_result_tab, "結果記録")

        # --- エクスポートタブ（プレースホルダー）---
        test_export_tab = QWidget()
        vbox_export = QVBoxLayout(test_export_tab)
        vbox_export.addWidget(QLabel("テスト結果エクスポート画面（今後拡張予定）"))
        self.test_tab.addTab(test_export_tab, "エクスポート")

        self.stack.addWidget(self.test_tab)

        # ボタンの画面遷移ロジック（例：実行ボタンで実行タブへ、結果記録ボタンで結果記録タブへ）
        def goto_test_exec():
            self.test_tab.setCurrentIndex(1)
        def goto_test_result():
            self.test_tab.setCurrentIndex(2)
        btn_test_exec.clicked.connect(goto_test_exec)
        btn_test_result.clicked.connect(goto_test_result)

        # 不具合管理（サブタブ：一覧・登録・編集・詳細・エクスポート）
        self.bug_tab = QTabWidget()
        # --- 一覧タブ ---
        bug_list_tab = QWidget()
        vbox_bug_list = QVBoxLayout(bug_list_tab)
        btn_area_bug = QHBoxLayout()
        btn_bug_new = QPushButton("新規登録")
        btn_bug_import = QPushButton("インポート")
        btn_bug_export = QPushButton("エクスポート")
        btn_area_bug.addWidget(btn_bug_new)
        btn_area_bug.addWidget(btn_bug_import)
        btn_area_bug.addWidget(btn_bug_export)
        btn_area_bug.addStretch()
        vbox_bug_list.addLayout(btn_area_bug)
        vbox_bug_list.addWidget(QLabel("バグ一覧画面（今後拡張予定）"))
        self.bug_tab.addTab(bug_list_tab, "一覧")

        # --- 登録タブ ---
        bug_register_tab = QWidget()
        vbox_bug_register = QVBoxLayout(bug_register_tab)
        vbox_bug_register.addWidget(BugEntryWidget())
        btn_to_bug_list = QPushButton("一覧へ")
        vbox_bug_register.addWidget(btn_to_bug_list)
        self.bug_tab.addTab(bug_register_tab, "登録")

        # --- 編集・詳細・エクスポートタブ（プレースホルダー）---
        bug_edit_tab = QWidget()
        vbox_bug_edit = QVBoxLayout(bug_edit_tab)
        vbox_bug_edit.addWidget(QLabel("バグ編集画面（今後拡張予定）"))
        self.bug_tab.addTab(bug_edit_tab, "編集")

        bug_detail_tab = QWidget()
        vbox_bug_detail = QVBoxLayout(bug_detail_tab)
        vbox_bug_detail.addWidget(QLabel("バグ詳細画面（今後拡張予定）"))
        self.bug_tab.addTab(bug_detail_tab, "詳細")

        bug_export_tab = QWidget()
        vbox_bug_export = QVBoxLayout(bug_export_tab)
        vbox_bug_export.addWidget(QLabel("バグエクスポート画面（今後拡張予定）"))
        self.bug_tab.addTab(bug_export_tab, "エクスポート")

        self.stack.addWidget(self.bug_tab)

        # ボタンの画面遷移ロジック
        def goto_bug_register():
            self.bug_tab.setCurrentIndex(1)
        def goto_bug_list():
            self.bug_tab.setCurrentIndex(0)
        btn_bug_new.clicked.connect(goto_bug_register)
        btn_to_bug_list.clicked.connect(goto_bug_list)

        # 運用管理（プロジェクト・画面・テストケース・テスト項目）
        self.management_tab = QTabWidget()
        # --- プロジェクト管理タブ ---
        self.management_tab.addTab(ProjectManagementWidget(), "プロジェクト管理")
        # --- 画面管理タブ ---
        self.management_tab.addTab(ScreenManagementWidget(), "画面管理")
        # --- テストケース管理タブ ---
        self.management_tab.addTab(TestCaseManagementWidget(), "テストケース管理")
        # --- テスト項目管理タブ ---
        self.management_tab.addTab(TestItemManagementWidget(), "テスト項目管理")
        self.stack.addWidget(self.management_tab)

        # システム管理（サブタブ：ユーザー管理・権限管理・ログ管理・設定）
        self.system_tab = QTabWidget()
        self.system_tab.addTab(QLabel("ユーザー管理画面（今後拡張予定）"), "ユーザー管理")
        self.system_tab.addTab(QLabel("権限管理画面（今後拡張予定）"), "権限管理")
        self.system_tab.addTab(QLabel("ログ管理画面（今後拡張予定）"), "ログ管理")
        self.system_tab.addTab(QLabel("システム設定画面（今後拡張予定）"), "設定")
        self.stack.addWidget(self.system_tab)

        # マスタ管理（サブタブ：一覧・新規作成・編集・削除・インポート・エクスポート）
        self.master_tab = QTabWidget()
        self.master_tab.addTab(QLabel("マスタ一覧画面（今後拡張予定）"), "一覧")
        self.master_tab.addTab(QLabel("マスタ新規作成画面（今後拡張予定）"), "新規作成")
        self.master_tab.addTab(QLabel("マスタ編集画面（今後拡張予定）"), "編集")
        self.master_tab.addTab(QLabel("マスタ削除画面（今後拡張予定）"), "削除")
        self.master_tab.addTab(QLabel("マスタインポート画面（今後拡張予定）"), "インポート")
        self.master_tab.addTab(QLabel("マスタエクスポート画面（今後拡張予定）"), "エクスポート")
        self.stack.addWidget(self.master_tab)

        self.sidebar.setCurrentRow(0)

    def _on_sidebar_changed(self, idx: int):
        """
        サイドバーの選択に応じてメインビューを切り替える
        """
        self.stack.setCurrentIndex(idx)

    def _create_management_tab(self) -> QWidget:
        """
        管理カテゴリ用のサブタブを作成
        運用管理（プロジェクト・画面・テストケース・テスト項目）とマスタ管理を分離
        """
        main_tab = QTabWidget()

        # 運用管理タブ
        operation_tab = QTabWidget()
        operation_tab.addTab(ProjectManagementWidget(), "プロジェクト")
        operation_tab.addTab(ScreenManagementWidget(), "画面")
        operation_tab.addTab(TestCaseManagementWidget(), "テストケース")
        operation_tab.addTab(TestItemManagementWidget(), "テスト項目")
        main_tab.addTab(operation_tab, "運用管理")

        # マスタ管理タブ（今後拡張予定。仮のプレースホルダーWidgetを設置）
        master_widget = QWidget()
        layout = QVBoxLayout(master_widget)
        layout.addWidget(QLabel("マスタ管理画面（今後拡張予定）"))
        main_tab.addTab(master_widget, "マスタ管理")

        return main_tab

    def open_test_execution(self, test_case_id: int):
        """
        テスト実行ウインドウを開く
        """
        self.exec_window = TestExecutionWindow(test_case_id)
        self.exec_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())