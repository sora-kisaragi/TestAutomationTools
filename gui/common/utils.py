"""
GUI共通ユーティリティ関数
"""
from PyQt5.QtWidgets import QInputDialog, QWidget, QListWidget, QAbstractItemView
from typing import List, Tuple

def get_text_dialog(parent: QWidget, msg: str):
    """
    テキスト入力ダイアログを表示し、(入力値, OKフラグ)を返す
    """
    return QInputDialog.getText(parent, "入力", msg)

def get_selected_rows_from_listwidget(list_widget: QListWidget, data_list: List[Tuple]) -> List[Tuple]:
    """
    QListWidgetの複数選択から、選択された行番号・値リストを返す共通関数。
    :param list_widget: 対象のQListWidget
    :param data_list: 対応するデータ（例: [(id, name), ...]）
    :return: 選択された[(id, name), ...]リスト
    """
    selected_indexes = list_widget.selectedIndexes()
    if not selected_indexes or not data_list:
        return []
    selected_rows = sorted([idx.row() for idx in selected_indexes], reverse=True)
    return [data_list[idx] for idx in selected_rows]
