import math
import random
import tempfile
import sys
from importlib import resources

import pygame

from .levels import levels

pg = pygame

DISPLAY_SIZE = WIDTH, HEIGHT = 800, 600

BG_COLOR = 0, 0, 0

BLOCK_SIZE = WIDTH / 32

SCREEN = None

class Interrupt(BaseException):
    pass


class LevelComplete(Interrupt):
    pass


class GameOver(Interrupt):
    pass


def init():
    global SCREEN, FONT
    pygame.init()
    SCREEN = pg.display.set_mode(DISPLAY_SIZE)

    # Workaround to read font file even from packaged gamefile:
    with tempfile.NamedTemporaryFile() as f_:
        f_.write(resources.open_binary("homekeeper.fonts", "pixelated.ttf").read())
        f_.seek(0)
        FONT = pygame.font.Font(f_.name, int(BLOCK_SIZE * 4))


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

    def update(self):
        pass

    def kill(self):
        super().kill()
        del self.board[self.x, self.y]

    def moved(self, direction):
        pass


    def __init_subclass__(cls):
        if "tile_char" in cls.__dict__:
            cls.tile_registry[cls.tile_char] = cls
        cls.image = pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE))
        cls.image.fill(cls.color)

vanish_states = "solid blinking dead".split()

class Vanishable:
    """Mixin class for things to go poof"""

    vanish_frames = 10
    blink_frame_count = 3

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.state = "solid"
        self.blank_image = Empty.image


    def update(self):
        if self.state == "blinking":
            if not (self.count_down - self.vanish_frames) % self.blink_frame_count:
                self.image = self.blank_image if self.image is self.original_image else self.original_image
            self.count_down -= 1

            if self.count_down == 0:
                self.state = "dead"
                self.final_kill()
        super().update()

    def kill(self):
        self.count_down = self.vanish_frames
        self.state = "blinking"
        self.original_image = self.image
        self.pushable = False

    def final_kill(self):
        super().kill()


class Empty(GameObject):
    color = 128, 128, 128
    tile_char = " "


class Wall(GameObject):
    color = 255, 255, 0
    traversable = False
    tile_char = "*"


class Dirty(Vanishable, GameObject):
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
        self.board.level.killed_blocks += len(equal_neighbours)

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


class Dirty2(Dirty):
    color = 0, 128, 255
    tile_char = "B"


class Level:
    def __init__(self, board, level_number):
        self.board = board
        self.__dict__.update(levels[level_number])
        self.start_time = pygame.time.get_ticks()
        self.killed_blocks = 0
        self.pre_pop_had_run = False
        classes = []
        for class_name, chances in self.classes:
            class_ = globals()[class_name]
            classes.extend([class_] * chances)

        #self.previous_time = 0

        self.classes = classes

    def pre_pop(self):
        for i in range(self.starting_blocks):
            self.pop_block()
        self.pre_pop_had_run = True

    def pop_block(self):
        class_ = random.choice(self.classes)
        counter = 0
        while True:
            x = random.randrange(0, self.board.width)
            y = random.randrange(0, self.board.height)
            if type(self.board[x, y]) == Empty:
                break
            counter += 1
            if counter > 3 * self.board.width * self.board.height:
                raise GameOver

        block = class_(self.board, (x, y))
        self.last_block = pygame.time.get_ticks() / 1000
        time_variation = self.dirty_pop_noise / 2
        self.next_block = self.last_block + (self.dirty_pop_rate + random.uniform(-time_variation, +time_variation))

    @property
    def remaining_time(self):
        return math.floor(self.total_time - self.elapsed_time)

    @property
    def elapsed_time(self):
        return (pygame.time.get_ticks() - self.start_time) / 1000

    def update(self):
        if not self.pre_pop_had_run:
            self.pre_pop()

        if self.elapsed_time >= self.next_block:
            self.pop_block()

        #if round(self.elapsed_time) > self.previous_time:
            #self.previous_time = round(self.elapsed_time)


        self.check_goals()

    def check_goals(self):
        if self.killed_blocks >= self.goal:
            raise LevelComplete
        if self.elapsed_time > self.total_time:
            raise GameOver


class Display:
    color = 0, 0, 0

    def __init__(self, board):
        self.board = board

    def update(self):
        goal_str = '/'.join(map(str, (self.board.level.killed_blocks, self.board.level.goal)))
        text = f"{self.board.score:<8d}{goal_str:^7s}{self.board.level.remaining_time:>4d}"
        rendered = FONT.render(text, True, self.color)
        SCREEN.blit(rendered, (WIDTH // 5, SCREEN.get_height() - rendered.get_height()))


class Board:
    def __init__(self, width=32, height=24, level_number=0):
        self.data = [None] * width * height
        self.width = width
        self.height = height
        self.clear()
        self.level = Level(self, level_number)
        self.display = Display(self)
        self.load_map(self.level.map)
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
        try:
            return self.data[item[1] * self.width + item[0]]
        except IndexError:
            print(f"Index out of range: {item!r}", file=sys.stderr)
            return Empty(self, (0, 0))

    def __setitem__(self, item, value):
        self.data[item[1] * self.width + item[0]] = value

    def __delitem__(self, item):
        self[item] = Empty(self, item)

    def __iter__(self):
        for x in range(self.width):
            for y in range(self.height):
                yield x, y, self[x, y]


    def update(self, screen):
        self.level.update()
        for x, y, block in self:
            block.update()
            screen.blit(block.image, (block.x * BLOCK_SIZE, block.y * BLOCK_SIZE))
        self.display.update()


class Character(GameObject):
    color = 255, 0, 0
    traversable = False
    pushable = False
    move_delay = 4
    strength = 2

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.move_count = self.move_delay


    def update_pos(self, keys):
        self.move_count -= 1

        if self.move_count > 0:
            return
        direction = (keys[pg.K_RIGHT] - keys[pg.K_LEFT]), (keys[pg.K_DOWN] - keys[pg.K_UP])

        if self.movable(direction, keys[pg.K_SPACE], self.strength):
            if direction[0] or direction[1]:
                self.move_count = self.move_delay * (1 + keys[pg.K_SPACE])
            self.move(direction, keys[pg.K_SPACE], self.strength)



def frame_clear():
    SCREEN.fill((0, 0, 0))


def scene_main():
    clk = pg.time.Clock()
    board = Board(level_number=0)
    character = Character(board, (1, 1))


    while True:
        frame_clear()
        keys = handle_input()
        character.update_pos(keys)
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

