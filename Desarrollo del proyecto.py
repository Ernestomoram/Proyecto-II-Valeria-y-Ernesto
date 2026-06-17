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
    
    def mostrar_top(self):
        self.limpiar()
        canvas, ancho, alto = self._crear_canvas_fondo("assets/facciones/fondos/inicio.png")
        cx = ancho // 2
        defensores = sorted(self.jugadores[:], key=lambda j: j.victorias_defensor, reverse=True)
        atacantes = sorted(self.jugadores[:], key=lambda j: j.victorias_atacante, reverse=True)
        n_def = min(5, len(defensores))
        n_atq = min(5, len(atacantes))
        total_h = 55 + 45 + n_def * 32 + 55 + 45 + n_atq * 32 + 55
        y = max(60, (alto - total_h) // 2)
        canvas.create_text(cx, y, text="Top de jugadores", font=("Arial", 22, "bold"), fill="white")
        y += 55
        canvas.create_text(cx, y, text="Top 5 defensores", font=("Arial", 15, "bold"), fill="white")
        y += 40
        for i in range(n_def):
            texto = str(i + 1) + ".  " + defensores[i].usuario + "  —  " + str(defensores[i].victorias_defensor) + " victorias"
            canvas.create_text(cx, y, text=texto, font=("Arial", 13), fill="white")
            y += 32
        y += 25
        canvas.create_text(cx, y, text="Top 5 atacantes", font=("Arial", 15, "bold"), fill="white")
        y += 40
        for i in range(n_atq):
            texto = str(i + 1) + ".  " + atacantes[i].usuario + "  —  " + str(atacantes[i].victorias_atacante) + " victorias"
            canvas.create_text(cx, y, text=texto, font=("Arial", 13), fill="white")
            y += 32
        y += 35
        canvas.create_window(cx, y, window=tk.Button(canvas, text="Volver", command=self.mostrar_login, width=20, font=("Arial", 12)))

    def mostrar_facciones(self):
        self.limpiar()
        canvas, ancho, alto = self._crear_canvas_fondo("assets/facciones/fondos/inicio.png")
        cx = ancho // 2
        total_h = 60 + 40 + 50 + len(FACCIONES) * 38 + 55 + len(FACCIONES) * 38 + 55
        y = max(50, (alto - total_h) // 2)
        canvas.create_text(cx, y, text="Selección de facciones", font=("Arial", 22, "bold"), fill="white")
        y += 50
        canvas.create_text(cx, y, text="El defensor y el atacante no pueden usar la misma facción.",
                           font=("Arial", 13), fill="white", width=ancho - 100)
        self.var_def = tk.StringVar(value=FACCIONES[0])
        self.var_atq = tk.StringVar(value=FACCIONES[1])
        y += 50
        canvas.create_text(cx, y, text="Facción defensor", font=("Arial", 15, "bold"), fill="white")
        for faccion in FACCIONES:
            y += 38
            rb = tk.Radiobutton(canvas, text=faccion, variable=self.var_def, value=faccion,
                                bg="#1a1a1a", fg="white", selectcolor="#444444",
                                activebackground="#333333", activeforeground="white", font=("Arial", 13))
            canvas.create_window(cx, y, window=rb)
        y += 55
        canvas.create_text(cx, y, text="Facción atacante", font=("Arial", 15, "bold"), fill="white")
        for faccion in FACCIONES:
            y += 38
            rb = tk.Radiobutton(canvas, text=faccion, variable=self.var_atq, value=faccion,
                                bg="#1a1a1a", fg="white", selectcolor="#444444",
                                activebackground="#333333", activeforeground="white", font=("Arial", 13))
            canvas.create_window(cx, y, window=rb)
        y += 55
        canvas.create_window(cx, y, window=tk.Button(canvas, text="Iniciar partida", command=self.iniciar_partida, width=26, font=("Arial", 12)))

    def iniciar_partida(self):
        if self.var_def.get() == self.var_atq.get():
            messagebox.showwarning("Error", "No pueden usar la misma facción.")
            return
        self.faccion_defensor = self.var_def.get()
        self.faccion_atacante = self.var_atq.get()
        self.victorias_defensor = 0
        self.victorias_atacante = 0
        self.ronda = 1
        self.bono_atacante = 0
        self.iniciar_ronda()

    def iniciar_ronda(self):
        self.torres = []
        self.unidades = []
        self.muros = []
        self.base = BaseCentral()
        self.dinero_defensor = 250 + self.ronda * 50
        self.dinero_atacante = 250 + self.ronda * 50 + self.bono_atacante
        self.fase = "defensa"
        self.seleccion = "muro"
        self.cargar_imagenes()
        self.mostrar_juego()
        self.escribir_log("Ronda " + str(self.ronda) + ": fase de construcción del defensor.")

    def cargar_imagenes(self):
        self.imagenes = {}
        self._imagenes_pil = {}
        self._cache_comp = {}
        objetos = ["base", "muro", "torre_basica", "torre_pesada", "torre_magica", "soldado", "tanque", "rapida"]
        for faccion in FACCIONES:
            for objeto in objetos:
                ruta = "assets/facciones/" + faccion + "/" + objeto + ".png"
                try:
                    if Image is not None:
                        if objeto == "base":
                            img = Image.open(ruta).resize((TAMANO_CELDA * 2, TAMANO_CELDA * 2), Image.LANCZOS).convert("RGBA")
                            t = TAMANO_CELDA
                            for sufijo, box in [("_base_00", (0, 0, t, t)), ("_base_01", (t, 0, t*2, t)),
                                                ("_base_10", (0, t, t, t*2)), ("_base_11", (t, t, t*2, t*2))]:
                                quad = img.crop(box)
                                self._imagenes_pil[faccion + sufijo] = quad
                                self.imagenes[faccion + sufijo] = ImageTk.PhotoImage(quad.convert("RGB"))
                        else:
                            img = Image.open(ruta).resize((TAMANO_CELDA, TAMANO_CELDA), Image.LANCZOS).convert("RGBA")
                            self._imagenes_pil[faccion + "_" + objeto] = img
                            self.imagenes[faccion + "_" + objeto] = ImageTk.PhotoImage(img.convert("RGB"))
                    else:
                        self.imagenes[faccion + "_" + objeto] = tk.PhotoImage(file=ruta)
                except Exception:
                    self.imagenes[faccion + "_" + objeto] = None

    def mostrar_juego(self):
        self.limpiar()
        self._img_vacia = tk.PhotoImage(width=TAMANO_CELDA, height=TAMANO_CELDA)
        self._cargar_tiles_arena()
        marco_info = tk.Frame(self.ventana)
        marco_info.pack(pady=5)
        self.label_info = tk.Label(marco_info, text="", font=("Arial", 12, "bold"))
        self.label_info.pack()
        marco = tk.Frame(self.ventana)
        marco.pack()
        self.botones = []
        for fila in range(TAMANO):
            fila_botones = []
            for columna in range(TAMANO):
                boton = tk.Button(marco, image=self._tile_arena(fila, columna),
                                  width=TAMANO_CELDA, height=TAMANO_CELDA,
                                  compound=tk.CENTER,
                                  relief=tk.FLAT, bd=0,
                                  highlightthickness=1, highlightbackground="#cccccc",
                                  command=lambda f=fila, c=columna: self.click_casilla(f, c))
                boton.grid(row=fila, column=columna, padx=0, pady=0)
                fila_botones.append(boton)
            self.botones.append(fila_botones)
        marco_controles = tk.Frame(self.ventana)
        marco_controles.pack(pady=8)
        self.marco_controles = marco_controles
        self.log = tk.Text(self.ventana, width=80, height=8)
        self.log.pack(pady=5)
        self.actualizar_controles()
        self.actualizar_tablero()

    def actualizar_controles(self):
        for widget in self.marco_controles.winfo_children():
            widget.destroy()
        if self.fase == "defensa":
            tk.Button(self.marco_controles, text="Muro $25", command=lambda: self.cambiar_seleccion("muro")).grid(row=0, column=0)
            tk.Button(self.marco_controles, text="Torre básica $60", command=lambda: self.cambiar_seleccion("torre_basica")).grid(row=0, column=1)
            tk.Button(self.marco_controles, text="Torre pesada $110", command=lambda: self.cambiar_seleccion("torre_pesada")).grid(row=0, column=2)
            tk.Button(self.marco_controles, text="Torre mágica $90", command=lambda: self.cambiar_seleccion("torre_magica")).grid(row=0, column=3)
            tk.Button(self.marco_controles, text="Terminar defensa", command=self.terminar_defensa).grid(row=0, column=4)
        elif self.fase == "ataque":
            tk.Button(self.marco_controles, text="Soldado $45", command=lambda: self.cambiar_seleccion("soldado")).grid(row=0, column=0)
            tk.Button(self.marco_controles, text="Tanque $95", command=lambda: self.cambiar_seleccion("tanque")).grid(row=0, column=1)
            tk.Button(self.marco_controles, text="Rápida $65", command=lambda: self.cambiar_seleccion("rapida")).grid(row=0, column=2)
            tk.Button(self.marco_controles, text="Iniciar combate", command=self.iniciar_combate).grid(row=0, column=3)
        elif self.fase == "combate":
            tk.Button(self.marco_controles, text="Ejecutar turno", command=self.turno_combate).grid(row=0, column=0)
        self.actualizar_info()

    def actualizar_info(self):
        texto = "Ronda: " + str(self.ronda)
        texto += " | Marcador defensor: " + str(self.victorias_defensor)
        texto += " | Marcador atacante: " + str(self.victorias_atacante)
        texto += " | Dinero defensor: $" + str(self.dinero_defensor)
        texto += " | Dinero atacante: $" + str(self.dinero_atacante)
        texto += " | Base: " + str(self.base.vida)
        texto += " | Fase: " + self.fase
        texto += " | Selección: " + self.seleccion
        self.label_info.config(text=texto)

    def escribir_log(self, texto):
        try:
            self.log.insert(tk.END, texto + "\n")
            self.log.see(tk.END)
        except Exception:
            pass

    def cambiar_seleccion(self, seleccion):
        self.seleccion = seleccion
        self.actualizar_info()

    def click_casilla(self, fila, columna):
        if self.fase == "defensa":
            self.colocar_defensa(fila, columna)
        elif self.fase == "ataque":
            self.colocar_unidad(fila, columna)

    def casilla_ocupada(self, fila, columna):
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
        return False

    def colocar_defensa(self, fila, columna):
        if self.casilla_ocupada(fila, columna):
            return
        if self.seleccion == "muro":
            costo = 25
            if self.dinero_defensor >= costo:
                self.muros.append([fila, columna, 90])
                self.dinero_defensor = self.dinero_defensor - costo
        else:
            torre = Torre(self.seleccion, fila, columna)
            if self.dinero_defensor >= torre.costo:
                self.torres.append(torre)
                self.dinero_defensor = self.dinero_defensor - torre.costo
        self.actualizar_tablero()
        self.actualizar_info()

    def terminar_defensa(self):
        self.fase = "ataque"
        self.seleccion = "soldado"
        self.actualizar_controles()
        self.escribir_log("Fase de ataque: coloque unidades en los bordes del mapa.")

    def colocar_unidad(self, fila, columna):
        if not (fila == 0 or fila == TAMANO - 1 or columna == 0 or columna == TAMANO - 1):
            messagebox.showwarning("Regla", "Las unidades se colocan en los bordes.")
            return
        if self.casilla_ocupada(fila, columna):
            return
        unidad = Unidad(self.seleccion, fila, columna)
        if self.dinero_atacante >= unidad.costo:
            self.unidades.append(unidad)
            self.dinero_atacante = self.dinero_atacante - unidad.costo
        self.actualizar_tablero()
        self.actualizar_info()

    def iniciar_combate(self):
        if len(self.unidades) == 0:
            messagebox.showwarning("Error", "El atacante debe colocar al menos una unidad.")
            return
        self.fase = "combate"
        self.ocultar_cuadricula()
        self.actualizar_controles()
        self.escribir_log("Combate iniciado. Presione 'Ejecutar turno'.")

    def ocultar_cuadricula(self):
        for fila in self.botones:
            for boton in fila:
                boton.config(highlightthickness=0)

    def actualizar_tablero(self):
        for fila in range(TAMANO):
            for columna in range(TAMANO):
                boton = self.botones[fila][columna]
                boton.config(text="", image=self._tile_arena(fila, columna), compound=tk.CENTER)
        self.pintar_base(self.faccion_defensor)
        for muro in self.muros:
            self.pintar_casilla(muro[0], muro[1], "muro", self.faccion_defensor)
        for torre in self.torres:
            self.pintar_casilla(torre.fila, torre.columna, torre.tipo, self.faccion_defensor)
        for unidad in self.unidades:
            self.pintar_casilla(unidad.fila, unidad.columna, unidad.tipo, self.faccion_atacante)
        self.actualizar_info()

ventana = tk.Tk()
juego = Juego(ventana)
ventana.mainloop()