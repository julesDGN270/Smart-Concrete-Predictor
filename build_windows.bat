@echo off
REM ============================================================
REM Construit un .exe Windows autonome de Smart Concrete Predictor
REM A executer SUR WINDOWS, avec Python 3.10+ deja installe.
REM ============================================================

echo [1/4] Installation des dependances...
pip install -r requirements.txt

echo [2/4] Nettoyage des builds precedents...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del SmartConcretePredictor.spec 2>nul

echo [3/4] Construction de l'executable (peut prendre plusieurs minutes)...
pyinstaller --onefile --windowed --noconfirm ^
    --name SmartConcretePredictor ^
    --add-data "best_concrete_model.pkl;." ^
    --collect-all catboost ^
    --collect-all sklearn ^
    --hidden-import sklearn.utils._typedefs ^
    --hidden-import sklearn.neighbors._partition_nodes ^
    app_v2.py

echo [4/4] Termine.
echo L'executable se trouve dans : dist\SmartConcretePredictor.exe
echo Copie ce seul fichier sur les autres PC pour l'installer.
pause
