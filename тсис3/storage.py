import json
from pathlib import Path

CAR_COLORS = {
    "blue": (40, 120, 255),
    "red": (230, 50, 50),
    "green": (40, 190, 90)
}

DIFFICULTY = {
    "easy": {"speed": 5, "spawn_rate": 1200},
    "normal": {"speed": 6, "spawn_rate": 900},
    "hard": {"speed": 7, "spawn_rate": 650}
}

def get_score(item):
    return item["score"]

def load_settings():
    try:
        file = open("settings.json", "r", encoding="utf-8")
        data = json.load(file)
        file.close()
    except:
        data = {
            "sound": True,
            "car_color": "blue",
            "difficulty": "normal"
        }

    return data

def save_settings(settings):
    file = open("settings.json", "w", encoding="utf-8")
    json.dump(settings, file, indent=4)
    file.close()

def load_scores():
    try:
        file = open("leaderboard.json", "r", encoding="utf-8")
        scores = json.load(file)
        file.close()
    except:
        scores = []

    scores.sort(key=get_score, reverse=True)

    return scores[:10]

def save_score(name, score, distance, coins):
    scores = load_scores()

    result = {
        "name": name,
        "score": int(score),
        "distance": int(distance),
        "coins": int(coins)
    }

    scores.append(result)
    scores.sort(key=get_score, reverse=True)
    scores = scores[:10]

    file = open("leaderboard.json", "w", encoding="utf-8")
    json.dump(scores, file, indent=4)
    file.close()

def next_value(values, current):
    index = values.index(current)
    index = index + 1

    if index >= len(values):
        index = 0

    return values[index]
