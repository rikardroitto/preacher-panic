# Ordlabyrint Spel

Ett Flask-baserat webbspel där spelaren tar sig genom en labyrint av ord.

## Installation

```bash
pip install -r requirements.txt
```

## Köra spelet

```bash
python app.py
```

Öppna sedan webbläsaren på `http://localhost:5000`

## Spelregler

- Klistra in ord i textrutan på startskärmen
- Använd piltangenterna för att röra spelaren
- Ta dig från vänster till höger genom labyrinten
- Undvik monsterna som vandrar runt
- Hitta vägen till det gröna målet!

## Funktioner

- Dynamisk labyrintgenerering med garanterad väg genom
- Ord från användaren bygger labyrintens väggar
- Monster med AI som rör sig några steg i varje riktning
- Canvas-baserad rendering med temporära rektanglar (redo för sprites)
