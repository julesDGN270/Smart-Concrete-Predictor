# Construire le .exe Windows

## Pourquoi le faire sur Windows et pas ailleurs
PyInstaller construit un executable pour le systeme sur lequel il tourne.
Un .exe Windows fiable doit donc etre construit SUR Windows (pas via
cross-compilation depuis Linux/Mac, qui donne des resultats peu fiables
avec des dependances C comme CatBoost/scikit-learn/matplotlib).

## Prerequis (sur le PC Windows qui construit le .exe)
- Python 3.10, 3.11 ou 3.12 installe (https://python.org, cocher
  "Add Python to PATH" a l'installation)

## Etapes
1. Copie tout le dossier du projet sur ce PC Windows.
2. Ouvre une invite de commandes (cmd) dans ce dossier.
3. Lance :
   ```
   build_windows.bat
   ```
4. Attends la fin (plusieurs minutes, CatBoost/scikit-learn sont volumineux).
5. Le fichier `dist\SmartConcretePredictor.exe` est ton executable autonome.

## Distribution sur d'autres PC
- Copie uniquement `SmartConcretePredictor.exe` (un seul fichier).
- Le PC qui le recoit n'a besoin ni de Python, ni d'aucune dependance.
- Au premier lancement, un dossier `history/` sera cree a cote de
  l'executable pour stocker la base SQLite -- garde l'exe dans un
  dossier ou l'utilisateur a le droit d'ecrire.

## Si tu changes le modele (best_concrete_model.pkl)
Il faut reconstruire le .exe (relancer build_windows.bat) : le modele
est embarque dans l'executable au moment de la construction.

## Problemes frequents
- **Antivirus qui bloque l'exe** : les .exe generes par PyInstaller
  sont parfois signales a tort par certains antivirus (faux positif
  connu et documente par le projet PyInstaller). Il faut alors ajouter
  une exception.
- **Fenetre qui s'ouvre puis se ferme immediatement** : relance depuis
  cmd (pas en double-cliquant) pour voir le message d'erreur.

## Aller plus loin : un vrai installeur (pas juste un .exe portable)

Ce que `build_windows.bat` produit est un executable **portable** :
il fonctionne en le double-cliquant, mais il n'apparait pas dans
"Programmes installes", n'a pas de raccourci menu Demarrer, pas de
desinstalleur. Si tu veux une vraie installation :

1. Installe **Inno Setup** (gratuit) : https://jrsoftware.org/isdl.php
2. Construis d'abord `SmartConcretePredictor.exe` avec `build_windows.bat`
   (celui-ci doit exister dans `dist\` avant l'etape suivante).
3. Ouvre `installer\setup.iss` avec Inno Setup Compiler.
4. Clique sur **Compile** (ou touche F9).
5. Le vrai installeur se trouve dans `installer_output\SmartConcretePredictor_Setup.exe`.

C'est ce fichier `..._Setup.exe` que tu distribues desormais : il
installe l'app dans Program Files (ou le dossier utilisateur), cree
les raccourcis, et ajoute un desinstalleur propre.
