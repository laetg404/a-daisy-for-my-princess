import turtle
import math
import random

# ==========================================
# CONFIGURACIÓN
# ==========================================

screen = turtle.Screen()
screen.setup(850, 750)
screen.bgcolor("#FFF9F0")
screen.title("Una margarita para ti ♡")
screen.tracer(0)

pen = turtle.Turtle()
pen.hideturtle()
pen.speed(0)

TOTAL_PETALOS = 13
CENTRO_Y = 80          # altura del centro de la flor
SUELO = -195           # altura del suelo
R0 = 22                # radio donde nace cada pétalo (queda bajo el centro)

Y_TALLO_ARRIBA = CENTRO_Y - 4
Y_TALLO_ABAJO = SUELO - 10

petalos_visibles = []
petalos_caidos = []

paso = 0

# Progreso de las animaciones de crecimiento (0 a 1)
TALLO_PROG = 0.0
HOJAS_ESC = 0.0

rng = random.Random(7)   # semilla fija: la flor siempre sale igual de natural


# ==========================================
# UTILIDADES
# ==========================================

def mezclar(c1, c2, t):
    """Mezcla dos colores hex. t=0 -> c1, t=1 -> c2."""
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))


def poligono(puntos, relleno, borde, grosor=1):
    pen.penup()
    pen.goto(puntos[0])
    pen.pendown()
    pen.color(borde, relleno)
    pen.width(grosor)
    pen.begin_fill()
    for p in puntos[1:]:
        pen.goto(p)
    pen.goto(puntos[0])
    pen.end_fill()
    pen.penup()


def polilinea(puntos, color, grosor=1):
    pen.penup()
    pen.goto(puntos[0])
    pen.pendown()
    pen.color(color)
    pen.width(grosor)
    for p in puntos[1:]:
        pen.goto(p)
    pen.penup()


# ==========================================
# GEOMETRÍA DE LOS PÉTALOS
# ==========================================

def construir_petalo(largo, ancho):
    """
    Pétalo alargado: estrecho en la base, más ancho cerca de la punta
    y con la punta redondeada, como una margarita real.
    Devuelve (contorno, capas de sombra, nervaduras) en coordenadas locales.
    """
    n = 28
    perfil = []
    for k in range(n + 1):
        t = k / n
        hw = ancho * max(0.0, math.sin(math.pi * t ** 1.3)) ** 0.75
        perfil.append((t, R0 + largo * t, hw))

    contorno = [(x, hw) for _, x, hw in perfil] + \
               [(x, -hw) for _, x, hw in reversed(perfil[1:-1])]

    def capa(tmax):
        arriba = []
        for t, x, hw in perfil:
            if t <= tmax:
                s = math.sqrt(max(0.0, 1 - (t / tmax) ** 3))
                arriba.append((x, hw * s))
        abajo = [(x, -y) for x, y in reversed(arriba[1:-1])]
        return arriba + abajo

    # Base del pétalo ligeramente cremosa (sombra suave hacia el centro)
    capas = [
        (capa(0.62), "#F6F2E6"),
        (capa(0.36), "#EEE5CE"),
    ]

    # Nervaduras (surcos largos típicos de la margarita)
    nervios = []
    for factor in (0.0, 0.45, -0.45):
        nervios.append([(x, hw * factor) for t, x, hw in perfil if 0.10 <= t <= 0.84])

    return contorno, capas, nervios


PETALOS = []
for _i in range(TOTAL_PETALOS):
    _largo = rng.uniform(98, 113)
    _ancho = rng.uniform(15, 18.5)
    PETALOS.append({
        "ang": _i * (360 / TOTAL_PETALOS) + rng.uniform(-3, 3),
        "pivote": R0 + _largo * 0.5,
        "geo": construir_petalo(_largo, _ancho),
    })

# Dónde aterriza cada pétalo (x, y, giro total en grados)
_xs = [-170 + k * (340 / (TOTAL_PETALOS - 1)) for k in range(TOTAL_PETALOS)]
rng.shuffle(_xs)
DESTINOS = []
for _i in range(TOTAL_PETALOS):
    DESTINOS.append((
        _xs[_i] + rng.uniform(-8, 8),
        SUELO - rng.uniform(8, 42),
        rng.choice((-1, 1)) * rng.uniform(220, 420),
    ))


def transformar(puntos, cx, cy, th, pivote, escala=1.0):
    c, s = math.cos(th), math.sin(th)
    res = []
    for x, y in puntos:
        lx = x - pivote
        ly = y * escala
        res.append((cx + lx * c - ly * s, cy + lx * s + ly * c))
    return res


def pose_flor(i):
    """Posición del pétalo i cuando sigue pegado a la flor."""
    p = PETALOS[i]
    th = math.radians(p["ang"])
    cx = p["pivote"] * math.cos(th)
    cy = CENTRO_Y + p["pivote"] * math.sin(th)
    return cx, cy, th


def pose_caida(i, p):
    """Posición del pétalo i durante su caída (p de 0 a 1)."""
    cx0, cy0, th0 = pose_flor(i)
    tx, ty, giro = DESTINOS[i]

    aceleracion = p ** 1.7
    suave = p * p * (3 - 2 * p)
    balanceo = 16 * math.sin(p * math.pi * 3) * (1 - p) * (1 if i % 2 == 0 else -1)

    cx = cx0 + (tx - cx0) * suave + balanceo
    cy = cy0 + (ty - cy0) * aceleracion
    th = th0 + math.radians(giro) * suave
    return cx, cy, th


def dibujar_petalo(i, pose, escala=1.0, con_sombra=True):
    cx, cy, th = pose
    p = PETALOS[i]
    contorno, capas, nervios = p["geo"]
    piv = p["pivote"]

    if con_sombra:
        sombra = transformar(contorno, cx + 3, cy - 3, th, piv, escala)
        poligono(sombra, "#EBDFC9", "#EBDFC9", 1)

    poligono(transformar(contorno, cx, cy, th, piv, escala), "#FFFFFF", "#CFC8B3", 1.2)

    for pts, color in capas:
        poligono(transformar(pts, cx, cy, th, piv, escala), color, color, 1)

    for linea in nervios:
        polilinea(transformar(linea, cx, cy, th, piv, escala), "#E2DCCB", 1)


# ==========================================
# CENTRO DE LA FLOR (disco con semillas en espiral)
# ==========================================

def construir_semillas():
    semillas = []
    angulo_dorado = math.radians(137.50776)
    r_max = 2.4 * math.sqrt(140)

    for n in range(1, 141):
        r = 2.4 * math.sqrt(n)
        a = n * angulo_dorado
        x = r * math.cos(a)
        y = r * math.sin(a)

        color = mezclar("#B5650A", "#F4C442", (r / r_max) ** 0.8)

        # Luz desde arriba a la izquierda para dar volumen de cúpula
        luz = (-x + y) / (2 * r_max)
        if luz > 0:
            color = mezclar(color, "#FFF0A0", luz * 0.6)
        else:
            color = mezclar(color, "#8A4A06", -luz * 0.5)

        semillas.append((x, y, 5, color))
    return semillas


SEMILLAS = construir_semillas()


def dibujar_centro():
    pen.penup()
    pen.goto(0, CENTRO_Y)
    pen.dot(68, "#A86A0E")
    pen.dot(62, "#D99A1A")

    for x, y, tam, color in SEMILLAS:
        pen.goto(x, CENTRO_Y + y)
        pen.dot(tam, color)


# ==========================================
# TALLO, HOJAS Y SUELO
# ==========================================

def tallo_x(y):
    """El tallo se curva suavemente en forma de S."""
    u = (Y_TALLO_ARRIBA - y) / (Y_TALLO_ARRIBA - Y_TALLO_ABAJO)
    return 6 * math.sin(2 * math.pi * u)


def dibujar_tallo():
    if TALLO_PROG <= 0:
        return

    y_actual = Y_TALLO_ABAJO + (Y_TALLO_ARRIBA - Y_TALLO_ABAJO) * TALLO_PROG
    N = 40
    puntos = []
    for k in range(N + 1):
        y = Y_TALLO_ABAJO + (Y_TALLO_ARRIBA - Y_TALLO_ABAJO) * k / N
        if y <= y_actual:
            puntos.append((tallo_x(y), y))

    if len(puntos) < 2:
        return

    polilinea(puntos, "#3F6E3A", 10)
    polilinea(puntos, "#5C9A4F", 7)
    polilinea([(x + 1.8, y) for x, y in puntos], "#86BC74", 2)


def dibujar_hoja(bx, by, ang, largo, ancho, curva):
    esc = HOJAS_ESC
    if esc <= 0:
        return

    largo *= esc
    ancho *= esc

    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    n = 18

    def centro(t):
        d = curva * largo * t * t * 0.35
        return (bx + dx * largo * t + px * d,
                by + dy * largo * t + py * d)

    def semiancho(t):
        return ancho * max(0.0, math.sin(math.pi * t ** 0.8)) ** 0.85

    centros = [centro(k / n) for k in range(n + 1)]
    lado_a = [(c[0] + px * semiancho(k / n), c[1] + py * semiancho(k / n))
              for k, c in enumerate(centros)]
    lado_b = [(c[0] - px * semiancho(k / n), c[1] - py * semiancho(k / n))
              for k, c in enumerate(centros)]

    # Dos mitades con distinto tono, separadas por la nervadura central
    poligono(lado_a + centros[::-1], "#7DB86E", "#3F7340", 1.2)
    poligono(lado_b + centros[::-1], "#5E9B55", "#3F7340", 1.2)
    polilinea(centros[:-1], "#3F7340", 1.5)

    # Nervaduras laterales
    for t in (0.22, 0.42, 0.62):
        c0 = centro(t)
        t2 = t + 0.15
        c1 = centro(t2)
        w = semiancho(t2) * 0.85
        polilinea([c0, (c1[0] + px * w, c1[1] + py * w)], "#4C8645", 1)
        polilinea([c0, (c1[0] - px * w, c1[1] - py * w)], "#4C8645", 1)


def dibujar_hojas():
    dibujar_hoja(tallo_x(-60), -60, 148, 105, 21, 0.5)
    dibujar_hoja(tallo_x(-115), -115, 32, 105, 21, -0.5)


def suelo_y(x):
    return SUELO + 7 * math.sin(x / 37) + 3 * math.sin(x / 11)


HIERBA = []
_colores_hierba = ["#5F9A52", "#6FAE5F", "#4C8444"]
for _x in range(-430, 431, 16):
    _xx = _x + rng.uniform(-5, 5)
    HIERBA.append((
        _xx,
        rng.uniform(16, 40),
        rng.uniform(-9, 9),
        rng.choice(_colores_hierba),
    ))


def dibujar_suelo():
    banda = [(-430, -380)]
    for x in range(-430, 431, 10):
        banda.append((x, suelo_y(x)))
    banda.append((430, -380))
    poligono(banda, "#A8CB8E", "#A8CB8E", 1)

    for x, alto, inclinacion, color in HIERBA:
        base = suelo_y(x) - 2
        poligono(
            [(x - 3, base), (x + inclinacion, base + alto), (x + 3, base)],
            color, color, 1
        )


# ==========================================
# DIBUJAR LA ESCENA
# ==========================================

def dibujar_escena(volador=None):
    """volador = (indice_petalo, progreso_de_caida) o None."""
    pen.clear()

    dibujar_tallo()
    dibujar_hojas()
    dibujar_suelo()

    # Pétalos que ya cayeron y descansan sobre la hierba
    for i in petalos_caidos:
        dibujar_petalo(i, pose_caida(i, 1.0), con_sombra=False)

    # Capullo verde (visible solo mientras no hay pétalos)
    if TALLO_PROG >= 1:
        pen.penup()
        pen.goto(0, CENTRO_Y)
        pen.dot(34, "#5E9A55")

    # Pétalos que permanecen en la flor
    for i in petalos_visibles:
        if i in petalos_caidos:
            continue
        if volador is not None and i == volador[0]:
            continue
        dibujar_petalo(i, pose_flor(i))

    # Centro cuando estén todos los pétalos
    if len(petalos_visibles) == TOTAL_PETALOS:
        dibujar_centro()

    # Pétalo en movimiento
    if volador is not None:
        i, p = volador
        # Efecto de aleteo: el pétalo se "voltea" mientras cae
        escala = 1 - 0.55 * (1 - p) * abs(math.sin(p * math.pi * 4))
        dibujar_petalo(i, pose_caida(i, p), escala)

    screen.update()


# ==========================================
# CRECIMIENTO DEL TALLO Y LAS HOJAS
# ==========================================

def animar_tallo(frame=0):
    global TALLO_PROG

    t = frame / 48
    TALLO_PROG = t * t * (3 - 2 * t)

    dibujar_escena()

    if frame < 48:
        screen.ontimer(
            lambda: animar_tallo(frame + 1),
            25
        )
    else:
        screen.ontimer(crecer_hojas, 300)


def crecer_hojas(frame=0):
    global HOJAS_ESC

    t = frame / 14
    HOJAS_ESC = t * t * (3 - 2 * t)

    dibujar_escena()

    if frame < 14:
        screen.ontimer(
            lambda: crecer_hojas(frame + 1),
            30
        )
    else:
        screen.ontimer(comenzar_petalo, 500)


# ==========================================
# CONSTRUCCIÓN DE LA FLOR
# ==========================================

def comenzar_petalo():
    if len(petalos_visibles) < TOTAL_PETALOS:

        indice = len(petalos_visibles)

        petalos_visibles.append(indice)

        dibujar_escena()

        screen.ontimer(
            comenzar_petalo,
            250
        )

    else:
        screen.ontimer(
            finalizar_flor,
            500
        )


def finalizar_flor():
    dibujar_escena()
    escribir_mensaje("Una pequeña margarita para tí, mi princesa... ♡ ")

    screen.update()

    screen.ontimer(
        iniciar_juego,
        1800
    )


# ==========================================
# JUEGO: ME QUIERE / NO ME QUIERE
# ==========================================

def iniciar_juego():
    global paso

    paso = 0
    animar_caida()


def animar_caida():
    global paso

    if paso >= TOTAL_PETALOS:
        dibujar_escena()

        def mensaje_dos():
            pen.clear()
            escribir_mensaje("¡Te amo, mi amorcito preciosa! ♡ ")
            screen.update()
            screen.ontimer(mensaje_tres, 2500)

        def mensaje_tres():
            pen.clear()
            pen.penup()
            pen.color("#795B55")

            lineas = [
                "¡Feliz cumpleaños, vida mía! ♡ ",
                "Todos los días celebro tu vida,",
                "porque tu existencia le da sentido",
                "a mi existencia."
            ]

            separacion = 35
            altura_total = (len(lineas) - 1) * separacion

            for i, linea in enumerate(lineas):
                pen.goto(0, altura_total / 2 - i * separacion)

                pen.write(
                    linea,
                    align="center",
                    font=("Georgia", 20, "italic")
                )

            screen.update()

        escribir_mensaje("¡Me quieres! ♡ ")
        screen.update()

        screen.ontimer(mensaje_dos, 2500)

        return

    frase = (
        "Me quieres..."
        if paso % 2 == 0
        else "No me quieres..."
    )

    frame = 0
    total_frames = 34

    def caer():
        nonlocal frame
        global paso

        p = min(1.0, frame / total_frames)

        dibujar_escena((paso, p))

        escribir_mensaje(frase)

        screen.update()

        frame += 1

        if frame <= total_frames:

            screen.ontimer(
                caer,
                30
            )

        else:

            petalos_caidos.append(paso)

            paso += 1

            dibujar_escena()

            screen.ontimer(
                animar_caida,
                450
            )

    caer()


# ==========================================
# MENSAJES
# ==========================================

def escribir_mensaje(texto):
    pen.penup()
    pen.goto(0, 270)
    pen.color("#795B55")

    pen.write(
        texto,
        align="center",
        font=("Georgia", 25, "italic")
    )


# ==========================================
# INICIAR ANIMACIÓN
# ==========================================

animar_tallo()

turtle.done()