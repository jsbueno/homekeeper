import pygame as pg

DISPLAY_SIZE = WIDTH, HEIGHT = 896, 672

class Interrupt(BaseException):
    pass


def init():
    global screen
    screen = pg.display.set_mode(DISPLAY_SIZE)


def handle_input():
    pg.event.pump()
    keys = pg.key.get_pressed()
    if keys[pg.K_ESCAPE]:
        raise Interrupt
    return keys

def game_body():
    x = y = 0
    w = h = 50
    clr = 255, 0, 0
    step = 10
    while True:
        keys = yield None
        x += step * (keys[pg.K_RIGHT] - keys[pg.K_LEFT])
        y += step * (keys[pg.K_DOWN] - keys[pg.K_UP])
        x %= WIDTH
        y %= HEIGHT
        
        pg.draw.rect(screen, clr, (x,y, w, h))


def frame_clear():
    screen.fill((0, 0, 0))


def scene_main():
    
    clk = pg.time.Clock()
    game = game_body()
    next(game)
    while True:
        frame_clear()
        game.send(handle_input())
        pg.display.flip()
        clk.tick(33)


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

