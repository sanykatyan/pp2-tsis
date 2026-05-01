import json
import random
from pathlib import Path

import pygame

from db import get_personal_best, save_result

WIDTH = 900
HEIGHT = 700
TOP_BAR = 70
CELL = 25

COLS = WIDTH // CELL
ROWS = (HEIGHT - TOP_BAR) // CELL

WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
GREEN = (40, 190, 90)
DARK_GREEN = (30, 120, 50)
YELLOW = (245, 220, 70)
RED = (140, 0, 0)
BLUE = (60, 120, 240)
GRAY = (110, 110, 110)

def load_settings():
    default_settings = {
        "snake_color": [40, 190, 90],
        "grid": True,
        "sound": True
    }

    path = Path("settings.json")

    if not path.exists():
        save_settings(default_settings)
        return default_settings

    try:
        file = open(path, "r", encoding="utf-8")
        settings = json.load(file)
        file.close()
    except:
        settings = default_settings

    return settings

def save_settings(settings):
    file = open("settings.json", "w", encoding="utf-8")
    json.dump(settings, file, indent=4)
    file.close()

class SnakeGame:
    def __init__(self, username, settings):
        self.username = username
        self.settings = settings

        self.snake = [
            (COLS // 2, ROWS // 2),
            (COLS // 2 - 1, ROWS // 2),
            (COLS // 2 - 2, ROWS // 2)
        ]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.score = 0
        self.level = 1
        self.eaten_food = 0
        self.speed = 8
        self.move_timer = 0

        self.food = None
        self.food_value = 1
        self.food_time = 0
        self.food_lifetime = 7000

        self.poison = None
        self.poison_time = 0
        self.poison_lifetime = 9000

        self.power = None
        self.power_type = None
        self.power_time = 0
        self.last_power_spawn_time = pygame.time.get_ticks()

        self.active_power = None
        self.active_until = 0
        self.shield = False

        self.obstacles = []

        self.game_over = False
        self.saved = False

        self.personal_best = get_personal_best(self.username)

        self.spawn_food()
        self.spawn_poison()

    def is_cell_free(self, cell):
        if cell in self.snake:
            return False

        if cell in self.obstacles:
            return False

        if cell == self.food:
            return False

        if cell == self.poison:
            return False

        if cell == self.power:
            return False

        return True

    def get_random_free_cell(self):
        for attempt in range(1000):
            x = random.randrange(1, COLS - 1)
            y = random.randrange(1, ROWS - 1)
            cell = (x, y)

            if self.is_cell_free(cell):
                return cell

        return None

    def spawn_food(self):
        self.food = self.get_random_free_cell()
        self.food_value = random.choice([1, 2, 3])
        self.food_time = pygame.time.get_ticks()

    def spawn_poison(self):
        self.poison = self.get_random_free_cell()
        self.poison_time = pygame.time.get_ticks()

    def spawn_power(self):
        self.power = self.get_random_free_cell()
        self.power_type = random.choice(["speed", "slow", "shield"])
        self.power_time = pygame.time.get_ticks()

    def cell_is_near_head(self, cell):
        head = self.snake[0]

        if cell == head:
            return True

        if cell == (head[0] + 1, head[1]):
            return True

        if cell == (head[0] - 1, head[1]):
            return True

        if cell == (head[0], head[1] + 1):
            return True

        if cell == (head[0], head[1] - 1):
            return True

        return False

    def make_obstacles(self):
        self.obstacles = []

        count = 4 + self.level * 2

        if count > 18:
            count = 18

        while len(self.obstacles) < count:
            x = random.randrange(2, COLS - 2)
            y = random.randrange(2, ROWS - 2)
            cell = (x, y)

            if cell in self.snake:
                continue

            if self.cell_is_near_head(cell):
                continue

            if cell in self.obstacles:
                continue

            self.obstacles.append(cell)

    def change_direction(self, new_direction):
        opposite_direction = (new_direction[0] * -1, new_direction[1] * -1)

        if opposite_direction == self.direction:
            return

        self.next_direction = new_direction

    def get_current_speed(self):
        current_speed = self.speed
        now = pygame.time.get_ticks()

        if self.active_power == "speed":
            if now < self.active_until:
                current_speed = current_speed + 5
            else:
                self.active_power = None

        if self.active_power == "slow":
            if now < self.active_until:
                current_speed = current_speed - 4

                if current_speed < 4:
                    current_speed = 4
            else:
                self.active_power = None

        return current_speed

    def finish_game(self):
        if self.shield:
            self.shield = False
            self.active_power = None
            return

        self.game_over = True

        if not self.saved:
            save_result(self.username, self.score, self.level)
            self.saved = True

    def eat_poison(self):
        for i in range(2):
            if len(self.snake) > 1:
                self.snake.pop()

        if len(self.snake) <= 1:
            self.finish_game()

        self.spawn_poison()

    def activate_power(self):
        now = pygame.time.get_ticks()

        if self.power_type == "speed":
            self.active_power = "speed"
            self.active_until = now + 5000
            self.shield = False

        elif self.power_type == "slow":
            self.active_power = "slow"
            self.active_until = now + 5000
            self.shield = False

        elif self.power_type == "shield":
            self.active_power = "shield"
            self.shield = True

        self.power = None
        self.power_type = None

    def update_level(self):
        if self.eaten_food >= self.level * 4:
            self.level = self.level + 1
            self.speed = self.speed + 1

            if self.level >= 3:
                self.make_obstacles()

    def update_timers(self):
        now = pygame.time.get_ticks()

        if now - self.food_time > self.food_lifetime:
            self.spawn_food()

        if now - self.poison_time > self.poison_lifetime:
            self.spawn_poison()

        if self.power is not None:
            if now - self.power_time > 8000:
                self.power = None
                self.power_type = None

        if self.power is None:
            if now - self.last_power_spawn_time > 10000:
                self.spawn_power()
                self.last_power_spawn_time = now

    def get_new_head(self):
        head = self.snake[0]

        head_x = head[0]
        head_y = head[1]

        dx = self.direction[0]
        dy = self.direction[1]

        new_head = (head_x + dx, head_y + dy)

        return new_head

    def has_collision(self, head):
        if head[0] < 0:
            return True

        if head[0] >= COLS:
            return True

        if head[1] < 0:
            return True

        if head[1] >= ROWS:
            return True

        if head in self.snake:
            return True

        if head in self.obstacles:
            return True

        return False

    def move(self):
        self.direction = self.next_direction
        new_head = self.get_new_head()

        if self.has_collision(new_head):
            self.finish_game()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score = self.score + self.food_value * 10
            self.eaten_food = self.eaten_food + 1
            self.spawn_food()
            self.update_level()

        elif new_head == self.poison:
            self.eat_poison()

        elif new_head == self.power:
            self.activate_power()
            self.snake.pop()

        else:
            self.snake.pop()

    def update(self, dt):
        if self.game_over:
            return

        self.update_timers()

        self.move_timer = self.move_timer + dt

        interval = 1000 / self.get_current_speed()

        if self.move_timer >= interval:
            self.move_timer = 0
            self.move()

    def get_cell_rect(self, cell):
        x = cell[0] * CELL
        y = TOP_BAR + cell[1] * CELL

        return pygame.Rect(x, y, CELL, CELL)

    def draw_cell(self, screen, cell, color):
        rect = self.get_cell_rect(cell)
        rect = rect.inflate(-2, -2)

        pygame.draw.rect(screen, color, rect)

    def draw_grid(self, screen):
        if not self.settings["grid"]:
            return

        x = 0

        while x < WIDTH:
            pygame.draw.line(screen, (225, 225, 225), (x, TOP_BAR), (x, HEIGHT))
            x = x + CELL

        y = TOP_BAR

        while y < HEIGHT:
            pygame.draw.line(screen, (225, 225, 225), (0, y), (WIDTH, y))
            y = y + CELL

    def draw_hud(self, screen, font):
        pygame.draw.rect(screen, (45, 45, 45), (0, 0, WIDTH, TOP_BAR))

        power_text = "none"

        if self.active_power is not None:
            power_text = self.active_power

        info = (
            "Player: " + self.username +
            " | Score: " + str(self.score) +
            " | Level: " + str(self.level) +
            " | Best: " + str(self.personal_best) +
            " | Power: " + power_text
        )

        label = font.render(info, True, WHITE)
        screen.blit(label, (15, 23))

    def draw(self, screen, font):
        screen.fill(WHITE)

        self.draw_grid(screen)

        for obstacle in self.obstacles:
            self.draw_cell(screen, obstacle, GRAY)

        if self.food is not None:
            self.draw_cell(screen, self.food, YELLOW)

        if self.poison is not None:
            self.draw_cell(screen, self.poison, RED)

        if self.power is not None:
            self.draw_cell(screen, self.power, BLUE)

        snake_color = tuple(self.settings["snake_color"])

        for index in range(len(self.snake)):
            cell = self.snake[index]

            if index == 0:
                self.draw_cell(screen, cell, DARK_GREEN)
            else:
                self.draw_cell(screen, cell, snake_color)

        if self.shield:
            head_rect = self.get_cell_rect(self.snake[0])
            pygame.draw.ellipse(screen, BLUE, head_rect.inflate(12, 12), 3)

        self.draw_hud(screen, font)
