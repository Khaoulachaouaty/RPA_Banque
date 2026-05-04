# Documentation de la Logique du Workflow - RPA_Banque

Ce document décrit la structure et le fonctionnement du processus d'automatisation de l'ouverture de compte bancaire (KYC et Création de Compte).

## Orchestration Principale (`Main.xaml`)

Le workflow `Main.xaml` orchestre l'ensemble du processus en suivant ces étapes :

1.  **Initialisation** : Charge la configuration depuis `Data/Config.csv`.
2.  **Capture des Données (Formulaire)** : 
    *   Le client remplit le formulaire web sur `http://localhost:5000/form`.
    *   Le serveur Python (`server.py`) reçoit les données et les images, puis les enregistre dans `Data/Input`.
3.  **Traitement par Client (UiPath)** : Pour chaque fichier JSON trouvé dans le dossier d'entrée :
    *   **Extraction des Données** : Lecture du JSON (Nom, Prénom, Email, CIN, Type de Compte).
    *   **Identification de l'Image CIN** : Recherche le fichier image correspondant au numéro de CIN.
    *   **Extraction OCR** : Appelle `OCR_Extraction.xaml` pour extraire le numéro de CIN de l'image et valider le document.
    *   **Validation des Documents** :
        *   Si valide :
            1.  **Vérification KYC** : Appelle `KYC_Verification.xaml` (Simulation d'API).
            2.  **Création de Compte** : Si le KYC est approuvé, automatise la saisie sur le portail bancaire via `Compte_Creation.xaml`.
            3.  **Génération de RIB** : Produit un fichier HTML personnalisé via `RIB_Generation.xaml`.
            4.  **Notification de Succès** : Envoie un email de confirmation avec le RIB en pièce jointe via `Notification.xaml`.
            5.  **Archivage** : Déplace le fichier JSON traité vers le dossier de sortie.
        *   Si invalide :
            1.  **Notification d'Erreur** : Envoie un email informant le client que les documents sont non-conformes.

---

## Détails des Workflows Secondaires

### 1. Initialisation (`Workflows\Initialisation.xaml`)
*   **Source** : `Data\Config.csv`.
*   **Logique** : Lit le fichier CSV ligne par ligne et remplit un dictionnaire `out_Config`. Les chemins se terminant par "path" sont convertis en chemins absolus.

### 2. OCR Extraction (`Workflows\OCR_Extraction.xaml`)
*   **Moteur** : Tesseract (Google OCR).
*   **Logique** : 
    *   Extrait le texte de l'image CIN.
    *   Utilise une expression régulière (`\d{8}`) pour trouver le numéro de CIN.
    *   **Fallback** : Si l'OCR échoue, tente d'extraire le numéro depuis le nom du fichier.
*   **Sortie** : Numéro de CIN et un booléen de validité.

### 3. KYC Verification (`Workflows\KYC_Verification.xaml`)
*   **Méthode** : Simulation d'appel API REST.
*   **Logique de Décision** :
    *   `isSanctioned = true` → **REJETE**.
    *   `riskScore > 70` → **A_VERIFIER**.
    *   Sinon → **APPROUVE**.

### 4. Compte Creation (`Workflows\Compte_Creation.xaml`)
*   **Interface** : Navigateur Edge (Portail Bancaire).
*   **Actions** :
    *   Connexion avec l'identifiant agent.
    *   Saisie du nom du client.
    *   Clic sur "Valider".
    *   Récupération du numéro de compte généré depuis l'interface.

### 5. RIB Generation (`Workflows\RIB_Generation.xaml`)
*   **Modèle** : `Templates\RIB_Template.html`.
*   **Logique** : Remplace les balises dynamiques (`{{NOM}}`, `{{PRENOM}}`, etc.) par les données réelles et enregistre le résultat dans `Data\Output`.

### 6. Notification (`Workflows\Notification.xaml`)
*   **Protocole** : SMTP.
*   **Types de notifications** :
    *   `CONFIRMATION` : Email de bienvenue avec RIB.
    *   `DOCS_INVALIDES` : Email de rejet pour non-conformité.
