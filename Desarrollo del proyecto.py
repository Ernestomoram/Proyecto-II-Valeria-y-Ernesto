import tkinter as tk  # Librería para crear la ventana y los botones de la interfaz gráfica
from tkinter import messagebox  # Para mostrar ventanas emergentes de aviso/error/información
import json  # Para guardar y leer los datos de los jugadores en un archivo .json

try:
    import pygame  # Librería que se usa para reproducir música de fondo
except Exception:
    pygame = None  # Si no está instalada, el juego sigue funcionando sin música

try:
    from PIL import Image, ImageTk  # Librería para abrir, redimensionar y mostrar imágenes
except Exception:
    Image = None  # Si no está instalada, el juego usa colores/texto en vez de imágenes
    ImageTk = None

ARCHIVO_JUGADORES = "jugadores.json"  # Nombre del archivo donde se guardan los jugadores registrados
TAMANO = 10  # El tablero es una cuadrícula de 10x10 casillas
BASE_FILA = 4  # Fila donde empieza la base central (un bloque de 2x2)
BASE_COLUMNA = 4  # Columna donde empieza la base central
TAMANO_CELDA = 64  # Tamaño en píxeles de cada casilla del tablero
BASE_CELDAS = {(BASE_FILA, BASE_COLUMNA), (BASE_FILA, BASE_COLUMNA + 1),  # Conjunto con las 4 casillas que ocupa la base
               (BASE_FILA + 1, BASE_COLUMNA), (BASE_FILA + 1, BASE_COLUMNA + 1)}

FACCIONES = ["medieval", "futurista", "naturaleza"]  # Las 3 facciones (temáticas visuales) que se pueden elegir

IMAGENES_SELECCION_FACCION = {  # Diccionario: qué imagen de botón mostrar para elegir cada facción
    "medieval": "boton_medieval.png",
    "futurista": "boton_futurista.png",
    "naturaleza": "boton_naturaleza.png"
}

class Jugador:  # Representa a un jugador guardado (usuario, contraseña y sus victorias)
    def __init__(self, usuario, contrasena, victorias_defensor=0, victorias_atacante=0):
        self.usuario = usuario  # Nombre de usuario
        self.contrasena = contrasena  # Contraseña del usuario
        self.victorias_defensor = victorias_defensor  # Veces que ganó jugando como defensor
        self.victorias_atacante = victorias_atacante  # Veces que ganó jugando como atacante

    def convertir_diccionario(self):  # Convierte el jugador a un diccionario para poder guardarlo en JSON
        return {
            "usuario": self.usuario,
            "contrasena": self.contrasena,
            "victorias_defensor": self.victorias_defensor,
            "victorias_atacante": self.victorias_atacante
        }


class Torre:  # Representa una torre defensiva colocada en el tablero
    def __init__(self, tipo, fila, columna):
        self.tipo = tipo  # Tipo de torre: torre_basica, torre_pesada o torre_magica
        self.fila = fila  # Fila donde está ubicada
        self.columna = columna  # Columna donde está ubicada
        self.turnos = 0  # Contador de turnos, para saber cuándo activar su habilidad especial

        if tipo == "torre_basica":  # Configuración de estadísticas según el tipo de torre
            self.nombre = "Torre básica"
            self.costo = 60  # Precio para construirla
            self.vida = 80  # Puntos de vida
            self.dano = 20  # Daño que hace por ataque
            self.alcance = 2  # Distancia máxima a la que puede atacar
            self.cooldown = 3  # Cada cuántos turnos se activa su habilidad
        elif tipo == "torre_pesada":
            self.nombre = "Torre pesada"
            self.costo = 110
            self.vida = 140
            self.dano = 35
            self.alcance = 2
            self.cooldown = 4
        else:  # Si no es básica ni pesada, entonces es mágica
            self.nombre = "Torre mágica"
            self.costo = 90
            self.vida = 70
            self.dano = 15
            self.alcance = 3
            self.cooldown = 3

    def habilidad(self, juego, unidad):  # Ejecuta la habilidad especial de la torre sobre una unidad enemiga
        if self.tipo == "torre_basica":
            juego.escribir_log("Habilidad torre básica: disparo doble.")  # Mensaje en el registro de eventos
            unidad.recibir_dano(self.dano, juego)  # Le hace daño extra (un segundo disparo)
        elif self.tipo == "torre_pesada":
            juego.escribir_log("Habilidad torre pesada: golpe reforzado.")
            unidad.recibir_dano(20, juego)  # Golpe adicional de 20 de daño
        elif self.tipo == "torre_magica":
            juego.escribir_log("Habilidad torre mágica: congela una unidad.")
            unidad.congelada = 1  # La unidad pierde su próximo turno


class Unidad:  # Representa una unidad de ataque colocada por el jugador atacante
    def __init__(self, tipo, fila, columna):
        self.tipo = tipo  # Tipo de unidad: soldado, tanque o rapida
        self.fila = fila  # Fila actual de la unidad
        self.columna = columna  # Columna actual de la unidad
        self.turnos = 0  # Contador de turnos para activar su habilidad
        self.congelada = 0  # Si es mayor que 0, la unidad no puede actuar (efecto de la torre mágica)
        self.escudo = False  # Si tiene escudo activo, el próximo daño que reciba se reduce

        if tipo == "soldado":  # Configuración de estadísticas según el tipo de unidad
            self.nombre = "Soldado"
            self.costo = 45  # Precio para colocarla
            self.vida = 70
            self.dano = 20
            self.velocidad = 1  # Casillas que avanza por turno
            self.cooldown = 3  # Cada cuántos turnos usa su habilidad
            self.recompensa = 25  # Dinero que gana el defensor si la elimina
        elif tipo == "tanque":
            self.nombre = "Tanque"
            self.costo = 95
            self.vida = 160
            self.dano = 30
            self.velocidad = 1
            self.cooldown = 4
            self.recompensa = 50
        else:  # Si no es soldado ni tanque, entonces es unidad rápida
            self.nombre = "Unidad rápida"
            self.costo = 65
            self.vida = 55
            self.dano = 15
            self.velocidad = 2
            self.cooldown = 3
            self.recompensa = 35

    def recibir_dano(self, cantidad, juego):  # Resta vida a la unidad cuando es atacada
        if self.escudo:  # Si tiene escudo activo, el daño se reduce a la mitad
            cantidad = cantidad // 2
            self.escudo = False  # El escudo se gasta después de usarse una vez
            juego.escribir_log(self.nombre + " usó escudo y redujo daño.")
        self.vida = self.vida - cantidad  # Se aplica el daño final a la vida

    def habilidad(self, juego):  # Activa la habilidad especial de la unidad y devuelve qué efecto produjo
        if self.tipo == "soldado":
            juego.escribir_log("Habilidad soldado: ataque doble listo.")
            return "ataque_doble"  # El soldado atacará dos veces este turno
        elif self.tipo == "tanque":
            self.escudo = True  # Activa el escudo para el próximo golpe que reciba
            juego.escribir_log("Habilidad tanque: escudo temporal.")
            return "escudo"
        elif self.tipo == "rapida":
            juego.escribir_log("Habilidad rápida: aumento de velocidad.")
            return "velocidad"  # Se moverá una casilla extra este turno
        return "nada"  # Por seguridad, si no coincide ningún tipo


class BaseCentral:  # Representa la base que el atacante debe destruir para ganar
    def __init__(self):
        self.fila = BASE_FILA  # Posición fija de la base (fila)
        self.columna = BASE_COLUMNA  # Posición fija de la base (columna)
        self.vida = 300  # Vida total de la base


class Juego:  # Clase principal que controla toda la lógica y la interfaz del juego
    def __init__(self, ventana):
        self.ventana = ventana  # Referencia a la ventana principal de tkinter
        self.ventana.title("Base Defensa - Proyecto Tkinter")  # Título de la ventana
        self.jugadores = self.cargar_jugadores()  # Carga la lista de jugadores guardados en el archivo JSON
        self.jugador_defensor = None  # Jugador que está controlando la defensa en la partida actual
        self.jugador_atacante = None  # Jugador que está controlando el ataque en la partida actual
        self.faccion_defensor = ""  # Facción visual elegida por el defensor
        self.faccion_atacante = ""  # Facción visual elegida por el atacante
        self.victorias_defensor = 0  # Rondas ganadas por el defensor en esta partida
        self.victorias_atacante = 0  # Rondas ganadas por el atacante en esta partida
        self.ronda = 1  # Número de ronda actual
        self.dinero_defensor = 0  # Dinero disponible del defensor en la ronda actual
        self.dinero_atacante = 0  # Dinero disponible del atacante en la ronda actual
        self.bono_atacante = 0  # Dinero extra que el atacante arrastra a la siguiente ronda
        self.seleccion = ""  # Qué elemento (muro, torre, unidad) está seleccionado para colocar
        self.fase = "login"  # Fase actual del juego: login, defensa, ataque o combate
        self.botones = []  # Matriz de botones que forman el tablero visual
        self.torres = []  # Lista de torres colocadas en el tablero
        self.unidades = []  # Lista de unidades de ataque colocadas en el tablero
        self.muros = []  # Lista de muros colocados en el tablero
        self.base = BaseCentral()  # Crea la base central con su vida inicial
        self.imagenes = {}  # Diccionario de imágenes ya convertidas para tkinter
        self._imagenes_pil = {}  # Diccionario de imágenes en formato PIL (para combinarlas con el fondo)
        self._tiles_arena = {}  # Imágenes recortadas del fondo de arena, una por casilla
        self._tiles_pil = {}  # Versión PIL de esos recortes de fondo
        self._cache_comp = {}  # Caché de imágenes ya compuestas (objeto + fondo) para no recalcular
        self._img_botones = []  # Lista que mantiene referencias a imágenes de botones (evita que se borren de memoria)
        self.iniciar_musica()  # Pone a reproducir la música de fondo
        self.mostrar_login()  # Muestra la primera pantalla: inicio de sesión

    def limpiar(self):  # Borra todos los elementos visuales actuales de la ventana
        for widget in self.ventana.winfo_children():  # Recorre cada elemento dentro de la ventana
            widget.destroy()  # Lo elimina para poder dibujar una pantalla nueva

    def cargar_jugadores(self):  # Lee el archivo JSON y construye la lista de objetos Jugador
        try:
            archivo = open(ARCHIVO_JUGADORES, "r", encoding="utf-8")  # Abre el archivo de jugadores para lectura
            datos = json.load(archivo)  # Convierte el contenido JSON a una lista de diccionarios
            archivo.close()  # Cierra el archivo
        except Exception:
            datos = []  # Si el archivo no existe o falla, empieza con una lista vacía
        lista = []
        for d in datos:  # Por cada diccionario leído, crea un objeto Jugador
            jugador = Jugador(d["usuario"], d["contrasena"], d["victorias_defensor"], d["victorias_atacante"])
            lista.append(jugador)
        return lista  # Devuelve la lista de jugadores ya armada

    def guardar_jugadores(self):  # Escribe la lista actual de jugadores en el archivo JSON
        datos = []
        for jugador in self.jugadores:  # Convierte cada jugador a diccionario
            datos.append(jugador.convertir_diccionario())
        archivo = open(ARCHIVO_JUGADORES, "w", encoding="utf-8")  # Abre el archivo para escritura
        json.dump(datos, archivo, indent=4, ensure_ascii=False)  # Guarda los datos con formato legible
        archivo.close()  # Cierra el archivo

    def buscar_jugador(self, usuario):  # Busca un jugador por su nombre de usuario
        for jugador in self.jugadores:
            if jugador.usuario == usuario:
                return jugador  # Lo devuelve si lo encuentra
        return None  # Si no existe, devuelve None

    def iniciar_musica(self):  # Inicia la reproducción de la música de fondo en bucle
        self._musica_reproduciendo = False  # Bandera que indica si la música está sonando
        if pygame is None:  # Si pygame no está disponible, no hace nada
            return
        try:
            pygame.mixer.init()  # Inicializa el sistema de audio
            pygame.mixer.music.load("assets/music/music.mp3")  # Carga el archivo de música
            pygame.mixer.music.play(-1)  # Lo reproduce en bucle infinito
            self._musica_reproduciendo = True
        except Exception:
            pass  # Si el archivo no existe o falla, el juego sigue sin música

    def alternar_musica_simple(self):  # Pausa o reanuda la música sin depender de un botón de texto
        if pygame is not None:
            try:
                if self._musica_reproduciendo:
                    pygame.mixer.music.pause()  # Pausa si estaba sonando
                else:
                    pygame.mixer.music.unpause()  # Reanuda si estaba pausada
            except Exception:
                pass
        self._musica_reproduciendo = not self._musica_reproduciendo  # Invierte la bandera de estado

    def alternar_musica(self, boton):  # Igual que alternar_musica_simple, pero también actualiza el texto del botón
        self.alternar_musica_simple()
        boton.config(text="Detener música" if self._musica_reproduciendo else "Reproducir música")  # Cambia el texto del botón según el estado

    def _crear_boton_musica(self, parent):  # Crea un botón de texto simple para controlar la música (respaldo sin imágenes)
        boton = tk.Button(parent, text="Detener música" if self._musica_reproduciendo else "Reproducir música",
                           font=("Copperplate Gothic Bold", 10))
        boton.config(command=lambda: self.alternar_musica(boton))  # Al hacer clic, alterna la música
        return boton

    def _crear_boton_musica_imagen(self, parent, bg="black", ancho_boton=160):  # Crea el botón de música como una imagen (ícono)
        if Image is not None:
            try:
                img = Image.open("assets/facciones/botones/boton_musica.png")  # Abre la imagen del ícono de música
                alto_boton = round(ancho_boton * img.height / img.width)  # Calcula el alto manteniendo la proporción
                img = img.resize((ancho_boton, alto_boton), Image.LANCZOS)  # Redimensiona la imagen
                foto = ImageTk.PhotoImage(img)  # La convierte a un formato que tkinter puede mostrar
                self._img_botones.append(foto)  # Guarda la referencia para que no se borre de memoria
                return tk.Button(parent, image=foto, command=self.alternar_musica_simple,
                                  bg=bg, activebackground=bg, bd=0, highlightthickness=0)  # Crea el botón con la imagen
            except Exception:
                pass  # Si falla la imagen, usa el botón de texto
        return self._crear_boton_musica(parent)

    def _agregar_boton_musica_canvas(self, canvas, ancho, ancho_boton=150):  # Coloca el botón de música dentro de un canvas (esquina superior derecha)
        if Image is not None:
            try:
                img = Image.open("assets/facciones/botones/boton_musica.png")
                alto_boton = round(ancho_boton * img.height / img.width)
                img = img.resize((ancho_boton, alto_boton), Image.LANCZOS)
                foto = ImageTk.PhotoImage(img)
                self._img_botones.append(foto)
                item = canvas.create_image(ancho - 10, 10, anchor=tk.NE, image=foto)  # Dibuja la imagen en la esquina
                canvas.tag_bind(item, "<Button-1>", lambda e: self.alternar_musica_simple())  # Clic izquierdo: alterna música
                canvas.tag_bind(item, "<Enter>", lambda e: canvas.config(cursor="hand2"))  # Cambia el cursor al pasar el mouse
                canvas.tag_bind(item, "<Leave>", lambda e: canvas.config(cursor="arrow"))  # Vuelve al cursor normal al salir
                return
            except Exception:
                pass  # Si falla, usa el botón de texto como respaldo
        boton = self._crear_boton_musica(canvas)
        canvas.create_window(ancho - 10, 10, anchor=tk.NE, window=boton)

    def _colocar_boton_imagen(self, canvas, cx, y, ruta, comando, texto_alt, ancho_boton=240):  # Dibuja un botón usando una imagen en una posición del canvas
        if Image is not None:
            try:
                img = Image.open(ruta)  # Abre la imagen indicada
                alto_boton = round(ancho_boton * img.height / img.width)  # Calcula el alto proporcional
                img = img.resize((ancho_boton, alto_boton), Image.LANCZOS)  # Redimensiona la imagen
                foto = ImageTk.PhotoImage(img)
                self._img_botones.append(foto)  # Evita que la imagen se borre de memoria
                item = canvas.create_image(cx, y, image=foto)  # Dibuja la imagen como botón
                canvas.tag_bind(item, "<Button-1>", lambda e: comando())  # Al hacer clic, ejecuta la función indicada
                canvas.tag_bind(item, "<Enter>", lambda e: canvas.config(cursor="hand2"))  # Cursor de mano al pasar por encima
                canvas.tag_bind(item, "<Leave>", lambda e: canvas.config(cursor="arrow"))  # Cursor normal al salir
                return
            except Exception:
                pass  # Si la imagen falla, se usa un botón de texto normal
        canvas.create_window(cx, y, window=tk.Button(canvas, text=texto_alt, command=comando, width=26, font=("Copperplate Gothic Bold", 11)))

    def _colocar_selector_facciones(self, canvas, cx, y, variable, ancho_img=110, espacio=20):  # Dibuja los 3 botones para elegir facción y marca cuál está seleccionada
        fotos = []  # Lista de imágenes cargadas para cada facción
        alturas = []  # Lista de alturas calculadas para cada imagen
        if Image is not None:
            for faccion in FACCIONES:  # Carga la imagen de cada facción
                ruta = "assets/facciones/botones/" + IMAGENES_SELECCION_FACCION[faccion]
                try:
                    img = Image.open(ruta)
                    alto_img = round(ancho_img * img.height / img.width)  # Mantiene la proporción de la imagen
                    img = img.resize((ancho_img, alto_img), Image.LANCZOS)
                    foto = ImageTk.PhotoImage(img)
                    self._img_botones.append(foto)
                    fotos.append(foto)
                    alturas.append(alto_img)
                except Exception:
                    fotos.append(None)  # Si una imagen falla, se marca como None
                    alturas.append(0)
        else:
            fotos = [None] * len(FACCIONES)  # Sin PIL, no hay imágenes disponibles
            alturas = [0] * len(FACCIONES)

        if max(alturas) == 0:  # Si ninguna imagen cargó, se usan botones de radio (texto) como respaldo
            x = cx - (len(FACCIONES) * 90) // 2
            for faccion in FACCIONES:
                rb = tk.Radiobutton(canvas, text=faccion, variable=variable, value=faccion,
                                    bg="#1a1a1a", fg="white", selectcolor="#444444",
                                    activebackground="#333333", activeforeground="white", font=("Copperplate Gothic Bold", 13))
                canvas.create_window(x, y, window=rb)
                x += 90  # Espacio horizontal entre cada opción
            return 30

        alto_max = max(alturas)  # Altura más grande entre las 3 imágenes, para alinearlas
        ancho_total = len(FACCIONES) * ancho_img + (len(FACCIONES) - 1) * espacio  # Ancho total que ocuparán las 3 imágenes juntas
        x = cx - ancho_total // 2 + ancho_img // 2  # Posición inicial en X para centrar el grupo
        marcos = {}  # Guarda el rectángulo de "marco" de cada facción para resaltar la seleccionada

        def redibujar():  # Vuelve a pintar los marcos: resalta la facción seleccionada con un borde
            for faccion, item_marco in marcos.items():
                if variable.get() == faccion:
                    canvas.itemconfig(item_marco, outline="black", width=4)  # Borde grueso si está seleccionada
                else:
                    canvas.itemconfig(item_marco, outline="", width=0)  # Sin borde si no está seleccionada

        for i, faccion in enumerate(FACCIONES):  # Dibuja cada imagen de facción con su marco
            foto = fotos[i]
            if foto is not None:
                marco = canvas.create_rectangle(x - ancho_img // 2 - 4, y - alto_max // 2 - 4,
                                                 x + ancho_img // 2 + 4, y + alto_max // 2 + 4,
                                                 outline="", width=0)  # Rectángulo invisible alrededor de la imagen
                item = canvas.create_image(x, y, image=foto)  # Dibuja la imagen de la facción
                marcos[faccion] = marco

                def click(evento, f=faccion):  # Al hacer clic en una facción, se selecciona
                    variable.set(f)
                    redibujar()

                canvas.tag_bind(item, "<Button-1>", click)  # Clic sobre la imagen selecciona la facción
                canvas.tag_bind(marco, "<Button-1>", click)  # Clic sobre el marco también selecciona la facción
                canvas.tag_bind(item, "<Enter>", lambda e: canvas.config(cursor="hand2"))
                canvas.tag_bind(item, "<Leave>", lambda e: canvas.config(cursor="arrow"))
            x += ancho_img + espacio  # Avanza la posición X para la siguiente facción
        redibujar()  # Pinta el marco de la facción seleccionada por defecto
        return alto_max

    def _crear_canvas_fondo(self, ruta):  # Crea un canvas que ocupa toda la ventana y le pone una imagen de fondo
        self.ventana.state("zoomed")  # Maximiza la ventana
        self.ventana.update()  # Actualiza la ventana para obtener su tamaño real
        ancho = self.ventana.winfo_width()  # Ancho actual de la ventana
        alto = self.ventana.winfo_height()  # Alto actual de la ventana
        canvas = tk.Canvas(self.ventana, width=ancho, height=alto, highlightthickness=0)  # Crea el lienzo donde se dibuja todo
        canvas.pack(fill=tk.BOTH, expand=True)  # Hace que el canvas llene toda la ventana
        self._img_fondo_actual = None
        if Image is not None:
            try:
                img = Image.open(ruta).resize((ancho, alto), Image.LANCZOS)  # Abre y ajusta la imagen al tamaño de la ventana
                self._img_fondo_actual = ImageTk.PhotoImage(img)
                canvas.create_image(0, 0, anchor=tk.NW, image=self._img_fondo_actual)  # Dibuja la imagen de fondo desde la esquina superior izquierda
            except Exception:
                pass  # Si falla la imagen, el canvas queda con fondo vacío
        return canvas, ancho, alto

    def _cargar_tiles_arena(self):  # Recorta la imagen del fondo de arena en 100 piezas (una por cada casilla del tablero)
        self._tiles_arena = {}
        self._tiles_pil = {}
        self._cache_comp = {}
        if Image is None:
            return  # Sin PIL no se pueden generar las piezas de fondo
        try:
            tam = TAMANO * TAMANO_CELDA  # Tamaño total de la imagen de arena (10 casillas x 64 px)
            arena = Image.open("assets/facciones/fondos/arena.png").resize((tam, tam), Image.LANCZOS).convert("RGBA")
            for fi in range(TAMANO):  # Recorre cada fila
                for ci in range(TAMANO):  # Recorre cada columna
                    tile = arena.crop((ci * TAMANO_CELDA, fi * TAMANO_CELDA,
                                       (ci + 1) * TAMANO_CELDA, (fi + 1) * TAMANO_CELDA))  # Recorta el pedazo correspondiente a esa casilla
                    self._tiles_pil[(fi, ci)] = tile  # Guarda la versión PIL (para combinar luego con objetos)
                    self._tiles_arena[(fi, ci)] = ImageTk.PhotoImage(tile.convert("RGB"))  # Guarda la versión para mostrar en tkinter
        except Exception:
            pass  # Si la imagen de arena no existe, no hay fondo de casillas

    def _tile_arena(self, fila, columna):  # Devuelve la imagen de fondo de una casilla específica
        return self._tiles_arena.get((fila, columna), self._img_vacia)  # Si no existe, devuelve una imagen vacía

    def _imagen_sobre_arena(self, clave, fila, columna):  # Combina la imagen de un objeto (torre, muro, unidad) con el fondo de su casilla
        key = (clave, fila, columna)
        if key in self._cache_comp:  # Si ya se generó antes, la reutiliza (más rápido)
            return self._cache_comp[key]
        resultado = None
        tile = self._tiles_pil.get((fila, columna))  # Fondo de esa casilla
        img_pil = self._imagenes_pil.get(clave)  # Imagen del objeto a dibujar encima
        if tile is not None and img_pil is not None:
            fondo = tile.copy().convert("RGBA")  # Copia el fondo para no modificar el original
            fondo.paste(img_pil.convert("RGBA"), (0, 0), img_pil.convert("RGBA"))  # Pega el objeto encima del fondo, respetando transparencia
            resultado = ImageTk.PhotoImage(fondo.convert("RGB"))  # Convierte la combinación a formato tkinter
        else:
            resultado = self.imagenes.get(clave)  # Si no hay fondo o imagen, usa la imagen simple sin combinar
        self._cache_comp[key] = resultado  # Guarda el resultado en caché para la próxima vez
        return resultado

    def mostrar_login(self):  # Dibuja la pantalla de inicio de sesión / registro
        self.limpiar()  # Borra lo que había en pantalla
        self.fase = "login"  # Marca la fase actual como login
        canvas, ancho, alto = self._crear_canvas_fondo("assets/facciones/fondos/inicio.png")  # Crea el fondo de esta pantalla
        self._img_botones = []  # Reinicia la lista de imágenes de botones de esta pantalla
        self._agregar_boton_musica_canvas(canvas, ancho)  # Coloca el botón de música arriba a la derecha
        cx = ancho // 2  # Centro horizontal de la pantalla
        ancho_titulo = min(420, ancho - 160)  # Ancho del título, sin pasarse del tamaño de la ventana
        alto_titulo = round(ancho_titulo * 306 / 874)  # Alto del título manteniendo su proporción original
        incremento_titulo = alto_titulo // 2 + 40  # Espacio que ocupará el título antes de continuar con el resto
        total_h = incremento_titulo + 413  # Altura total estimada de todo el contenido de la pantalla
        y = (alto - total_h) // 2  # Posición Y inicial para centrar verticalmente todo el contenido
        self._img_titulo = None
        if Image is not None:
            try:
                img_titulo = Image.open("assets/facciones/botones/label_titulo.png").resize(
                    (ancho_titulo, alto_titulo), Image.LANCZOS)  # Carga y ajusta la imagen del título
                self._img_titulo = ImageTk.PhotoImage(img_titulo)
                canvas.create_image(cx, y, image=self._img_titulo)  # Dibuja el título en el centro
            except Exception:
                canvas.create_text(cx, y, text="Eclipse of Kingdoms", font=("Copperplate Gothic Bold", 22, "bold"), fill="white")  # Si falla, usa texto
        else:
            canvas.create_text(cx, y, text="Eclipse of Kingdoms", font=("Copperplate Gothic Bold", 22, "bold"), fill="white")
        y += incremento_titulo  # Avanza hacia abajo después del título
        canvas.create_text(cx, y, text="Jugador defensor", font=("Copperplate Gothic Bold", 14, "bold"), fill="white")  # Etiqueta de sección
        y += 32
        self.usuario_def = tk.Entry(canvas, width=30, font=("Copperplate Gothic Bold", 12), bg="black", fg="white", insertbackground="white")  # Campo de texto para el usuario defensor
        canvas.create_window(cx, y, window=self.usuario_def)
        y += 34
        self.pass_def = tk.Entry(canvas, show="*", width=30, font=("Copperplate Gothic Bold", 12), bg="black", fg="white", insertbackground="white")  # Campo de contraseña (oculta con *) del defensor
        canvas.create_window(cx, y, window=self.pass_def)
        y += 54
        canvas.create_text(cx, y, text="Jugador atacante", font=("Copperplate Gothic Bold", 14, "bold"), fill="white")  # Etiqueta de sección
        y += 32
        self.usuario_atq = tk.Entry(canvas, width=30, font=("Copperplate Gothic Bold", 12), bg="black", fg="white", insertbackground="white")  # Campo de texto para el usuario atacante
        canvas.create_window(cx, y, window=self.usuario_atq)
        y += 34
        self.pass_atq = tk.Entry(canvas, show="*", width=30, font=("Copperplate Gothic Bold", 12), bg="black", fg="white", insertbackground="white")  # Campo de contraseña del atacante
        canvas.create_window(cx, y, window=self.pass_atq)
        y += 54
        self._colocar_boton_imagen(canvas, cx, y, "assets/facciones/botones/boton_registro.png",
                                    self.registrar_ambos, "Registrar ambos")  # Botón para registrar a ambos jugadores
        y += 64
        self._colocar_boton_imagen(canvas, cx, y, "assets/facciones/botones/boton_iniciar_sesion.png",
                                    self.iniciar_sesion, "Iniciar sesión")  # Botón para iniciar sesión con ambos jugadores
        y += 64
        self._colocar_boton_imagen(canvas, cx, y, "assets/facciones/botones/boton_top_jugadores.png",
                                    self.mostrar_top, "Ver top de jugadores")  # Botón para ver el ranking de jugadores
        y += 45

    def registrar_ambos(self):  # Crea dos cuentas nuevas (defensor y atacante) con los datos ingresados
        u1 = self.usuario_def.get()  # Lee el texto escrito en el campo de usuario defensor
        p1 = self.pass_def.get()  # Lee la contraseña del defensor
        u2 = self.usuario_atq.get()  # Lee el usuario atacante
        p2 = self.pass_atq.get()  # Lee la contraseña del atacante
        if u1 == "" or p1 == "" or u2 == "" or p2 == "":  # Verifica que ningún campo esté vacío
            messagebox.showwarning("Error", "Complete todos los espacios.")
            return
        if u1 == u2:  # Verifica que los dos usuarios no sean el mismo nombre
            messagebox.showwarning("Error", "Los usuarios deben ser diferentes.")
            return
        if self.buscar_jugador(u1) is not None or self.buscar_jugador(u2) is not None:  # Verifica que ningún usuario ya exista
            messagebox.showwarning("Error", "Uno de los usuarios ya existe.")
            return
        self.jugadores.append(Jugador(u1, p1))  # Crea y agrega el jugador defensor
        self.jugadores.append(Jugador(u2, p2))  # Crea y agrega el jugador atacante
        self.guardar_jugadores()  # Guarda los cambios en el archivo JSON
        messagebox.showinfo("Listo", "Jugadores registrados. Ahora pueden iniciar sesión.")

    def iniciar_sesion(self):  # Valida usuario y contraseña de ambos jugadores y comienza la selección de facciones
        u1 = self.usuario_def.get()
        p1 = self.pass_def.get()
        u2 = self.usuario_atq.get()
        p2 = self.pass_atq.get()
        jugador1 = self.buscar_jugador(u1)  # Busca si el usuario defensor existe
        jugador2 = self.buscar_jugador(u2)  # Busca si el usuario atacante existe
        if jugador1 is None or jugador2 is None:  # Si alguno no existe, muestra error
            messagebox.showwarning("Error", "Algún jugador no existe.")
            return
        if jugador1.contrasena != p1 or jugador2.contrasena != p2:  # Verifica que las contraseñas coincidan
            messagebox.showwarning("Error", "Contraseña incorrecta.")
            return
        if jugador1.usuario == jugador2.usuario:  # No se permite que el mismo jugador sea defensor y atacante
            messagebox.showwarning("Error", "No puede ser el mismo jugador.")
            return
        self.jugador_defensor = jugador1  # Guarda quién es el defensor de esta partida
        self.jugador_atacante = jugador2  # Guarda quién es el atacante de esta partida
        self.mostrar_facciones()  # Pasa a la pantalla de selección de facciones

    def mostrar_top(self):  # Muestra el ranking de los 5 mejores defensores y 5 mejores atacantes
        self.limpiar()
        canvas, ancho, alto = self._crear_canvas_fondo("assets/facciones/fondos/inicio.png")
        self._img_botones = []
        self._agregar_boton_musica_canvas(canvas, ancho)
        cx = ancho // 2
        defensores = sorted(self.jugadores[:], key=lambda j: j.victorias_defensor, reverse=True)  # Ordena jugadores de más a menos victorias como defensor
        atacantes = sorted(self.jugadores[:], key=lambda j: j.victorias_atacante, reverse=True)  # Ordena jugadores de más a menos victorias como atacante
        n_def = min(5, len(defensores))  # Solo se muestran hasta 5 defensores
        n_atq = min(5, len(atacantes))  # Solo se muestran hasta 5 atacantes
        total_h = 55 + 45 + n_def * 32 + 55 + 45 + n_atq * 32 + 55  # Calcula la altura total del contenido para centrarlo
        y = max(60, (alto - total_h) // 2)
        canvas.create_text(cx, y, text="Top de jugadores", font=("Copperplate Gothic Bold", 22, "bold"), fill="white")  # Título de la pantalla
        y += 55
        canvas.create_text(cx, y, text="Top 5 defensores", font=("Copperplate Gothic Bold", 15, "bold"), fill="white")  # Subtítulo defensores
        y += 40
        for i in range(n_def):  # Dibuja cada defensor del ranking con su posición y victorias
            texto = str(i + 1) + ".  " + defensores[i].usuario + "  —  " + str(defensores[i].victorias_defensor) + " victorias"
            canvas.create_text(cx, y, text=texto, font=("Copperplate Gothic Bold", 13), fill="white")
            y += 32
        y += 25
        canvas.create_text(cx, y, text="Top 5 atacantes", font=("Copperplate Gothic Bold", 15, "bold"), fill="white")  # Subtítulo atacantes
        y += 40
        for i in range(n_atq):  # Dibuja cada atacante del ranking con su posición y victorias
            texto = str(i + 1) + ".  " + atacantes[i].usuario + "  —  " + str(atacantes[i].victorias_atacante) + " victorias"
            canvas.create_text(cx, y, text=texto, font=("Copperplate Gothic Bold", 13), fill="white")
            y += 32
        y += 35
        self._colocar_boton_imagen(canvas, cx, y, "assets/facciones/botones/boton_volver.png",
                                    self.mostrar_login, "Volver")  # Botón para volver a la pantalla de login

    def mostrar_facciones(self):  # Pantalla donde cada jugador elige su facción (medieval, futurista o naturaleza)
        self.limpiar()
        canvas, ancho, alto = self._crear_canvas_fondo("assets/facciones/fondos/inicio.png")
        self._img_botones = []
        self._agregar_boton_musica_canvas(canvas, ancho)
        cx = ancho // 2
        ancho_label = min(480, ancho - 160)  # Ancho del título de la pantalla
        alto_label = round(ancho_label * 90 / 756)  # Alto proporcional del título
        incremento_label = alto_label // 2 + 45
        total_h = incremento_label + 603  # Altura total estimada del contenido
        y = max(50, (alto - total_h) // 2)
        self._img_label_facciones = None
        if Image is not None:
            try:
                img_label = Image.open("assets/facciones/botones/label_seleccion_facciones.png").resize(
                    (ancho_label, alto_label), Image.LANCZOS)  # Carga la imagen del título "Selección de facciones"
                self._img_label_facciones = ImageTk.PhotoImage(img_label)
                canvas.create_image(cx, y, image=self._img_label_facciones)
            except Exception:
                canvas.create_text(cx, y, text="Selección de facciones", font=("Copperplate Gothic Bold", 22, "bold"), fill="white")
        else:
            canvas.create_text(cx, y, text="Selección de facciones", font=("Copperplate Gothic Bold", 22, "bold"), fill="white")
        y += incremento_label
        canvas.create_text(cx, y, text="El defensor y el atacante no pueden usar la misma facción.",  # Aviso de la regla principal de esta pantalla
                           font=("Copperplate Gothic Bold", 13), fill="white", width=ancho - 100)
        self.var_def = tk.StringVar(value=FACCIONES[0])  # Variable que guarda la facción elegida por el defensor (por defecto, la primera)
        self.var_atq = tk.StringVar(value=FACCIONES[1])  # Variable que guarda la facción elegida por el atacante (por defecto, la segunda)
        y += 50
        canvas.create_text(cx, y, text="Reino defensor", font=("Copperplate Gothic Bold", 15, "bold"), fill="white")
        y += 125
        alto_def = self._colocar_selector_facciones(canvas, cx, y, self.var_def)  # Dibuja los 3 botones de facción para el defensor
        y += alto_def // 2 + 55
        canvas.create_text(cx, y, text="Reino atacante", font=("Copperplate Gothic Bold", 15, "bold"), fill="white")
        y += 125
        alto_atq = self._colocar_selector_facciones(canvas, cx, y, self.var_atq)  # Dibuja los 3 botones de facción para el atacante
        y += alto_atq // 2 + 64
        self._colocar_boton_imagen(canvas, cx, y, "assets/facciones/botones/boton_iniciar_partida.png",
                                    self.iniciar_partida, "Iniciar partida")  # Botón para confirmar y comenzar la partida

    def iniciar_partida(self):  # Valida las facciones elegidas y prepara el inicio de la partida
        if self.var_def.get() == self.var_atq.get():  # No se permite que ambos elijan la misma facción
            messagebox.showwarning("Error", "No pueden usar la misma facción.")
            return
        self.faccion_defensor = self.var_def.get()  # Guarda la facción elegida por el defensor
        self.faccion_atacante = self.var_atq.get()  # Guarda la facción elegida por el atacante
        self.victorias_defensor = 0  # Reinicia el marcador de victorias del defensor
        self.victorias_atacante = 0  # Reinicia el marcador de victorias del atacante
        self.ronda = 1  # Empieza desde la ronda 1
        self.bono_atacante = 0  # Reinicia el dinero extra acumulado del atacante
        self.iniciar_ronda()  # Comienza la primera ronda

    def iniciar_ronda(self):  # Prepara el tablero y el dinero para el inicio de una nueva ronda
        self.torres = []  # Limpia las torres de la ronda anterior
        self.unidades = []  # Limpia las unidades de la ronda anterior
        self.muros = []  # Limpia los muros de la ronda anterior
        self.base = BaseCentral()  # Crea una base nueva con toda su vida
        self.dinero_defensor = 250 + self.ronda * 50  # El defensor recibe más dinero en rondas avanzadas
        self.dinero_atacante = 250 + self.ronda * 50 + self.bono_atacante  # El atacante recibe dinero base más el bono ganado antes
        self.fase = "defensa"  # La ronda inicia en fase de construcción del defensor
        self.seleccion = "muro"  # Por defecto, el elemento seleccionado es el muro
        self.cargar_imagenes()  # Carga las imágenes según las facciones elegidas
        self.mostrar_juego()  # Dibuja la pantalla del tablero de juego
        self.escribir_log("Ronda " + str(self.ronda) + ": fase de construcción del defensor.")  # Mensaje informativo en el registro

    def cargar_imagenes(self):  # Carga todas las imágenes necesarias (base, muro, torres, unidades) para ambas facciones
        self.imagenes = {}
        self._imagenes_pil = {}
        self._cache_comp = {}
        objetos = ["base", "muro", "torre_basica", "torre_pesada", "torre_magica", "soldado", "tanque", "rapida"]  # Lista de todos los elementos visuales que existen
        for faccion in FACCIONES:  # Por cada facción del juego...
            for objeto in objetos:  # ...y por cada tipo de objeto...
                ruta = "assets/facciones/" + faccion + "/" + objeto + ".png"  # Construye la ruta del archivo de imagen
                try:
                    if Image is not None:
                        if objeto == "base":  # La base es una imagen grande dividida en 4 cuadrantes (2x2 casillas)
                            img = Image.open(ruta).resize((TAMANO_CELDA * 2, TAMANO_CELDA * 2), Image.LANCZOS).convert("RGBA")
                            t = TAMANO_CELDA
                            for sufijo, box in [("_base_00", (0, 0, t, t)), ("_base_01", (t, 0, t*2, t)),
                                                ("_base_10", (0, t, t, t*2)), ("_base_11", (t, t, t*2, t*2))]:  # Recorta cada uno de los 4 cuadrantes
                                quad = img.crop(box)
                                self._imagenes_pil[faccion + sufijo] = quad
                                self.imagenes[faccion + sufijo] = ImageTk.PhotoImage(quad.convert("RGB"))
                        else:  # Para los demás objetos, la imagen ocupa solo una casilla
                            img = Image.open(ruta).resize((TAMANO_CELDA, TAMANO_CELDA), Image.LANCZOS).convert("RGBA")
                            self._imagenes_pil[faccion + "_" + objeto] = img
                            self.imagenes[faccion + "_" + objeto] = ImageTk.PhotoImage(img.convert("RGB"))
                    else:
                        self.imagenes[faccion + "_" + objeto] = tk.PhotoImage(file=ruta)  # Sin PIL, carga la imagen de forma básica
                except Exception:
                    self.imagenes[faccion + "_" + objeto] = None  # Si la imagen no existe, se usará color/texto en su lugar

    def mostrar_juego(self):  # Dibuja la pantalla principal del tablero, con casillas, controles y registro de eventos
        self.limpiar()
        self.ventana.state("zoomed")  # Maximiza la ventana
        self.ventana.update()
        ancho = self.ventana.winfo_width()
        alto = self.ventana.winfo_height()
        self._img_fondo_juego = None
        if Image is not None:
            try:
                img_fondo = Image.open("assets/facciones/fondos/fondo_arena.png").resize((ancho, alto), Image.LANCZOS)  # Imagen de fondo de toda la pantalla de juego
                self._img_fondo_juego = ImageTk.PhotoImage(img_fondo)
                tk.Label(self.ventana, image=self._img_fondo_juego, bd=0).place(x=0, y=0, relwidth=1, relheight=1)  # Coloca el fondo ocupando toda la ventana
            except Exception:
                pass
        self._img_vacia = tk.PhotoImage(width=TAMANO_CELDA, height=TAMANO_CELDA)  # Imagen transparente de respaldo para casillas sin imagen
        self._cargar_tiles_arena()  # Genera las 100 piezas de fondo de arena, una por casilla
        self._img_botones = []
        marco_superior = tk.Frame(self.ventana, bg="black")  # Barra superior negra con el botón de música y la info
        marco_superior.pack(fill=tk.X)
        self._crear_boton_musica_imagen(marco_superior, bg="black", ancho_boton=100).pack(side=tk.RIGHT, padx=10, pady=3)  # Botón de música a la derecha
        self.label_info = tk.Label(marco_superior, text="", font=("Copperplate Gothic Bold", 8, "bold"), bg="black", fg="white")  # Etiqueta que muestra ronda, dinero, vida, etc.
        self.label_info.pack(side=tk.LEFT, padx=10, pady=5)
        marco = tk.Frame(self.ventana)  # Contenedor donde se dibuja la cuadrícula del tablero
        marco.pack()
        self.botones = []  # Aquí se guardarán los 100 botones (casillas) del tablero
        for fila in range(TAMANO):  # Crea cada fila del tablero
            fila_botones = []
            for columna in range(TAMANO):  # Crea cada casilla de la fila
                boton = tk.Button(marco, image=self._tile_arena(fila, columna),
                                  width=TAMANO_CELDA, height=TAMANO_CELDA,
                                  compound=tk.CENTER,
                                  relief=tk.FLAT, bd=0,
                                  highlightthickness=1, highlightbackground="#cccccc",
                                  command=lambda f=fila, c=columna: self.click_casilla(f, c))  # Al hacer clic, se llama a click_casilla con su posición
                boton.grid(row=fila, column=columna, padx=0, pady=0)  # Ubica el botón en la cuadrícula
                fila_botones.append(boton)
            self.botones.append(fila_botones)
        marco_controles = tk.Frame(self.ventana, bg="black")  # Contenedor donde van los botones de acciones (comprar, terminar fase, etc.)
        marco_controles.pack(pady=8)
        self.marco_controles = marco_controles
        self.log = tk.Text(self.ventana, width=80, height=8, bg="black", fg="white", insertbackground="white")  # Cuadro de texto donde se muestra el historial de eventos
        self.log.pack(pady=5)
        self.actualizar_controles()  # Dibuja los botones de control según la fase actual
        self.actualizar_tablero()  # Dibuja el contenido actual del tablero (base, muros, torres, unidades)

    def _crear_boton_control(self, texto, comando):  # Crea un botón estándar para la barra de controles inferior
        return tk.Button(self.marco_controles, text=texto, command=comando,
                          bg="black", fg="white", activebackground="#333333", activeforeground="white")

    def actualizar_controles(self):  # Vuelve a dibujar los botones de control según la fase actual del juego
        for widget in self.marco_controles.winfo_children():  # Borra los botones de control anteriores
            widget.destroy()
        if self.fase == "defensa":  # En fase de defensa: comprar muro o torres, y terminar la fase
            self._crear_boton_control("Muro $25", lambda: self.cambiar_seleccion("muro")).grid(row=0, column=0)
            self._crear_boton_control("Torre básica $60", lambda: self.cambiar_seleccion("torre_basica")).grid(row=0, column=1)
            self._crear_boton_control("Torre pesada $110", lambda: self.cambiar_seleccion("torre_pesada")).grid(row=0, column=2)
            self._crear_boton_control("Torre mágica $90", lambda: self.cambiar_seleccion("torre_magica")).grid(row=0, column=3)
            self._crear_boton_control("Terminar defensa", self.terminar_defensa).grid(row=0, column=4)
        elif self.fase == "ataque":  # En fase de ataque: comprar unidades e iniciar el combate
            self._crear_boton_control("Soldado $45", lambda: self.cambiar_seleccion("soldado")).grid(row=0, column=0)
            self._crear_boton_control("Tanque $95", lambda: self.cambiar_seleccion("tanque")).grid(row=0, column=1)
            self._crear_boton_control("Rápida $65", lambda: self.cambiar_seleccion("rapida")).grid(row=0, column=2)
            self._crear_boton_control("Iniciar combate", self.iniciar_combate).grid(row=0, column=3)
        elif self.fase == "combate":  # En fase de combate: solo se puede avanzar turno por turno
            self._crear_boton_control("Ejecutar turno", self.turno_combate).grid(row=0, column=0)
        self.actualizar_info()  # Refresca el texto con la información general de la partida

    def actualizar_info(self):  # Construye y muestra el texto con el estado actual de la partida
        texto = "Ronda: " + str(self.ronda)
        texto += " | Marcador defensor: " + str(self.victorias_defensor)
        texto += " | Marcador atacante: " + str(self.victorias_atacante)
        texto += " | Dinero defensor: $" + str(self.dinero_defensor)
        texto += " | Dinero atacante: $" + str(self.dinero_atacante)
        texto += " | Base: " + str(self.base.vida)
        texto += " | Fase: " + self.fase
        texto += " | Selección: " + self.seleccion
        self.label_info.config(text=texto)  # Actualiza la etiqueta visual con todo el texto armado

    def escribir_log(self, texto):  # Agrega una línea de texto al historial de eventos en pantalla
        try:
            self.log.insert(tk.END, texto + "\n")  # Inserta el texto al final del cuadro de texto
            self.log.see(tk.END)  # Hace scroll automático para mostrar la última línea
        except Exception:
            pass  # Si el cuadro de log aún no existe, ignora el error

    def cambiar_seleccion(self, seleccion):  # Cambia qué objeto (muro, torre o unidad) se va a colocar al hacer clic en el tablero
        self.seleccion = seleccion
        self.actualizar_info()

    def click_casilla(self, fila, columna):  # Se ejecuta al hacer clic en una casilla del tablero
        if self.fase == "defensa":
            self.colocar_defensa(fila, columna)  # En fase de defensa, intenta colocar muro/torre
        elif self.fase == "ataque":
            self.colocar_unidad(fila, columna)  # En fase de ataque, intenta colocar una unidad

    def casilla_ocupada(self, fila, columna):  # Revisa si una casilla ya tiene algo (base, muro, torre o unidad)
        if (fila, columna) in BASE_CELDAS:
            return True
        for muro in self.muros:
            if muro[0] == fila and muro[1] == columna:
                return True
        for torre in self.torres:
            if torre.fila == fila and torre.columna == columna:
                return True
        for unidad in self.unidades:
            if unidad.fila == fila and unidad.columna == columna:
                return True
        return False  # Si no coincide con nada, la casilla está libre

    def colocar_defensa(self, fila, columna):  # Coloca un muro o una torre en la casilla indicada, si hay dinero y está libre
        if self.casilla_ocupada(fila, columna):  # No se puede construir sobre algo que ya existe
            return
        if self.seleccion == "muro":
            costo = 25
            if self.dinero_defensor >= costo:  # Solo si el defensor tiene suficiente dinero
                self.muros.append([fila, columna, 90])  # Cada muro se guarda como [fila, columna, vida]
                self.dinero_defensor = self.dinero_defensor - costo
        else:
            torre = Torre(self.seleccion, fila, columna)  # Crea la torre del tipo seleccionado
            if self.dinero_defensor >= torre.costo:  # Solo si hay suficiente dinero para esa torre
                self.torres.append(torre)
                self.dinero_defensor = self.dinero_defensor - torre.costo
        self.actualizar_tablero()  # Redibuja el tablero con el nuevo elemento
        self.actualizar_info()  # Actualiza el dinero mostrado

    def terminar_defensa(self):  # Pasa de la fase de defensa a la fase de ataque
        self.fase = "ataque"
        self.seleccion = "soldado"  # Selección por defecto al entrar a la fase de ataque
        self.actualizar_controles()  # Cambia los botones de control a los de la fase de ataque
        self.escribir_log("Fase de ataque: coloque unidades en los bordes del mapa.")

    def colocar_unidad(self, fila, columna):  # Coloca una unidad de ataque en el borde del tablero, si hay dinero y está libre
        if not (fila == 0 or fila == TAMANO - 1 or columna == 0 or columna == TAMANO - 1):  # Solo se permite colocar unidades en el borde del mapa
            messagebox.showwarning("Regla", "Las unidades se colocan en los bordes.")
            return
        if self.casilla_ocupada(fila, columna):  # No se puede colocar sobre algo que ya existe
            return
        unidad = Unidad(self.seleccion, fila, columna)  # Crea la unidad del tipo seleccionado
        if self.dinero_atacante >= unidad.costo:  # Solo si el atacante tiene suficiente dinero
            self.unidades.append(unidad)
            self.dinero_atacante = self.dinero_atacante - unidad.costo
        self.actualizar_tablero()  # Redibuja el tablero con la nueva unidad
        self.actualizar_info()

    def iniciar_combate(self):  # Pasa de la fase de ataque a la fase de combate (turnos automáticos)
        if len(self.unidades) == 0:  # El atacante debe tener al menos una unidad para poder atacar
            messagebox.showwarning("Error", "El atacante debe colocar al menos una unidad.")
            return
        self.fase = "combate"
        self.ocultar_cuadricula()  # Quita los bordes de las casillas (ya no se puede seguir construyendo/colocando)
        self.actualizar_controles()  # Cambia los botones de control a los de combate
        self.escribir_log("Combate iniciado. Presione 'Ejecutar turno'.")

    def ocultar_cuadricula(self):  # Quita el borde visual de todas las casillas del tablero
        for fila in self.botones:
            for boton in fila:
                boton.config(highlightthickness=0)

    def actualizar_tablero(self):  # Redibuja todo el tablero: fondo, base, muros, torres y unidades
        for fila in range(TAMANO):  # Primero limpia todas las casillas dejando solo el fondo
            for columna in range(TAMANO):
                boton = self.botones[fila][columna]
                boton.config(text="", image=self._tile_arena(fila, columna), compound=tk.CENTER)
        self.pintar_base(self.faccion_defensor)  # Dibuja la base con la facción del defensor
        for muro in self.muros:  # Dibuja cada muro existente
            self.pintar_casilla(muro[0], muro[1], "muro", self.faccion_defensor)
        for torre in self.torres:  # Dibuja cada torre existente
            self.pintar_casilla(torre.fila, torre.columna, torre.tipo, self.faccion_defensor)
        for unidad in self.unidades:  # Dibuja cada unidad de ataque existente
            self.pintar_casilla(unidad.fila, unidad.columna, unidad.tipo, self.faccion_atacante)
        self.actualizar_info()  # Refresca el texto de información general

    def pintar_base(self, faccion):  # Dibuja los 4 cuadrantes de la base usando las imágenes de la facción correspondiente
        cuadrantes = [("_base_00", BASE_FILA, BASE_COLUMNA),
                      ("_base_01", BASE_FILA, BASE_COLUMNA + 1),
                      ("_base_10", BASE_FILA + 1, BASE_COLUMNA),
                      ("_base_11", BASE_FILA + 1, BASE_COLUMNA + 1)]
        for sufijo, fila, columna in cuadrantes:  # Por cada uno de los 4 cuadrantes de la base
            boton = self.botones[fila][columna]
            imagen = self._imagen_sobre_arena(faccion + sufijo, fila, columna)  # Combina el cuadrante de base con el fondo de esa casilla
            if imagen is not None:
                boton.config(image=imagen, text="", compound=tk.CENTER)
            else:
                boton.config(image=self._tile_arena(fila, columna), text="B", compound=tk.CENTER)  # Si no hay imagen, usa color y la letra "B"

    def pintar_casilla(self, fila, columna, objeto, faccion):  # Dibuja un objeto (muro, torre o unidad) en una casilla específica
        boton = self.botones[fila][columna]
        imagen = self._imagen_sobre_arena(faccion + "_" + objeto, fila, columna)  # Combina la imagen del objeto con el fondo de esa casilla
        if imagen is not None:
            boton.config(image=imagen, text="", compound=tk.CENTER)
        else:  # Si no hay imagen disponible, se usa un color de fondo y una letra identificadora
            pass

    def distancia(self, f1, c1, f2, c2):  # Calcula la distancia entre dos casillas (suma de filas y columnas de diferencia)
        return abs(f1 - f2) + abs(c1 - c2)

    def unidad_mas_cercana(self, torre):  # Busca la unidad enemiga más cercana que esté dentro del alcance de la torre
        mejor = None
        mejor_distancia = 999
        for unidad in self.unidades:
            d = self.distancia(torre.fila, torre.columna, unidad.fila, unidad.columna)
            if d <= torre.alcance and d < mejor_distancia:  # Debe estar dentro del alcance y ser más cercana que la anterior encontrada
                mejor = unidad
                mejor_distancia = d
        return mejor  # Devuelve la unidad más cercana, o None si ninguna está en rango

    def torre_en_posicion(self, fila, columna):  # Busca si hay una torre exactamente en esa casilla
        for torre in self.torres:
            if torre.fila == fila and torre.columna == columna:
                return torre
        return None

    def muro_en_posicion(self, fila, columna):  # Busca si hay un muro exactamente en esa casilla
        for muro in self.muros:
            if muro[0] == fila and muro[1] == columna:
                return muro
        return None

    def turno_combate(self):  # Ejecuta un turno completo de combate: torres atacan, luego unidades se mueven/atacan
        self.escribir_log("---- Nuevo turno ----")
        self.ataque_torres()  # Las torres disparan primero
        self.eliminar_unidades_muertas()  # Se quitan del tablero las unidades que murieron
        if self.revisar_fin_ronda():  # Si la ronda terminó (base destruida o no quedan unidades), se detiene aquí
            return
        self.turno_unidades()  # Las unidades se mueven o atacan
        self.eliminar_torres_y_muros_muertos()  # Se quitan las torres/muros destruidos
        self.actualizar_tablero()  # Redibuja el tablero con los cambios del turno
        self.revisar_fin_ronda()  # Vuelve a comprobar si la ronda terminó después del turno

    def ataque_torres(self):  # Cada torre ataca a la unidad enemiga más cercana dentro de su alcance
        for torre in self.torres:
            torre.turnos = torre.turnos + 1  # Avanza el contador de turnos de la torre
            unidad = self.unidad_mas_cercana(torre)  # Busca un objetivo válido
            if unidad is not None:
                unidad.recibir_dano(torre.dano, self)  # La torre hace daño normal
                self.escribir_log(torre.nombre + " atacó a " + unidad.nombre + ".")
                if torre.turnos >= torre.cooldown:  # Si ya pasó el tiempo de espera, activa su habilidad especial
                    torre.habilidad(self, unidad)
                    torre.turnos = 0  # Reinicia el contador después de usar la habilidad

    def eliminar_unidades_muertas(self):  # Quita del tablero las unidades sin vida y le da dinero al defensor por cada una
        vivas = []
        for unidad in self.unidades:
            if unidad.vida <= 0:
                self.dinero_defensor = self.dinero_defensor + unidad.recompensa  # El defensor gana dinero por eliminar la unidad
                self.escribir_log("El defensor ganó $" + str(unidad.recompensa) + " por eliminar " + unidad.nombre + ".")
            else:
                vivas.append(unidad)  # Las unidades con vida siguen en juego
        self.unidades = vivas

    def turno_unidades(self):  # Hace que cada unidad viva actúe: se congela, usa habilidad, se mueve o ataca
        for unidad in self.unidades:
            if unidad.congelada > 0:  # Si está congelada, pierde el turno
                unidad.congelada = unidad.congelada - 1
                self.escribir_log(unidad.nombre + " está congelada y pierde el turno.")
            else:
                unidad.turnos = unidad.turnos + 1  # Avanza el contador de turnos de la unidad
                efecto = "nada"
                if unidad.turnos >= unidad.cooldown:  # Si ya puede usar su habilidad, la activa
                    efecto = unidad.habilidad(self)
                    unidad.turnos = 0
                ataques = 1
                velocidad_turno = unidad.velocidad
                if efecto == "ataque_doble":  # El soldado puede atacar dos veces este turno
                    ataques = 2
                if efecto == "velocidad":  # La unidad rápida se mueve una casilla extra este turno
                    velocidad_turno = velocidad_turno + 1
                self.mover_o_atacar(unidad, velocidad_turno, ataques)  # Ejecuta el movimiento o ataque de la unidad

    def mover_o_atacar(self, unidad, velocidad_turno, ataques):  # Decide si la unidad ataca algo cercano o avanza hacia la base
        i = 0
        while i < velocidad_turno:  # Repite el proceso según cuántas casillas puede avanzar este turno
            objetivo = self.buscar_objetivo_cerca(unidad)  # Revisa si hay algo atacable junto a la unidad
            if objetivo != "nada":
                j = 0
                while j < ataques:  # Ataca tantas veces como le corresponda (normalmente 1, o 2 con ataque doble)
                    self.atacar_objetivo(unidad, objetivo)
                    j = j + 1
                return  # Si atacó, no sigue moviéndose este turno
            self.mover_hacia_base(unidad)  # Si no hay nada para atacar, avanza una casilla hacia la base
            i = i + 1

    def buscar_objetivo_cerca(self, unidad):  # Revisa las 4 casillas vecinas en busca de la base, una torre o un muro
        posiciones = [[unidad.fila - 1, unidad.columna], [unidad.fila + 1, unidad.columna], [unidad.fila, unidad.columna - 1], [unidad.fila, unidad.columna + 1]]
        for p in posiciones:
            f = p[0]
            c = p[1]
            if (f, c) in BASE_CELDAS:  # Si una casilla vecina es parte de la base
                return "base"
            torre = self.torre_en_posicion(f, c)  # Si hay una torre vecina
            if torre is not None:
                return torre
            muro = self.muro_en_posicion(f, c)  # Si hay un muro vecino
            if muro is not None:
                return muro
        return "nada"  # Si no hay nada cerca, no hay objetivo

    def atacar_objetivo(self, unidad, objetivo):  # Aplica el daño de la unidad sobre el objetivo encontrado (base, torre o muro)
        if objetivo == "base":
            self.base.vida = self.base.vida - unidad.dano  # Resta vida a la base
            self.dinero_atacante = self.dinero_atacante + unidad.dano  # El atacante gana dinero igual al daño hecho
            self.bono_atacante = self.bono_atacante + unidad.dano  # Ese dinero también se guarda como bono para la siguiente ronda
            self.escribir_log(unidad.nombre + " dañó la base. +$" + str(unidad.dano) + " para atacante.")
        elif type(objetivo) == Torre:
            objetivo.vida = objetivo.vida - unidad.dano  # Resta vida a la torre atacada
            ganancia = unidad.dano // 2  # Atacar una torre da la mitad de dinero que atacar la base
            self.dinero_atacante = self.dinero_atacante + ganancia
            self.bono_atacante = self.bono_atacante + ganancia
            self.escribir_log(unidad.nombre + " dañó una torre. +$" + str(ganancia) + " para atacante.")
        else:  # Si no es la base ni una torre, entonces es un muro (lista [fila, columna, vida])
            objetivo[2] = objetivo[2] - unidad.dano  # Resta vida (posición 2 de la lista) al muro
            self.escribir_log(unidad.nombre + " atacó un muro.")

    def mover_hacia_base(self, unidad):  # Mueve la unidad una casilla más cerca de la base, si la casilla destino está libre
        objetivo_fila, objetivo_columna = min(
            BASE_CELDAS,
            key=lambda c: abs(c[0] - unidad.fila) + abs(c[1] - unidad.columna)
        )  # Encuentra la casilla de la base más cercana a la unidad
        nueva_fila = unidad.fila
        nueva_columna = unidad.columna
        if unidad.fila < objetivo_fila:  # Prioriza moverse en el eje de filas primero
            nueva_fila = unidad.fila + 1
        elif unidad.fila > objetivo_fila:
            nueva_fila = unidad.fila - 1
        elif unidad.columna < objetivo_columna:  # Si ya está alineada en filas, se mueve en columnas
            nueva_columna = unidad.columna + 1
        elif unidad.columna > objetivo_columna:
            nueva_columna = unidad.columna - 1
        if not self.casilla_ocupada(nueva_fila, nueva_columna):  # Solo se mueve si la casilla destino está libre
            unidad.fila = nueva_fila
            unidad.columna = nueva_columna

    def eliminar_torres_y_muros_muertos(self):  # Quita las torres y muros sin vida, dando dinero al atacante por las torres destruidas
        nuevas_torres = []
        for torre in self.torres:
            if torre.vida <= 0:
                self.dinero_atacante = self.dinero_atacante + 30  # El atacante gana dinero fijo por destruir una torre
                self.bono_atacante = self.bono_atacante + 30
                self.escribir_log("El atacante destruyó una torre y ganó $30.")
            else:
                nuevas_torres.append(torre)  # Las torres con vida siguen en juego
        self.torres = nuevas_torres
        nuevos_muros = []
        for muro in self.muros:
            if muro[2] > 0:  # Si el muro todavía tiene vida, sigue en juego
                nuevos_muros.append(muro)
            else:
                self.escribir_log("Un muro fue destruido.")
        self.muros = nuevos_muros

    def revisar_fin_ronda(self):  # Comprueba si la ronda ya terminó (base destruida o atacante sin unidades)
        if self.base.vida <= 0:  # Si la base se quedó sin vida, gana el atacante
            self.victorias_atacante = self.victorias_atacante + 1
            self.escribir_log("El atacante ganó la ronda.")
            self.fin_ronda()
            return True
        if len(self.unidades) == 0 and self.fase == "combate":  # Si ya no quedan unidades de ataque en combate, gana el defensor
            self.victorias_defensor = self.victorias_defensor + 1
            self.escribir_log("El defensor ganó la ronda.")
            self.fin_ronda()
            return True
        return False  # La ronda continúa si ninguna condición se cumplió

    def fin_ronda(self):  # Procesa el final de una ronda: revisa si alguien ganó la partida o si se pasa a la siguiente ronda
        self.actualizar_tablero()
        if self.victorias_defensor >= 3:  # Gana la partida el defensor si llega a 3 victorias
            self.jugador_defensor.victorias_defensor = self.jugador_defensor.victorias_defensor + 1  # Suma una victoria histórica a su perfil
            self.guardar_jugadores()  # Guarda el progreso en el archivo JSON
            messagebox.showinfo("Fin de partida", "Ganó la partida el defensor: " + self.jugador_defensor.usuario)
            self.mostrar_login()  # Vuelve a la pantalla de inicio de sesión
        elif self.victorias_atacante >= 3:  # Gana la partida el atacante si llega a 3 victorias
            self.jugador_atacante.victorias_atacante = self.jugador_atacante.victorias_atacante + 1
            self.guardar_jugadores()
            messagebox.showinfo("Fin de partida", "Ganó la partida el atacante: " + self.jugador_atacante.usuario)
            self.mostrar_login()
        else:  # Si nadie llegó a 3 victorias todavía, se continúa con la siguiente ronda
            messagebox.showinfo("Ronda terminada", "Marcador: Defensor " + str(self.victorias_defensor) + " - Atacante " + str(self.victorias_atacante))
            self.ronda = self.ronda + 1
            self.iniciar_ronda()


ventana = tk.Tk()  # Crea la ventana principal de la aplicación
juego = Juego(ventana)  # Crea el objeto Juego, que arma toda la interfaz y la lógica
ventana.mainloop()  # Mantiene la ventana abierta esperando las acciones del usuario
