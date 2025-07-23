"""
シナリオ情報をSQLiteに保存・取得するためのモジュール
"""
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'scenarios.db')

# テーブル作成SQL
CREATE_PROJECTS_TABLE = '''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    remarks TEXT
);
'''

CREATE_SCREENS_TABLE = '''
CREATE TABLE IF NOT EXISTS screens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    remarks TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
'''

CREATE_TEST_CASES_TABLE = '''
CREATE TABLE IF NOT EXISTS test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT '未実行',
    last_run TEXT,
    result TEXT,
    remarks TEXT,
    FOREIGN KEY(screen_id) REFERENCES screens(id)
);
'''

CREATE_TEST_ITEMS_TABLE = '''
CREATE TABLE IF NOT EXISTS test_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    input_data TEXT,
    operation TEXT,
    expected TEXT,
    priority TEXT,
    tester TEXT,
    exec_date TEXT,
    result TEXT,
    bug_id INTEGER,  -- bugs.idを参照する場合はINTEGER
    remarks TEXT,
    FOREIGN KEY(test_case_id) REFERENCES test_cases(id),
    FOREIGN KEY(bug_id) REFERENCES bugs(id)
);
'''

CREATE_BUGS_TABLE = '''
CREATE TABLE IF NOT EXISTS bugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    bug_no INTEGER NOT NULL,
    test_item_id INTEGER,
    reported_date TEXT,
    summary TEXT,
    details TEXT,
    cause_category TEXT,
    severity TEXT,
    reproducibility TEXT,
    status TEXT,
    assignee TEXT,
    fix_date TEXT,
    remarks TEXT,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(project_id, bug_no),
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(test_item_id) REFERENCES test_items(id)
);
'''

CREATE_SCENARIOS_TABLE = '''
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_name TEXT NOT NULL,
    status TEXT,
    last_run TEXT,
    result TEXT,
    project_id INTEGER,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
'''

CREATE_MASTER_TABLES = [
    '''
    CREATE TABLE IF NOT EXISTS master_testers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_test_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_severities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_execution_statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_priorities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_test_environments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_cause_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS master_reproducibilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    '''
]

# 初期マスターデータ
INITIAL_MASTER_DATA = {
    "master_testers": ["テスターA", "テスターB", "テスターC", "テスターD"],
    "master_test_types": ["単体テスト", "結合テスト", "システムテスト", "受入テスト", "回帰テスト"],
    "master_statuses": ["未対応", "対応中", "修正済み", "保留", "却下", "再現不可", "クローズ"],
    "master_severities": ["致命的", "高", "中", "低"],
    "master_execution_statuses": ["未実施", "実施中", "実施済", "保留", "完了"],
    "master_priorities": ["高", "中", "低"],
    "master_results": ["未実施", "成功", "失敗", "要確認", "再実施中"],
    "master_test_environments": ["ローカル", "開発環境", "ステージング", "本番環境"],
    "master_cause_categories": ["仕様漏れ", "要件誤解", "実装ミス", "環境依存", "外部要因", "テスト不備", "その他"],
    "master_reproducibilities": ["毎回発生", "条件付きで発生", "まれに発生", "再現不可"]
}

def init_db():
    """
    DBファイルとテーブルを初期化
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # 新スキーマ
        conn.execute(CREATE_PROJECTS_TABLE)
        conn.execute(CREATE_SCENARIOS_TABLE)
        conn.execute(CREATE_SCREENS_TABLE)
        conn.execute(CREATE_TEST_CASES_TABLE)
        conn.execute(CREATE_TEST_ITEMS_TABLE)
        conn.execute(CREATE_BUGS_TABLE)
        
        # マスターテーブルを作成
        for table_sql in CREATE_MASTER_TABLES:
            conn.execute(table_sql)
        
        # 初期マスターデータを投入
        for table_name, values in INITIAL_MASTER_DATA.items():
            for value in values:
                try:
                    conn.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (value,))
                except sqlite3.IntegrityError:
                    # 既に存在する場合はスキップ
                    pass
        
        # マイグレーション: test_casesテーブルにカラムを追加
        _migrate_test_cases_table(conn)
        
        conn.commit()

def _migrate_test_cases_table(conn):
    """
    test_casesテーブルのマイグレーション
    既存のテーブルに新しいカラムを追加
    """
    try:
        # カラムの存在確認
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(test_cases)")
        columns = [row[1] for row in cur.fetchall()]
        
        # 不足しているカラムを追加
        if 'status' not in columns:
            conn.execute("ALTER TABLE test_cases ADD COLUMN status TEXT DEFAULT '未実行'")
        if 'last_run' not in columns:
            conn.execute("ALTER TABLE test_cases ADD COLUMN last_run TEXT")
        if 'result' not in columns:
            conn.execute("ALTER TABLE test_cases ADD COLUMN result TEXT")
            
        print("test_casesテーブルのマイグレーション完了")
    except Exception as e:
        print(f"マイグレーションエラー: {e}")

def get_next_bug_no(project_id: int) -> int:
    """
    指定プロジェクトの次のBUG番号を返す（1から連番）
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(bug_no) FROM bugs WHERE project_id = ?", (project_id,))
        row = cur.fetchone()
        return (row[0] or 0) + 1

def get_master_data(table_name: str) -> list:
    """
    指定したマスターテーブルからname一覧を取得
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT name FROM {table_name} ORDER BY id")
        rows = cur.fetchall()
        return [row[0] for row in rows]

def get_all_scenarios() -> list:
    """
    シナリオ一覧表示用のデータを取得
    各テスト項目（test_items）を、画面名・シナリオ名などと一緒に返す
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT 
                ti.id, 
                s.name as screen_name, 
                tc.name as scenario_name, 
                '' as attribute, -- 属性は未実装のため空文字
                ti.priority, 
                ti.tester, 
                ti.result
            FROM test_items ti
            JOIN test_cases tc ON ti.test_case_id = tc.id
            JOIN screens s ON tc.screen_id = s.id
            ORDER BY ti.id
        ''')
        rows = cur.fetchall()
        # カラム名に合わせて辞書化
        scenarios = []
        for row in rows:
            scenarios.append({
                'id': row[0],
                'screen_name': row[1],
                'scenario_name': row[2],
                'attribute': row[3],
                'priority': row[4],
                'tester': row[5],
                'result': row[6],
            })
        return scenarios

def delete_project(project_id: int) -> None:
    """
    指定したプロジェクトと関連データ（画面・テストケース・テスト項目）を全て削除する
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # 画面ID取得
        cur.execute("SELECT id FROM screens WHERE project_id=?", (project_id,))
        screen_ids = [row[0] for row in cur.fetchall()]
        # テストケースID取得
        case_ids = []
        for sid in screen_ids:
            cur.execute("SELECT id FROM test_cases WHERE screen_id=?", (sid,))
            case_ids.extend([row[0] for row in cur.fetchall()])
        # テスト項目削除
        if case_ids:
            cur.executemany("DELETE FROM test_items WHERE test_case_id=?", [(cid,) for cid in case_ids])
        # テストケース削除
        if screen_ids:
            cur.executemany("DELETE FROM test_cases WHERE screen_id=?", [(sid,) for sid in screen_ids])
        # 画面削除
        cur.execute("DELETE FROM screens WHERE project_id=?", (project_id,))
        # プロジェクト削除
        cur.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()

def insert_bug(data: dict) -> str:
    """
    不具合情報をDBに登録し、表示用BUG-ID（例: BUG-0001）を返す
    dataにはproject_id, その他項目が含まれること
    """
    project_id = data.get("project_id")
    if not project_id:
        raise ValueError("project_idは必須です")
    bug_no = get_next_bug_no(project_id)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bugs (
                project_id, bug_no, test_item_id, reported_date, summary, details, cause_category, severity, reproducibility, status, assignee, fix_date, remarks, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                bug_no,
                data.get("test_item_id"),
                data.get("reported_date"),
                data.get("summary"),
                data.get("details"),
                data.get("cause_category"),
                data.get("severity"),
                data.get("reproducibility"),
                data.get("status"),
                data.get("assignee"),
                data.get("fix_date"),
                data.get("remarks"),
                now,
                now
            )
        )
        conn.commit()
    # 表示用BUG-IDを返す
    return f"BUG-{bug_no:04d}"