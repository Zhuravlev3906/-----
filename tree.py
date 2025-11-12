import sys
import time
import shutil
import signal
import random
import math

try:
    import colorama
    colorama.just_fix_windows_console()
except Exception:
    pass


class Terminal:
    CSI = "\x1b["
    RESET = "\x1b[0m"
    HIDE_CURSOR = CSI + "?25l"
    SHOW_CURSOR = CSI + "?25h"
    CLEAR = CSI + "2J" + CSI + "H"

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        return f"\x1b[38;2;{r};{g};{b}m"

    @staticmethod
    def move_to(row: int, col: int) -> str:
        return f"{Terminal.CSI}{row};{col}H"

    @staticmethod
    def get_size():
        size = shutil.get_terminal_size(fallback=(80, 24))
        return size.columns, size.lines

    @staticmethod
    def write(text: str):
        sys.stdout.write(text)

    @staticmethod
    def flush():
        sys.stdout.flush()


class Colors:
    GREEN = (0, 140, 0)
    RED = (255, 60, 60)
    CYAN = (80, 200, 255)
    YELLOW = (255, 210, 60)
    WHITE = (255, 255, 255)
    BROWN = (139, 69, 19)
    BRIGHT_GREEN = (0, 255, 0)
    MIN_BRIGHTNESS = 0.15
    BLUE = (60, 100, 255)
    PURPLE = (186, 85, 211)
    TURQUOISE = (64, 224, 208)
    PINK = (255, 105, 180)
    ORANGE = (255, 165, 0)


class Tree:
    LINES = [
        "      /\\",
        "     /  \\",
        "    /  o \\",
        "    /    \\",
        "   / o   o\\",
        "  /        \\",
        "  /    o   \\",
        " /          \\",
        "/  o       o \\",
        "      | |",
    ]

    def __init__(self):
        self._bulb_positions = self._find_bulb_positions()
        self._trunk_line_index = len(self.LINES) - 1

    def _find_bulb_positions(self):
        positions = []
        for line_idx, line in enumerate(self.LINES):
            for col_idx, char in enumerate(line):
                if char == 'o':
                    positions.append((line_idx, col_idx))
        return positions

    @property
    def bulb_positions(self):
        return self._bulb_positions

    @property
    def width(self):
        return max(len(line) for line in self.LINES)

    @property
    def height(self):
        return len(self.LINES)

    def get_char_at(self, line_idx: int, col_idx: int) -> str | None:
        if line_idx < 0 or line_idx >= len(self.LINES):
            return None
        line = self.LINES[line_idx]
        if col_idx < 0 or col_idx >= len(line):
            return None
        char = line[col_idx]
        return None if char == ' ' else char

    def is_trunk_char(self, line_idx: int, char: str) -> bool:
        return line_idx == self._trunk_line_index and char == '|'

    def draw(self, base_row: int, base_col: int):
        Terminal.write(Terminal.CLEAR)
        green = Terminal.rgb(*Colors.GREEN)
        brown = Terminal.rgb(*Colors.BROWN)

        for line_idx, line in enumerate(self.LINES):
            if line_idx == self._trunk_line_index:
                rendered = []
                for char in line:
                    if char == '|':
                        rendered.append(brown + '|' + Terminal.RESET)
                    else:
                        rendered.append(char)
                Terminal.write(Terminal.move_to(base_row + line_idx, base_col) + ''.join(rendered))
            else:
                Terminal.write(Terminal.move_to(base_row + line_idx, base_col) + green + line + Terminal.RESET)
        Terminal.flush()

    def redraw_char_at(self, abs_row: int, abs_col: int, base_row: int, base_col: int):
        line_idx = abs_row - base_row
        col_idx = abs_col - base_col
        char = self.get_char_at(line_idx, col_idx)

        if char is None:
            return False

        if self.is_trunk_char(line_idx, char):
            Terminal.write(Terminal.move_to(abs_row, abs_col) + Terminal.rgb(*Colors.BROWN) + '|' + Terminal.RESET)
        else:
            Terminal.write(Terminal.move_to(abs_row, abs_col) + Terminal.rgb(*Colors.GREEN) + char + Terminal.RESET)
        return True


class Message:
    TEXT = "С Новым годом!!!"

    def __init__(self, tree: Tree):
        self._tree = tree

    def _get_position(self, base_row: int, base_col: int):
        msg_row = base_row + self._tree.height + 1
        msg_col = base_col + max(0, (self._tree.width - len(self.TEXT)) // 2)
        return msg_row, msg_col

    def draw(self, base_row: int, base_col: int):
        msg_row, msg_col = self._get_position(base_row, base_col)
        Terminal.write(Terminal.move_to(msg_row, msg_col) + Terminal.rgb(*Colors.BRIGHT_GREEN) + self.TEXT + Terminal.RESET)
        Terminal.flush()

    def get_char_at(self, abs_row: int, abs_col: int, base_row: int, base_col: int) -> str | None:
        msg_row, msg_col = self._get_position(base_row, base_col)
        if abs_row != msg_row:
            return None
        col_idx = abs_col - msg_col
        if col_idx < 0 or col_idx >= len(self.TEXT):
            return None
        return self.TEXT[col_idx]

    def redraw_char_at(self, abs_row: int, abs_col: int, base_row: int, base_col: int):
        char = self.get_char_at(abs_row, abs_col, base_row, base_col)
        if char is not None:
            Terminal.write(Terminal.move_to(abs_row, abs_col) + Terminal.rgb(*Colors.BRIGHT_GREEN) + char + Terminal.RESET)
            return True
        return False


class Bulb:
    PHASE_OFF = 'off'
    PHASE_FADE_IN = 'fade_in'
    PHASE_ON = 'on'
    PHASE_FADE_OUT = 'fade_out'

    def __init__(self, colors: list, base_fade_in: float, base_on: float, base_fade_out: float):
        self.phase = self.PHASE_OFF
        self.time = random.uniform(0.0, 2.0)
        self.off_delay = random.uniform(0.5, 2.0)
        self.colors = colors[:]
        self.color_index = random.randrange(len(colors))
        self.fade_in_duration = base_fade_in * random.uniform(0.7, 1.3)
        self.on_duration = base_on * random.uniform(0.7, 1.3)
        self.fade_out_duration = base_fade_out * random.uniform(0.7, 1.3)

    def update(self, delta_time: float):
        if self.phase == self.PHASE_OFF:
            self.time += delta_time
            if self.time >= self.off_delay:
                self.phase = self.PHASE_FADE_IN
                self.time = 0.0
                self.fade_in_duration = random.uniform(0.7, 1.3) * 1.5
                self.on_duration = random.uniform(0.7, 1.3) * 3.0
                self.fade_out_duration = random.uniform(0.7, 1.3) * 1.5

        elif self.phase == self.PHASE_FADE_IN:
            self.time += delta_time
            if self.time >= self.fade_in_duration:
                self.phase = self.PHASE_ON
                self.time = 0.0
            else:
                pass

        elif self.phase == self.PHASE_ON:
            self.time += delta_time
            if self.time >= self.on_duration:
                self.phase = self.PHASE_FADE_OUT
                self.time = 0.0

        elif self.phase == self.PHASE_FADE_OUT:
            self.time += delta_time
            if self.time >= self.fade_out_duration:
                self.color_index = (self.color_index + 1) % len(self.colors)
                self.phase = self.PHASE_OFF
                self.time = 0.0
                self.off_delay = random.uniform(0.5, 2.0)

    def get_brightness_factor(self) -> float:
        if self.phase == self.PHASE_OFF:
            return Colors.MIN_BRIGHTNESS
        elif self.phase == self.PHASE_FADE_IN:
            progress = min(1.0, self.time / self.fade_in_duration)
            exp_factor = 1.0 - math.exp(-5.0 * progress)
            return Colors.MIN_BRIGHTNESS + (1.0 - Colors.MIN_BRIGHTNESS) * exp_factor
        elif self.phase == self.PHASE_ON:
            return 1.0
        elif self.phase == self.PHASE_FADE_OUT:
            progress = min(1.0, self.time / self.fade_out_duration)
            exp_factor = math.exp(-5.0 * progress)
            return Colors.MIN_BRIGHTNESS + (1.0 - Colors.MIN_BRIGHTNESS) * exp_factor
        return Colors.MIN_BRIGHTNESS

    def get_color(self) -> tuple:
        base_color = self.colors[self.color_index]
        factor = self.get_brightness_factor()
        r, g, b = base_color
        scaled_r = int(r * factor)
        scaled_g = int(g * factor)
        scaled_b = int(b * factor)

        cool_r = max(0, int(scaled_r * 0.95))
        cool_g = max(0, int(scaled_g * 0.98))
        cool_b = min(255, int(scaled_b * 1.10) + 8)
        return (cool_r, cool_g, cool_b)


class Snowflake:
    CHARS = ['.', '*', '·']
    DENSITY = 0.015

    def __init__(self, cols: int, rows: int):
        self.col = random.randint(1, cols)
        self.y = random.uniform(1, rows)
        self.speed = random.uniform(5.0, 15.0)
        self.char = random.choice(self.CHARS)
        self.prev_row = None

    def update(self, delta_time: float, rows: int, cols: int):
        self.y += self.speed * delta_time
        if self.y > rows:
            self.y = 1
            self.col = random.randint(1, cols)
            self.speed = random.uniform(5.0, 15.0)
            self.char = random.choice(self.CHARS)

    def get_position(self) -> tuple[int, int]:
        return int(self.y), self.col


class TreeAnimation:
    def __init__(self):
        self.tree = Tree()
        self.message = Message(self.tree)
        self.bulbs = []
        self.snowflakes = []
        self.base_row = 0
        self.base_col = 0
        self.cols = 0
        self.rows = 0
        self.frame_dt = 1.0 / 30.0

    def _init_bulbs(self):
        colors = [
            Colors.RED,
            Colors.GREEN,
            Colors.CYAN,
            Colors.BLUE,
            Colors.YELLOW,
            Colors.WHITE,
            Colors.PURPLE,
            Colors.TURQUOISE,
            Colors.PINK,
            Colors.ORANGE,
        ]
        for _ in self.tree.bulb_positions:
            bulb = Bulb(colors, 1.5, 3.0, 1.5)
            self.bulbs.append(bulb)

    def _init_snowflakes(self):
        self.cols, self.rows = Terminal.get_size()
        count = max(20, int(self.cols * self.rows * Snowflake.DENSITY))
        self.snowflakes = [Snowflake(self.cols, self.rows) for _ in range(count)]

    def _center_tree(self):
        self.cols, self.rows = Terminal.get_size()
        tree_width = self.tree.width
        tree_height = self.tree.height
        self.base_row = max(1, (self.rows - tree_height) // 2 + 1)
        self.base_col = max(1, (self.cols - tree_width) // 2 + 1)

    def _is_occupied(self, row: int, col: int) -> bool:
        if self.tree.get_char_at(row - self.base_row, col - self.base_col) is not None:
            return True
        if self.message.get_char_at(row, col, self.base_row, self.base_col) is not None:
            return True
        return False

    def _redraw_background_at(self, row: int, col: int):
        if self.tree.redraw_char_at(row, col, self.base_row, self.base_col):
            return
        if self.message.redraw_char_at(row, col, self.base_row, self.base_col):
            return
        Terminal.write(Terminal.move_to(row, col) + ' ')

    def _update_snow(self):
        for flake in self.snowflakes:
            if flake.prev_row is not None:
                pr, pc = flake.prev_row, flake.col
                if 1 <= pr <= self.rows and 1 <= pc <= self.cols:
                    self._redraw_background_at(pr, pc)

            flake.update(self.frame_dt, self.rows, self.cols)
            r_int, c_int = flake.get_position()
            flake.prev_row = r_int

            if not self._is_occupied(r_int, c_int) and 1 <= r_int <= self.rows and 1 <= c_int <= self.cols:
                color = Terminal.rgb(*Colors.WHITE)
                Terminal.write(Terminal.move_to(r_int, c_int) + color + flake.char + Terminal.RESET)

    def _update_bulbs(self):
        for idx, (line_idx, col_idx) in enumerate(self.tree.bulb_positions):
            bulb = self.bulbs[idx]
            bulb.update(self.frame_dt)

            color = bulb.get_color()
            color_seq = Terminal.rgb(*color)
            abs_row = self.base_row + line_idx
            abs_col = self.base_col + col_idx
            Terminal.write(Terminal.move_to(abs_row, abs_col) + color_seq + 'o' + Terminal.RESET)

    def _setup_signal_handler(self):
        def cleanup(*_):
            Terminal.write(Terminal.RESET + Terminal.SHOW_CURSOR + "\nСчастливого рождества!\n")
            Terminal.flush()
            try:
                signal.signal(signal.SIGINT, signal.SIG_DFL)
            except Exception:
                pass
            raise SystemExit(0)

        try:
            signal.signal(signal.SIGINT, lambda *_: cleanup())
        except Exception:
            pass

    def run(self):
        self._init_bulbs()
        self._center_tree()
        self._init_snowflakes()
        self._setup_signal_handler()

        Terminal.write(Terminal.HIDE_CURSOR)
        Terminal.flush()

        try:
            self.tree.draw(self.base_row, self.base_col)
            self.message.draw(self.base_row, self.base_col)

            last_size = Terminal.get_size()

            while True:
                size_now = Terminal.get_size()
                if size_now != last_size:
                    self._center_tree()
                    self.tree.draw(self.base_row, self.base_col)
                    self.message.draw(self.base_row, self.base_col)
                    last_size = size_now
                    self._init_snowflakes()

                self._update_snow()
                self._update_bulbs()

                Terminal.flush()
                time.sleep(self.frame_dt)

        except KeyboardInterrupt:
            Terminal.write(Terminal.RESET + Terminal.SHOW_CURSOR + "\nСчастливого рождества!\n")
            Terminal.flush()
        finally:
            Terminal.write(Terminal.RESET + Terminal.SHOW_CURSOR + "\n")
            Terminal.flush()


def main():
    animation = TreeAnimation()
    animation.run()


if __name__ == "__main__":
    main()
