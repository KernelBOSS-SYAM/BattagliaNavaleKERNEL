from cmath import rect
import pygame
import Grid

class Nave:
    nome = "Nave"
    dimesione = 0
    path_img = ""

    def __init__(self, nome, path_img, dimensione=2):
        self.nome = nome
        self.path_img = path_img
        self.dimesione = dimensione
        self.dragging = False
        self.rect = None
        self.rotation = 0

    def draw_nave(self, screen, pos_x, pos_y, rotation = 0):
        global img
        img = pygame.image.load(self.path_img).convert_alpha()
        img = pygame.transform.rotate(img, self.rotation)

        if self.rect is None:
            self.rect = img.get_rect(topleft=(pos_x, pos_y))
        else:
            center = self.rect.center
            self.rect = img.get_rect(center=center)

        screen.blit(img, self.rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 1: # Tasto sinistro
                    self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Muove il rettangolo seguendo il mouse
                self.rect.move_ip(event.rel)
        
    def rotazione (self, event, rotation):    #Problema da risolvere ruotano tutte le navi insieme, non riesco a far ruotare solo quella selezionata
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    self.rotation += 90
                if event.key == pygame.K_r:
                        self.rotation -= 90
            
        self.rotation = max(0, min(90, self.rotation))