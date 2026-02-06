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

    def draw_nave(self, screen, offset_x, offset_y, rotation = 0):
        img = pygame.image.load(self.path_img).convert_alpha()
        img = pygame.transform.rotate(img, rotation)
        img_rect = img.get_rect(topleft=(offset_x, offset_y))
        screen.blit(img, img_rect)
        self.rect = img_rect
        return img_rect

    def is_clicked(self, pos):
        return hasattr(self, 'rect') and self.rect.collidepoint(pos)
        