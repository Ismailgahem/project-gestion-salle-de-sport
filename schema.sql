-- Schéma de la base gym.db (3 tables)
PRAGMA foreign_keys = ON;

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
