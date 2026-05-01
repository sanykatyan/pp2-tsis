import pygame

from racer import RacerGame, WIDTH, HEIGHT
from storage import load_settings, save_settings, load_scores, CAR_COLORS, DIFFICULTY, next_value

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
    buttons["sound"] = Button("Toggle Sound", (x, 250, 300, 50))
    buttons["color"] = Button("Car Color", (x, 320, 300, 50))
    buttons["difficulty"] = Button("Difficulty", (x, 390, 300, 50))
    buttons["back"] = Button("Back", (x, 500, 300, 50))

    return buttons

def make_game_over_buttons():
    x = WIDTH // 2 - 130

    buttons = {}
    buttons["retry"] = Button("Retry", (x, 440, 260, 52))
    buttons["menu"] = Button("Main Menu", (x, 510, 260, 52))

    return buttons

def draw_menu(screen, title_font, font, buttons):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "TSIS3 Racer", 120)
    draw_center_text(screen, font, "Advanced Driving, Leaderboard & Power-Ups", 170)

    for key in buttons:
        buttons[key].draw(screen, font)

def draw_name_screen(screen, title_font, font, username):
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

def draw_leaderboard(screen, title_font, font, back_button):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "Leaderboard", 80)

    scores = load_scores()

    y = 150
    draw_text(screen, font, "Rank", 80, y)
    draw_text(screen, font, "Name", 155, y)
    draw_text(screen, font, "Score", 340, y)
    draw_text(screen, font, "Distance", 460, y)
    draw_text(screen, font, "Coins", 600, y)

    y = y + 40

    if len(scores) == 0:
        draw_center_text(screen, font, "No scores yet", 250)

    rank = 1

    for item in scores:
        draw_text(screen, font, rank, 92, y)
        draw_text(screen, font, item["name"], 155, y)
        draw_text(screen, font, item["score"], 340, y)
        draw_text(screen, font, item["distance"], 460, y)
        draw_text(screen, font, item["coins"], 600, y)

        y = y + 34
        rank = rank + 1

    back_button.draw(screen, font)

def draw_settings(screen, title_font, font, buttons, settings):
    screen.fill((235, 235, 245))
    draw_center_text(screen, title_font, "Settings", 115)

    sound_text = "On"

    if not settings["sound"]:
        sound_text = "Off"

    draw_center_text(screen, font, "Sound: " + sound_text, 190)
    draw_center_text(screen, font, "Car color: " + settings["car_color"], 250)
    draw_center_text(screen, font, "Difficulty: " + settings["difficulty"], 310)

    for key in buttons:
        buttons[key].draw(screen, font)

def draw_game_over(screen, title_font, font, buttons, game):
    screen.fill((235, 235, 245))

    if game.finished:
        title = "Finish!"
    else:
        title = "Game Over"

    draw_center_text(screen, title_font, title, 130)
    draw_center_text(screen, font, "Player: " + game.username, 220)
    draw_center_text(screen, font, "Score: " + str(game.score), 260)
    draw_center_text(screen, font, "Distance: " + str(int(game.distance)), 300)
    draw_center_text(screen, font, "Coins: " + str(game.coins), 340)

    for key in buttons:
        buttons[key].draw(screen, font)

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TSIS3 Racer")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 24)
    small_font = pygame.font.SysFont("arial", 20)
    title_font = pygame.font.SysFont("arial", 52, bold=True)

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
                        if username.strip() == "":
                            username = "Player"

                        game = RacerGame(username, settings)
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
                if settings_buttons["sound"].clicked(event):
                    settings["sound"] = not settings["sound"]
                    save_settings(settings)

                elif settings_buttons["color"].clicked(event):
                    values = list(CAR_COLORS.keys())
                    settings["car_color"] = next_value(values, settings["car_color"])
                    save_settings(settings)

                elif settings_buttons["difficulty"].clicked(event):
                    values = list(DIFFICULTY.keys())
                    settings["difficulty"] = next_value(values, settings["difficulty"])
                    save_settings(settings)

                elif settings_buttons["back"].clicked(event):
                    state = "menu"

            elif state == "game":
                if event.type == pygame.KEYDOWN:
                    game.handle_key(event)

            elif state == "game_over":
                if game_over_buttons["retry"].clicked(event):
                    game = RacerGame(username, settings)
                    state = "game"

                elif game_over_buttons["menu"].clicked(event):
                    state = "menu"

        if state == "menu":
            draw_menu(screen, title_font, font, menu_buttons)

        elif state == "name":
            draw_name_screen(screen, title_font, font, username)

        elif state == "leaderboard":
            draw_leaderboard(screen, title_font, small_font, back_button)

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
