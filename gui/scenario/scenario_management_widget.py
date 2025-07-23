"""
シナリオ編集ウィジェット（作成・削除を統合）
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal
from .scenario_creation_widget import ScenarioCreationWidget
from .scenario_delete_widget import ScenarioDeleteWidget

class ScenarioManagementWidget(QWidget):
    """
    シナリオ編集用ウィジェット（作成・削除を統合）
    """
    # シナリオ変更通知用シグナル
    scenario_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 上部タイトル
        title_layout = QHBoxLayout()
        title_label = QLabel("シナリオ編集")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 作成タブ
        self.creation_widget = ScenarioCreationWidget()
        self.tab_widget.addTab(self.creation_widget, "📝 作成・追加")
        
        # 削除タブ
        self.delete_widget = ScenarioDeleteWidget()
        self.tab_widget.addTab(self.delete_widget, "🗑️ 削除")
        
        layout.addWidget(self.tab_widget)
    
    def _connect_signals(self):
        """シグナル接続"""
        # 作成・削除時に外部に通知
        self.creation_widget.scenario_created.connect(self.scenario_changed.emit)
        self.delete_widget.deletion_completed.connect(self.scenario_changed.emit)
        
        # 作成・削除相互の更新
        self.creation_widget.scenario_created.connect(self._on_scenario_updated)
        self.delete_widget.deletion_completed.connect(self._on_scenario_updated)
    
    def _on_scenario_updated(self):
        """シナリオ更新時の内部処理"""
        # 削除タブの一覧を更新
        if hasattr(self.delete_widget, '_load_table'):
            self.delete_widget._load_table()
        
        # 作成タブのプロジェクト一覧を更新
        if hasattr(self.creation_widget, '_load_projects'):
            self.creation_widget._load_projects()