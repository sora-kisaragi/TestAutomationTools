"""
Excelインポート結果ダイアログ
"""
import sys
import os
if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QDialog, QHBoxLayout, QSplitter, QWidget, QVBoxLayout, QListWidget, QScrollArea, QLabel
from PyQt5.QtCore import Qt
from .constants import *

class ImportResultDialog(QDialog):
    """
    Excelインポート結果を画面ごとに詳細表示する専用ダイアログ
    左: 画面リスト, 右: 詳細（シナリオ・テスト項目数）
    右側はスクロール可能
    左リストはサイズ固定・スクロール対応
    """
    def __init__(self, import_result, parent=None):
        super().__init__(parent)
        self.setWindowTitle("インポート結果詳細")
        self.resize(*DIALOG_SIZE)  # 定数利用
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # 左: 画面リスト（スクロール対応・サイズ固定）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.screen_list = QListWidget()
        for s in import_result:
            self.screen_list.addItem(s["screen"])
        self.screen_list.setMinimumWidth(SCREEN_LIST_MIN_WIDTH)
        self.screen_list.setMaximumWidth(SCREEN_LIST_MAX_WIDTH)
        self.screen_list.setFixedWidth(SCREEN_LIST_FIXED_WIDTH)
        # スクロールエリアでラップ
        scroll_left = QScrollArea()
        scroll_left.setWidgetResizable(True)
        scroll_left.setWidget(self.screen_list)
        scroll_left.setFixedWidth(SCROLL_LEFT_FIXED_WIDTH)
        left_layout.addWidget(scroll_left)
        splitter.addWidget(left_widget)

        # 右: 詳細表示（スクロール可・上揃え）
        self.detail_area = QScrollArea()
        self.detail_area.setWidgetResizable(True)
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setAlignment(Qt.AlignTop)
        self.detail_area.setWidget(self.detail_widget)
        self.detail_area.setMinimumWidth(DETAIL_AREA_MIN_WIDTH)
        self.detail_area.setMaximumWidth(DETAIL_AREA_MAX_WIDTH)
        splitter.addWidget(self.detail_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # 初期表示
        if import_result:
            self._show_detail(import_result[0])
        self.screen_list.currentRowChanged.connect(
            lambda idx: self._show_detail(import_result[idx]) if 0 <= idx < len(import_result) else None
        )

    def _show_detail(self, screen_data):
        # 右側の詳細エリアをクリア
        for i in reversed(range(self.detail_layout.count())):
            w = self.detail_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        # タイトル
        self.detail_layout.addWidget(QLabel(f"<b>画面名：</b>{screen_data['screen']}"))
        # シナリオ一覧
        for sc in screen_data["scenarios"]:
            label = QLabel(f"・<b>{sc['name']}</b>（テスト項目数: {sc['testcase_count']}）")
            label.setWordWrap(True)
            self.detail_layout.addWidget(label)
