# Deployer la version web (gratuit, modifiable apres mise en ligne)

## Pourquoi Render
- Gratuit pour un usage modeste (le service "s'endort" apres 15 min sans
  visite et se reveille en quelques secondes au prochain visiteur -- normal
  sur le plan gratuit, pas un bug).
- Chaque `git push` redeploie automatiquement -- c'est le "modifiable
  meme apres hebergement" que tu voulais : tu changes le code, tu push,
  c'est en ligne quelques minutes plus tard.
- Domaine personnalise branchable gratuitement des que tu en achetes un
  (Settings > Custom Domain sur Render, puis un enregistrement CNAME/A
  chez ton registrar).

## Etape 1 : mettre le projet sur GitHub
1. Cree un compte GitHub si tu n'en as pas (gratuit).
2. Cree un nouveau repository (peut etre prive).
3. Depuis le dossier du projet :
   ```
   git init
   git add .
   git commit -m "Version initiale"
   git branch -M main
   git remote add origin https://github.com/<ton-compte>/<ton-repo>.git
   git push -u origin main
   ```

## Etape 2 : creer le service sur Render
1. Va sur https://render.com, cree un compte (gratuit, via GitHub direct
   si tu veux).
2. "New +" -> "Web Service".
3. Connecte ton repository GitHub.
4. Render detecte `render.yaml` automatiquement (Build command et Start
   command deja configures) -- sinon renseigne manuellement :
   - Build command : `pip install -r webapp/requirements.txt`
   - Start command : `gunicorn --chdir . webapp.app:app`
5. Choisis le plan **Free**.
6. "Create Web Service" -- le premier deploiement prend quelques minutes
   (CatBoost/scikit-learn sont volumineux).

## Etape 3 : verifier
Render te donne une URL du type `https://smart-concrete-predictor.onrender.com`.
Ouvre-la : tu dois voir la page de prediction, puis teste l'onglet
Formulation IA.

## Mettre a jour l'app plus tard
```
git add .
git commit -m "Description du changement"
git push
```
Render redeploie automatiquement. Rien d'autre a faire.

## Quand tu achetes un domaine
1. Sur Render : Settings du service -> Custom Domain -> renseigne ton
   domaine.
2. Render te donne un enregistrement DNS (CNAME le plus souvent) a
   ajouter chez ton registrar (Namecheap, OVH, etc.).
3. Propagation DNS : quelques minutes a quelques heures.

## Limites du plan gratuit a connaitre
- Le service s'endort apres 15 min d'inactivite -- le premier visiteur
  apres une pause attend ~30-50 secondes le temps du reveil.
- Ressources limitees (RAM/CPU) : suffisant pour un usage labo/etudiant,
  pas pour un trafic important.
- Si ca devient un probleme, le plan payant le moins cher de Render leve
  ces limites sans changer de code.
