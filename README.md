# AudioScreenRecorder

Petite application Windows pour enregistrer le son du PC, un micro, ou les
deux dans un fichier WAV.

> **Projet personnel expérimental — purement vibecodé.** Il a été réalisé avec
> l'aide d'outils d'IA et n'est pas un logiciel professionnel. Il peut contenir
> des bugs : faites un essai avant toute utilisation importante.

## Fonctionnalités

- Capture de la sortie audio Windows avec WASAPI loopback.
- Capture d'un microphone, ou des deux sources simultanément.
- Sélection des périphériques et affichage des niveaux en direct.
- Enregistrement au format WAV dans le dossier `Music\Enregistrements` par
  défaut.
- Quand les deux sources sont enregistrées, elles sont mixées en stéréo à
  48 kHz. Une source seule conserve le format fourni par son périphérique.

## Utiliser l'application

### Depuis les sources

Windows et Python 3 sont nécessaires :

```powershell
python -m pip install -r requirements.txt
python app.py
```

### Exécutable Windows sans Python

Sur un PC Windows de construction, installez Python puis lancez `build.bat`.
Le script installe les dépendances et crée :

```text
dist\AudioRecorder.exe
```

Copiez cet exécutable sur un PC Windows compatible : Python n'est pas requis
sur le PC cible. La compilation doit être faite sous Windows, idéalement avec
la même architecture (64 bits) que le PC cible.

Pour distribuer le binaire, publiez-le comme fichier joint à une **GitHub
Release** plutôt que de l'ajouter au dépôt source.

## Fichiers du projet

- `app.py` : interface graphique Tkinter.
- `recorder.py` : détection des périphériques, capture et mixage audio.
- `requirements.txt` : dépendances Python et outil de création de l'exécutable.
- `build.bat` : script de construction de l'exécutable Windows.

## Limites connues

- WAV uniquement.
- Le mixage des deux sources est réalisé en mémoire et peut consommer beaucoup
  de RAM pour les longues sessions.
- Pas de pause/reprise ni de raccourcis clavier globaux.
- Les configurations avec plusieurs sorties audio ou Bluetooth ne sont pas
  testées exhaustivement.

## Contributions

Les retours et propositions d'amélioration sont les bienvenus. Pour signaler
un problème, indiquez votre version de Windows, le périphérique audio utilisé
et les étapes pour reproduire le problème. Évitez de joindre des
enregistrements contenant des données personnelles.
