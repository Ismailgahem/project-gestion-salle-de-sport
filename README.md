





🏋️ Application de Gestion d'une Salle de Sport
Une application de bureau Python simple et intuitive pour gérer les adhérents, leurs abonnements et leurs paiements dans une salle de sport.

Projet du module Python avancé — ENSAM Casablanca, IAGI 1ère année — 2026 – 2027.

📌 Présentation du Projet
Base de données (SQLite3) : un fichier gym.db, créé automatiquement au premier lancement, avec 3 tables liées par des clés étrangères.
Interface graphique (Tkinter) : fenêtre à onglets avec recherche, formulaires, contrôles de saisie et tableau de bord.
✨ Fonctionnalités Principales
👤 Adhérents : ajout, modification, suppression et recherche en direct, avec contrôle du téléphone et de l'email.
🗓️ Abonnements : formules de 1, 3, 6 ou 12 mois ; date de fin et prix calculés automatiquement ; statut en couleur (Actif, Expire bientôt, Expiré) ; renouvellement en un clic.
💰 Paiements : prix, montant déjà payé et reste à payer ; modes Espèces, Carte Bancaire, Chèque ou Virement ; historique.
📊 Tableau de bord : nombre d'adhérents, abonnements actifs et expirés, revenus du mois, expirations sous 7 jours et histogramme des revenus.
🗄️ Schéma de la Base de Données
Entité	Attributs	Description
adherents	id (PK), nom, prenom, telephone, email, date_inscription	Informations sur les adhérents.
abonnements	id (PK), adherent_id (FK), type, date_debut, date_fin, prix	Abonnements souscrits.
paiements	id (PK), abonnement_id (FK), montant, date_paiement, mode	Règlements d'un abonnement.
Remarque : Un adhérent a plusieurs abonnements et un abonnement a plusieurs paiements. Supprimer un adhérent supprime ses abonnements et leurs paiements (ON DELETE CASCADE). Le statut et le reste à payer sont calculés, jamais stockés.

🛠️ Stack Technique
Langage : Python 3.x (bibliothèque standard uniquement)
Interface Graphique (GUI) : Tkinter
Base de données : SQLite3
🚀 Lancement
python gestion_salle_sport.py
👥 Équipe
Réalisé par : GURAINI YAHYA · GAHEM ISMAIL · QUASSAY SAAD
Encadrant : M. MUSTAPHA HAIN
