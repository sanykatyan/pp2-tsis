import pygame
import math
from pathlib import Path
from datetime import datetime

WIDTH = 1100
HEIGHT = 760
TOOLBAR_HEIGHT = 110
CANVAS_HEIGHT = HEIGHT - TOOLBAR_HEIGHT

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class Button:
    def __init__(self, key, text, rect):
        self.key = key
        self.text = text
        self.rect = pygame.Rect(rect)

def draw_button(screen, font, button, active):
    if active:
        color = (190, 190, 190)
    else:
        color = (230, 230, 230)

    pygame.draw.rect(screen, color, button.rect)
    pygame.draw.rect(screen, BLACK, button.rect, 2)

    label = font.render(button.text, True, BLACK)
    screen.blit(label, (button.rect.x + 5, button.rect.y + 6))

def point_is_on_canvas(point):
    if point[1] >= TOOLBAR_HEIGHT:
        return True

    return False

def convert_to_canvas(point):
    x = point[0]
    y = point[1] - TOOLBAR_HEIGHT

    return (x, y)

def keep_inside_canvas(point):
    x, y = convert_to_canvas(point)

    if x < 0:
        x = 0
    if x >= WIDTH:
        x = WIDTH - 1

    if y < 0:
        y = 0
    if y >= CANVAS_HEIGHT:
        y = CANVAS_HEIGHT - 1

    return (x, y)

def make_rectangle(start, end):
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]

    if x1 < x2:
        left = x1
    else:
        left = x2

    if y1 < y2:
        top = y1
    else:
        top = y2

    width = abs(x2 - x1)
    height = abs(y2 - y1)

    return pygame.Rect(left, top, width, height)

def make_square(start, end):
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]

    dx = x2 - x1
    dy = y2 - y1

    side = max(abs(dx), abs(dy))

    if dx < 0:
        x2 = x1 - side
    else:
        x2 = x1 + side

    if dy < 0:
        y2 = y1 - side
    else:
        y2 = y1 + side

    return make_rectangle(start, (x2, y2))

def draw_shape(surface, tool, start, end, color, size):
    if start is None:
        return
    if end is None:
        return

    if tool == "line":
        pygame.draw.line(surface, color, start, end, size)

    elif tool == "rectangle":
        rect = make_rectangle(start, end)
        pygame.draw.rect(surface, color, rect, size)

    elif tool == "circle":
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        radius = int((dx * dx + dy * dy) ** 0.5)
        pygame.draw.circle(surface, color, start, radius, size)

    elif tool == "square":
        rect = make_square(start, end)
        pygame.draw.rect(surface, color, rect, size)

    elif tool == "right_triangle":
        x1 = start[0]
        y1 = start[1]
        x2 = end[0]
        y2 = end[1]
        points = [(x1, y1), (x2, y1), (x2, y2)]
        pygame.draw.polygon(surface, color, points, size)

    elif tool == "equilateral_triangle":
        x1 = start[0]
        y1 = start[1]
        x2 = end[0]
        y2 = end[1]
        left = min(x1, x2)
        right = max(x1, x2)
        top_x = (left + right) // 2
        points = [(left, y2), (right, y2), (top_x, y1)]
        pygame.draw.polygon(surface, color, points, size)

    elif tool == "rhombus":
        rect = make_rectangle(start, end)
        points = [
            (rect.centerx, rect.top),
            (rect.right, rect.centery),
            (rect.centerx, rect.bottom),
            (rect.left, rect.centery)
        ]
        pygame.draw.polygon(surface, color, points, size)

def flood_fill(surface, start, new_color):
    width, height = surface.get_size()
    start_x = start[0]
    start_y = start[1]

    old_color = surface.get_at((start_x, start_y))
    new_color = pygame.Color(new_color[0], new_color[1], new_color[2], 255)

    if old_color == new_color:
        return

    pixels = []
    pixels.append((start_x, start_y))

    while len(pixels) > 0:
        x, y = pixels.pop()

        if x < 0 or y < 0 or x >= width or y >= height:
            continue

        if surface.get_at((x, y)) != old_color:
            continue

        surface.set_at((x, y), new_color)

        pixels.append((x + 1, y))
        pixels.append((x - 1, y))
        pixels.append((x, y + 1))
        pixels.append((x, y - 1))

def save_canvas(canvas):
    folder = Path("saves")

    if not folder.exists():
        folder.mkdir()

    filename = datetime.now().strftime("paint_%Y%m%d_%H%M%S.png")
    path = folder / filename

    pygame.image.save(canvas, str(path))

    return str(path)

def make_tool_buttons():
    buttons = []

    buttons.append(Button("pencil", "Pencil", (8, 8, 75, 28)))
    buttons.append(Button("line", "Line", (88, 8, 75, 28)))
    buttons.append(Button("rectangle", "Rect", (168, 8, 75, 28)))
    buttons.append(Button("circle", "Circle", (248, 8, 75, 28)))
    buttons.append(Button("eraser", "Eraser", (328, 8, 75, 28)))
    buttons.append(Button("fill", "Fill", (408, 8, 75, 28)))
    buttons.append(Button("text", "Text", (488, 8, 75, 28)))
    buttons.append(Button("picker", "Picker", (568, 8, 75, 28)))
    buttons.append(Button("square", "Square", (648, 8, 75, 28)))
    buttons.append(Button("right_triangle", "R.Tri", (728, 8, 75, 28)))
    buttons.append(Button("equilateral_triangle", "E.Tri", (808, 8, 75, 28)))
    buttons.append(Button("rhombus", "Rhomb", (888, 8, 75, 28)))

    return buttons

def make_size_buttons():
    buttons = []

    buttons.append(Button("2", "S", (350, 58, 40, 30)))
    buttons.append(Button("5", "M", (398, 58, 40, 30)))
    buttons.append(Button("10", "L", (446, 58, 40, 30)))

    return buttons

def make_color_buttons():
    colors = [BLACK, WHITE, (255, 0, 0), (0, 160, 0), (0, 0, 255), (255, 220, 0)]
    buttons = []
    x = 8

    for color in colors:
        rect = pygame.Rect(x, 60, 28, 28)
        buttons.append((color, rect))
        x = x + 36

    return buttons

def draw_toolbar(screen, font, tool_buttons, size_buttons, color_buttons, tool, color, size, message):
    pygame.draw.rect(screen, (220, 220, 220), (0, 0, WIDTH, TOOLBAR_HEIGHT))

    for button in tool_buttons:
        active = button.key == tool
        draw_button(screen, font, button, active)

    for color_value, rect in color_buttons:
        pygame.draw.rect(screen, color_value, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)

    for button in size_buttons:
        active = int(button.key) == size
        draw_button(screen, font, button, active)

    text = "Tool: " + tool + " | Size: " + str(size) + " | Ctrl+S save | " + message
    label = font.render(text, True, BLACK)
    screen.blit(label, (520, 66))

    pygame.draw.line(screen, BLACK, (0, TOOLBAR_HEIGHT - 1), (WIDTH, TOOLBAR_HEIGHT - 1), 2)

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TSIS2 Paint")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 15)
    text_font = pygame.font.SysFont("arial", 28)

    canvas = pygame.Surface((WIDTH, CANVAS_HEIGHT))
    canvas.fill(WHITE)

    tool_buttons = make_tool_buttons()
    size_buttons = make_size_buttons()
    color_buttons = make_color_buttons()

    tool = "pencil"
    color = BLACK
    size = 5

    drawing = False
    start_point = None
    last_point = None

    typing = False
    typed_text = ""
    text_position = None

    message = ""
    message_time = 0

    running = True

    while running:
        now = pygame.time.get_ticks()

        if message != "":
            if now - message_time > 2500:
                message = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

                if ctrl_pressed and event.key == pygame.K_s:
                    message = "Saved: " + save_canvas(canvas)
                    message_time = pygame.time.get_ticks()

                elif typing:
                    if event.key == pygame.K_RETURN:
                        if typed_text.strip() != "":
                            image = text_font.render(typed_text, True, color)
                            canvas.blit(image, text_position)

                        typing = False
                        typed_text = ""
                        text_position = None

                    elif event.key == pygame.K_ESCAPE:
                        typing = False
                        typed_text = ""
                        text_position = None

                    elif event.key == pygame.K_BACKSPACE:
                        typed_text = typed_text[:-1]

                    else:
                        if event.unicode.isprintable():
                            typed_text = typed_text + event.unicode

                else:
                    if event.key == pygame.K_1:
                        size = 2
                    elif event.key == pygame.K_2:
                        size = 5
                    elif event.key == pygame.K_3:
                        size = 10

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not point_is_on_canvas(event.pos):
                        typing = False

                        for button in tool_buttons:
                            if button.rect.collidepoint(event.pos):
                                tool = button.key

                        for color_value, rect in color_buttons:
                            if rect.collidepoint(event.pos):
                                color = color_value

                        for button in size_buttons:
                            if button.rect.collidepoint(event.pos):
                                size = int(button.key)

                    else:
                        point = keep_inside_canvas(event.pos)

                        if tool == "fill":
                            flood_fill(canvas, point, color)

                        elif tool == "picker":
                            picked = canvas.get_at(point)
                            color = (picked.r, picked.g, picked.b)

                        elif tool == "text":
                            typing = True
                            typed_text = ""
                            text_position = point

                        elif tool == "pencil":
                            drawing = True
                            last_point = point

                        elif tool == "eraser":
                            drawing = True
                            last_point = point

                        else:
                            drawing = True
                            start_point = point

            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    if tool == "pencil" or tool == "eraser":
                        if point_is_on_canvas(event.pos):
                            point = keep_inside_canvas(event.pos)

                            if tool == "eraser":
                                draw_color = WHITE
                            else:
                                draw_color = color

                            pygame.draw.line(canvas, draw_color, last_point, point, size)
                            last_point = point

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if drawing:
                        end_point = keep_inside_canvas(event.pos)

                        if tool != "pencil" and tool != "eraser":
                            draw_shape(canvas, tool, start_point, end_point, color, size)

                    drawing = False
                    start_point = None
                    last_point = None

        screen.fill((200, 200, 200))
        screen.blit(canvas, (0, TOOLBAR_HEIGHT))

        if drawing:
            if tool != "pencil" and tool != "eraser":
                if start_point is not None:
                    preview = canvas.copy()
                    mouse_point = keep_inside_canvas(pygame.mouse.get_pos())
                    draw_shape(preview, tool, start_point, mouse_point, color, size)
                    screen.blit(preview, (0, TOOLBAR_HEIGHT))

        if typing:
            if text_position is not None:
                x = text_position[0]
                y = text_position[1] + TOOLBAR_HEIGHT
                image = text_font.render(typed_text, True, color)
                screen.blit(image, (x, y))

        draw_toolbar(screen, font, tool_buttons, size_buttons, color_buttons, tool, color, size, message)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
