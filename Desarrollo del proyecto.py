import tkinter as tk
from tkinter import messagebox
import json

try:
    import pygame
except Exception:
    pygame = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

ARCHIVO_JUGADORES = "jugadores.json"
TAMANO = 10
BASE_FILA = 4
BASE_COLUMNA = 4
TAMANO_CELDA = 64
BASE_CELDAS = {(BASE_FILA, BASE_COLUMNA), (BASE_FILA, BASE_COLUMNA + 1),
               (BASE_FILA + 1, BASE_COLUMNA), (BASE_FILA + 1, BASE_COLUMNA + 1)}

FACCIONES = ["medieval", "futurista", "naturaleza"]

class Jugador:
    def __init__(self, usuario, contrasena, victorias_defensor=0, victorias_atacante=0):
        self.usuario = usuario
        self.contrasena = contrasena
        self.victorias_defensor = victorias_defensor
        self.victorias_atacante = victorias_atacante

    def convertir_diccionario(self):
        return {
            "usuario": self.usuario,
            "contrasena": self.contrasena,
            "victorias_defensor": self.victorias_defensor,
            "victorias_atacante": self.victorias_atacante
        }


class Torre:
    def __init__(self, tipo, fila, columna):
        self.tipo = tipo
        self.fila = fila
        self.columna = columna
        self.turnos = 0

        if tipo == "torre_basica":
            self.nombre = "Torre básica"
            self.costo = 60
            self.vida = 80
            self.dano = 20
            self.alcance = 2
            self.cooldown = 3
        elif tipo == "torre_pesada":
            self.nombre = "Torre pesada"
            self.costo = 110
            self.vida = 140
            self.dano = 35
            self.alcance = 2
            self.cooldown = 4
        else:
            self.nombre = "Torre mágica"
            self.costo = 90
            self.vida = 70
            self.dano = 15
            self.alcance = 3
            self.cooldown = 3

    def habilidad(self, juego, unidad):
        if self.tipo == "torre_basica":
            juego.escribir_log("Habilidad torre básica: disparo doble.")
            unidad.recibir_dano(self.dano, juego)
        elif self.tipo == "torre_pesada":
            juego.escribir_log("Habilidad torre pesada: golpe reforzado.")
            unidad.recibir_dano(20, juego)
        elif self.tipo == "torre_magica":
            juego.escribir_log("Habilidad torre mágica: congela una unidad.")
            unidad.congelada = 1


class Unidad:
    def __init__(self, tipo, fila, columna):
        self.tipo = tipo
        self.fila = fila
        self.columna = columna
        self.turnos = 0
        self.congelada = 0
        self.escudo = False

        if tipo == "soldado":
            self.nombre = "Soldado"
            self.costo = 45
            self.vida = 70
            self.dano = 20
            self.velocidad = 1
            self.cooldown = 3
            self.recompensa = 25
        elif tipo == "tanque":
            self.nombre = "Tanque"
            self.costo = 95
            self.vida = 160
            self.dano = 30
            self.velocidad = 1
            self.cooldown = 4
            self.recompensa = 50
        else:
            self.nombre = "Unidad rápida"
            self.costo = 65
            self.vida = 55
            self.dano = 15
            self.velocidad = 2
            self.cooldown = 3
            self.recompensa = 35

    def recibir_dano(self, cantidad, juego):
        if self.escudo:
            cantidad = cantidad // 2
            self.escudo = False
            juego.escribir_log(self.nombre + " usó escudo y redujo daño.")
        self.vida = self.vida - cantidad

    def habilidad(self, juego):
        if self.tipo == "soldado":
            juego.escribir_log("Habilidad soldado: ataque doble listo.")
            return "ataque_doble"
        elif self.tipo == "tanque":
            self.escudo = True
            juego.escribir_log("Habilidad tanque: escudo temporal.")
            return "escudo"
        elif self.tipo == "rapida":
            juego.escribir_log("Habilidad rápida: aumento de velocidad.")
            return "velocidad"
        return "nada"


class BaseCentral:
    def __init__(self):
        self.fila = BASE_FILA
        self.columna = BASE_COLUMNA
        self.vida = 300


class Juego:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Base Defensa - Proyecto Tkinter")
        self.jugadores = self.cargar_jugadores()
        self.jugador_defensor = None
        self.jugador_atacante = None
        self.faccion_defensor = ""
        self.faccion_atacante = ""
        self.victorias_defensor = 0
        self.victorias_atacante = 0
        self.ronda = 1
        self.dinero_defensor = 0
        self.dinero_atacante = 0
        self.bono_atacante = 0
        self.seleccion = ""
        self.fase = "login"
        self.botones = []
        self.torres = []
        self.unidades = []
        self.muros = []
        self.base = BaseCentral()
        self.imagenes = {}
        self._imagenes_pil = {}
        self._tiles_arena = {}
        self._tiles_pil = {}
        self._cache_comp = {}
        self.iniciar_musica()
        self.mostrar_login()

    def limpiar(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()

    def cargar_jugadores(self):
        try:
            archivo = open(ARCHIVO_JUGADORES, "r", encoding="utf-8")
            datos = json.load(archivo)
            archivo.close()
        except Exception:
            datos = []
        lista = []
        for d in datos:
            jugador = Jugador(d["usuario"], d["contrasena"], d["victorias_defensor"], d["victorias_atacante"])
            lista.append(jugador)
        return lista

    def guardar_jugadores(self):
        datos = []
        for jugador in self.jugadores:
            datos.append(jugador.convertir_diccionario())
        archivo = open(ARCHIVO_JUGADORES, "w", encoding="utf-8")
        json.dump(datos, archivo, indent=4, ensure_ascii=False)
        archivo.close()

    def buscar_jugador(self, usuario):
        for jugador in self.jugadores:
            if jugador.usuario == usuario:
                return jugador
        return None

    def iniciar_musica(self):
        if pygame is None:
            return
        try:
            pygame.mixer.init()
            pygame.mixer.music.load("assets/music/musica.mp3")
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def _crear_canvas_fondo(self, ruta):
        self.ventana.state("zoomed")
        self.ventana.update()
        ancho = self.ventana.winfo_width()
        alto = self.ventana.winfo_height()
        canvas = tk.Canvas(self.ventana, width=ancho, height=alto, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self._img_fondo_actual = None
        if Image is not None:
            try:
                img = Image.open(ruta).resize((ancho, alto), Image.LANCZOS)
                self._img_fondo_actual = ImageTk.PhotoImage(img)
                canvas.create_image(0, 0, anchor=tk.NW, image=self._img_fondo_actual)
            except Exception:
                pass
        return canvas, ancho, alto

    def _cargar_tiles_arena(self):
        self._tiles_arena = {}
        self._tiles_pil = {}
        self._cache_comp = {}
        if Image is None:
            return
        try:
            tam = TAMANO * TAMANO_CELDA
            arena = Image.open("assets/facciones/fondos/arena.png").resize((tam, tam), Image.LANCZOS).convert("RGBA")
            for fi in range(TAMANO):
                for ci in range(TAMANO):
                    tile = arena.crop((ci * TAMANO_CELDA, fi * TAMANO_CELDA,
                                       (ci + 1) * TAMANO_CELDA, (fi + 1) * TAMANO_CELDA))
                    self._tiles_pil[(fi, ci)] = tile
                    self._tiles_arena[(fi, ci)] = ImageTk.PhotoImage(tile.convert("RGB"))
        except Exception:
            pass

    def _tile_arena(self, fila, columna):
        return self._tiles_arena.get((fila, columna), self._img_vacia)

    def _imagen_sobre_arena(self, clave, fila, columna):
        key = (clave, fila, columna)
        if key in self._cache_comp:
            return self._cache_comp[key]
        resultado = None
        tile = self._tiles_pil.get((fila, columna))
        img_pil = self._imagenes_pil.get(clave)
        if tile is not None and img_pil is not None:
            fondo = tile.copy().convert("RGBA")
            fondo.paste(img_pil.convert("RGBA"), (0, 0), img_pil.convert("RGBA"))
            resultado = ImageTk.PhotoImage(fondo.convert("RGB"))
        else:
            resultado = self.imagenes.get(clave)
        self._cache_comp[key] = resultado
        return resultado

    def mostrar_login(self):
        self.limpiar()
        self.fase = "login"
        canvas, ancho, alto = self._crear_canvas_fondo("assets/facciones/fondos/inicio.png")
        cx = ancho // 2
        total_h = 490
        y = (alto - total_h) // 2
        canvas.create_text(cx, y, text="Registro e inicio de sesión", font=("Arial", 22, "bold"), fill="white")
        y += 60
        canvas.create_text(cx, y, text="Jugador defensor", font=("Arial", 14, "bold"), fill="white")
        y += 32
        self.usuario_def = tk.Entry(canvas, width=30, font=("Arial", 12))
        canvas.create_window(cx, y, window=self.usuario_def)
        y += 34
        self.pass_def = tk.Entry(canvas, show="*", width=30, font=("Arial", 12))
        canvas.create_window(cx, y, window=self.pass_def)
        y += 54
        canvas.create_text(cx, y, text="Jugador atacante", font=("Arial", 14, "bold"), fill="white")
        y += 32
        self.usuario_atq = tk.Entry(canvas, width=30, font=("Arial", 12))
        canvas.create_window(cx, y, window=self.usuario_atq)
        y += 34
        self.pass_atq = tk.Entry(canvas, show="*", width=30, font=("Arial", 12))
        canvas.create_window(cx, y, window=self.pass_atq)
        y += 54
        canvas.create_window(cx, y, window=tk.Button(canvas, text="Registrar ambos", command=self.registrar_ambos, width=26, font=("Arial", 11)))
        y += 44
        canvas.create_window(cx, y, window=tk.Button(canvas, text="Iniciar sesión", command=self.iniciar_sesion, width=26, font=("Arial", 11)))
        y += 44
        canvas.create_window(cx, y, window=tk.Button(canvas, text="Ver top de jugadores", command=self.mostrar_top, width=26, font=("Arial", 11)))
        y += 50
        canvas.create_text(cx, y, text="Nota: el jugador 1 será defensor y el jugador 2 será atacante.",
                           font=("Arial", 11), fill="white", width=ancho - 100)

    def registrar_ambos(self):
        u1 = self.usuario_def.get()
        p1 = self.pass_def.get()
        u2 = self.usuario_atq.get()
        p2 = self.pass_atq.get()
        if u1 == "" or p1 == "" or u2 == "" or p2 == "":
            messagebox.showwarning("Error", "Complete todos los espacios.")
            return
        if u1 == u2:
            messagebox.showwarning("Error", "Los usuarios deben ser diferentes.")
            return
        if self.buscar_jugador(u1) is not None or self.buscar_jugador(u2) is not None:
            messagebox.showwarning("Error", "Uno de los usuarios ya existe.")
            return
        self.jugadores.append(Jugador(u1, p1))
        self.jugadores.append(Jugador(u2, p2))
        self.guardar_jugadores()
        messagebox.showinfo("Listo", "Jugadores registrados. Ahora pueden iniciar sesión.")

    def iniciar_sesion(self):
        u1 = self.usuario_def.get()
        p1 = self.pass_def.get()
        u2 = self.usuario_atq.get()
        p2 = self.pass_atq.get()
        jugador1 = self.buscar_jugador(u1)
        jugador2 = self.buscar_jugador(u2)
        if jugador1 is None or jugador2 is None:
            messagebox.showwarning("Error", "Algún jugador no existe.")
            return
        if jugador1.contrasena != p1 or jugador2.contrasena != p2:
            messagebox.showwarning("Error", "Contraseña incorrecta.")
            return
        if jugador1.usuario == jugador2.usuario:
            messagebox.showwarning("Error", "No puede ser el mismo jugador.")
            return
        self.jugador_defensor = jugador1
        self.jugador_atacante = jugador2
        self.mostrar_facciones()

ventana = tk.Tk()
juego = Juego(ventana)
ventana.mainloop()