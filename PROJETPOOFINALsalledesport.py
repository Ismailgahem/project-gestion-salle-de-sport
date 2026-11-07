import sys
import sqlite3
import calendar
import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk, messagebox

TYPES = {
    "1 Mois": (1, 300),
    "3 Mois": (3, 800),
    "6 Mois": (6, 1500),
    "12 Mois": (12, 2800)
}
MODES_PAIEMENT = ["Espèces", "Carte Bancaire", "Chèque", "Virement"]
MOIS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
COULEURS = {"actif": "#d5ecd9", "bientot": "#ffe5b4", "expire": "#f8d7da"}

def add_months(d, months):
    """Ajoute un nombre de mois à une date en gérant les fins de mois."""
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)

def statut(date_fin_str):
    """Retourne le texte et le tag de couleur pour le statut d'un abonnement."""
    if not date_fin_str:
        return "Inconnu", "expire"
    fin = date.fromisoformat(date_fin_str)
    ajd = date.today()
    if fin < ajd:
        return "Expiré", "expire"
    elif (fin - ajd).days <= 7:
        return "Expire bientôt", "bientot"
    return "Actif", "actif"

def creer_tableau(parent, colonnes, hauteur=8):
    """Crée un Treeview avec barre de défilement."""
    cadre = ttk.Frame(parent)
    tv = ttk.Treeview(cadre, columns=[c[0] for c in colonnes],
                      show="headings", height=hauteur, selectmode="browse")
    for titre, largeur in colonnes:
        tv.heading(titre, text=titre)
        tv.column(titre, width=largeur, anchor="w")
    for tag, couleur in COULEURS.items():
        tv.tag_configure(tag, background=couleur)
    sb = ttk.Scrollbar(cadre, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return cadre, tv

def champ(parent, libelle, colonne, largeur=18, ligne=0):
    """Étiquette + zone de saisie placées dans une grille."""
    ttk.Label(parent, text=libelle).grid(row=ligne, column=colonne, sticky="w", padx=4)
    var = tk.StringVar()
    ttk.Entry(parent, textvariable=var, width=largeur).grid(
        row=ligne + 1, column=colonne, sticky="w", padx=4, pady=(0, 6))
    return var

# Classe de gestion de la base de données SQLite3

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

# Interface Graphique 

class OngletAdherents(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app, self.db, self.selection = app, app.db, None

        self.var_rech = tk.StringVar()
        barre = ttk.Frame(self)
        barre.pack(fill="x")
        ttk.Label(barre, text="Rechercher").grid(row=0, column=0, sticky="w")
        ttk.Entry(barre, textvariable=self.var_rech, width=30).grid(row=1, column=0)
        ttk.Button(barre, text="Rechercher", command=self.rafraichir).grid(row=1, column=1, padx=6)
        self.var_rech.trace_add("write", lambda *_: self.rafraichir())

        cadre, self.tv = creer_tableau(
            self, [("ID", 40), ("Nom", 120), ("Prénom", 120),
                   ("Téléphone", 120), ("Email", 200), ("Inscrit", 100)], 9)
        cadre.pack(fill="both", expand=True, pady=8)
        self.tv.bind("<<TreeviewSelect>>", self.on_select)

        form = ttk.Frame(self)
        form.pack(fill="x")
        self.v_nom = champ(form, "Nom", 0)
        self.v_prenom = champ(form, "Prénom", 1)
        self.v_tel = champ(form, "Téléphone", 2)
        self.v_email = champ(form, "Email", 3, 28)

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=4)
        for texte, cmd in [("Ajouter", self.ajouter), ("Modifier", self.modifier),
                           ("Supprimer", self.supprimer), ("Vider les champs", self.vider)]:
            ttk.Button(btns, text=texte, command=cmd).pack(side="left", padx=4)

    def rafraichir(self):
        self.tv.delete(*self.tv.get_children())
        for r in self.db.lister_adherents(self.var_rech.get().strip()):
            self.tv.insert("", "end", iid=str(r["id"]), values=(
                r["id"], r["nom"], r["prenom"], r["telephone"],
                r["email"], r["date_inscription"]))
        if self.selection is not None and self.tv.exists(str(self.selection)):
            self.tv.selection_set(str(self.selection))

    def on_select(self, _=None):
        sel = self.tv.selection()
        if not sel:
            return
        self.selection = int(sel[0])
        v = self.tv.item(sel[0], "values")
        self.v_nom.set(v[1]); self.v_prenom.set(v[2])
        self.v_tel.set(v[3]); self.v_email.set(v[4])

    def lire_formulaire(self):
        nom, prenom = self.v_nom.get().strip(), self.v_prenom.get().strip()
        tel, email = self.v_tel.get().strip(), self.v_email.get().strip()
        if not nom or not prenom:
            messagebox.showwarning("Champs manquants", "Le nom et le prénom sont obligatoires.")
            return None
        if tel and not tel.replace(" ", "").replace("+", "").isdigit():
            messagebox.showwarning("Téléphone invalide", "Le téléphone ne doit contenir que des chiffres.")
            return None
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            messagebox.showwarning("Email invalide", "Veuillez saisir une adresse email valide.")
            return None
        return nom, prenom, tel, email

    def ajouter(self):
        donnees = self.lire_formulaire()
        if donnees:
            self.db.ajouter_adherent(*donnees)
            self.vider()
            self.app.rafraichir_tout()

    def modifier(self):
        if self.selection is None:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord un adhérent dans le tableau.")
            return
        donnees = self.lire_formulaire()
        if donnees:
            self.db.modifier_adherent(self.selection, *donnees)
            self.app.rafraichir_tout()

    def supprimer(self):
        if self.selection is None:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord un adhérent dans le tableau.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer cet adhérent ?\nSes abonnements et paiements seront également supprimés."):
            self.db.supprimer_adherent(self.selection)
            self.vider()
            self.app.rafraichir_tout()

    def vider(self):
        self.selection = None
        for v in (self.v_nom, self.v_prenom, self.v_tel, self.v_email):
            v.set("")
        if self.tv.selection():
            self.tv.selection_remove(self.tv.selection())


class OngletAbonnements(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app, self.db = app, app.db
        self.adherents = {}

        form = ttk.Frame(self)
        form.pack(fill="x")
        ttk.Label(form, text="Adhérent").grid(row=0, column=0, sticky="w", padx=4)
        self.cb_adh = ttk.Combobox(form, state="readonly", width=22)
        self.cb_adh.grid(row=1, column=0, padx=4)
        ttk.Label(form, text="Type").grid(row=0, column=1, sticky="w", padx=4)
        self.cb_type = ttk.Combobox(form, state="readonly", values=list(TYPES), width=14)
        self.cb_type.current(0)
        self.cb_type.grid(row=1, column=1, padx=4)
        self.v_debut = tk.StringVar(value=date.today().isoformat())
        ttk.Label(form, text="Début").grid(row=0, column=2, sticky="w", padx=4)
        ttk.Entry(form, textvariable=self.v_debut, width=12).grid(row=1, column=2, padx=4)
        self.v_fin = tk.StringVar()
        ttk.Label(form, text="Fin (automatique)").grid(row=0, column=3, sticky="w", padx=4)
        ttk.Entry(form, textvariable=self.v_fin, width=12, state="readonly").grid(row=1, column=3, padx=4)
        self.v_prix = tk.StringVar()
        ttk.Label(form, text="Prix (DH)").grid(row=0, column=4, sticky="w", padx=4)
        ttk.Entry(form, textvariable=self.v_prix, width=8).grid(row=1, column=4, padx=4)
        ttk.Button(form, text="Créer l'abonnement", command=self.creer).grid(row=1, column=5, padx=8)

        self.cb_type.bind("<<ComboboxSelected>>", self.on_type)
        self.v_debut.trace_add("write", lambda *_: self.calculer_fin())
        self.on_type()

        cadre, self.tv = creer_tableau(
            self, [("ID", 40), ("Adhérent", 150), ("Type", 100),
                   ("Début", 100), ("Fin", 100), ("Statut", 150)], 10)
        cadre.pack(fill="both", expand=True, pady=10)
        ttk.Label(self, text="Vert : actif · Orange : expire sous 7 jours · Rouge : expiré", font=("Segoe UI", 8)).pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=8)
        ttk.Button(btns, text="Renouveler l'abonnement sélectionné", command=self.renouveler).pack(side="left", padx=4)
        ttk.Button(btns, text="Supprimer l'abonnement sélectionné", command=self.supprimer).pack(side="left", padx=4)

    def on_type(self, _=None):
        self.v_prix.set(str(TYPES[self.cb_type.get()][1]))
        self.calculer_fin()

    def calculer_fin(self):
        try:
            debut = date.fromisoformat(self.v_debut.get())
            self.v_fin.set(add_months(debut, TYPES[self.cb_type.get()][0]).isoformat())
        except ValueError:
            self.v_fin.set("")

    def rafraichir(self):
        self.adherents = {f"{r['nom']} {r['prenom']}": r["id"] for r in self.db.lister_adherents()}
        courant = self.cb_adh.get()
        self.cb_adh["values"] = list(self.adherents)
        if courant not in self.adherents:
            self.cb_adh.set("")
        self.tv.delete(*self.tv.get_children())
        for r in self.db.lister_abonnements():
            texte, tag = statut(r["date_fin"])
            self.tv.insert("", "end", iid=str(r["id"]), tags=(tag,), values=(
                r["id"], f"{r['nom']} {r['prenom']}", r["type"],
                r["date_debut"], r["date_fin"], texte))

    def creer(self):
        nom = self.cb_adh.get()
        if nom not in self.adherents:
            messagebox.showwarning("Adhérent", "Choisissez un adhérent.")
            return
        try:
            prix = float(self.v_prix.get().replace(",", "."))
            if prix <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Prix", "Le prix doit être un nombre positif.")
            return
        if not self.v_fin.get():
            messagebox.showwarning("Date", "Date de début invalide (format AAAA-MM-JJ).")
            return
        self.db.ajouter_abonnement(self.adherents[nom], self.cb_type.get(), self.v_debut.get(), self.v_fin.get(), prix)
        self.app.rafraichir_tout()

    def _id_selectionne(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord un abonnement.")
            return None
        return int(sel[0])

    def renouveler(self):
        id_ = self._id_selectionne()
        if id_:
            self.db.renouveler_abonnement(id_)
            self.app.rafraichir_tout()

    def supprimer(self):
        id_ = self._id_selectionne()
        if id_ and messagebox.askyesno("Confirmation", "Supprimer cet abonnement et ses paiements ?"):
            self.db.supprimer_abonnement(id_)
            self.app.rafraichir_tout()


class OngletPaiements(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app, self.db = app, app.db
        self.abos = {}

        ttk.Label(self, text="Abonnement").pack(anchor="w")
        self.cb_abo = ttk.Combobox(self, state="readonly", width=45)
        self.cb_abo.pack(anchor="w", pady=(0, 6))
        self.cb_abo.bind("<<ComboboxSelected>>", self.on_abo)

        resume = ttk.LabelFrame(self, text="Situation de l'abonnement", padding=8)
        resume.pack(fill="x")
        self.lbl = {}
        for i, nom in enumerate(["Prix", "Déjà payé", "Reste à payer"]):
            ttk.Label(resume, text=nom).grid(row=0, column=i, sticky="w", padx=20)
            self.lbl[nom] = ttk.Label(resume, text="-", font=("Segoe UI", 10, "bold"))
            self.lbl[nom].grid(row=1, column=i, sticky="w", padx=20)

        saisie = ttk.Frame(self)
        saisie.pack(fill="x", pady=8)
        ttk.Label(saisie, text="Montant (DH)").grid(row=0, column=0, sticky="w", padx=4)
        self.v_montant = tk.StringVar()
        ttk.Entry(saisie, textvariable=self.v_montant, width=12).grid(row=1, column=0, padx=4)
        ttk.Label(saisie, text="Mode").grid(row=0, column=1, sticky="w", padx=4)
        self.cb_mode = ttk.Combobox(saisie, state="readonly", values=MODES_PAIEMENT, width=12)
        self.cb_mode.current(0)
        self.cb_mode.grid(row=1, column=1, padx=4)
        ttk.Button(saisie, text="Enregistrer le paiement", command=self.enregistrer).grid(row=1, column=2, padx=8)
        ttk.Button(saisie, text="Supprimer le paiement", command=self.supprimer).grid(row=1, column=3, padx=4)

        cadre, self.tv = creer_tableau(
            self, [("ID", 40), ("Abonnement", 200), ("Montant", 100),
                   ("Date", 110), ("Mode", 110)], 9)
        cadre.pack(fill="both", expand=True)

    def rafraichir(self):
        self.abos = {}
        for r in self.db.lister_abonnements():
            libelle = f"#{r['id']} · {r['nom']} {r['prenom']} · {r['type']}"
            self.abos[libelle] = (r["id"], r["prix"])
        courant = self.cb_abo.get()
        self.cb_abo["values"] = list(self.abos)
        if courant not in self.abos:
            self.cb_abo.set("")
        self.on_abo(remplir=False)
        self.tv.delete(*self.tv.get_children())
        for p in self.db.lister_paiements():
            self.tv.insert("", "end", iid=str(p["id"]), values=(
                p["id"], f"#{p['abonnement_id']} {p['nom']} {p['prenom']}",
                f"{p['montant']:g} DH", p["date_paiement"], p["mode"]))

    def on_abo(self, _=None, remplir=True):
        if self.cb_abo.get() not in self.abos:
            for l in self.lbl.values():
                l.config(text="-")
            return
        id_, prix = self.abos[self.cb_abo.get()]
        paye = self.db.total_paye(id_)
        reste = max(prix - paye, 0)
        self.lbl["Prix"].config(text=f"{prix:g} DH")
        self.lbl["Déjà payé"].config(text=f"{paye:g} DH")
        self.lbl["Reste à payer"].config(text=f"{reste:g} DH")
        if remplir:
            self.v_montant.set(f"{reste:g}")

    def enregistrer(self):
        if self.cb_abo.get() not in self.abos:
            messagebox.showwarning("Abonnement", "Choisissez un abonnement.")
            return
        id_, prix = self.abos[self.cb_abo.get()]
        try:
            montant = float(self.v_montant.get().replace(",", "."))
            if montant <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Montant", "Le montant doit être un nombre positif.")
            return
        reste = prix - self.db.total_paye(id_)
        if montant > reste and not messagebox.askyesno(
                "Montant supérieur au reste",
                f"Le montant dépasse le reste à payer ({max(reste, 0):g} DH).\nContinuer ?"):
            return
        self.db.ajouter_paiement(id_, montant, self.cb_mode.get())
        self.app.rafraichir_tout()
        self.on_abo()

    def supprimer(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Sélection", "Sélectionnez d'abord un paiement.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer ce paiement ?"):
            self.db.supprimer_paiement(int(sel[0]))
            self.app.rafraichir_tout()


class OngletDashboard(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app, self.db = app, app.db

        cartes = ttk.Frame(self)
        cartes.pack(fill="x")
        self.val = {}
        for i, nom in enumerate(["Adhérents", "Abonnements actifs", "Expirés", "Revenus du mois"]):
            c = ttk.LabelFrame(cartes, padding=8)
            c.grid(row=0, column=i, padx=5, sticky="ew")
            cartes.columnconfigure(i, weight=1)
            self.val[nom] = ttk.Label(c, text="0", font=("Segoe UI", 18, "bold"))
            self.val[nom].pack(anchor="w")
            ttk.Label(c, text=nom).pack(anchor="w")

        bas = ttk.Frame(self)
        bas.pack(fill="both", expand=True, pady=12)
        gauche = ttk.Frame(bas)
        gauche.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ttk.Label(gauche, text="Expirent sous 7 jours", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        cadre, self.tv = creer_tableau(gauche, [("Adhérent", 150), ("Fin", 90), ("Reste", 70)], 8)
        cadre.pack(fill="both", expand=True)

        droite = ttk.Frame(bas)
        droite.pack(side="left", fill="both", expand=True)
        ttk.Label(droite, text="Revenus par mois (DH)", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.canvas = tk.Canvas(droite, width=380, height=220, bg="white", highlightthickness=1, highlightbackground="#bbb")
        self.canvas.pack(fill="both", expand=True)

    def rafraichir(self):
        db = self.db
        self.val["Adhérents"].config(text=str(db.nb_adherents()))
        self.val["Abonnements actifs"].config(text=str(db.nb_abonnements_actifs()))
        self.val["Expirés"].config(text=str(db.nb_abonnements_expires()))
        self.val["Revenus du mois"].config(text=f"{db.revenus_du_mois():,.0f} DH".replace(",", " "))

        self.tv.delete(*self.tv.get_children())
        for r in db.expirent_bientot(7):
            jours = (date.fromisoformat(r["date_fin"]) - date.today()).days
            self.tv.insert("", "end", tags=("bientot",), values=(
                f"{r['nom']} {r['prenom']}", r["date_fin"], f"{jours} jours"))
        self.dessiner_histogramme(db.revenus_par_mois(6))

    def dessiner_histogramme(self, donnees):
        c = self.canvas
        c.delete("all")
        c.update_idletasks()
        w, h = max(c.winfo_width(), 380), max(c.winfo_height(), 220)
        marge_bas, marge_haut = 28, 22
        maximum = max((d[2] for d in donnees), default=0) or 1
        largeur = (w - 20) / len(donnees) if donnees else w
        for i, (annee, mois, total) in enumerate(donnees):
            haut = (h - marge_bas - marge_haut) * total / maximum
            x0 = 10 + i * largeur + largeur * 0.15
            x1 = 10 + (i + 1) * largeur - largeur * 0.15
            y1 = h - marge_bas
            c.create_rectangle(x0, y1 - haut, x1, y1, fill="#2f6fa3", outline="")
            c.create_text((x0 + x1) / 2, y1 - haut - 8, text=f"{total:,.0f}".replace(",", " "), font=("Segoe UI", 8))
            c.create_text((x0 + x1) / 2, y1 + 12, text=MOIS[mois - 1], font=("Segoe UI", 8))
        c.create_line(10, h - marge_bas, w - 10, h - marge_bas, fill="#555")

# Fenêtre principale et Lancement

class Application(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Gestion Salle de Sport")
        self.geometry("960x600")
        self.minsize(900, 560)
        ttk.Style(self).theme_use("clam")

        ttk.Label(self, text="Gestion Salle de Sport", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        self.onglets = [OngletAdherents(self.nb, self), OngletAbonnements(self.nb, self),
                        OngletPaiements(self.nb, self), OngletDashboard(self.nb, self)]
        for onglet, titre in zip(self.onglets, ["Adhérents", "Abonnements", "Paiements", "Tableau de bord"]):
            self.nb.add(onglet, text=titre)

        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.rafraichir_tout())
        self.rafraichir_tout()

    def rafraichir_tout(self):
        for onglet in self.onglets:
            onglet.rafraichir()

if __name__ == "__main__":
    base = Database()
    if "--demo" in sys.argv:
        base.charger_demo()
    Application(base).mainloop()