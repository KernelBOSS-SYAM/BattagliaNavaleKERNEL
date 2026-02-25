import pygame

class Nave:

    def __init__(self, nome, path_img, dimensione=2):

        self.nome = nome
        self.dimensione = dimensione

        self.dragging = False
        self.rotation = 0
        self.placed = False

        self.rect = None
        self.grid_position = None

        self.image_original = pygame.image.load(path_img).convert_alpha()
        self.image = self.image_original

    def draw_nave(self, screen, pos_x, pos_y):

        self.image = pygame.transform.rotate(self.image_original, self.rotation)

        if self.rect is None:
            self.rect = self.image.get_rect(topleft=(pos_x, pos_y))
        else:
            center = self.rect.center
            self.rect = self.image.get_rect(center=center)

        screen.blit(self.image, self.rect.topleft)

    def handle_event(self, event):

        if self.placed:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:
                self.dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.move_ip(event.rel)

        elif event.type == pygame.KEYDOWN:
            if self.dragging:
                if event.key == pygame.K_e:
                    self.rotation = (self.rotation + 90) % 180
                elif event.key == pygame.K_r:
                    self.rotation = (self.rotation - 90) % 180

        return False