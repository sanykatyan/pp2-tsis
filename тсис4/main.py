import pygame
import psycopg2

from db import setup_database, get_leaderboard
from game import WIDTH, HEIGHT, SnakeGame, load_settings, save_settings

class Button:
    def __init__(self, text, rect):
        self.text = text
        self.rect = pygame.Rect(rect)

    def draw(self, screen, font):
        pygame.draw.rect(screen, (220, 220, 220), self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)

        label = font.render(self.text, True, (0, 0, 0))
        screen.blit(label, (self.rect.x + 15, self.rect.y + 13))

    def clicked(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        if event.button != 1:
            return False

        if self.rect.collidepoint(event.pos):
            return True

        return False

def draw_center_text(screen, font, value, y):
    label = font.render(str(value), True, (20, 20, 20))
    rect = label.get_rect(center=(WIDTH // 2, y))
    screen.blit(label, rect)

def draw_text(screen, font, value, x, y):
    label = font.render(str(value), True, (20, 20, 20))
    screen.blit(label, (x, y))

def make_menu_buttons():
    x = WIDTH // 2 - 130

    buttons = {}
    buttons["play"] = Button("Play", (x, 220, 260, 52))
    buttons["leaderboard"] = Button("Leaderboard", (x, 290, 260, 52))
    buttons["settings"] = Button("Settings", (x, 360, 260, 52))
    buttons["quit"] = Button("Quit", (x, 430, 260, 52))

    return buttons

def make_settings_buttons():
    x = WIDTH // 2 - 150

    buttons = {}
    buttons["grid"] = Button("Toggle Grid", (x, 230, 300, 50))
    buttons["sound"] = Button("Toggle Sound", (x, 300, 300, 50))
    buttons["color"] = Button("Snake Color", (x, 370, 300, 50))
    buttons["save"] = Button("Save & Back", (x, 470, 300, 50))

    return buttons

def make_game_over_buttons():
    x = WIDTH // 2 - 130

    buttons = {}
    buttons["retry"] = Button("Retry", (x, 430, 260, 52))
    buttons["menu"] = Button("Main Menu", (x, 500, 260, 52))

    return buttons

def next_color(color):
    colors = [
        [40, 190, 90],
        [60, 120, 240],
        [230, 60, 60],
        [240, 210, 60]
    ]

    if color not in colors:
        return colors[0]

    index = colors.index(color)
    index = index + 1

    if index >= len(colors):
        index = 0

    return colors[index]

def draw_menu(screen, title_font, font, buttons, database_error):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "TSIS4 Snake", 130)
    draw_center_text(screen, font, "PostgreSQL Leaderboard & Advanced Gameplay", 180)

    for key in buttons:
        buttons[key].draw(screen, font)

    if database_error is not None:
        draw_center_text(screen, font, "PostgreSQL error. Create snake_db and check config.py", 640)

def draw_name_screen(screen, title_font, font, username, database_error):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "Enter username", 210)

    rect = pygame.Rect(WIDTH // 2 - 170, 305, 340, 54)
    pygame.draw.rect(screen, (255, 255, 255), rect)
    pygame.draw.rect(screen, (0, 0, 0), rect, 2)

    shown = username

    if pygame.time.get_ticks() // 450 % 2 == 0:
        shown = shown + "|"

    draw_text(screen, font, shown, rect.x + 15, rect.y + 14)
    draw_center_text(screen, font, "Enter = start, Escape = back", 405)

    if database_error is not None:
        draw_center_text(screen, font, "Database is not ready", 500)

def draw_leaderboard(screen, title_font, font, back_button, database_error):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "Top 10 Leaderboard", 80)

    if database_error is not None:
        draw_center_text(screen, font, "Database error. Check PostgreSQL.", 240)
    else:
        rows = get_leaderboard()

        y = 150

        draw_text(screen, font, "Rank", 80, y)
        draw_text(screen, font, "Username", 155, y)
        draw_text(screen, font, "Score", 340, y)
        draw_text(screen, font, "Level", 460, y)
        draw_text(screen, font, "Date", 570, y)

        y = y + 38
        rank = 1

        if len(rows) == 0:
            draw_center_text(screen, font, "No scores yet", 250)

        for row in rows:
            username = row[0]
            score = row[1]
            level = row[2]
            date = row[3]

            draw_text(screen, font, rank, 92, y)
            draw_text(screen, font, username, 155, y)
            draw_text(screen, font, score, 340, y)
            draw_text(screen, font, level, 460, y)
            draw_text(screen, font, date, 570, y)

            y = y + 34
            rank = rank + 1

    back_button.draw(screen, font)

def draw_settings(screen, title_font, font, buttons, settings):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "Settings", 115)

    if settings["grid"]:
        grid_text = "On"
    else:
        grid_text = "Off"

    if settings["sound"]:
        sound_text = "On"
    else:
        sound_text = "Off"

    draw_center_text(screen, font, "Grid: " + grid_text, 190)
    draw_center_text(screen, font, "Sound: " + sound_text, 250)
    draw_center_text(screen, font, "Snake color: " + str(settings["snake_color"]), 310)

    for key in buttons:
        buttons[key].draw(screen, font)

def draw_game_over(screen, title_font, font, buttons, game):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "Game Over", 130)
    draw_center_text(screen, font, "Player: " + game.username, 220)
    draw_center_text(screen, font, "Final score: " + str(game.score), 260)
    draw_center_text(screen, font, "Level reached: " + str(game.level), 300)
    draw_center_text(screen, font, "Personal best before run: " + str(game.personal_best), 340)

    for key in buttons:
        buttons[key].draw(screen, font)

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TSIS4 Snake")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 24)
    small_font = pygame.font.SysFont("arial", 20)
    title_font = pygame.font.SysFont("arial", 52, bold=True)

    database_error = None

    try:
        setup_database()
    except psycopg2.Error as error:
        database_error = str(error)

    settings = load_settings()

    state = "menu"
    username = ""
    game = None

    menu_buttons = make_menu_buttons()
    settings_buttons = make_settings_buttons()
    game_over_buttons = make_game_over_buttons()
    back_button = Button("Back", (35, 620, 150, 48))

    running = True

    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "menu":
                if menu_buttons["play"].clicked(event):
                    username = ""
                    state = "name"

                elif menu_buttons["leaderboard"].clicked(event):
                    state = "leaderboard"

                elif menu_buttons["settings"].clicked(event):
                    state = "settings"

                elif menu_buttons["quit"].clicked(event):
                    running = False

            elif state == "name":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if database_error is None:
                            if username.strip() == "":
                                username = "Player"

                            game = SnakeGame(username, settings)
                            state = "game"

                    elif event.key == pygame.K_ESCAPE:
                        state = "menu"

                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]

                    else:
                        if event.unicode.isprintable():
                            if len(username) < 16:
                                username = username + event.unicode

            elif state == "leaderboard":
                if back_button.clicked(event):
                    state = "menu"

            elif state == "settings":
                if settings_buttons["grid"].clicked(event):
                    settings["grid"] = not settings["grid"]

                elif settings_buttons["sound"].clicked(event):
                    settings["sound"] = not settings["sound"]

                elif settings_buttons["color"].clicked(event):
                    settings["snake_color"] = next_color(settings["snake_color"])

                elif settings_buttons["save"].clicked(event):
                    save_settings(settings)
                    state = "menu"

            elif state == "game":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        game.change_direction((0, -1))

                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        game.change_direction((0, 1))

                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        game.change_direction((-1, 0))

                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        game.change_direction((1, 0))

            elif state == "game_over":
                if game_over_buttons["retry"].clicked(event):
                    game = SnakeGame(username, settings)
                    state = "game"

                elif game_over_buttons["menu"].clicked(event):
                    state = "menu"

        if state == "menu":
            draw_menu(screen, title_font, font, menu_buttons, database_error)

        elif state == "name":
            draw_name_screen(screen, title_font, font, username, database_error)

        elif state == "leaderboard":
            draw_leaderboard(screen, title_font, small_font, back_button, database_error)

        elif state == "settings":
            draw_settings(screen, title_font, font, settings_buttons, settings)

        elif state == "game":
            game.update(dt)
            game.draw(screen, small_font)

            if game.game_over:
                state = "game_over"

        elif state == "game_over":
            draw_game_over(screen, title_font, font, game_over_buttons, game)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
