import random
import pygame

from storage import CAR_COLORS, DIFFICULTY, save_score

WIDTH = 900
HEIGHT = 700

ROAD_X = 220
ROAD_WIDTH = 460
LANES = 4
LANE_WIDTH = ROAD_WIDTH // LANES

PLAYER_Y = 570
FINISH_DISTANCE = 5000

class RacerGame:
    def __init__(self, username, settings):
        self.username = username

        difficulty = DIFFICULTY[settings["difficulty"]]

        self.speed = difficulty["speed"]
        self.spawn_rate = difficulty["spawn_rate"]
        self.car_color = CAR_COLORS[settings["car_color"]]

        self.player_lane = 1
        self.player_rect = pygame.Rect(0, PLAYER_Y, 52, 82)
        self.update_player_position()

        self.objects = []

        self.coins = 0
        self.power_bonus = 0
        self.score = 0
        self.distance = 0

        self.active_power = None
        self.power_end_time = 0
        self.shield = False
        self.slow_end_time = 0

        self.game_over = False
        self.finished = False
        self.saved = False

        now = pygame.time.get_ticks()
        self.last_traffic_time = now
        self.last_obstacle_time = now
        self.last_coin_time = now
        self.last_power_time = now
        self.last_event_time = now

        self.road_y = 0

    def update_player_position(self):
        lane_center = ROAD_X + self.player_lane * LANE_WIDTH + LANE_WIDTH // 2
        self.player_rect.centerx = lane_center

    def get_current_speed(self):
        current_speed = self.speed

        if self.distance > 1000:
            current_speed = current_speed + 1

        if self.distance > 2000:
            current_speed = current_speed + 1

        if self.distance > 3000:
            current_speed = current_speed + 1

        now = pygame.time.get_ticks()

        if self.active_power == "nitro":
            if now < self.power_end_time:
                current_speed = current_speed + 4
            else:
                self.active_power = None

        if now < self.slow_end_time:
            current_speed = current_speed - 3

            if current_speed < 3:
                current_speed = 3

        return current_speed

    def get_lane_rect(self, lane, y, width, height):
        x = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH // 2 - width // 2
        return pygame.Rect(x, y, width, height)

    def choose_lane(self):
        lane = random.randint(0, LANES - 1)

        if self.distance < 700:
            while lane == self.player_lane:
                lane = random.randint(0, LANES - 1)

        return lane

    def lane_is_busy(self, lane):
        for obj in self.objects:
            if obj["lane"] == lane and obj["rect"].y < 120:
                return True

        return False

    def add_object(self, kind, lane, width, height, value):
        if self.lane_is_busy(lane):
            return

        rect = self.get_lane_rect(lane, -height, width, height)

        obj = {
            "kind": kind,
            "lane": lane,
            "rect": rect,
            "value": value,
            "created": pygame.time.get_ticks(),
            "move_side": random.choice([-1, 1])
        }

        self.objects.append(obj)

    def spawn_traffic(self):
        lane = self.choose_lane()
        self.add_object("traffic", lane, 54, 82, 0)

    def spawn_obstacle(self):
        lane = self.choose_lane()
        kind = random.choice(["barrier", "oil", "pothole"])
        self.add_object(kind, lane, 58, 34, 0)

    def spawn_coin(self):
        lane = self.choose_lane()
        value = random.choice([1, 2, 3])
        self.add_object("coin", lane, 32, 32, value)

    def spawn_power(self):
        lane = self.choose_lane()
        kind = random.choice(["nitro", "shield", "repair"])
        self.add_object(kind, lane, 38, 38, 0)

    def spawn_road_event(self):
        lane = self.choose_lane()
        kind = random.choice(["moving_barrier", "speed_bump", "boost_strip"])
        self.add_object(kind, lane, 70, 30, 0)

    def activate_power(self, kind):
        now = pygame.time.get_ticks()

        if kind == "nitro":
            self.active_power = "nitro"
            self.power_end_time = now + 4000
            self.shield = False
            self.power_bonus = self.power_bonus + 60

        elif kind == "shield":
            self.active_power = "shield"
            self.shield = True
            self.power_bonus = self.power_bonus + 40

        elif kind == "repair":
            self.repair()
            self.power_bonus = self.power_bonus + 30

    def repair(self):
        danger_types = ["traffic", "barrier", "oil", "pothole", "moving_barrier", "speed_bump"]

        for obj in self.objects:
            if obj["kind"] in danger_types:
                self.objects.remove(obj)
                break

    def save_result(self):
        if not self.saved:
            save_score(self.username, self.score, self.distance, self.coins)
            self.saved = True

    def hit_danger(self, obj):
        if self.shield:
            self.shield = False
            self.active_power = None

            if obj in self.objects:
                self.objects.remove(obj)

            return

        self.game_over = True
        self.save_result()

    def handle_key(self, event):
        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.player_lane = self.player_lane - 1

            if self.player_lane < 0:
                self.player_lane = 0

            self.update_player_position()

        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.player_lane = self.player_lane + 1

            if self.player_lane >= LANES:
                self.player_lane = LANES - 1

            self.update_player_position()

    def update(self, dt):
        if self.game_over:
            return

        now = pygame.time.get_ticks()
        speed = self.get_current_speed()

        self.distance = self.distance + speed * dt / 18

        if self.distance >= FINISH_DISTANCE:
            self.finished = True
            self.game_over = True
            self.save_result()
            return

        current_spawn_rate = self.spawn_rate

        if self.distance > 1500:
            current_spawn_rate = current_spawn_rate - 150

        if self.distance > 3000:
            current_spawn_rate = current_spawn_rate - 150

        if current_spawn_rate < 400:
            current_spawn_rate = 400

        if now - self.last_traffic_time > current_spawn_rate:
            self.spawn_traffic()
            self.last_traffic_time = now

        if now - self.last_obstacle_time > current_spawn_rate + 350:
            self.spawn_obstacle()
            self.last_obstacle_time = now

        if now - self.last_coin_time > 900:
            self.spawn_coin()
            self.last_coin_time = now

        if now - self.last_power_time > 5000:
            self.spawn_power()
            self.last_power_time = now

        if now - self.last_event_time > 3500:
            self.spawn_road_event()
            self.last_event_time = now

        self.road_y = self.road_y + speed

        if self.road_y > 60:
            self.road_y = 0

        for obj in self.objects[:]:
            if obj["kind"] == "moving_barrier":
                obj["rect"].x = obj["rect"].x + obj["move_side"] * 2

                if obj["rect"].left < ROAD_X:
                    obj["move_side"] = 1

                if obj["rect"].right > ROAD_X + ROAD_WIDTH:
                    obj["move_side"] = -1

            obj["rect"].y = obj["rect"].y + int(speed)

            if obj["rect"].top > HEIGHT:
                self.objects.remove(obj)
                continue

            if obj["rect"].colliderect(self.player_rect):
                self.handle_collision(obj)

        self.score = self.coins * 25 + int(self.distance) + self.power_bonus

    def handle_collision(self, obj):
        kind = obj["kind"]

        if kind == "coin":
            self.coins = self.coins + obj["value"]
            self.objects.remove(obj)

        elif kind == "nitro":
            self.activate_power("nitro")
            self.objects.remove(obj)

        elif kind == "shield":
            self.activate_power("shield")
            self.objects.remove(obj)

        elif kind == "repair":
            self.activate_power("repair")
            self.objects.remove(obj)

        elif kind == "boost_strip":
            self.activate_power("nitro")
            self.objects.remove(obj)

        elif kind == "oil" or kind == "pothole" or kind == "speed_bump":
            self.slow_end_time = pygame.time.get_ticks() + 2000
            self.objects.remove(obj)

        else:
            self.hit_danger(obj)

    def draw_road(self, screen):
        screen.fill((35, 140, 55))

        road_rect = pygame.Rect(ROAD_X, 0, ROAD_WIDTH, HEIGHT)
        pygame.draw.rect(screen, (65, 65, 65), road_rect)

        pygame.draw.line(screen, (240, 240, 240), (ROAD_X, 0), (ROAD_X, HEIGHT), 4)
        pygame.draw.line(screen, (240, 240, 240), (ROAD_X + ROAD_WIDTH, 0), (ROAD_X + ROAD_WIDTH, HEIGHT), 4)

        for lane in range(1, LANES):
            x = ROAD_X + lane * LANE_WIDTH
            y = -60 + self.road_y

            while y < HEIGHT:
                pygame.draw.line(screen, (240, 240, 240), (x, y), (x, y + 35), 3)
                y = y + 60

    def get_object_color(self, kind):
        if kind == "traffic":
            return (190, 40, 40)
        if kind == "coin":
            return (255, 220, 40)
        if kind == "nitro":
            return (0, 170, 255)
        if kind == "shield":
            return (70, 80, 255)
        if kind == "repair":
            return (60, 210, 90)
        if kind == "oil":
            return (20, 20, 20)
        if kind == "pothole":
            return (90, 55, 25)
        if kind == "boost_strip":
            return (0, 230, 230)
        if kind == "speed_bump":
            return (160, 100, 40)

        return (255, 120, 0)

    def draw_objects(self, screen, font):
        for obj in self.objects:
            color = self.get_object_color(obj["kind"])
            pygame.draw.rect(screen, color, obj["rect"], border_radius=6)
            pygame.draw.rect(screen, (20, 20, 20), obj["rect"], 2, border_radius=6)

            label_text = ""

            if obj["kind"] == "coin":
                label_text = str(obj["value"])
            elif obj["kind"] == "nitro":
                label_text = "N"
            elif obj["kind"] == "shield":
                label_text = "S"
            elif obj["kind"] == "repair":
                label_text = "R"

            if label_text != "":
                label = font.render(label_text, True, (0, 0, 0))
                screen.blit(label, label.get_rect(center=obj["rect"].center))

    def draw_player(self, screen):
        pygame.draw.rect(screen, self.car_color, self.player_rect, border_radius=8)
        pygame.draw.rect(screen, (20, 20, 20), self.player_rect, 2, border_radius=8)

        if self.shield:
            shield_rect = self.player_rect.inflate(20, 24)
            pygame.draw.ellipse(screen, (80, 150, 255), shield_rect, 3)

    def draw_hud(self, screen, font):
        pygame.draw.rect(screen, (30, 30, 30), (0, 0, WIDTH, 55))

        remaining = FINISH_DISTANCE - int(self.distance)

        if remaining < 0:
            remaining = 0

        power = "none"

        if self.active_power is not None:
            power = self.active_power

        info = (
            "Player: " + self.username +
            " | Score: " + str(self.score) +
            " | Coins: " + str(self.coins) +
            " | Distance: " + str(int(self.distance)) +
            " | Left: " + str(remaining) +
            " | Power: " + power
        )

        label = font.render(info, True, (255, 255, 255))
        screen.blit(label, (15, 18))

    def draw(self, screen, font):
        self.draw_road(screen)
        self.draw_objects(screen, font)
        self.draw_player(screen)
        self.draw_hud(screen, font)
