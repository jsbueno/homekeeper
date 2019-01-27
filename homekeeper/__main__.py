import heapq
import math
import random
import tempfile
import sys
from importlib import resources


import pygame

from .levels import levels
from .sound import synthesize_sounds

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

class GameComplete(GameOver):
    pass


class UserQuit(Interrupt):
    pass


def init():
    global SCREEN, SOUNDS, FONT, SMALL_FONT, BIG_FONT
    pygame.mixer.init(22100, -16, 2, 64)
    pygame.init()
    FONT = load_font("BalooThambi-Regular.ttf", (60, ))
    BIG_FONT = load_font("BalooThambi-Regular.ttf", (100, ))
    SMALL_FONT = load_font("BalooThambi-Regular.ttf", (40, ))
    SCREEN = pg.display.set_mode(DISPLAY_SIZE)


    SOUNDS = synthesize_sounds()

    reload_images()

def reload_images():

    for cls in GameObject.tile_registry.values():
        if not 'image_file' in cls.__dict__:
            cls.image = pygame.surface.Surface((BLOCK_SIZE, BLOCK_SIZE))
            cls.image.fill(cls.color)
            continue
        # cls.image = load_image(cls.image_file, size=BLOCK_SIZE)
        cls.image = load_image(cls.image_file, size=BLOCK_SIZE)



def _load_resource(filename, module_name, pg_builder, args):
    # Workaround to read resource files even from packaged gamefile:
    with tempfile.NamedTemporaryFile() as f_:
        f_.write(resources.open_binary("homekeeper." + module_name, filename).read())
        f_.seek(0)
        return pg_builder(f_.name, *args)


def load_font(filename, args):
    return _load_resource(filename, "fonts", pygame.font.Font, args)


def load_image(filename, size=None):
    img = _load_resource(filename, "images", pygame.image.load, ())
    if size:
        img = pygame.transform.rotozoom(img, 0, size/img.get_width())
    return img



def handle_input():
    pg.event.pump()
    keys = pg.key.get_pressed()
    if keys[pg.K_ESCAPE]:
        raise UserQuit
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

    def draw(self, screen):
        pos = (self.x * BLOCK_SIZE, self.y * BLOCK_SIZE)
        if not hasattr(self, "bg_image"):
            new = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
            new.fill(self.color)
            self.bg_image = new
        screen.blit(self.bg_image, pos)

        if self.previous:
            screen.blit(self.previous.image, pos)
        screen.blit(self.image, pos)

    def __init_subclass__(cls):
        if "tile_char" in cls.__dict__:
            cls.tile_registry[cls.tile_char] = cls


vanish_states = "solid blinking dead".split()

class Vanishable:
    """Mixin class for things to go poof"""

    vanish_frames = 30
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

class Forniture(GameObject):
    color = 192, 100, 0
    traversable = False
    tile_char = "!"


class Dirty(Vanishable, GameObject):
    color = Empty.color
    traversable = True
    pushable = True
    tile_char = "A"
    image_file = "blue_dirty.png"
    number_to_vanish = 4

    def moved(self, direction):
        if not (direction[0] or direction[1]):
            return
        SOUNDS["swype"].play()
        self.check_vanish()

    def check_vanish(self):
        global SCORE
        equal_neighbours = self.get_equal_neighbours()
        if len(equal_neighbours) < self.number_to_vanish:
            return
        score_bonus = 1
        score = 0
        for neighbour in equal_neighbours:
            score += score_bonus
            score_bonus *= 2
            neighbour.kill()

        SCORE += score
        SOUNDS["vanish"].play()
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
    image_file = "cyan_dirty.png"
    tile_char = "B"

class Dirty3(Dirty):
    number_to_vanish = 5
    image_file = "yellow_dirty.png"
    tile_char = "C"

class Dirty4(Dirty):
    image_file = "red_dirty.png"
    tile_char = "D"

class Dirty5(Dirty):
    image_file = "black_dirty.png"
    tile_char = "E"


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
        block.check_vanish()
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

        if pg.time.get_ticks() / 1000 >= self.next_block:
            self.pop_block()

        #if round(self.elapsed_time) > self.previous_time:
            #self.previous_time = round(self.elapsed_time)

        self.check_goals()


    def check_goals(self):
        if self.killed_blocks >= self.goal and not self.board.level_up_triggered:
            SOUNDS["level_up"].play()
            self.board.level_up_triggered = True
            self.board.add_event(time_offset=1, event="LevelComplete")
        if self.elapsed_time > self.total_time:
            raise GameOver


class Display:
    color = 0, 0, 0

    def __init__(self, board):
        self.board = board
        self.x_offset = None
        self.previous_text = ""

    def update(self):
        goal_str = '/'.join(map(str, (self.board.level.killed_blocks, self.board.level.goal)))
        text = f"{SCORE:<6d}{goal_str:^15s}{self.board.level.remaining_time:>4d}"
        if text != self.previous_text:
            self.rendered = FONT.render(text, True, self.color)
            self.previous_text = text
        if self.x_offset is None:
            self.x_offset = (WIDTH - self.rendered.get_width()) // 2
            self.y_offset = HEIGHT - self.rendered.get_height()
        SCREEN.blit(self.rendered, (self.x_offset, self.y_offset))


class Board:
    def __init__(self, level_number=0):
        self.level = Level(self, level_number)
        self.load_map(self.level.map)
        self.display = Display(self)
        self.score = 0
        self.level_up_triggered = False
        self.events = []
        self.last_event = None

    def clear(self):
        for x, y, _ in self:
            empty = Empty(self, (x, y))


    def load_map(self, mapname):
        global BLOCK_SIZE
        with resources.open_text("homekeeper.maps", mapname) as map_:
            data = map_.read()
        map_ = data.split("\n")
        if not map_[-1].strip("\n"):
            map_.pop()

        self.width = len(map_[0])
        self.height = len(map_)

        self.data = [None] * self.width * self.height

        for y, row in enumerate(map_):
            for x, char in enumerate(row):
                if x >= self.width:
                    continue
                cls = GameObject.tile_registry.get(char, Empty)
                self[x, y] = cls(self, (x, y))

        BLOCK_SIZE = WIDTH // self.width
        reload_images()
        if hasattr(self, "display"):
            self.display.x_offset = None


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

    def add_event(self, time_offset, event):
        heapq.heappush(self.events, (pygame.time.get_ticks() + time_offset * 1000, event)   )

    def check_events(self):

        while self.events and pygame.time.get_ticks() >= self.events[0][0]:
            event = heapq.heappop(self.events)
            self.last_event = event
            if event[1] == "LevelComplete":
                raise LevelComplete

    def update(self, screen):
        self.level.update()
        self.check_events()
        for x, y, block in self:
            block.update()
            block.draw(screen)

        self.display.update()


class Character(GameObject):
    color = Empty.color
    traversable = False
    pushable = False
    move_delay = 4
    strength = 2
    image_file = "broom_0.png"
    tile_char = "#"

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


def scene_main(clk, level_number):

    board = Board(level_number=level_number)
    character = Character(board, (1, 1))


    while True:
        frame_clear()
        keys = handle_input()
        character.update_pos(keys)
        board.update(SCREEN)
        pg.display.flip()
        clk.tick(30)


def game_over_screen(clk, message):
    SCREEN.fill((127, 127, 127))
    text1 = message, BIG_FONT
    text2 = f"FINAL SCORE: {SCORE}", FONT
    text3 = "<Space> to play", SMALL_FONT
    text4 = "Q to quit", SMALL_FONT

    color_level = 255
    count = 0
    while True:
        pygame.event.pump()

        for i, (message, font) in enumerate((text1, text2, text3, text4)):
            rendered = font.render(message, True, (0, 0, color_level))
            y = HEIGHT // 6 * (1 + i)
            x = (WIDTH - rendered.get_width() ) // 2
            SCREEN.blit(rendered, (x, y))

        color_level -= 3
        color_level += 255 if color_level < 0 else 0

        keys = pygame.key.get_pressed()
        if keys[pg.K_q] or keys[pg.K_ESCAPE] and count > 15:
            raise UserQuit

        if keys[pg.K_SPACE] and count > 15:
            break

        count += 1
        pygame.display.flip()
        clk.tick(30)



def main():
    global SCORE
    init()
    clk = pg.time.Clock()
    try:
        while True:
            level_number = 0
            SCORE = 0
            try:
                while True:
                    try:
                        scene_main(clk, level_number)
                    except LevelComplete:
                        # TODO: level transition graphics
                        pygame.time.delay(1000)
                        level_number += 1
                        if level_number >= len(levels):
                            # Game Over: Win graphics
                            raise GameComplete
            except GameComplete:
                game_over_screen(clk, "Game Complete")

            except (GameOver, UserQuit):
                game_over_screen(clk, "Game Over")
    except Interrupt: # ESC or Q at GameOver screen
        pass
    finally:
        pg.display.quit()
        pg.quit()

    
if __name__ == "__main__":
    main()

