# RPA_BanqueKYC

Projet UiPath RPA – Ouverture de compte bancaire automatisée

## Structure
- `Workflows/` : Contient les séquences d'automatisation (Main, OCR, KYC, etc.)
- `Data/` : Dossiers d'entrée/sortie, logs et fichier de configuration
- `Templates/` : Modèles HTML pour les emails et les RIBs

## Fonctionnalités
1. OCR_Extraction : Extraction des informations client depuis les documents fournis.
2. KYC_Verification : Vérification des sanctions et de l'identité.
3. Compte_Creation : Saisie automatique dans l'application bancaire.
4. RIB_Generation : Création de la preuve (RIB).
5. Notification : Envoi d'emails.
