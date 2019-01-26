from pathlib import Path

import pygame

pg = pygame

DISPLAY_SIZE = WIDTH, HEIGHT = 800, 600

BG_COLOR = 0, 0, 0

BLOCK_SIZE = WIDTH / 32



class Interrupt(BaseException):
    pass


def init():
    global SCREEN
    SCREEN = pg.display.set_mode(DISPLAY_SIZE)


def handle_input():
    pg.event.pump()
    keys = pg.key.get_pressed()
    if keys[pg.K_ESCAPE]:
        raise Interrupt
    return keys


class Character(pygame.sprite.Sprite):
    def __init__(self):
        self.step = BLOCK_SIZE
        self.rect = pygame.Rect((0,0, BLOCK_SIZE, BLOCK_SIZE))
        super().__init__()
        self.color = 255, 0, 0
        self.image = pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE))
        self.image.fill(self.color)

    def update(self, keys):
        self.rect.x += self.step * (keys[pg.K_RIGHT] - keys[pg.K_LEFT])
        self.rect.y += self.step * (keys[pg.K_DOWN] - keys[pg.K_UP])
        self.rect.x %= WIDTH
        self.rect.y %= HEIGHT



def frame_clear():
    SCREEN.fill((0, 0, 0))


def scene_main():
    
    clk = pg.time.Clock()
    character = pygame.sprite.Group()
    character.add(Character())

    while True:
        frame_clear()
        keys = handle_input()
        character.update(keys)
        character.draw(SCREEN)
        pg.display.flip()
        clk.tick(30)


def main():
    init()
    try:
        scene_main()
    except Interrupt:
        pass
    finally:
        pg.display.quit()
        pg.quit()
    
    
if __name__ == "__main__":
    main()

