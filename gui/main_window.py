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
from gui.scenario.scenario_delete_widget import ScenarioDeleteWidget
from gui.bug.bug_entry_widget import BugEntryWidget
from gui.scenario.scenario_list_widget import ScenarioListWidget
from gui.project.project_management_widget import ProjectManagementWidget
from gui.screen.screen_management_widget import ScreenManagementWidget
from gui.testcase_management_widget import TestCaseManagementWidget
from gui.testitem_management_widget import TestItemManagementWidget
from gui.test.test_execution_window import TestExecutionWindow
from gui.test.test_scenario_select_window import TestScenarioSelectWindow
from gui.common.import_excel_tab import ImportExcelTab

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
        # ツールバーを削除し、一覧テーブルのみ配置
        self.scenario_list_widget = ScenarioListWidget()
        vbox.addWidget(self.scenario_list_widget)
        self.scenario_tab.addTab(scenario_list_tab, "一覧")

        # --- プロジェクト管理タブ (追加・削除) ---
        proj_manage_tab = QWidget()
        vbox_pm = QVBoxLayout(proj_manage_tab)
        self.project_management_widget = ProjectManagementWidget()
        # プロジェクト変更時に他のタブを更新
        self.project_management_widget.project_changed.connect(self._on_project_changed)
        vbox_pm.addWidget(self.project_management_widget)
        self.scenario_tab.addTab(proj_manage_tab, "プロジェクト管理")

        # --- シナリオ編集タブ（作成・削除統合） ---
        from gui.scenario.scenario_management_widget import ScenarioManagementWidget
        self.scenario_management_widget = ScenarioManagementWidget()
        # シナリオ変更時に他のタブを更新
        self.scenario_management_widget.scenario_changed.connect(self._on_scenario_changed)
        self.scenario_tab.addTab(self.scenario_management_widget, "シナリオ編集")

        # --- インポート・エクスポートタブ ---
        import_tab = ImportExcelTab()
        import_tab.import_completed.connect(self.scenario_list_widget._force_refresh)
        self.scenario_tab.addTab(import_tab, "一括インポート")

        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.addWidget(QLabel("Excelエクスポート画面（今後拡張予定）"))
        self.scenario_tab.addTab(export_tab, "エクスポート")

        self.stack.addWidget(self.scenario_tab)

        # 一覧タブとシナリオ管理タブの遷移は上部タブのクリック操作に統一

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
        self.management_project_widget = ProjectManagementWidget()
        self.management_project_widget.project_changed.connect(self._on_project_changed)
        self.management_tab.addTab(self.management_project_widget, "プロジェクト管理")
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

    def _on_project_changed(self):
        """
        プロジェクト変更時に他のタブを更新
        """
        # シナリオ一覧タブを更新
        if hasattr(self, 'scenario_list_widget'):
            self.scenario_list_widget._force_refresh()
        
        # 統合されたシナリオ管理ウィジェット内の作成・削除タブを更新
        if hasattr(self, 'scenario_management_widget'):
            if hasattr(self.scenario_management_widget.creation_widget, '_load_projects'):
                self.scenario_management_widget.creation_widget._load_projects()
            if hasattr(self.scenario_management_widget.delete_widget, '_load_projects'):
                self.scenario_management_widget.delete_widget._load_projects()

    def _on_scenario_changed(self):
        """
        シナリオ・テスト項目作成時に他のタブを更新
        """
        # シナリオ一覧タブを更新
        if hasattr(self, 'scenario_list_widget'):
            self.scenario_list_widget._force_refresh()
        
        # 統合されたシナリオ管理ウィジェット内の削除タブを更新
        if hasattr(self, 'scenario_management_widget'):
            self.scenario_management_widget._on_scenario_updated()

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