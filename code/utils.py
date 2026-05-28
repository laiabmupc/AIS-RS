import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RANDOM_SEED = 42

# The categories are the "vocabulary" used to match tourists and POIs.
INTERESTS = [
    "architecture",
    "religious",
    "museum",
    "park",
    "market",
    "food",
    "beach",
    "viewpoint",
    "shopping",
    "nightlife",
    "family",
    "science",
    "local",
]


CENTRAL_NEIGHBOURHOODS = {
    "Gotic",
    "El Raval",
    "La Rambla",
    "El Born",
    "La Barceloneta",
    "Dreta Eixample",
    "Sagrada Familia",
    "Sant Pere",
}

STRATEGIES = ["popularity", "personalized", "sustainable"]


STRATEGY_COLORS = {
    "popularity": "#1F4E79",
    "personalized": "#73A9C2",
    "sustainable": "#0B2E4A",
}


DEFAULT_RULE_CONFIG = {
    "popularity": {
        "popularity": 0.80,
        "budget": 0.10,
        "distance": 0.06,
        "culture": 0.04,
    },
    "personalized": {
        "interest": 0.55,
        "popularity": 0.16,
        "budget": 0.12,
        "distance": 0.08,
        "crowd_base": 0.05,
        "crowd_user": 0.12,
        "outdoor": 0.04,
        "culture": 0.03,
    },
    "sustainable": {
        "social": {
            "crowd": 0.30,
            "neighbourhood_relief": 0.25,
            "sustainable_value": 0.20,
            "local_economy": 0.15,
            "distance": 0.10,
        },
        "personal": {
            "interest": 0.48,
            "budget": 0.15,
            "distance": 0.16,
            "outdoor": 0.10,
            "popularity": 0.06,
            "culture": 0.05,
        },
        "alpha_base": 0.42,
        "alpha_user": 0.28,
    },
}


def finalize_pois(pois):
    """Validate and enrich a structured POI table."""
    pois = pois.copy()
    required = [
        "poi_name",
        "neighbourhood",
        "lat",
        "lon",
        "categories",
        "popularity",
        "capacity",
        "cost",
        "outdoor",
        "culture",
        "local_economy",
        "green",
    ]
    missing = [col for col in required if col not in pois.columns]
    if missing:
        raise ValueError(f"Missing POI columns: {missing}")

    if "poi_id" not in pois.columns:
        pois.insert(0, "poi_id", range(len(pois)))
    else:
        pois["poi_id"] = range(len(pois))

    pois["categories"] = (
        pois["categories"]
        .astype(str)
        .str.lower()
        .str.replace(" ", "", regex=False)
    )
    for column in ["lat", "lon", "popularity", "capacity", "cost", "outdoor", "culture", "local_economy", "green"]:
        pois[column] = pd.to_numeric(pois[column], errors="coerce")

    pois["popularity"] = pois["popularity"].clip(0, 1)
    pois["outdoor"] = pois["outdoor"].clip(0, 1)
    pois["culture"] = pois["culture"].clip(0, 1)
    pois["local_economy"] = pois["local_economy"].clip(0, 1)
    pois["green"] = pois["green"].clip(0, 1)
    pois["cost"] = pois["cost"].clip(lower=0)

    # We simulate one time slot at a time, so capacity is treated as a slot
    # capacity proxy, not as the total daily capacity of the attraction.
    pois["capacity"] = pois["capacity"].round().astype(int)
    pois["capacity"] = pois["capacity"].clip(lower=50)

    # A simple proxy: famous central places start with higher pressure.
    pois["is_central"] = pois["neighbourhood"].isin(CENTRAL_NEIGHBOURHOODS)
    pois["baseline_pressure"] = 0.65 * pois["popularity"] + 0.20 * pois["is_central"].astype(int)

    # Sustainability is multi-criteria, not only ecological.
    pois["sustainable_value"] = (
        0.30 * pois["culture"]
        + 0.25 * pois["local_economy"]
        + 0.25 * pois["green"]
        + 0.20 * (1 - pois["baseline_pressure"])
    )

    # Convert category strings into one-hot columns for easy scoring.
    for interest in INTERESTS:
        pois[interest] = pois["categories"].str.contains(interest).astype(int)

    return pois


def load_pois_from_file(path):
    """Load a prepared POI database."""
    path = str(path)
    if path.endswith(".json"):
        pois = pd.read_json(path)
    else:
        pois = pd.read_csv(path)
    return finalize_pois(pois)


def normalise_tourist_segments(segments):
    """Convert tourist segment data into the simulator schema."""
    if isinstance(segments, str):
        with open(segments, encoding="utf-8") as file:
            segments = json.load(file)
    if isinstance(segments, dict) and "segments" in segments:
        segments = segments["segments"]
    if isinstance(segments, dict):
        return segments

    normalised = {}
    for item in segments:
        name = item.get("segment") or item.get("name")
        if not name:
            raise ValueError("Every tourist segment needs a 'segment' or 'name' field.")
        normalised[name] = {
            "p": float(item.get("probability", item.get("p", 1 / len(segments)))),
            "likes": item.get("likes", item.get("interests", [])),
            "budget_probs": item.get("budget_probs", {"low": 0.32, "medium": 0.48, "high": 0.20}),
            "mobility_probs": item.get("mobility_probs", {"walk": 0.25, "bike": 0.10, "transit": 0.42, "mixed": 0.17, "taxi": 0.06}),
            "with_kids_probability": float(item.get("with_kids_probability", 0.12)),
            "crowd_aversion_mean": float(item.get("crowd_aversion_mean", 0.52)),
            "sustainability_mean": float(item.get("sustainability_mean", 0.45)),
            "outdoor_mean": float(item.get("outdoor_mean", 0.50)),
        }
    return normalised


def normalise_hotel_distribution(hotels):
    """Validate the accommodation-area distribution."""
    if not hotels:
        raise ValueError("The tourist profile file needs a non-empty hotel_distribution list.")

    normalised = []
    for item in hotels:
        normalised.append(
            {
                "neighbourhood": item["neighbourhood"],
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "p": float(item.get("probability", item.get("p", 0))),
            }
        )

    total = sum(item["p"] for item in normalised)
    if total <= 0:
        raise ValueError("hotel_distribution probabilities must sum to a positive value.")
    for item in normalised:
        item["p"] = item["p"] / total
    return normalised


def load_tourist_profiles(path):
    """Load tourist segments and accommodation areas."""
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    return {
        "segments": normalise_tourist_segments(data),
        "hotel_distribution": normalise_hotel_distribution(data.get("hotel_distribution")),
    }


def merge_weight_group(source, defaults):
    """Keep only expected rule weights and cast them to numeric values."""
    source = source or {}
    return {key: round(max(0.0, float(source.get(key, value))), 4) for key, value in defaults.items()}


def normalise_rule_config(raw):
    """Validate and complete a rule configuration."""
    raw = raw or {}
    config = json.loads(json.dumps(DEFAULT_RULE_CONFIG))
    config["popularity"] = merge_weight_group(raw.get("popularity"), DEFAULT_RULE_CONFIG["popularity"])
    config["personalized"] = merge_weight_group(raw.get("personalized"), DEFAULT_RULE_CONFIG["personalized"])
    config["sustainable"]["social"] = merge_weight_group(raw.get("sustainable", {}).get("social"), DEFAULT_RULE_CONFIG["sustainable"]["social"])
    config["sustainable"]["personal"] = merge_weight_group(raw.get("sustainable", {}).get("personal"), DEFAULT_RULE_CONFIG["sustainable"]["personal"])
    config["sustainable"]["alpha_base"] = float(raw.get("sustainable", {}).get("alpha_base", DEFAULT_RULE_CONFIG["sustainable"]["alpha_base"]))
    config["sustainable"]["alpha_user"] = float(raw.get("sustainable", {}).get("alpha_user", DEFAULT_RULE_CONFIG["sustainable"]["alpha_user"]))
    config["sustainable"]["alpha_base"] = round(float(np.clip(config["sustainable"]["alpha_base"], 0.0, 0.8)), 4)
    config["sustainable"]["alpha_user"] = round(float(np.clip(config["sustainable"]["alpha_user"], 0.0, 0.8)), 4)
    config["metadata"] = raw.get("metadata", {})
    return config


def load_rule_config(path):
    """Load the recommender rule configuration."""
    with open(path, encoding="utf-8") as file:
        return normalise_rule_config(json.load(file))


def sample_around_mean(rng, mean, strength=8):
    """Sample a 0-1 value around a segment mean."""
    mean = min(0.95, max(0.05, float(mean)))
    return rng.beta(mean * strength, (1 - mean) * strength)


def create_tourists(n_tourists, tourist_profiles, seed=RANDOM_SEED):
    """Generate individual tourists from segment profiles."""
    rng = np.random.default_rng(seed)
    segments = tourist_profiles["segments"]
    hotels = tourist_profiles["hotel_distribution"]

    segment_names = list(segments.keys())
    segment_probs = np.array([segments[s]["p"] for s in segment_names])
    segment_probs = segment_probs / segment_probs.sum()
    hotel_probs = np.array([h["p"] for h in hotels])

    rows = []
    for tourist_id in range(n_tourists):
        segment = rng.choice(segment_names, p=segment_probs)
        segment_info = segments[segment]

        budget_probs = segment_info.get("budget_probs", {"low": 0.32, "medium": 0.48, "high": 0.20})
        budget_names = list(budget_probs.keys())
        budget_values = np.array(list(budget_probs.values()), dtype=float)
        budget_values = budget_values / budget_values.sum()
        budget = rng.choice(budget_names, p=budget_values)

        if budget == "low":
            max_cost = rng.normal(7, 2)
        elif budget == "medium":
            max_cost = rng.normal(18, 5)
        else:
            max_cost = rng.normal(38, 8)
        max_cost = max(0, min(55, max_cost))

        mobility_probs = segment_info.get("mobility_probs", {"walk": 0.25, "bike": 0.10, "transit": 0.42, "mixed": 0.17, "taxi": 0.06})
        mobility_names = list(mobility_probs.keys())
        mobility_values = np.array(list(mobility_probs.values()), dtype=float)
        mobility_values = mobility_values / mobility_values.sum()
        mobility = rng.choice(mobility_names, p=mobility_values)
        if mobility == "walk":
            max_distance = rng.uniform(1.2, 3.5)
        elif mobility == "bike":
            max_distance = rng.uniform(3.5, 7.5)
        elif mobility == "transit":
            max_distance = rng.uniform(5.0, 12.0)
        elif mobility == "mixed":
            max_distance = rng.uniform(3.0, 9.0)
        else:
            max_distance = rng.uniform(8.0, 16.0)

        with_kids_probability = segment_info.get("with_kids_probability", 0.30 if segment == "family_green" else 0.12)
        with_kids = rng.random() < with_kids_probability
        if with_kids:
            max_distance *= 0.85

        hotel_idx = rng.choice(len(hotels), p=hotel_probs)
        hotel = hotels[hotel_idx]
        hotel_name, hotel_lat, hotel_lon = hotel["neighbourhood"], hotel["lat"], hotel["lon"]

        # Start coordinates are around the hotel neighbourhood, not exactly the same point.
        start_lat = hotel_lat + rng.normal(0, 0.004)
        start_lon = hotel_lon + rng.normal(0, 0.004)

        row = {
            "tourist_id": tourist_id,
            "segment": segment,
            "budget": budget,
            "max_cost": max_cost,
            "mobility": mobility,
            "max_distance": max_distance,
            "crowd_aversion": sample_around_mean(rng, segment_info.get("crowd_aversion_mean", 0.52)),
            "sustainability_sensitivity": sample_around_mean(rng, segment_info.get("sustainability_mean", 0.45)),
            "outdoor_preference": sample_around_mean(rng, segment_info.get("outdoor_mean", 0.50)),
            "with_kids": with_kids,
            "hotel_neighbourhood": hotel_name,
            "current_lat": start_lat,
            "current_lon": start_lon,
            "visited": set(),
        }

        # Interest weights: liked categories get a larger value.
        for interest in INTERESTS:
            row[interest] = 0.05
        for interest in segments[segment]["likes"]:
            row[interest] += rng.uniform(0.45, 0.85)

        total = sum(row[interest] for interest in INTERESTS)
        for interest in INTERESTS:
            row[interest] = row[interest] / total

        rows.append(row)

    return pd.DataFrame(rows)


def distance_km(lat1, lon1, lat2, lon2):
    """Approximate geographic distance using the haversine formula."""
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def gini(values):
    """Measure concentration. 0 means equal distribution, 1 means very unequal."""
    x = np.sort(np.array(values, dtype=float))
    if x.sum() == 0:
        return 0
    n = len(x)
    return (2 * np.sum((np.arange(1, n + 1)) * x)) / (n * x.sum()) - (n + 1) / n


def entropy(values):
    """Normalised entropy for the distribution of visits over neighbourhoods."""
    x = np.array(values, dtype=float)
    if x.sum() == 0:
        return 0
    p = x[x > 0] / x.sum()
    return -(p * np.log(p)).sum() / np.log(len(x))


def add_common_scores(pois, tourist, current_crowd, neighbourhood_visits):
    """Calculate the same basic scores for all recommender strategies."""
    scores = pois.copy()

    interest_cols = pois[INTERESTS].values
    tourist_interests = tourist[INTERESTS].values.astype(float)
    scores["interest_match"] = interest_cols.dot(tourist_interests)

    dist = distance_km(tourist["current_lat"], tourist["current_lon"], scores["lat"], scores["lon"])
    scores["distance_km"] = dist
    scores["distance_score"] = np.exp(-dist / max(tourist["max_distance"], 0.5))

    # Budget is a soft constraint. A POI can still be selected, but it loses score.
    extra_cost = np.maximum(0, scores["cost"] - tourist["max_cost"])
    scores["budget_score"] = np.clip(1 - extra_cost / (tourist["max_cost"] + 12), 0, 1)

    scores["current_crowd"] = current_crowd[scores["poi_id"].values]
    scores["crowd_ratio"] = scores["current_crowd"] / scores["capacity"]
    scores["crowd_score"] = np.clip(1 - scores["crowd_ratio"] / 1.35, 0, 1)

    scores["outdoor_match"] = 1 - abs(scores["outdoor"] - tourist["outdoor_preference"])

    # Neighbourhood relief rewards areas that have received fewer visits so far.
    if neighbourhood_visits.sum() == 0:
        scores["neighbourhood_relief"] = 1.0
    else:
        max_visits = neighbourhood_visits.max()
        used = scores["neighbourhood"].map(neighbourhood_visits).fillna(0)
        scores["neighbourhood_relief"] = 1 - used / max(max_visits, 1)

    if tourist["with_kids"]:
        scores["interest_match"] += 0.06 * scores["family"]
        scores["interest_match"] -= 0.05 * scores["nightlife"]

    return scores


def recommend_pois(strategy, pois, tourist, current_crowd, neighbourhood_visits, k=5, rule_config=None):
    """Return a top-k recommendation list for one tourist.

    The function also returns the scored candidate table, so later we can reuse
    it for evaluation instead of recalculating everything.
    """
    if rule_config is None:
        rule_config = DEFAULT_RULE_CONFIG

    candidate_pois = pois[~pois["poi_id"].isin(tourist["visited"])].copy()
    scored = add_common_scores(candidate_pois, tourist, current_crowd, neighbourhood_visits)

    if strategy == "popularity":
        w = rule_config["popularity"]
        scored["score"] = (
            w["popularity"] * scored["popularity"]
            + w["budget"] * scored["budget_score"]
            + w["distance"] * scored["distance_score"]
            + w["culture"] * scored["culture"]
        )

    elif strategy == "personalized":
        w = rule_config["personalized"]
        scored["score"] = (
            w["interest"] * scored["interest_match"]
            + w["popularity"] * scored["popularity"]
            + w["budget"] * scored["budget_score"]
            + w["distance"] * scored["distance_score"]
            + (w["crowd_base"] + w["crowd_user"] * tourist["crowd_aversion"]) * scored["crowd_score"]
            + w["outdoor"] * scored["outdoor_match"]
            + w["culture"] * scored["culture"]
        )

    elif strategy == "sustainable":
        social_w = rule_config["sustainable"]["social"]
        personal_w = rule_config["sustainable"]["personal"]
        social_score = (
            social_w["crowd"] * scored["crowd_score"]
            + social_w["neighbourhood_relief"] * scored["neighbourhood_relief"]
            + social_w["sustainable_value"] * scored["sustainable_value"]
            + social_w["local_economy"] * scored["local_economy"]
            + social_w["distance"] * scored["distance_score"]
        )
        personal_score = (
            personal_w["interest"] * scored["interest_match"]
            + personal_w["budget"] * scored["budget_score"]
            + personal_w["distance"] * scored["distance_score"]
            + personal_w["outdoor"] * scored["outdoor_match"]
            + personal_w["popularity"] * scored["popularity"]
            + personal_w["culture"] * scored["culture"]
        )

        # More sustainability-sensitive tourists accept more collective criteria.
        alpha = (
            rule_config["sustainable"]["alpha_base"]
            + rule_config["sustainable"]["alpha_user"] * tourist["sustainability_sensitivity"]
        )
        scored["score"] = (1 - alpha) * personal_score + alpha * social_score

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    ordered = scored.sort_values("score", ascending=False)

    # For the sustainable strategy, try to avoid putting the whole list in the
    # same neighbourhood. This is simple and easy to explain in the report.
    if strategy == "sustainable" and rule_config["sustainable"].get("diversity_rule", True):
        diverse = ordered.drop_duplicates("neighbourhood").head(k)
        if len(diverse) < k:
            missing = k - len(diverse)
            extra = ordered[~ordered["poi_id"].isin(diverse["poi_id"])].head(missing)
            ordered = pd.concat([diverse, extra])
        else:
            ordered = diverse

    recs = ordered.head(k)["poi_id"].astype(int).tolist()
    return recs, scored


def tourist_utility(recommendations, pois, tourist, current_crowd):
    """Estimate how attractive each recommended POI is for a tourist."""
    scored = add_common_scores(pois[pois["poi_id"].isin(recommendations)], tourist, current_crowd, pd.Series(dtype=float))

    utility = (
        0.46 * scored["interest_match"]
        + 0.13 * scored["popularity"]
        + 0.13 * scored["budget_score"]
        + 0.10 * scored["distance_score"]
        + (0.05 + 0.13 * tourist["crowd_aversion"]) * scored["crowd_score"]
        + 0.08 * tourist["sustainability_sensitivity"] * scored["sustainable_value"]
        + 0.05 * scored["outdoor_match"]
    )

    if tourist["with_kids"]:
        utility += 0.04 * scored["family"]
        utility -= 0.05 * scored["nightlife"]

    scored["utility"] = utility.clip(0, 1)
    return scored


def choose_one_poi(scored_recommendations, rng):
    """Choose one POI from the recommendation list using softmax probabilities."""
    utility = scored_recommendations["utility"].values
    utility = utility - utility.max()
    probabilities = np.exp(utility / 0.11)
    probabilities = probabilities / probabilities.sum()
    selected_position = rng.choice(len(scored_recommendations), p=probabilities)
    return scored_recommendations.iloc[selected_position]


def recommendation_quality(recommendations, pois, tourist, scored_candidates):
    """Compute simple recommendation metrics for one top-5 list."""
    # A POI is considered relevant if it is in the best 28% for this tourist.
    relevance = (
        0.58 * scored_candidates["interest_match"]
        + 0.17 * scored_candidates["budget_score"]
        + 0.10 * scored_candidates["distance_score"]
        + 0.08 * scored_candidates["outdoor_match"]
        + 0.07 * scored_candidates["culture"]
    )
    threshold = relevance.quantile(0.72)
    relevant_pois = set(scored_candidates.loc[relevance >= threshold, "poi_id"])

    precision = len(set(recommendations) & relevant_pois) / len(recommendations)
    recall = len(set(recommendations) & relevant_pois) / max(len(relevant_pois), 1)

    rec_rows = pois[pois["poi_id"].isin(recommendations)]
    categories = rec_rows["categories"].apply(lambda x: set(x.split(","))).tolist()
    similarities = []
    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            union = categories[i] | categories[j]
            intersection = categories[i] & categories[j]
            similarities.append(len(intersection) / len(union))
    diversity = 1 - np.mean(similarities) if similarities else 0

    budget_ok = (rec_rows["cost"] <= tourist["max_cost"] * 1.15 + 1).mean()
    mean_sustainable = rec_rows["sustainable_value"].mean()

    return {
        "precision_at_5": precision,
        "recall_at_5": recall,
        "diversity": diversity,
        "constraint_respect": budget_ok,
        "mean_recommendation_sustainability": mean_sustainable,
    }


def estimate_co2(row, tourist):
    """Very simple CO2 proxy based on distance and mobility mode."""
    if tourist["mobility"] in ["walk", "bike"]:
        return 0.0
    if tourist["mobility"] == "transit":
        return 0.0 if row["distance_km"] <= 1.2 else row["distance_km"] * 0.035
    if tourist["mobility"] == "mixed":
        return 0.0 if row["distance_km"] <= tourist["max_distance"] else row["distance_km"] * 0.060
    return row["distance_km"] * 0.180


def run_simulation(strategy, pois, tourists, steps=5, seed=RANDOM_SEED, rule_config=None):
    """Run one complete scenario for one recommender strategy."""
    rng = np.random.default_rng(seed)
    tourists = tourists.copy(deep=True)
    tourists["visited"] = tourists["visited"].apply(lambda visited: set(visited))

    visit_rows = []
    quality_rows = []
    crowd_rows = []

    total_poi_visits = pd.Series(0, index=pois["poi_id"])
    neighbourhood_visits = pd.Series(0, index=sorted(pois["neighbourhood"].unique()))

    for step in range(1, steps + 1):
        current_crowd = np.zeros(len(pois), dtype=int)

        # Random order avoids giving the same tourists priority in every step.
        for tourist_index in rng.permutation(tourists.index):
            tourist = tourists.loc[tourist_index]
            recs, scored_candidates = recommend_pois(
                strategy,
                pois,
                tourist,
                current_crowd,
                neighbourhood_visits,
                k=5,
                rule_config=rule_config,
            )

            quality = recommendation_quality(recs, pois, tourist, scored_candidates)
            quality["strategy"] = strategy
            quality["step"] = step
            rec_rows = pois.set_index("poi_id").loc[recs]
            quality["recommended_poi_ids"] = "|".join(map(str, recs))
            quality["recommended_poi_names"] = " | ".join(rec_rows["poi_name"].astype(str))
            quality["recommended_neighbourhoods"] = " | ".join(rec_rows["neighbourhood"].astype(str))
            quality_rows.append(quality)

            scored_recs = tourist_utility(recs, pois, tourist, current_crowd)
            chosen = choose_one_poi(scored_recs, rng)
            poi_id = int(chosen["poi_id"])

            current_crowd[poi_id] += 1
            total_poi_visits.loc[poi_id] += 1
            neighbourhood_visits.loc[chosen["neighbourhood"]] += 1

            tourists.at[tourist_index, "current_lat"] = chosen["lat"]
            tourists.at[tourist_index, "current_lon"] = chosen["lon"]
            tourists.at[tourist_index, "visited"].add(poi_id)

            visit = {
                "strategy": strategy,
                "step": step,
                "tourist_id": tourist["tourist_id"],
                "segment": tourist["segment"],
                "poi_id": poi_id,
                "poi_name": chosen["poi_name"],
                "neighbourhood": chosen["neighbourhood"],
                "is_central": chosen["is_central"],
                "satisfaction": chosen["utility"],
                "interest_match": chosen["interest_match"],
                "distance_km": chosen["distance_km"],
                "cost": chosen["cost"],
                "crowd_ratio_after_visit": current_crowd[poi_id] / chosen["capacity"],
                "sustainable_value": chosen["sustainable_value"],
                "local_economy": chosen["local_economy"],
                "green": chosen["green"],
                "baseline_pressure": chosen["baseline_pressure"],
            }
            visit["co2_kg"] = estimate_co2(visit, tourist)
            visit_rows.append(visit)

        for _, poi in pois.iterrows():
            crowd_rows.append(
                {
                    "strategy": strategy,
                    "step": step,
                    "poi_id": poi["poi_id"],
                    "poi_name": poi["poi_name"],
                    "neighbourhood": poi["neighbourhood"],
                    "visits_this_step": current_crowd[int(poi["poi_id"])],
                    "capacity": poi["capacity"],
                    "crowd_ratio": current_crowd[int(poi["poi_id"])] / poi["capacity"],
                }
            )

    visits = pd.DataFrame(visit_rows)
    quality = pd.DataFrame(quality_rows)
    crowd = pd.DataFrame(crowd_rows)
    return visits, quality, crowd


def summarise_results(strategy, pois, visits, quality, crowd):
    """Create one row with the main comparison metrics."""
    poi_counts = visits.groupby("poi_id").size().reindex(pois["poi_id"], fill_value=0)
    neighbourhood_counts = visits.groupby("neighbourhood").size().reindex(sorted(pois["neighbourhood"].unique()), fill_value=0)

    summary = {
        "strategy": strategy,
        "total_visits": len(visits),
        "avg_satisfaction": visits["satisfaction"].mean(),
        "avg_interest_match": visits["interest_match"].mean(),
        "avg_distance_km": visits["distance_km"].mean(),
        "total_co2_kg": visits["co2_kg"].sum(),
        "avg_visit_sustainability": visits["sustainable_value"].mean(),
        "avg_local_economy": visits["local_economy"].mean(),
        "green_visit_share": (visits["green"] >= 0.80).mean(),
        "central_visit_share": visits["is_central"].mean(),
        "hotspot_visit_share": (visits["baseline_pressure"] >= 0.75).mean(),
        "poi_coverage": (poi_counts > 0).mean(),
        "neighbourhood_entropy": entropy(neighbourhood_counts),
        "poi_visit_gini": gini(poi_counts),
        "neighbourhood_visit_gini": gini(neighbourhood_counts),
        "top_5_poi_visit_share": poi_counts.sort_values(ascending=False).head(5).sum() / len(visits),
        "top_3_neighbourhood_visit_share": neighbourhood_counts.sort_values(ascending=False).head(3).sum() / len(visits),
        "overcrowding_index": np.maximum(0, crowd["visits_this_step"] - crowd["capacity"]).div(crowd["capacity"]).mean(),
        "max_slot_crowd_ratio": crowd["crowd_ratio"].max(),
        "visit_over_capacity_share": (visits["crowd_ratio_after_visit"] > 1).mean(),
    }

    for metric in [
        "precision_at_5",
        "recall_at_5",
        "diversity",
        "constraint_respect",
        "mean_recommendation_sustainability",
    ]:
        summary[f"avg_{metric}"] = quality[metric].mean()

    return pd.DataFrame([summary])


def create_detail_tables(strategy, pois, visits, crowd):
    """Create POI-level and neighbourhood-level result tables."""
    poi_visits = visits.groupby("poi_id").size().rename("visits")
    poi_crowd = crowd.groupby("poi_id")["crowd_ratio"].max().rename("max_slot_crowd_ratio")

    poi_table = pois[
        ["poi_id", "poi_name", "neighbourhood", "popularity", "capacity", "baseline_pressure", "sustainable_value"]
    ].merge(poi_visits, on="poi_id", how="left")
    poi_table = poi_table.merge(poi_crowd, on="poi_id", how="left")
    poi_table["visits"] = poi_table["visits"].fillna(0).astype(int)
    poi_table["strategy"] = strategy
    poi_table = poi_table.sort_values("visits", ascending=False)

    neighbourhood_table = visits.groupby("neighbourhood").agg(
        visits=("poi_id", "size"),
        avg_satisfaction=("satisfaction", "mean"),
        central=("is_central", "max"),
    )
    neighbourhood_table["visit_share"] = neighbourhood_table["visits"] / neighbourhood_table["visits"].sum()
    neighbourhood_table["strategy"] = strategy
    neighbourhood_table = neighbourhood_table.reset_index().sort_values("visits", ascending=False)

    return poi_table, neighbourhood_table


def plot_results(summary, neighbourhood_table, poi_table, output_dir):
    """Save a few simple figures for the report."""
    metrics = [
        ("avg_satisfaction", "Mean satisfaction"),
        ("max_slot_crowd_ratio", "Maximum crowd ratio"),
        ("neighbourhood_entropy", "Neighbourhood entropy"),
        ("top_5_poi_visit_share", "Top-5 POI share"),
        ("central_visit_share", "Central visit share"),
        ("avg_diversity", "Recommendation diversity"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for ax, (metric, title) in zip(axes.flat, metrics):
        values = [summary.loc[summary["strategy"] == strategy, metric].iloc[0] for strategy in STRATEGIES]
        ax.bar(
            STRATEGIES,
            values,
            color=[STRATEGY_COLORS[strategy] for strategy in STRATEGIES],
            width=0.62,
        )
        ax.set_title(title.upper(), fontsize=12, weight="bold")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(output_dir / "strategy_comparison.png", dpi=180)
    plt.close(fig)

    top_neighbourhoods = (
        neighbourhood_table.groupby("neighbourhood")["visits"].sum().sort_values(ascending=False).head(12).index
    )
    plot_data = neighbourhood_table[neighbourhood_table["neighbourhood"].isin(top_neighbourhoods)]
    pivot = plot_data.pivot_table(
        index="neighbourhood",
        columns="strategy",
        values="visit_share",
        fill_value=0,
    )
    pivot = pivot.reindex(columns=STRATEGIES).sort_values("popularity", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    y_positions = np.arange(len(pivot))
    bar_height = 0.24
    for offset, strategy in zip([-bar_height, 0, bar_height], STRATEGIES):
        ax.barh(
            y_positions + offset,
            pivot[strategy],
            height=bar_height,
            color=STRATEGY_COLORS[strategy],
            label=strategy,
        )
    ax.set_yticks(y_positions)
    ax.set_yticklabels(pivot.index)
    ax.set_title("DISTRIBUTION OF VISITS BY NEIGHBOURHOOD", fontsize=12, weight="bold")
    ax.set_xlabel("Share of visits")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "neighbourhood_distribution.png", dpi=180)
    plt.close(fig)

    top_pois = poi_table.groupby("poi_name")["visits"].sum().sort_values(ascending=False).head(12).index
    plot_data = poi_table[poi_table["poi_name"].isin(top_pois)]
    pivot = plot_data.pivot_table(
        index="poi_name",
        columns="strategy",
        values="max_slot_crowd_ratio",
        fill_value=0,
    )
    pivot = pivot.reindex(columns=STRATEGIES).sort_values("popularity", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    y_positions = np.arange(len(pivot))
    for offset, strategy in zip([-bar_height, 0, bar_height], STRATEGIES):
        ax.barh(
            y_positions + offset,
            pivot[strategy],
            height=bar_height,
            color=STRATEGY_COLORS[strategy],
            label=strategy,
        )
    ax.axvline(1.0, color="#C44E52", linestyle="--", linewidth=1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(pivot.index)
    ax.set_title("PEAK CROWDING AT MAIN POIS", fontsize=12, weight="bold")
    ax.set_xlabel("Maximum crowd / capacity")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "top_poi_crowding.png", dpi=180)
    plt.close(fig)
