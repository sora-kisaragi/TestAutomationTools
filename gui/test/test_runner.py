"""Thread to run pytest script for a given test_case_id and update DB."""
from PyQt5.QtCore import QThread, pyqtSignal
import os
import subprocess
import sys
import sqlite3
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
        if not os.path.isfile(script_path):
            msg = f"スクリプトが見つかりません: {script_path}"
            self._update_db(False)
            self.finished_signal.emit(self.test_case_id, False, msg)
            return

        # Run pytest as subprocess to easily capture output
        cmd = [sys.executable, "-m", "pytest", script_path, "-q"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        out, _ = proc.communicate()
        success = proc.returncode == 0
        # update DB
        self._update_db(success)
        self.finished_signal.emit(self.test_case_id, success, out)

    def _update_db(self, success: bool):
        result_text = "成功" if success else "失敗"
        with sqlite3.connect(scenario_db.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE test_items SET result=? WHERE test_case_id=?", (result_text, self.test_case_id))
            conn.commit() 