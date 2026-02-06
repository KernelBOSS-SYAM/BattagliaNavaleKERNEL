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

    def draw_nave(self, screen, offset_x, offset_y, rotation = 0):
        img = pygame.image.load(self.path_img).convert_alpha()
        img = pygame.transform.rotate(img, rotation)

        if self.rect is None:
            self.rect = img.get_rect(topleft=(offset_x, offset_y))

        screen.blit(img, self.rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Tasto sinistro
                if self.rect.collidepoint(event.pos):
                    self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Muove il rettangolo seguendo il mouse
                self.rect.move_ip(event.rel)

    
        