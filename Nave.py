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

    def draw_nave(self, screen, offset_x, offset_y, cell_dimension=30):
        img = pygame.image.load(self.path_img)
        img = pygame.transform.scale(img, (cell_dimension * self.dimesione, cell_dimension))
        img = pygame.transform.rotate(img, 90)
        screen.blit(img, (offset_x, offset_y))
        