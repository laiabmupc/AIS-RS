import json
import os
import subprocess
from pathlib import Path
import pandas as pd
from utils import DEFAULT_RULE_CONFIG, gini, normalise_rule_config

LLM_AGENT_ROLES = ["Input assumptions auditor", "Sustainable tourism evaluator"]
POI_ROWS = [
    ("Sagrada Familia", "Sagrada Familia", 41.4036, 2.1744, "religious,architecture,museum", 1.00, 900, 26, 0.20, 0.95, 0.30, 0.10),
    ("Park Guell", "La Salut", 41.4145, 2.1527, "park,architecture,viewpoint,family", 0.95, 850, 10, 0.90, 0.85, 0.35, 0.90),
    ("Casa Batllo", "Dreta Eixample", 41.3917, 2.1649, "architecture,museum", 0.91, 500, 35, 0.20, 0.90, 0.30, 0.05),
    ("La Pedrera", "Dreta Eixample", 41.3954, 2.1619, "architecture,museum", 0.88, 450, 28, 0.20, 0.90, 0.30, 0.05),
    ("La Rambla", "La Rambla", 41.3800, 2.1730, "food,shopping,nightlife,local", 0.93, 1200, 0, 0.80, 0.70, 0.45, 0.20),
    ("Mercat de la Boqueria", "El Raval", 41.3817, 2.1717, "market,food,local", 0.90, 650, 0, 0.30, 0.70, 0.85, 0.10),
    ("Barri Gotic", "Gotic", 41.3839, 2.1763, "architecture,shopping,nightlife,local", 0.89, 1000, 0, 0.80, 0.85, 0.55, 0.20),
    ("Barcelona Cathedral", "Gotic", 41.3839, 2.1762, "religious,architecture", 0.84, 550, 14, 0.20, 0.92, 0.35, 0.05),
    ("Santa Maria del Mar", "El Born", 41.3839, 2.1821, "religious,architecture", 0.72, 400, 5, 0.20, 0.90, 0.50, 0.05),
    ("Picasso Museum", "El Born", 41.3852, 2.1809, "museum", 0.78, 350, 14, 0.10, 0.94, 0.45, 0.05),
    ("Ciutadella Park", "Sant Pere", 41.3881, 2.1875, "park,family,local", 0.69, 1000, 0, 0.95, 0.70, 0.55, 0.95),
    ("Arc de Triomf", "Sant Pere", 41.3910, 2.1806, "architecture,viewpoint", 0.61, 700, 0, 0.90, 0.70, 0.45, 0.25),
    ("Barceloneta Beach", "La Barceloneta", 41.3784, 2.1926, "beach,family,nightlife", 0.82, 1100, 0, 1.00, 0.45, 0.55, 0.85),
    ("Montjuic Castle", "Montjuic", 41.3635, 2.1660, "viewpoint,museum,family", 0.63, 500, 12, 0.75, 0.86, 0.45, 0.65),
    ("Magic Fountain", "Montjuic", 41.3712, 2.1517, "viewpoint,family", 0.76, 900, 0, 0.95, 0.60, 0.40, 0.45),
    ("MNAC", "Montjuic", 41.3688, 2.1534, "museum,viewpoint", 0.68, 450, 12, 0.20, 0.95, 0.42, 0.10),
    ("Fundacio Joan Miro", "Montjuic", 41.3686, 2.1594, "museum", 0.59, 280, 15, 0.20, 0.91, 0.45, 0.10),
    ("Poble Espanyol", "Montjuic", 41.3687, 2.1484, "architecture,family,shopping,local", 0.58, 500, 14, 0.70, 0.77, 0.72, 0.35),
    ("Palau de la Musica", "Sant Pere", 41.3876, 2.1753, "architecture", 0.67, 300, 18, 0.15, 0.94, 0.35, 0.05),
    ("Camp Nou Museum", "Les Corts", 41.3809, 2.1228, "museum,family", 0.74, 700, 28, 0.20, 0.65, 0.48, 0.05),
    ("Temple del Tibidabo", "Tibidabo", 41.4225, 2.1186, "religious,viewpoint,architecture", 0.55, 450, 0, 0.75, 0.88, 0.40, 0.55),
    ("Tibidabo Park", "Tibidabo", 41.4218, 2.1191, "family,viewpoint", 0.54, 600, 35, 0.80, 0.50, 0.45, 0.50),
    ("Bunkers del Carmel", "El Carmel", 41.4186, 2.1619, "viewpoint,local", 0.64, 400, 0, 1.00, 0.68, 0.35, 0.65),
    ("Hospital de Sant Pau", "Guinardo", 41.4129, 2.1744, "architecture,museum", 0.62, 400, 16, 0.45, 0.92, 0.42, 0.22),
    ("Gracia Squares", "Vila de Gracia", 41.4020, 2.1585, "food,nightlife,local", 0.53, 700, 0, 0.90, 0.70, 0.86, 0.25),
    ("Mercat dels Encants", "Fort Pienc", 41.4031, 2.1870, "market,shopping,local", 0.47, 500, 0, 0.45, 0.65, 0.95, 0.18),
    ("Design Museum", "Glories", 41.4032, 2.1879, "museum,architecture", 0.45, 300, 6, 0.15, 0.80, 0.52, 0.10),
    ("Torre Glories", "Glories", 41.4036, 2.1896, "architecture,viewpoint", 0.52, 300, 15, 0.20, 0.60, 0.40, 0.05),
    ("Rambla del Poblenou", "Poblenou", 41.4004, 2.2038, "food,beach,local", 0.45, 600, 0, 0.90, 0.62, 0.86, 0.35),
    ("Bogatell Beach", "Poblenou", 41.3915, 2.2053, "beach,family", 0.46, 800, 0, 1.00, 0.35, 0.62, 0.86),
    ("Forum Park", "Diagonal Mar", 41.4114, 2.2236, "park,architecture,beach,family", 0.38, 900, 0, 0.95, 0.45, 0.55, 0.85),
    ("Sant Pau del Camp", "El Raval", 41.3764, 2.1705, "religious,architecture", 0.32, 200, 3, 0.20, 0.84, 0.55, 0.08),
    ("Maritime Museum", "El Raval", 41.3769, 2.1761, "museum,family", 0.50, 350, 10, 0.15, 0.86, 0.50, 0.06),
    ("CCCB", "El Raval", 41.3830, 2.1665, "museum", 0.48, 300, 8, 0.10, 0.83, 0.50, 0.05),
    ("MACBA", "El Raval", 41.3839, 2.1664, "museum", 0.56, 320, 12, 0.20, 0.86, 0.48, 0.08),
    ("Born Centre Cultural", "El Born", 41.3847, 2.1836, "museum,local", 0.46, 350, 5, 0.25, 0.84, 0.62, 0.08),
    ("History Museum of Catalonia", "La Barceloneta", 41.3801, 2.1858, "museum", 0.44, 300, 6, 0.20, 0.83, 0.55, 0.06),
    ("Sant Antoni Market", "Sant Antoni", 41.3787, 2.1622, "market,food,local", 0.42, 450, 0, 0.35, 0.58, 0.94, 0.10),
    ("Hostafrancs Market", "Hostafrancs", 41.3769, 2.1439, "market,food,local", 0.30, 350, 0, 0.35, 0.52, 0.94, 0.10),
    ("Joan Miro Park", "Nova Esquerra Eixample", 41.3796, 2.1495, "park,family,local", 0.34, 600, 0, 0.95, 0.50, 0.75, 0.88),
    ("Pedralbes Monastery", "Pedralbes", 41.3957, 2.1112, "religious,architecture,park", 0.35, 250, 5, 0.60, 0.90, 0.60, 0.65),
    ("Pedralbes Gardens", "Pedralbes", 41.3863, 2.1184, "park,family", 0.31, 650, 0, 0.95, 0.45, 0.65, 0.94),
    ("Labyrinth Park of Horta", "Horta", 41.4387, 2.1475, "park,family", 0.37, 500, 2, 0.95, 0.70, 0.58, 0.96),
    ("Fabra i Coats", "Sant Andreu", 41.4323, 2.1907, "museum,local", 0.25, 300, 0, 0.25, 0.67, 0.92, 0.15),
    ("Sant Andreu Old Town", "Sant Andreu", 41.4351, 2.1903, "food,local", 0.28, 450, 0, 0.85, 0.62, 0.92, 0.18),
    ("Clot Park", "El Clot", 41.4105, 2.1872, "park,family,local", 0.24, 450, 0, 0.95, 0.42, 0.82, 0.90),
    ("Can Framis Museum", "Poblenou", 41.4040, 2.1970, "museum,local", 0.26, 220, 8, 0.15, 0.78, 0.82, 0.08),
    ("Palo Alto Market", "Poblenou", 41.3991, 2.2067, "market,food,shopping,local", 0.33, 350, 5, 0.60, 0.55, 0.96, 0.28),
    ("Torre Bellesguard", "Sant Gervasi", 41.4097, 2.1269, "architecture", 0.29, 180, 16, 0.45, 0.86, 0.55, 0.22),
    ("CosmoCaixa", "Sant Gervasi", 41.4132, 2.1314, "museum,family,science", 0.57, 550, 6, 0.20, 0.74, 0.55, 0.08),
    ("Museu Frederic Mares", "Gotic", 41.3843, 2.1768, "museum", 0.36, 180, 6, 0.10, 0.82, 0.45, 0.04),
    ("Chocolate Museum", "El Born", 41.3868, 2.1818, "museum,food,family", 0.39, 220, 6, 0.10, 0.56, 0.60, 0.04),
    ("Creueta del Coll Park", "La Salut", 41.4177, 2.1481, "park,family", 0.27, 500, 0, 0.95, 0.42, 0.70, 0.94),
    ("Sarria Old Town", "Sarria", 41.3987, 2.1213, "food,local", 0.25, 400, 0, 0.85, 0.60, 0.90, 0.20),
    ("Mercat de la Llibertat", "Vila de Gracia", 41.3998, 2.1536, "market,food,local", 0.29, 300, 0, 0.35, 0.52, 0.95, 0.10),
    ("Guinardo Park", "Guinardo", 41.4165, 2.1681, "park,viewpoint,family", 0.30, 700, 0, 0.95, 0.44, 0.65, 0.94),
    ("Carretera de les Aigues", "Collserola", 41.4158, 2.1040, "park,viewpoint", 0.26, 800, 0, 1.00, 0.48, 0.45, 0.96),
    ("Natural Science Museum", "Diagonal Mar", 41.4111, 2.2193, "museum,family,science", 0.34, 300, 6, 0.20, 0.72, 0.55, 0.06),
    ("Fabra Observatory", "Tibidabo", 41.4182, 2.1239, "science,viewpoint,family", 0.28, 200, 15, 0.60, 0.68, 0.48, 0.40),
    ("Olympic Port", "La Barceloneta", 41.3870, 2.1993, "beach,food,nightlife", 0.50, 700, 0, 0.90, 0.40, 0.65, 0.35),
    ("Casa Vicens", "Vila de Gracia", 41.4036, 2.1507, "architecture,museum", 0.55, 250, 18, 0.35, 0.88, 0.45, 0.12),
]

TOURIST_PROFILES = {
    "segments": [
        {"segment": "architecture_fans", "probability": 0.24, "likes": ["architecture", "museum", "religious", "viewpoint"], "budget_probs": {"low": 0.16, "medium": 0.54, "high": 0.30}, "mobility_probs": {"walk": 0.22, "bike": 0.08, "transit": 0.45, "mixed": 0.18, "taxi": 0.07}, "with_kids_probability": 0.08, "crowd_aversion_mean": 0.42, "sustainability_mean": 0.38, "outdoor_mean": 0.34},
        {"segment": "history_religion", "probability": 0.15, "likes": ["religious", "architecture", "museum", "local"], "budget_probs": {"low": 0.26, "medium": 0.55, "high": 0.19}, "mobility_probs": {"walk": 0.28, "bike": 0.05, "transit": 0.48, "mixed": 0.16, "taxi": 0.03}, "with_kids_probability": 0.10, "crowd_aversion_mean": 0.50, "sustainability_mean": 0.48, "outdoor_mean": 0.35},
        {"segment": "food_local_markets", "probability": 0.18, "likes": ["food", "market", "local", "shopping"], "budget_probs": {"low": 0.38, "medium": 0.50, "high": 0.12}, "mobility_probs": {"walk": 0.32, "bike": 0.12, "transit": 0.40, "mixed": 0.13, "taxi": 0.03}, "with_kids_probability": 0.10, "crowd_aversion_mean": 0.58, "sustainability_mean": 0.62, "outdoor_mean": 0.52},
        {"segment": "family_green", "probability": 0.17, "likes": ["family", "park", "beach", "science"], "budget_probs": {"low": 0.28, "medium": 0.52, "high": 0.20}, "mobility_probs": {"walk": 0.18, "bike": 0.10, "transit": 0.47, "mixed": 0.18, "taxi": 0.07}, "with_kids_probability": 0.68, "crowd_aversion_mean": 0.70, "sustainability_mean": 0.66, "outdoor_mean": 0.82},
        {"segment": "beach_nightlife", "probability": 0.12, "likes": ["beach", "nightlife", "food", "shopping"], "budget_probs": {"low": 0.34, "medium": 0.48, "high": 0.18}, "mobility_probs": {"walk": 0.25, "bike": 0.16, "transit": 0.35, "mixed": 0.18, "taxi": 0.06}, "with_kids_probability": 0.04, "crowd_aversion_mean": 0.34, "sustainability_mean": 0.36, "outdoor_mean": 0.78},
        {"segment": "museum_culture", "probability": 0.14, "likes": ["museum", "architecture", "local", "science"], "budget_probs": {"low": 0.20, "medium": 0.58, "high": 0.22}, "mobility_probs": {"walk": 0.20, "bike": 0.08, "transit": 0.52, "mixed": 0.16, "taxi": 0.04}, "with_kids_probability": 0.14, "crowd_aversion_mean": 0.55, "sustainability_mean": 0.54, "outdoor_mean": 0.42},
    ],
    "hotel_distribution": [
        {"neighbourhood": "Gotic", "lat": 41.3839, "lon": 2.1763, "probability": 0.16},
        {"neighbourhood": "El Raval", "lat": 41.3812, "lon": 2.1686, "probability": 0.12},
        {"neighbourhood": "Dreta Eixample", "lat": 41.3918, "lon": 2.1649, "probability": 0.19},
        {"neighbourhood": "Sagrada Familia", "lat": 41.4036, "lon": 2.1744, "probability": 0.13},
        {"neighbourhood": "La Barceloneta", "lat": 41.3806, "lon": 2.1894, "probability": 0.08},
        {"neighbourhood": "Vila de Gracia", "lat": 41.4017, "lon": 2.1565, "probability": 0.09},
        {"neighbourhood": "Poblenou", "lat": 41.4004, "lon": 2.2038, "probability": 0.08},
        {"neighbourhood": "Montjuic", "lat": 41.3705, "lon": 2.1540, "probability": 0.06},
        {"neighbourhood": "Les Corts", "lat": 41.3860, "lon": 2.1300, "probability": 0.04},
        {"neighbourhood": "Sant Andreu", "lat": 41.4335, "lon": 2.1903, "probability": 0.03},
        {"neighbourhood": "Sarria", "lat": 41.3987, "lon": 2.1213, "probability": 0.02},
    ],
}


def llm_credentials_available(model_name):
    """Check if a lightweight local or remote LLM can be called."""
    if model_name.startswith("ollama/"):
        model = model_name.replace("ollama/", "", 1)
        result = subprocess.run(["ollama", "list"], check=False, capture_output=True, text=True, timeout=10)
        return result.returncode == 0 and model in result.stdout
    if model_name.startswith("openai/"):
        return bool(os.getenv("OPENAI_API_KEY"))
    return False


def build_poi_catalogue():
    """Create the curated Barcelona POI catalogue used by the simulator."""
    columns = ["poi_name", "neighbourhood", "lat", "lon", "categories", "popularity", "capacity", "cost", "outdoor", "culture", "local_economy", "green"]
    return pd.DataFrame(POI_ROWS, columns=columns)


def build_rule_config(pois):
    """Calibrate transparent rules from POI concentration statistics."""
    config = json.loads(json.dumps(DEFAULT_RULE_CONFIG))
    popularity_gini = gini(pois["popularity"])
    central_hotspot_share = pois.sort_values("popularity", ascending=False).head(10)["neighbourhood"].isin({"Gotic", "El Raval", "El Born", "La Barceloneta", "Dreta Eixample", "Sagrada Familia"}).mean()
    pressure_signal = min(1.0, 0.55 * popularity_gini + 0.45 * central_hotspot_share)

    social = config["sustainable"]["social"]
    social["crowd"] = round(0.24 + 0.12 * pressure_signal, 3)
    social["neighbourhood_relief"] = round(0.20 + 0.12 * pressure_signal, 3)
    social["sustainable_value"] = round(0.22 - 0.03 * pressure_signal, 3)
    social["local_economy"] = round(0.16 - 0.02 * pressure_signal, 3)
    social["distance"] = round(1 - sum(value for key, value in social.items() if key != "distance"), 3)

    personal = config["sustainable"]["personal"]
    personal["popularity"] = round(0.08 - 0.04 * pressure_signal, 3)
    personal["distance"] = round(0.14 + 0.05 * (1 - pois["capacity"].mean() / pois["capacity"].max()), 3)
    personal["interest"] = round(0.49 - 0.04 * pressure_signal, 3)
    fixed = personal["popularity"] + personal["distance"] + personal["interest"] + personal["budget"] + personal["outdoor"] + personal["culture"]
    personal["budget"] = round(personal["budget"] + (1 - fixed), 3)

    config["metadata"] = {
        "source": "curated_rules_from_poi_statistics",
        "popularity_gini": round(float(popularity_gini), 4),
        "central_hotspot_share_top10": round(float(central_hotspot_share), 4),
        "pressure_signal": round(float(pressure_signal), 4),
        "reason": "Rules are calibrated from popularity concentration and central hotspot pressure.",
        "llm_usage": "LLM is used for a simple input audit and the final interpretation; simulation choices stay rule-based.",
    }
    return normalise_rule_config(config)


def prepare_input_data(output_dir, model_name=None):
    """Write all simulator inputs quickly and reproducibly."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pois = build_poi_catalogue()
    poi_path = output_dir / "poi_catalogue.csv"
    profile_path = output_dir / "tourist_profiles.json"
    rule_path = output_dir / "rule_config_input.json"
    pois.to_csv(poi_path, index=False)
    profile_path.write_text(json.dumps(TOURIST_PROFILES, indent=2), encoding="utf-8")
    rule_path.write_text(json.dumps(build_rule_config(pois), indent=2), encoding="utf-8")
    return {"pois": poi_path, "segments": profile_path, "rules": rule_path}
