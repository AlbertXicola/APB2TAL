import pygame, sys
from pygame.locals import *
from random import randint
from juego import nivel1
from juegom import nivel2
from juegodi import nivel3

pygame.init()
pygame.mixer.init()
def opciones_nivel():
    # INICIACION DE PYGAME



    # PANTALLA VENTANA
    W,H = 1200,900
    menu = pygame.display.set_mode((W,H))

    # VELOCIDAD POR SEGUNDO A CUANTO SE MUEVE ALGO
    fps = 50
    reloj = pygame.time.Clock()

    # FUENTE DE LOS TEXTOS
    fuente = pygame.font.Font(None, 20)

    # FONDO DEL JUEGO
    fondo = pygame.image.load("images/fondomenu2.png")
    # Variable de el fondo, x empieza en 0
    x=0



    # IMAGENES MENU Y SUS COORDS

    playfacil = pygame.image.load("images/modo1.png")
    coordsplayfa = (175, 200)

    playmedio = pygame.image.load("images/modo2.png")
    coordsplayme = (475, 200)

    playfdif = pygame.image.load("images/modo3.png")
    coordsplaydi = (775, 200)

    fondopciones = pygame.image.load("images/fondopciones.png")
    cordsfondopciones = (100, 70)



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

    # EL MARCO QUE SI PULSAS DENTRO, PASA LO QUE DICE EN EL BUCLE

    #                        posicion  ,  tamaño
    botonback = pygame.Rect(450, 720,300, 85)


    #                        posicion  ,  tamaño
    playfacilbot = pygame.Rect(175, 200,249, 485)
    playmediobot = pygame.Rect(475, 200,249, 485)
    playfdifbot = pygame.Rect(775, 200,249, 485)


    # BUCLE DEL JUEGO

    while True:


        #SE PUEDE DESGLOSaR PERO ES MEJOR ASI 


        # FONDO EN MOVIMIENTO
        # SE DIVIDE EL VALOR DE X POR  EL ANCHO DE LA IMAGEN DEL FONDO Y DEVUELVE EL RESTO
        x_bailonga = x % fondo.get_rect().width
        menu.blit(fondo,(x_bailonga - fondo.get_rect().width,0))
        if x_bailonga < W:
            menu.blit(fondo,(x_bailonga,0))
        x -= 1

        # DIBUJA LAS IMAGENES
        menu.blit(fondopciones, cordsfondopciones)
        menu.blit(playfacil,coordsplayfa)
        menu.blit(playmedio,coordsplayme)
        menu.blit(playfdif,coordsplaydi)
        menu.blit(mensaje, coordstextoversion)
        menu.blit(back, coordsback)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()

            # Verifica si se hizo clic en el botón
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if playfacilbot.collidepoint(evento.pos):
                    nivel1()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if playmediobot.collidepoint(evento.pos):
                    nivel2()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if playfdifbot.collidepoint(evento.pos):
                    nivel3()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if botonback.collidepoint(evento.pos):
                    return 

            
            pygame.display.update()
            reloj.tick(fps)



