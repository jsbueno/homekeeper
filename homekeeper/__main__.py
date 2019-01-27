from importlib import resources
from pathlib import Path

import pygame

pg = pygame

DISPLAY_SIZE = WIDTH, HEIGHT = 800, 600

BG_COLOR = 0, 0, 0

BLOCK_SIZE = WIDTH / 32

SCREEN = None

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


class GameObject(pygame.sprite.Sprite):
    tile_registry = {}
    color = BG_COLOR

    traversable = True
    pushable = False


    def __init__(self, board, pos=(0,0)):
        self.board = board
        self.x, self.y = pos
        self.step = BLOCK_SIZE
        self.rect = pygame.Rect((pos[0] * BLOCK_SIZE, pos[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
        super().__init__()
        self.image = pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE))
        self.image.fill(self.color)
        self.board[self.x, self.y] = self
        self.previous = None

    def __hash__(self):
        return hash((self.x, self.y))



    def movable(self, direction, pushing=False, count=0):
        new_x = self.x + direction[0]
        new_y = self.y + direction[1]
        if not 0 <= new_x < self.board.width or not 0 < new_y < self.board.height:
            return False

        new_pos = self.board[new_x, new_y]
        if not new_pos.traversable:
            return False

        if not new_pos.pushable:
            return True

        if not pushing:
            return True

        if count > 0 and new_pos.movable(direction, pushing, count - 1):
            return True

        return False

    def move(self, direction, pushing, count):
        if not self.movable(direction, pushing, count):
            return
        new_x = self.x + direction[0]
        new_y = self.y + direction[1]
        new_pos = self.board[new_x, new_y]
        if new_pos.pushable and pushing:
            new_pos.move(direction, pushing, count - 1)

        self.board[self.x, self.y] = self.previous if self.previous else Empty(self.board, (self.x, self.y))
        self.x = new_x
        self.y = new_y
        self.previous = self.board[self.x, self.y]
        self.board[self.x, self.y] = self
        self.moved(direction)

    def kill(self):
        super().kill()
        del self.board[self.x, self.y]

    def moved(self, direction):
        pass


    def __init_subclass__(cls):
        if "tile_char" in cls.__dict__:
            cls.tile_registry[cls.tile_char] = cls


class Empty(GameObject):
    color = 128, 128, 128
    tile_char = " "


class Wall(GameObject):
    color = 255, 255, 0
    traversable = False
    tile_char = "*"


class Dirty(GameObject):
    color = 0, 0, 255
    traversable = True
    pushable = True
    tile_char = "A"

    def moved(self, direction):
        if not (direction[0] or direction[1]):
            return

        equal_neighbours = self.get_equal_neighbours()
        if len(equal_neighbours) < 4:
            return
        score_bonus = 1
        score = 0
        for neighbour in equal_neighbours:
            score += score_bonus
            score_bonus *= 2
            neighbour.kill()

        self.board.score += score
        print(self.board.score)

    def get_equal_neighbours(self, group = None, seen=None):
        if seen == None:
            seen = {(self.x, self.y),}
            group = {self,}
        for direction in ((-1, 0), (1, 0), (0, -1), (-0, 1)):
            new_pos = self.x + direction[0], self.y + direction[1]
            if new_pos in seen:
                continue
            obj = self.board.__getitem__(new_pos)
            if type(obj) == type(self):
                group.add(obj)
                seen.add(new_pos)
                obj.get_equal_neighbours(group, seen)
        return group


class Board:
    def __init__(self, width=32, height=24, mapname=""):
        self.data = [None] * width * height
        self.width = width
        self.height = height
        self.clear()
        if map:
            self.load_map(mapname)
        self.score = 0

    def clear(self):
        for x, y, _ in self:
            empty = Empty(self, (x, y))


    def load_map(self, mapname):
        with resources.open_text("homekeeper.maps", mapname) as map_:
            for y, row in enumerate(map_):
                for x, char in enumerate(row):
                    if x >= self.width:
                        continue
                    cls = GameObject.tile_registry.get(char, Empty)
                    self[x, y] = cls(self, (x, y))


    def __getitem__(self, item):
        return self.data[item[1] * self.width + item[0]]

    def __setitem__(self, item, value):
        self.data[item[1] * self.width + item[0]] = value

    def __delitem__(self, item):
        self[item] = Empty(self, item)

    def __iter__(self):
        for x in range(self.width):
            for y in range(self.height):
                yield x, y, self[x, y]

    def draw(self, screen):
        pass

    def update(self, screen):
        for x, y, block in self:
            screen.blit(block.image, (block.x * BLOCK_SIZE, block.y * BLOCK_SIZE))


class Character(GameObject):
    color = 255, 0, 0
    traversable = False
    pushable = False
    move_delay = 4

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.move_count = self.move_delay


    def update(self, keys):
        self.move_count -= 1

        if self.move_count > 0:
            return
        direction = (keys[pg.K_RIGHT] - keys[pg.K_LEFT]), (keys[pg.K_DOWN] - keys[pg.K_UP])

        if self.movable(direction, keys[pg.K_SPACE], 2):
            if direction[0] or direction[1]:
                self.move_count = self.move_delay * (1 + keys[pg.K_SPACE])
            self.move(direction, keys[pg.K_SPACE], 1)



def frame_clear():
    SCREEN.fill((0, 0, 0))


def scene_main():
    clk = pg.time.Clock()
    board = Board(mapname="bedroom.txt")
    character = Character(board, (1, 1))


    while True:
        frame_clear()
        keys = handle_input()
        character.update(keys)
        board.update(SCREEN)
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

