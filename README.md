# Proyecto-II-Valeria-y-Ernesto
Este es el segundo proyecto de introducción a la progración, de defensa y asalto de base 

# Proyecto: Base Defensa

Juego de estrategia para dos jugadores hecho con Python + Tkinter. Pygame se usa únicamente para música.

## Cómo ejecutar

## Archivos principales

- `main.py`: archivo principal del juego.
- `jugadores.json`: guarda usuarios, contraseñas y victorias.
- `assets/`: carpeta para música e imágenes.

## Dónde reemplazar los assets

La música debe ir aquí:

```text
assets/music/musica.mp3
```

Las imágenes deben ser PNG y tener estos nombres exactos:

```text
assets/facciones/medieval/base.png
assets/facciones/medieval/muro.png
assets/facciones/medieval/torre_basica.png
assets/facciones/medieval/torre_pesada.png
assets/facciones/medieval/torre_magica.png
assets/facciones/medieval/soldado.png
assets/facciones/medieval/tanque.png
assets/facciones/medieval/rapida.png

assets/facciones/futurista/base.png
assets/facciones/futurista/muro.png
assets/facciones/futurista/torre_basica.png
assets/facciones/futurista/torre_pesada.png
assets/facciones/futurista/torre_magica.png
assets/facciones/futurista/soldado.png
assets/facciones/futurista/tanque.png
assets/facciones/futurista/rapida.png

assets/facciones/naturaleza/base.png
assets/facciones/naturaleza/muro.png
assets/facciones/naturaleza/torre_basica.png
assets/facciones/naturaleza/torre_pesada.png
assets/facciones/naturaleza/torre_magica.png
assets/facciones/naturaleza/soldado.png
assets/facciones/naturaleza/tanque.png
assets/facciones/naturaleza/rapida.png
```


## Clases usadas

- `Jugador`: usuario, contraseña y victorias.
- `Torre`: torres defensivas con daño, vida, alcance y habilidad.
- `Unidad`: unidades atacantes con daño, vida, velocidad y habilidad.
- `BaseCentral`: base fija del defensor.
- `Juego`: controla ventanas, rondas, combate, dinero, JSON y tablero.

## Habilidades

Torres:

- Torre básica: disparo doble.
- Torre pesada: golpe reforzado.
- Torre mágica: congela una unidad.

Unidades:

- Soldado: ataque doble.
- Tanque: escudo temporal.
- Unidad rápida: aumento de velocidad.