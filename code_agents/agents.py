import json
import os
import re
import urllib.request
from pathlib import Path
DEFAULT_MODEL = os.getenv("AIS_AGENT_MODEL", "ollama/qwen2.5:3b")
INTERESTS = ["architecture", "religious", "museum", "park", "market", "food", "beach", "viewpoint", "shopping", "nightlife", "family", "science", "local"]
REQUIRED_POI_FIELDS = ["poi_name", "neighbourhood", "lat", "lon", "categories", "popularity", "capacity", "cost", "outdoor", "culture", "local_economy", "green"]


def model_name(name):
    """Convert CrewAI-style names to Ollama model names."""
    return name.replace("ollama/", "", 1) if name.startswith("ollama/") else name


def extract_json(text):
    """Extract a JSON object from an LLM answer."""
    cleaned = text.strip().replace("```json", "```")
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start = min([i for i in [cleaned.find("{"), cleaned.find("[")] if i >= 0], default=-1)
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if start < 0 or end <= start:
        raise ValueError("No JSON object found in LLM output.")
    candidate = cleaned[start:end + 1]
    candidate = re.sub(r"//.*", "", candidate)
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
    return json.loads(candidate)


def complete_tourist_profiles(data):
    """Fill small gaps left by the tourist-profile agent."""
    default_hotels = [
        {"neighbourhood": "Gotic", "lat": 41.3839, "lon": 2.1763, "probability": 0.14},
        {"neighbourhood": "El Raval", "lat": 41.3812, "lon": 2.1686, "probability": 0.11},
        {"neighbourhood": "Dreta Eixample", "lat": 41.3918, "lon": 2.1649, "probability": 0.17},
        {"neighbourhood": "Sagrada Familia", "lat": 41.4036, "lon": 2.1744, "probability": 0.12},
        {"neighbourhood": "La Barceloneta", "lat": 41.3806, "lon": 2.1894, "probability": 0.08},
        {"neighbourhood": "Vila de Gracia", "lat": 41.4017, "lon": 2.1565, "probability": 0.09},
        {"neighbourhood": "Poblenou", "lat": 41.4004, "lon": 2.2038, "probability": 0.08},
        {"neighbourhood": "Montjuic", "lat": 41.3705, "lon": 2.1540, "probability": 0.07},
        {"neighbourhood": "Les Corts", "lat": 41.3860, "lon": 2.1300, "probability": 0.06},
        {"neighbourhood": "Sarria", "lat": 41.3987, "lon": 2.1213, "probability": 0.04},
        {"neighbourhood": "Sant Andreu", "lat": 41.4335, "lon": 2.1903, "probability": 0.04},
    ]
    if len(data.get("hotel_distribution", [])) < 8:
        data["hotel_distribution"] = default_hotels
        data.setdefault("metadata", {})["hotel_distribution_repaired"] = True
    return data


def ollama_generate(prompt, model=DEFAULT_MODEL, temperature=0.1, num_predict=3072, json_mode=False):
    """Call a local Ollama model using the standard library."""
    payload = {
        "model": model_name(model),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    if json_mode:
        payload["format"] = "json"
    request = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))["response"]


class LLMAgent:
    """Small role-based agent wrapper around Ollama."""

    def __init__(self, role, goal, model=DEFAULT_MODEL, output_dir=Path("output_agents/agent_logs")):
        self.role = role
        self.goal = goal
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, task, name, json_mode=False, temperature=0.1, num_predict=3072):
        """Run one agent task and persist the raw answer."""
        prompt = (
            f"You are the agent: {self.role}.\n"
            f"Goal: {self.goal}\n"
            "Follow the task exactly. Be concise. Do not invent explanations outside the requested format.\n\n"
            f"Task:\n{task}"
        )
        answer = ollama_generate(prompt, model=self.model, temperature=temperature, num_predict=num_predict, json_mode=json_mode)
        log_file = self.output_dir / f"{name}.md"
        log_file.write_text(f"# {self.role}\n\n## Prompt\n\n{prompt}\n\n## Answer\n\n{answer}\n", encoding="utf-8")
        return extract_json(answer) if json_mode else answer.strip()


def clean_poi(row):
    """Validate and coerce one LLM-created POI."""
    aliases = {"poi_name": "n", "neighbourhood": "nb", "categories": "cats", "popularity": "pop", "capacity": "cap", "outdoor": "out", "culture": "cult", "local_economy": "local"}
    clean = {key: row.get(key, row.get(aliases.get(key, key))) for key in REQUIRED_POI_FIELDS}
    if not clean["poi_name"] or not clean["neighbourhood"]:
        return None
    if str(clean["neighbourhood"]).strip().isdigit():
        return None
    cats = clean["categories"]
    if isinstance(cats, list):
        cats = ",".join(cats)
    tag_map = {"art": "museum", "history": "museum", "culture": "local", "nature": "park", "church": "religious", "gastronomy": "food", "views": "viewpoint"}
    clean_tags = []
    for tag in str(cats).split(","):
        tag = tag.strip().lower().replace(" ", "_")
        tag = tag_map.get(tag, tag)
        if tag in INTERESTS and tag not in clean_tags:
            clean_tags.append(tag)
    cats = ",".join(clean_tags)
    if not cats:
        return None
    clean["categories"] = cats
    for key in ["lat", "lon", "popularity", "capacity", "cost", "outdoor", "culture", "local_economy", "green"]:
        try:
            clean[key] = float(clean[key])
        except (TypeError, ValueError):
            return None
    clean["popularity"] = min(1.0, max(0.05, clean["popularity"]))
    clean["capacity"] = int(min(1500, max(80, round(clean["capacity"]))))
    clean["cost"] = max(0.0, clean["cost"])
    for key in ["outdoor", "culture", "local_economy", "green"]:
        clean[key] = min(1.0, max(0.0, clean[key]))
    cat_set = set(clean["categories"].split(","))
    if cat_set & {"park", "beach", "viewpoint"}:
        clean["outdoor"] = max(clean["outdoor"], 0.75)
    if cat_set & {"museum", "religious", "architecture", "science"}:
        clean["culture"] = max(clean["culture"], 0.65)
    if cat_set & {"market", "food", "shopping", "local"}:
        clean["local_economy"] = max(clean["local_economy"], 0.70)
    if cat_set & {"park", "beach"}:
        clean["green"] = max(clean["green"], 0.75)
    return clean


def generate_pois(output_dir, model=DEFAULT_MODEL):
    """Use POI curator agents to create a Barcelona POI database by city zone."""
    output_dir = Path(output_dir)
    log_dir = output_dir / "agent_logs"
    agent = LLMAgent(
        "Barcelona POI database curator",
        "Create realistic structured POI records for a sustainable tourism recommender simulation.",
        model=model,
        output_dir=log_dir,
    )
    zones = [
        ("Historic centre", ["Gotic", "El Raval", "El Born", "La Rambla", "La Barceloneta", "Sant Pere"], "Barcelona Cathedral, Santa Maria del Mar, Picasso Museum, Mercat de la Boqueria, Maritime Museum, History Museum of Catalonia, Ciutadella Park, Palau Guell, Barceloneta Beach, Born Cultural Centre"),
        ("Eixample and Sagrada Familia", ["Dreta Eixample", "Esquerra Eixample", "Sagrada Familia", "Sant Antoni", "Fort Pienc", "Nova Esquerra Eixample"], "Sagrada Familia, Casa Batllo, La Pedrera, Casa Amatller, Sant Antoni Market, Mercat dels Encants, Design Museum, Palau Macaya, Egyptian Museum, Joan Miro Park"),
        ("Montjuic and port area", ["Montjuic", "Poble Sec", "Hostafrancs", "Port Vell", "Sants"], "MNAC, Montjuic Castle, Fundacio Joan Miro, Poble Espanyol, Magic Fountain, CaixaForum, Olympic Stadium, Joan Miro Foundation gardens, Hostafrancs Market, Port Vell promenade"),
        ("Gracia and northern viewpoints", ["Vila de Gracia", "La Salut", "El Carmel", "Horta", "Tibidabo", "Guinardo"], "Park Guell, Casa Vicens, Bunkers del Carmel, Temple del Tibidabo, Tibidabo Park, Labyrinth Park of Horta, Gracia squares, Guinardo Park, Mercat de la Llibertat, Fabra Observatory"),
        ("Eastern innovation and beach areas", ["Poblenou", "Glories", "Diagonal Mar", "Sant Marti", "Sant Andreu", "El Clot"], "Glories Tower, Design Museum, Mercat dels Encants, Rambla del Poblenou, Bogatell Beach, Forum Park, Natural Science Museum, Fabra i Coats, Sant Andreu old town, Clot Park"),
        ("Western and mountain areas", ["Les Corts", "Sarria", "Pedralbes", "Sant Gervasi", "Collserola"], "Camp Nou Museum, Pedralbes Monastery, Pedralbes Gardens, Torre Bellesguard, Sarria old town, CosmoCaixa, Carretera de les Aigues, Collserola viewpoints, Monastery gardens, Sant Gervasi market area"),
    ]
    pois = []
    schema = {"pois": [{"n": "POI name", "neighbourhood": "one allowed neighbourhood", "lat": "float", "lon": "float", "cats": "comma tags", "pop": "0-1", "cap": "integer", "cost": "euros", "outdoor": "0-1", "culture": "0-1", "local_economy": "0-1", "green": "0-1"}]}
    for idx, (zone, allowed_neighbourhoods, hints) in enumerate(zones, start=1):
        print(f"  POI zone {idx}/{len(zones)}: {zone}", flush=True)
        task = (
            f"Create exactly 10 distinct Barcelona POIs for this zone: {zone}.\n"
            f"The neighbourhood value must be exactly one of these names, never a number: {', '.join(allowed_neighbourhoods)}.\n"
            f"Useful real-place hints for this zone: {hints}.\n"
            "POI names should be actual attractions, parks, museums, markets, streets, churches or viewpoints, not generic numbered items.\n"
            "Do not repeat any POI name inside the answer. Do not put Sagrada Familia or Casa Batllo outside the Eixample/Sagrada Familia zone.\n"
            f"Use only these category tags, comma separated: {', '.join(INTERESTS)}.\n"
            "Use plausible Barcelona coordinates. Numeric scores must be between 0 and 1, except capacity and cost.\n"
            "Popularity should reflect expected tourist fame, not personal preference. Include famous and less famous places.\n"
            "Use varied numeric values. Do not copy the same scores for every POI.\n"
            "Outdoor guidance: parks, beaches, viewpoints and streets should have outdoor above 0.75; indoor museums and churches below 0.35.\n"
            "Cost guidance: streets, parks, beaches and markets can be 0; museums usually 6-20; iconic paid monuments 15-35.\n"
            "Capacity guidance: small museums/churches 150-450; big parks/beaches/streets 700-1500; markets/monuments 300-900.\n"
            "Use the compact keys from the schema to keep the answer short.\n"
            "Return only valid JSON with this schema:\n"
            f"{json.dumps(schema)}"
        )
        data = extract_json(agent.run(task, f"poi_zone_{idx}", json_mode=False, temperature=0.08, num_predict=2600))
        for row in data.get("pois", data if isinstance(data, list) else []):
            clean = clean_poi(row)
            if clean:
                pois.append(clean)

    seen, unique = set(), []
    for poi in pois:
        key = poi["poi_name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(poi)
    if len(unique) < 50:
        raise RuntimeError(f"POI agents produced only {len(unique)} valid unique POIs.")
    return unique


def generate_tourist_profiles(output_dir, model=DEFAULT_MODEL):
    """Use a tourist modeller agent to create segment profiles."""
    agent = LLMAgent(
        "Tourist population modeller",
        "Create structured tourist segment profiles for an agent-based tourism simulation.",
        model=model,
        output_dir=Path(output_dir) / "agent_logs",
    )
    schema = {
        "segments": [
            {
                "segment": "architecture_fans",
                "probability": 0.2,
                "likes": ["architecture", "museum"],
                "budget_probs": {"low": 0.25, "medium": 0.55, "high": 0.20},
                "mobility_probs": {"walk": 0.25, "bike": 0.10, "transit": 0.45, "mixed": 0.15, "taxi": 0.05},
                "with_kids_probability": 0.1,
                "crowd_aversion_mean": 0.5,
                "sustainability_mean": 0.5,
                "outdoor_mean": 0.5,
            }
        ],
        "hotel_distribution": [{"neighbourhood": "Gotic", "lat": 41.38, "lon": 2.17, "probability": 0.1}],
    }
    task = (
        "Create 6 tourist segments for Barcelona tourism: architecture/culture, religion/history, food/markets, family/green, beach/nightlife and science/museums.\n"
        f"Use only these interest tags in likes: {', '.join(INTERESTS)}.\n"
        "Segment probabilities must sum to 1. Hotel distribution should contain 10 neighbourhoods and probabilities must sum to 1.\n"
        "Return a complete JSON object. Do not include comments, ellipses, placeholders or explanatory text.\n"
        "Return only valid JSON using this schema:\n"
        f"{json.dumps(schema)}"
    )
    data = extract_json(agent.run(task, "tourist_profiles", json_mode=False, temperature=0.08, num_predict=3200))
    return complete_tourist_profiles(data)


def generate_rule_config(pois, output_dir, model=DEFAULT_MODEL):
    """Use a rule analyst agent to create transparent recommender weights."""
    popular = sorted(pois, key=lambda row: row["popularity"], reverse=True)[:10]
    central_names = {"Gotic", "El Raval", "El Born", "La Barceloneta", "Dreta Eixample", "Sagrada Familia", "La Rambla", "Sant Antoni"}
    central_share = sum(row["neighbourhood"] in central_names for row in popular) / len(popular)
    avg_pop = sum(row["popularity"] for row in pois) / len(pois)
    stats = {"n_pois": len(pois), "avg_popularity": round(avg_pop, 4), "central_share_top10": round(central_share, 4), "top10": popular}
    agent = LLMAgent(
        "Recommender rule calibration analyst",
        "Design transparent weights for popularity, personalized and sustainable POI recommenders.",
        model=model,
        output_dir=Path(output_dir) / "agent_logs",
    )
    schema = {
        "popularity": {"popularity": 0.80, "budget": 0.10, "distance": 0.06, "culture": 0.04},
        "personalized": {"interest": 0.55, "popularity": 0.16, "budget": 0.12, "distance": 0.08, "crowd_base": 0.05, "crowd_user": 0.12, "outdoor": 0.04, "culture": 0.03},
        "sustainable": {
            "social": {"crowd": 0.30, "neighbourhood_relief": 0.25, "sustainable_value": 0.20, "local_economy": 0.15, "distance": 0.10},
            "personal": {"interest": 0.48, "budget": 0.15, "distance": 0.16, "outdoor": 0.10, "popularity": 0.06, "culture": 0.05},
            "alpha_base": 0.42,
            "alpha_user": 0.28,
            "diversity_rule": True,
        },
        "metadata": {"agent_reason": "string"},
    }
    task = (
        "Given the following POI statistics, return recommender weights for three strategies.\n"
        "The sustainable strategy must reduce crowding and central hotspot pressure without ignoring tourist interests.\n"
        "Weights inside popularity, personalized, sustainable.social and sustainable.personal should each be easy to interpret and roughly sum to 1.\n"
        "Return only valid JSON using this schema:\n"
        f"{json.dumps(schema)}\n\nPOI statistics:\n{json.dumps(stats)[:6000]}"
    )
    return extract_json(agent.run(task, "rule_config", json_mode=False, temperature=0.05, num_predict=1800))


def write_agent_interpretation(summary_text, output_dir, model=DEFAULT_MODEL):
    """Use an analyst agent to write the final interpretation."""
    agent = LLMAgent(
        "Sustainable tourism evaluation analyst",
        "Interpret simulation results for a responsible tourism recommender comparison.",
        model=model,
        output_dir=Path(output_dir) / "agent_logs",
    )
    task = (
        "Write a concise Markdown interpretation of these verified simulation metrics.\n"
        "Do not invent numbers. Explain trade-offs between satisfaction, crowding, central pressure, hotspot pressure and distribution.\n\n"
        f"{summary_text}"
    )
    return agent.run(task, "final_interpretation", json_mode=False, temperature=0.05, num_predict=2048)


def write_input_audit(input_summary, output_dir, model=DEFAULT_MODEL):
    """Use an audit agent to describe the generated simulation inputs."""
    agent = LLMAgent(
        "Synthetic data audit analyst",
        "Audit LLM-generated POI, tourist and recommender-rule inputs for a seminar simulation.",
        model=model,
        output_dir=Path(output_dir) / "agent_logs",
    )
    task = (
        "Write a short Markdown audit of these generated inputs.\n"
        "Explain why they are coherent for a simulation, but be explicit that they are synthetic and not official measurements.\n"
        "Do not invent new numbers or new POIs.\n\n"
        f"{input_summary}"
    )
    return agent.run(task, "input_audit", json_mode=False, temperature=0.05, num_predict=2048)
