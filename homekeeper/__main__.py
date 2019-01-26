from pathlib import Path

import pygame

pg = pygame

DISPLAY_SIZE = WIDTH, HEIGHT = 800, 600

BG_COLOR = 0, 0, 0

BLOCK_SIZE = WIDTH / 32

SCREEN = None
TILES = None

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


class Base(pygame.sprite.Sprite):
    color = BG_COLOR
    def __init__(self, pos=(0,0)):
        self.step = BLOCK_SIZE
        self.rect = pygame.Rect((pos[0] * BLOCK_SIZE, pos[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
        super().__init__()
        self.image = pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE))
        self.image.fill(self.color)


class Empty(Base):
    color = 128, 128, 128
    pass


class Board:
    def __init__(self, width=32, height=24):
        global TILES
        TILES  = pygame.sprite.Group()
        self.data = [None] * width * height
        self.width = width
        self.height = height
        self.clear()

    def clear(self):
        for x, y, _ in self:
            empty = Empty((x, y))
            TILES.add(empty)


    def __getitem__(self, item):
        return self.data[item[1] * self.width + item[0]]

    def __setitem__(self, item, value):
        if isinstance(self[item], Base):
            self[item].kill()
        self.data[item[1] * self.width + item[0]] = value

    def __delitem__(self, item):
        self[item].kill()
        self[item] = Empty(item)

    def __iter__(self):
        for x in range(self.width):
            for y in range(self.height):
                yield x, y, self[x, y]

    def draw(self, screen):
        pass



class Character(Base):
    color = 255, 0, 0


    def update(self, keys):
        self.rect.x += self.step * (keys[pg.K_RIGHT] - keys[pg.K_LEFT])
        self.rect.y += self.step * (keys[pg.K_DOWN] - keys[pg.K_UP])
        self.rect.x %= WIDTH
        self.rect.y %= HEIGHT



def frame_clear():
    SCREEN.fill((0, 0, 0))


def scene_main():
    global TILES
    clk = pg.time.Clock()
    character = pygame.sprite.Group()
    character.add(Character())
    board = Board()
    tiles = TILES


    while True:
        frame_clear()
        keys = handle_input()
        tiles.update()
        character.update(keys)
        tiles.draw(SCREEN)
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

