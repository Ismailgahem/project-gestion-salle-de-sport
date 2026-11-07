"""Base de données de l'application Gestion Salle de Sport (SQLite).

Contient le schéma des 3 tables (adherents, abonnements, paiements) et la
classe Database qui regroupe toutes les requêtes SQL.

Test rapide :  python database.py
"""
import calendar
import sqlite3
from datetime import date, timedelta

# Type d'abonnement -> (durée en mois, prix en DH)
TYPES = {
    "1 Mois": (1, 300),
    "3 Mois": (3, 800),
    "6 Mois": (6, 1500),
    "12 Mois": (12, 2800)
}


def add_months(d, months):
    """Ajoute un nombre de mois à une date en gérant les fins de mois."""
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


class Database:
    def __init__(self, db_file="gym.db"):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row 
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS adherents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    telephone TEXT,
                    email TEXT,
                    date_inscription TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS abonnements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adherent_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    date_debut TEXT NOT NULL,
                    date_fin TEXT NOT NULL,
                    prix REAL NOT NULL,
                    FOREIGN KEY(adherent_id) REFERENCES adherents(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS paiements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    abonnement_id INTEGER NOT NULL,
                    montant REAL NOT NULL,
                    date_paiement TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    FOREIGN KEY(abonnement_id) REFERENCES abonnements(id) ON DELETE CASCADE
                );
            """)

    def charger_demo(self):
        pass                 # On peut ajouter des données de test ici

    def lister_adherents(self, recherche=""):
        if recherche:
            return self.conn.execute(
                "SELECT * FROM adherents WHERE nom LIKE ? OR prenom LIKE ?", 
                (f"%{recherche}%", f"%{recherche}%")
            ).fetchall()
        return self.conn.execute("SELECT * FROM adherents").fetchall()

    def ajouter_adherent(self, nom, prenom, tel, email):
        with self.conn:
            self.conn.execute(
                "INSERT INTO adherents (nom, prenom, telephone, email, date_inscription) VALUES (?, ?, ?, ?, ?)",
                (nom, prenom, tel, email, date.today().isoformat())
            )

    def modifier_adherent(self, id_, nom, prenom, tel, email):
        with self.conn:
            self.conn.execute(
                "UPDATE adherents SET nom=?, prenom=?, telephone=?, email=? WHERE id=?",
                (nom, prenom, tel, email, id_)
            )

    def supprimer_adherent(self, id_):
        with self.conn:
            self.conn.execute("DELETE FROM adherents WHERE id=?", (id_,))

    def lister_abonnements(self):
        return self.conn.execute("""
            SELECT a.id, a.type, a.date_debut, a.date_fin, a.prix, ad.nom, ad.prenom 
            FROM abonnements a JOIN adherents ad ON a.adherent_id = ad.id
        """).fetchall()

    def ajouter_abonnement(self, id_adh, type_abo, debut, fin, prix):
        with self.conn:
            self.conn.execute(
                "INSERT INTO abonnements (adherent_id, type, date_debut, date_fin, prix) VALUES (?, ?, ?, ?, ?)",
                (id_adh, type_abo, debut, fin, prix)
            )

    def renouveler_abonnement(self, id_):
        abo = self.conn.execute("SELECT type, date_fin FROM abonnements WHERE id=?", (id_,)).fetchone()
        if abo:
            nouvelle_fin = add_months(date.fromisoformat(abo['date_fin']), TYPES[abo['type']][0]).isoformat()
            with self.conn:
                self.conn.execute("UPDATE abonnements SET date_fin=? WHERE id=?", (nouvelle_fin, id_))

    def supprimer_abonnement(self, id_):
        with self.conn:
            self.conn.execute("DELETE FROM abonnements WHERE id=?", (id_,))

    def lister_paiements(self):
        return self.conn.execute("""
            SELECT p.id, p.abonnement_id, p.montant, p.date_paiement, p.mode, ad.nom, ad.prenom 
            FROM paiements p 
            JOIN abonnements a ON p.abonnement_id = a.id
            JOIN adherents ad ON a.adherent_id = ad.id
        """).fetchall()

    def total_paye(self, id_abo):
        res = self.conn.execute(
            "SELECT SUM(montant) as total FROM paiements WHERE abonnement_id=?", 
            (id_abo,)
        ).fetchone()
        return res['total'] if res['total'] else 0.0

    def ajouter_paiement(self, id_abo, montant, mode):
        with self.conn:
            self.conn.execute(
                "INSERT INTO paiements (abonnement_id, montant, date_paiement, mode) VALUES (?, ?, ?, ?)",
                (id_abo, montant, date.today().isoformat(), mode)
            )

    def supprimer_paiement(self, id_):
        with self.conn:
            self.conn.execute("DELETE FROM paiements WHERE id=?", (id_,))

    def nb_adherents(self):
        return self.conn.execute("SELECT COUNT(*) FROM adherents").fetchone()[0]

    def nb_abonnements_actifs(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM abonnements WHERE date_fin >= ?", 
            (date.today().isoformat(),)
        ).fetchone()[0]

    def nb_abonnements_expires(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM abonnements WHERE date_fin < ?", 
            (date.today().isoformat(),)
        ).fetchone()[0]

    def revenus_du_mois(self):
        debut_mois = date.today().replace(day=1).isoformat()
        res = self.conn.execute(
            "SELECT SUM(montant) FROM paiements WHERE date_paiement >= ?", 
            (debut_mois,)
        ).fetchone()[0]
        return res if res else 0.0

    def expirent_bientot(self, jours):
        ajd = date.today()
        limite = (ajd + timedelta(days=jours)).isoformat()
        return self.conn.execute("""
            SELECT ad.nom, ad.prenom, a.date_fin 
            FROM abonnements a JOIN adherents ad ON a.adherent_id = ad.id 
            WHERE a.date_fin BETWEEN ? AND ? ORDER BY a.date_fin
        """, (ajd.isoformat(), limite)).fetchall()

    def revenus_par_mois(self, mois_limite):
        res = self.conn.execute("""
            SELECT strftime('%Y', date_paiement) as annee, 
                   strftime('%m', date_paiement) as mois, 
                   SUM(montant) as total 
            FROM paiements 
            GROUP BY annee, mois 
            ORDER BY annee DESC, mois DESC LIMIT ?
        """, (mois_limite,)).fetchall()
        donnees = [(int(r['annee']), int(r['mois']), float(r['total'])) for r in res]
        return sorted(donnees)


if __name__ == "__main__":
    base = Database()
    print("Base gym.db prête : adhérents =", base.nb_adherents(),
          "| abonnements actifs =", base.nb_abonnements_actifs())
