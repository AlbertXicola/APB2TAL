import pygame
from pygame.locals import *
from random import randint

pygame.init()
pygame.mixer.init()

def mostrar_puntuacion(menu):
    # FUENTE DE LOS TEXTOS
    fuente = pygame.font.Font(None, 20)

    # Abre el archivo de puntuación en modo de lectura
    with open("puntuacion.txt", "r") as archivo:
        lineas = archivo.readlines()

    # Invierte el orden de las líneas
    lineas = lineas[::-1]

    # Dibuja el objeto de texto en la pantalla
    y = 100  # Posición vertical inicial
    for linea in lineas:
        texto = fuente.render(linea.strip(), True, (255, 255, 255))
        menu.blit(texto, (440, y))
        y += 20  # Aumenta la posición vertical para la siguiente línea

def rankingmenu():
    # INICIACION DE PYGAME
    pygame.init()
    pygame.mixer.init()

    # PANTALLA VENTANA
    W,H = 1200,900
    menu = pygame.display.set_mode((W,H))

    # VELOCIDAD POR SEGUNDO A CUANTO SE MUEVE ALGO
    fps = 20
    reloj = pygame.time.Clock()

    # FUENTE DE LOS TEXTOS
    fuente = pygame.font.Font(None, 20)

    # FONDO DEL JUEGO
    fondo = pygame.image.load("images/fondomenu2.png")
    # Variable de el fondo, x empieza en 0
    x=0

    # IMAGENES MENU Y SUS COORDS

    back = pygame.image.load("images/back.png")
    coordsback = (450, 720)

    # ICONO Y TITULO
    pygame.display.set_caption("SnakeThon")
    icon = pygame.image.load('images/logo.png').convert()
    pygame.display.set_icon(icon)

    # TEXTO DE LA PANTALLA
    text = "snapshot V3.1"
    mensaje = fuente.render(text, 10, (255,255,255))
    coordstextoversion = (1100, 880)

    panel = pygame.image.load("images/score.png")
    coordspanel = (350, 75)

    # EL MARCO QUE SI PULSAS DENTRO, PASA LO QUE DICE EN EL BUCLE

    #                        posicion  ,  tamaño
    botonback = pygame.Rect(450, 720,300, 85)

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if botonback.collidepoint(evento.pos):
                    return

        # FONDO EN MOVIMIENTO
        # SE DIVIDE EL VALOR DE X POR  EL ANCHO DE LA IMAGEN DEL FONDO Y DEVUELVE EL RESTO
        x_bailonga = x % fondo.get_rect().width
        menu.blit(fondo,(x_bailonga - fondo.get_rect().width,0))
        if x_bailonga < W:
            menu.blit(fondo,(x_bailonga,0))
        x -= 1

        # DIBUJA LAS IMAGENES
        menu.blit(panel, coordspanel)
        menu.blit(mensaje, coordstextoversion)
        menu.blit(back, coordsback)
        
        mostrar_puntuacion(menu)
        pygame.display.flip()       


        reloj.tick(fps)
        pygame.display.update()
