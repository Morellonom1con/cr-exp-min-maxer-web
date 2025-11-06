from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# === CONFIGURATION ===
# ------------------------------

xp_table = {  # (unchanged)
    1: 20, 2: 50, 3: 50, 4: 50, 5: 80, 6: 120, 7: 125, 8: 130, 9: 145, 10: 200,
    11: 220, 12: 280, 13: 300, 14: 350, 15: 450, 16: 550, 17: 650, 18: 800, 19: 1200, 20: 1400,
    21: 1600, 22: 2000, 23: 2300, 24: 2700, 25: 3000, 26: 4000, 27: 4600, 28: 5400, 29: 6000,
    30: 7000, 31: 8000, 32: 9000, 33: 11000, 34: 12500, 35: 12500, 36: 12500, 37: 12500,
    38: 15000, 39: 18000, 40: 22000, 41: 25000, 42: 25000, 43: 25000, 44: 25000, 45: 25000,
    46: 25000, 47: 25000, 48: 25000, 49: 25000, 50: 25000, 51: 50000, 52: 75000, 53: 100000,
    54: 125000, 55: 150000, 56: 175000, 57: 200000, 58: 225000, 59: 250000, 60: 275000,
    61: 300000, 62: 325000, 63: 350000, 64: 375000, 65: 400000, 66: 425000, 67: 450000,
    68: 475000, 69: 500000, 70: None
}

def get_env_var(key, path=".env"):
    with open(path) as f:
        for line in f:
            if line.strip().startswith(f"{key}="):
                return line.strip().split("=", 1)[1]
    return None

API_TOKEN = get_env_var("API_TOKEN")


# ------------------------------
# === INPUT MODEL ===
# ------------------------------

class InputData(BaseModel):
    player_tag: str
    total_gold: int
    common_wildcards: int
    rare_wildcards: int
    epic_wildcards: int
    legendary_wildcards: int
    champion_wildcards: int


# ------------------------------
# === HELPER FUNCTIONS ===
# ------------------------------

def true_level(level, rarity):
    offsets = {"common": 0, "rare": 2, "epic": 5, "legendary": 8, "champion": 10}
    return level + offsets.get(rarity.lower(), 0)


def greedy_upgrade_plan(upgrade_steps, total_gold, wildcards, cards, target_xp):
    gold_left = total_gold
    total_xp = 0
    used_gold = 0
    plan = []
    card_counts = {c["name"]: c["count"] for c in cards}
    rarity_weights = {"common": 0.5, "rare": 1, "epic": 2, "legendary": 3, "champion": 4}

    for s in upgrade_steps:
        rarity = s["rarity"]
        req = s["cards_needed"]
        exp = s["exp_gain"]
        gold = s["gold_needed"]
        wild_penalty = rarity_weights[rarity] * (req / max(1, (card_counts[s["card"]] + wildcards[rarity])))
        s["efficiency"] = (exp / gold) - (0.001 * wild_penalty)

    upgrade_steps.sort(key=lambda x: x["efficiency"], reverse=True)

    for step in upgrade_steps:
        name, rarity = step["card"], step["rarity"]
        need = step["cards_needed"]
        gold = step["gold_needed"]
        exp = step["exp_gain"]

        if gold_left < gold:
            continue

        have = card_counts[name]
        use_owned = min(need, have)
        use_wild = need - use_owned

        if use_wild > wildcards[rarity]:
            continue

        gold_left -= gold
        used_gold += gold
        total_xp += exp
        wildcards[rarity] -= use_wild
        card_counts[name] -= use_owned

        plan.append((step, use_owned, use_wild))

        if total_xp >= target_xp:
            break

    return total_xp, used_gold, plan


# ------------------------------
# === API ENDPOINT ===
# ------------------------------

@app.post("/upgrade_plan")
def get_upgrade_plan(data: InputData):
    # Fetch player data
    tag = data.player_tag.strip("#")
    res = requests.get(
        f"https://api.clashroyale.com/v1/players/%23{tag}",
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    player_data = res.json()

    # Calculate target XP
    next_level = player_data["expLevel"] + 1
    target_xp = xp_table[next_level] - player_data["expPoints"] if xp_table[next_level] else 0

    # Build card list
    cards = [{
        "name": c["name"],
        "rarity": c["rarity"].lower(),
        "count": c["count"],
        "level": true_level(c["level"], c["rarity"].lower())
    } for c in player_data["cards"]]

    # Static tables
    cards_required = {
        "common":     [2,4,10,20,50,100,200,400,800,1000,1500,3000,5000],
        "rare":       [0,1,2,4,10,20,50,100,200,400,500,750,1250],
        "epic":       [0,0,0,0,1,2,4,10,20,40,50,100,200],
        "legendary":  [0,0,0,0,0,0,0,1,2,4,6,10,20],
        "champion":   [0,0,0,0,0,0,0,0,0,1,2,8,20]
    }

    progression = [
        {"level": 1, "gold": 5, "exp": 4},
        {"level": 2, "gold": 20, "exp": 5},
        {"level": 3, "gold": 50, "exp": 6},
        {"level": 4, "gold": 150, "exp": 10},
        {"level": 5, "gold": 400, "exp": 25},
        {"level": 6, "gold": 1000, "exp": 50},
        {"level": 7, "gold": 2000, "exp": 100},
        {"level": 8, "gold": 4000, "exp": 200},
        {"level": 9, "gold": 8000, "exp": 400},
        {"level": 10, "gold": 15000, "exp": 600},
        {"level": 11, "gold": 35000, "exp": 800},
        {"level": 12, "gold": 75000, "exp": 1600},
        {"level": 13, "gold": 100000, "exp": 2000},
    ]

    wildcards = {
        "common": data.common_wildcards,
        "rare": data.rare_wildcards,
        "epic": data.epic_wildcards,
        "legendary": data.legendary_wildcards,
        "champion": data.champion_wildcards,
    }

    # Generate upgrade steps
    upgrade_steps = []
    for c in cards:
        rarity = c["rarity"]
        lvl = c["level"]
        count = c["count"]
        available = count + wildcards[rarity]

        while lvl < len(cards_required[rarity]) and available >= cards_required[rarity][lvl - 1]:
            req_cards = cards_required[rarity][lvl - 1]
            gold_needed = progression[lvl - 1]["gold"]
            exp_gain = progression[lvl - 1]["exp"]

            upgrade_steps.append({
                "card": c["name"],
                "rarity": rarity,
                "from_lvl": lvl,
                "to_lvl": lvl + 1,
                "cards_needed": req_cards,
                "gold_needed": gold_needed,
                "exp_gain": exp_gain,
            })
            available -= req_cards
            lvl += 1

    # Run optimizer
    total_xp, gold_used, plan = greedy_upgrade_plan(upgrade_steps, data.total_gold, wildcards, cards, target_xp)

    results = [{
        "card": s["card"],
        "from_to": f"{s['from_lvl']} → {s['to_lvl']}",
        "rarity": s["rarity"],
        "gold": s["gold_needed"],
        "xp": s["exp_gain"],
        "efficiency": round(s["efficiency"], 6)
    } for (s, _, _) in plan]

    return {
        "player": player_data["name"],
        "target_xp": target_xp,
        "xp_gained": total_xp,
        "gold_spent": gold_used,
        "plan": results
    }
