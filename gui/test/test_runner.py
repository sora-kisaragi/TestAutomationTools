"""Thread to run pytest script for a given test_case_id and update DB."""
from PyQt5.QtCore import QThread, pyqtSignal
import os
import subprocess
import sys
import sqlite3
import logging
from core import scenario_db


class TestRunnerThread(QThread):
    finished_signal = pyqtSignal(int, bool, str)  # test_case_id, success, log text

    def __init__(self, test_case_id: int, parent=None):
        super().__init__(parent)
        self.test_case_id = test_case_id
        # base dir where e2e scripts are stored
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "e2e")

    def run(self):
        script_path = os.path.join(self.base_dir, str(self.test_case_id), "run.py")
        
        # パス検証
        if not self._is_safe_path(script_path):
            msg = f"不正なパスが指定されました: {script_path}"
            logging.warning(msg)
            self._update_db(False)
            self.finished_signal.emit(self.test_case_id, False, msg)
            return
            
        if not os.path.isfile(script_path):
            msg = f"スクリプトが見つかりません: {script_path}"
            self._update_db(False)
            self.finished_signal.emit(self.test_case_id, False, msg)
            return

        try:
            cmd = [sys.executable, "-m", "pytest", script_path, "-q"]
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                shell=False,
                timeout=300
            )
            out, _ = proc.communicate(timeout=300)
            success = proc.returncode == 0
            # update DB
            self._update_db(success)
            self.finished_signal.emit(self.test_case_id, success, out)
        except subprocess.TimeoutExpired:
            proc.kill()
            msg = "テスト実行がタイムアウトしました"
            logging.error(msg)
            self._update_db(False)
            self.finished_signal.emit(self.test_case_id, False, msg)
        except Exception as e:
            msg = f"テスト実行中にエラーが発生しました: {str(e)}"
            logging.exception("テスト実行エラー")
            self._update_db(False)
            self.finished_signal.emit(self.test_case_id, False, msg)

    def _is_safe_path(self, path: str) -> bool:
        try:
            normalized_path = os.path.normpath(os.path.abspath(path))
            normalized_base = os.path.normpath(os.path.abspath(self.base_dir))
            
            if not normalized_path.startswith(normalized_base):
                return False
                
            if not str(self.test_case_id).isdigit():
                return False
                
            return True
        except Exception:
            return False

    def _update_db(self, success: bool):
        result_text = "成功" if success else "失敗"
        try:
            with sqlite3.connect(scenario_db.DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("UPDATE test_items SET result=? WHERE test_case_id=?", (result_text, self.test_case_id))
                conn.commit()
        except Exception as e:
            logging.exception("データベース更新エラー") 