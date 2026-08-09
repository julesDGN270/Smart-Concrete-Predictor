import sqlite3
import os
import csv
from datetime import datetime

DB_PATH = os.path.join("history", "concrete_history.db")
LEGACY_CSV_PATH = os.path.join("history", "predictions.csv")


class Database:
    """
    Couche unique d'acces aux donnees de l'application.
    Remplace l'ancien HistoryManager (CSV) : toutes les fenetres
    (main_window, history_window, analysis_window) passent desormais
    par cette classe pour lire/ecrire l'historique des predictions.
    """

    def __init__(self, db_path=DB_PATH):
        os.makedirs("history", exist_ok=True)
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.create_table()
        self._migrate_legacy_csv_if_needed()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                cement REAL,
                slag REAL,
                fly_ash REAL,
                water REAL,
                superplasticizer REAL,
                coarse REAL,
                fine REAL,
                age REAL,
                prediction REAL,
                source TEXT DEFAULT 'manuel'
            )
        """)
        self.connection.commit()

        self.cursor.execute("PRAGMA table_info(predictions)")
        existing_cols = [row[1] for row in self.cursor.fetchall()]
        if "source" not in existing_cols:
            self.cursor.execute(
                "ALTER TABLE predictions ADD COLUMN source TEXT DEFAULT 'manuel'"
            )
            self.connection.commit()
        if "user_id" not in existing_cols:
            self.cursor.execute(
                "ALTER TABLE predictions ADD COLUMN user_id INTEGER"
            )
            self.connection.commit()
        if "company_id" not in existing_cols:
            self.cursor.execute(
                "ALTER TABLE predictions ADD COLUMN company_id INTEGER"
            )
            self.connection.commit()

    def _migrate_legacy_csv_if_needed(self):
        self.cursor.execute("SELECT COUNT(*) FROM predictions")
        count = self.cursor.fetchone()[0]

        if count > 0 or not os.path.exists(LEGACY_CSV_PATH):
            return

        try:
            with open(LEGACY_CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except OSError:
            return

        if len(rows) <= 1:
            return

        for row in rows[1:]:
            if len(row) < 10:
                continue
            date_str = row[0]
            try:
                values = [float(v) for v in row[1:9]]
                prediction = float(row[9])
            except ValueError:
                continue

            self.cursor.execute("""
                INSERT INTO predictions(
                    date, cement, slag, fly_ash, water,
                    superplasticizer, coarse, fine, age,
                    prediction, source
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (date_str, *values, prediction, "migration_csv"))

        self.connection.commit()

    def insert(self, values, prediction, source="manuel", user_id=None, company_id=None):
        self.cursor.execute("""
            INSERT INTO predictions(
                date, cement, slag, fly_ash, water,
                superplasticizer, coarse, fine, age,
                prediction, source, user_id, company_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            *values,
            prediction,
            source,
            user_id,
            company_id
        ))
        self.connection.commit()
        return self.cursor.lastrowid

    def fetch_all(self, user_id=None, company_id=None):
        """Historique des predictions.
        - company_id fourni -> historique partage de toute l'entreprise
        - sinon user_id fourni -> historique personnel de ce compte
        - aucun des deux -> tout l'historique (usage interne/legacy)"""
        cols = "id, date, cement, slag, fly_ash, water, superplasticizer, coarse, fine, age, prediction, source"
        if company_id is not None:
            self.cursor.execute(
                f"SELECT {cols} FROM predictions WHERE company_id=? ORDER BY id DESC",
                (company_id,)
            )
        elif user_id is not None:
            self.cursor.execute(
                f"SELECT {cols} FROM predictions WHERE user_id=? ORDER BY id DESC",
                (user_id,)
            )
        else:
            self.cursor.execute(f"SELECT {cols} FROM predictions ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_all(self, user_id=None, company_id=None):
        return self.fetch_all(user_id=user_id, company_id=company_id)

    def search(self, text, user_id=None, company_id=None):
        text = f"%{text.lower()}%"
        cols = "id, date, cement, slag, fly_ash, water, superplasticizer, coarse, fine, age, prediction, source"
        if company_id is not None:
            scope_clause, scope_value = "company_id=?", company_id
        elif user_id is not None:
            scope_clause, scope_value = "user_id=?", user_id
        else:
            scope_clause, scope_value = None, None

        if scope_clause:
            self.cursor.execute(f"""
                SELECT {cols} FROM predictions
                WHERE {scope_clause} AND (LOWER(date) LIKE ? OR CAST(prediction AS TEXT) LIKE ?)
                ORDER BY id DESC
            """, (scope_value, text, text))
        else:
            self.cursor.execute(f"""
                SELECT {cols} FROM predictions
                WHERE LOWER(date) LIKE ? OR CAST(prediction AS TEXT) LIKE ?
                ORDER BY id DESC
            """, (text, text))
        return self.cursor.fetchall()

    def delete(self, record_id):
        self.cursor.execute(
            "DELETE FROM predictions WHERE id=?", (record_id,)
        )
        self.connection.commit()

    def count(self):
        self.cursor.execute("SELECT COUNT(*) FROM predictions")
        return self.cursor.fetchone()[0]

    def close(self):
        self.connection.close()
