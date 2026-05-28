import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INTERESTS = ["architecture", "religious", "museum", "park", "market", "food", "beach", "viewpoint", "shopping", "nightlife", "family", "science", "local"]
STRATEGIES = ["popularity", "personalized", "sustainable"]
STRATEGY_COLORS = {"popularity": "#1F4E79", "personalized": "#6FA8C9", "sustainable": "#0B2E4A"}
CENTRAL_KEYS = ["gotic", "gothic", "raval", "born", "barceloneta", "rambla", "eixample", "sagrada", "sant pere"]
DEFAULT_RULE_CONFIG = {
    "popularity": {"popularity": 0.80, "budget": 0.10, "distance": 0.06, "culture": 0.04},
    "personalized": {"interest": 0.55, "popularity": 0.16, "budget": 0.12, "distance": 0.08, "crowd_base": 0.05, "crowd_user": 0.12, "outdoor": 0.04, "culture": 0.03},
    "sustainable": {
        "social": {"crowd": 0.30, "neighbourhood_relief": 0.25, "sustainable_value": 0.20, "local_economy": 0.15, "distance": 0.10},
        "personal": {"interest": 0.48, "budget": 0.15, "distance": 0.16, "outdoor": 0.10, "popularity": 0.06, "culture": 0.05},
        "alpha_base": 0.42,
        "alpha_user": 0.28,
        "diversity_rule": True}}


def normalise_group(source, defaults):
    """Keep expected weights and scale them to a clean convex combination."""
    values = {key: max(0.0, float((source or {}).get(key, value))) for key, value in defaults.items()}
    total = sum(values.values())
    return {key: round(value / total, 4) for key, value in values.items()} if total > 0 else defaults


def normalise_rule_config(raw):
    """Validate an agent-generated rule configuration."""
    raw = raw or {}
    config = json.loads(json.dumps(DEFAULT_RULE_CONFIG))
    config["popularity"] = normalise_group(raw.get("popularity"), DEFAULT_RULE_CONFIG["popularity"])
    config["personalized"] = normalise_group(raw.get("personalized"), DEFAULT_RULE_CONFIG["personalized"])
    config["sustainable"]["social"] = normalise_group(raw.get("sustainable", {}).get("social"), DEFAULT_RULE_CONFIG["sustainable"]["social"])
    config["sustainable"]["personal"] = normalise_group(raw.get("sustainable", {}).get("personal"), DEFAULT_RULE_CONFIG["sustainable"]["personal"])
    config["sustainable"]["alpha_base"] = round(float(np.clip(raw.get("sustainable", {}).get("alpha_base", 0.42), 0.0, 0.85)), 4)
    config["sustainable"]["alpha_user"] = round(float(np.clip(raw.get("sustainable", {}).get("alpha_user", 0.28), 0.0, 0.85)), 4)
    config["sustainable"]["diversity_rule"] = bool(raw.get("sustainable", {}).get("diversity_rule", True))
    config["metadata"] = raw.get("metadata", {})
    return config


def finalize_pois(pois):
    """Coerce the agent-generated POI database into the simulator schema."""
    pois = pois.copy()
    required = ["poi_name", "neighbourhood", "lat", "lon", "categories", "popularity", "capacity", "cost", "outdoor", "culture", "local_economy", "green"]
    missing = [column for column in required if column not in pois.columns]
    if missing:
        raise ValueError(f"Missing POI columns: {missing}")
    pois = pois.dropna(subset=["poi_name", "neighbourhood", "lat", "lon"]).reset_index(drop=True)
    pois.insert(0, "poi_id", range(len(pois)))
    pois["categories"] = pois["categories"].astype(str).str.lower().str.replace(" ", "", regex=False)
    for column in ["lat", "lon", "popularity", "capacity", "cost", "outdoor", "culture", "local_economy", "green"]:
        pois[column] = pd.to_numeric(pois[column], errors="coerce")
    pois = pois.dropna(subset=["lat", "lon", "popularity", "capacity", "cost", "outdoor", "culture", "local_economy", "green"]).reset_index(drop=True)
    pois["poi_id"] = range(len(pois))
    pois["popularity"] = pois["popularity"].clip(0.05, 1.0)
    pois["capacity"] = pois["capacity"].round().astype(int).clip(lower=60)
    pois["cost"] = pois["cost"].clip(lower=0)
    for column in ["outdoor", "culture", "local_economy", "green"]:
        pois[column] = pois[column].clip(0, 1)
    neighbourhood_text = pois["neighbourhood"].astype(str).str.lower()
    pois["is_central"] = neighbourhood_text.apply(lambda value: any(key in value for key in CENTRAL_KEYS))
    pois["baseline_pressure"] = (0.65 * pois["popularity"] + 0.20 * pois["is_central"].astype(float)).clip(0, 1)
    pois["sustainable_value"] = 0.30 * pois["culture"] + 0.25 * pois["local_economy"] + 0.25 * pois["green"] + 0.20 * (1 - pois["baseline_pressure"])
    for interest in INTERESTS:
        pois[interest] = pois["categories"].str.contains(interest).astype(int)
    return pois


def normalise_tourist_profiles(raw):
    """Convert LLM tourist segments into clean sampling distributions."""
    segments = raw["segments"] if isinstance(raw, dict) else raw
    hotel_distribution = raw.get("hotel_distribution", []) if isinstance(raw, dict) else []
    segment_rows = {}
    total_p = sum(max(0, float(row.get("probability", 0))) for row in segments) or len(segments)
    for row in segments:
        name = row.get("segment") or row.get("name")
        likes = [interest for interest in row.get("likes", []) if interest in INTERESTS]
        segment_rows[name] = {
            "p": max(0, float(row.get("probability", 1 / len(segments)))) / total_p,
            "likes": likes or ["architecture", "museum"],
            "budget_probs": row.get("budget_probs", {"low": 0.30, "medium": 0.50, "high": 0.20}),
            "mobility_probs": row.get("mobility_probs", {"walk": 0.25, "bike": 0.10, "transit": 0.45, "mixed": 0.15, "taxi": 0.05}),
            "with_kids_probability": float(row.get("with_kids_probability", 0.12)),
            "crowd_aversion_mean": float(row.get("crowd_aversion_mean", 0.52)),
            "sustainability_mean": float(row.get("sustainability_mean", 0.50)),
            "outdoor_mean": float(row.get("outdoor_mean", 0.50))}
    hotels = []
    total_h = sum(max(0, float(row.get("probability", 0))) for row in hotel_distribution) or len(hotel_distribution)
    for row in hotel_distribution:
        hotels.append({"neighbourhood": row["neighbourhood"], "lat": float(row["lat"]), "lon": float(row["lon"]), "p": max(0, float(row.get("probability", 1 / len(hotel_distribution)))) / total_h})
    if not hotels:
        raise ValueError("Tourist profiles need a non-empty hotel_distribution list.")
    return {"segments": segment_rows, "hotel_distribution": hotels}


def sample_around_mean(rng, mean, strength=8):
    """Sample a profile attribute near its segment mean."""
    mean = min(0.95, max(0.05, float(mean)))
    return rng.beta(mean * strength, (1 - mean) * strength)


def sample_named_distribution(rng, probs):
    """Sample one key from an arbitrary probability dictionary."""
    names = list(probs.keys())
    values = np.array(list(probs.values()), dtype=float)
    values = values / values.sum()
    return rng.choice(names, p=values)


def create_tourists(n_tourists, tourist_profiles, seed=42):
    """Create the individual tourist agents used by the ABM."""
    rng = np.random.default_rng(seed)
    profiles = normalise_tourist_profiles(tourist_profiles)
    segments, hotels = profiles["segments"], profiles["hotel_distribution"]
    segment_names = list(segments.keys())
    segment_probs = np.array([segments[name]["p"] for name in segment_names])
    hotel_probs = np.array([hotel["p"] for hotel in hotels])
    rows = []
    for tourist_id in range(n_tourists):
        segment = rng.choice(segment_names, p=segment_probs / segment_probs.sum())
        info = segments[segment]
        budget = sample_named_distribution(rng, info["budget_probs"])
        max_cost = {"low": rng.normal(7, 2), "medium": rng.normal(18, 5), "high": rng.normal(38, 8)}.get(budget, rng.normal(18, 5))
        mobility = sample_named_distribution(rng, info["mobility_probs"])
        max_distance = {"walk": rng.uniform(1.2, 3.5), "bike": rng.uniform(3.5, 7.5), "transit": rng.uniform(5.0, 12.0), "mixed": rng.uniform(3.0, 9.0), "taxi": rng.uniform(8.0, 16.0)}.get(mobility, rng.uniform(5.0, 12.0))
        with_kids = rng.random() < info["with_kids_probability"]
        if with_kids:
            max_distance *= 0.85
        hotel = hotels[rng.choice(len(hotels), p=hotel_probs / hotel_probs.sum())]
        row = {
            "tourist_id": tourist_id,
            "segment": segment,
            "budget": budget,
            "max_cost": max(0, min(55, max_cost)),
            "mobility": mobility,
            "max_distance": max_distance,
            "crowd_aversion": sample_around_mean(rng, info["crowd_aversion_mean"]),
            "sustainability_sensitivity": sample_around_mean(rng, info["sustainability_mean"]),
            "outdoor_preference": sample_around_mean(rng, info["outdoor_mean"]),
            "with_kids": with_kids,
            "hotel_neighbourhood": hotel["neighbourhood"],
            "current_lat": hotel["lat"] + rng.normal(0, 0.004),
            "current_lon": hotel["lon"] + rng.normal(0, 0.004),
            "visited": set()}
        for interest in INTERESTS:
            row[interest] = 0.05
        for interest in info["likes"]:
            row[interest] += rng.uniform(0.45, 0.85)
        total = sum(row[interest] for interest in INTERESTS)
        for interest in INTERESTS:
            row[interest] /= total
        rows.append(row)
    return pd.DataFrame(rows)


def distance_km(lat1, lon1, lat2, lon2):
    """Approximate geographic distance using the haversine formula."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def gini(values):
    """Measure concentration, where 0 is equal and 1 is highly concentrated."""
    x = np.sort(np.array(values, dtype=float))
    if x.sum() == 0:
        return 0
    n = len(x)
    return (2 * np.sum(np.arange(1, n + 1) * x)) / (n * x.sum()) - (n + 1) / n


def entropy(values):
    """Normalised entropy of visits over neighbourhoods."""
    x = np.array(values, dtype=float)
    if x.sum() == 0:
        return 0
    p = x[x > 0] / x.sum()
    return -(p * np.log(p)).sum() / np.log(len(x))


def add_common_scores(pois, tourist, current_crowd, neighbourhood_visits):
    """Calculate the base features used by all recommenders."""
    scores = pois.copy()
    scores["interest_match"] = scores[INTERESTS].values.dot(tourist[INTERESTS].values.astype(float))
    dist = distance_km(tourist["current_lat"], tourist["current_lon"], scores["lat"], scores["lon"])

    scores["distance_km"] = dist
    scores["distance_score"] = np.exp(-dist / max(tourist["max_distance"], 0.5))

    extra_cost = np.maximum(0, scores["cost"] - tourist["max_cost"])
    scores["budget_score"] = np.clip(1 - extra_cost / (tourist["max_cost"] + 12), 0, 1)

    scores["current_crowd"] = current_crowd[scores["poi_id"].values]
    scores["crowd_ratio"] = scores["current_crowd"] / scores["capacity"]
    scores["crowd_score"] = np.clip(1 - scores["crowd_ratio"] / 1.35, 0, 1)

    scores["outdoor_match"] = 1 - abs(scores["outdoor"] - tourist["outdoor_preference"])

    if neighbourhood_visits.sum() == 0:
        scores["neighbourhood_relief"] = 1.0
    else:
        used = scores["neighbourhood"].map(neighbourhood_visits).fillna(0)
        scores["neighbourhood_relief"] = 1 - used / max(neighbourhood_visits.max(), 1)
    if tourist["with_kids"]:
        scores["interest_match"] += 0.06 * scores["family"] - 0.05 * scores["nightlife"]
    return scores


def recommend_pois(strategy, pois, tourist, current_crowd, neighbourhood_visits, rule_config, k=5):
    """Return top-k recommendations for one tourist agent."""
    candidate_pois = pois[~pois["poi_id"].isin(tourist["visited"])].copy()
    scored = add_common_scores(candidate_pois, tourist, current_crowd, neighbourhood_visits)

    if strategy == "popularity":
        w = rule_config["popularity"]
        scored["score"] = w["popularity"] * scored["popularity"] + w["budget"] * scored["budget_score"] + w["distance"] * scored["distance_score"] + w["culture"] * scored["culture"]
    elif strategy == "personalized":
        w = rule_config["personalized"]
        scored["score"] = w["interest"] * scored["interest_match"] + w["popularity"] * scored["popularity"] + w["budget"] * scored["budget_score"] + w["distance"] * scored["distance_score"] + (w["crowd_base"] + w["crowd_user"] * tourist["crowd_aversion"]) * scored["crowd_score"] + w["outdoor"] * scored["outdoor_match"] + w["culture"] * scored["culture"]
    elif strategy == "sustainable":
        social_w, personal_w = rule_config["sustainable"]["social"], rule_config["sustainable"]["personal"]
        social = social_w["crowd"] * scored["crowd_score"] + social_w["neighbourhood_relief"] * scored["neighbourhood_relief"] + social_w["sustainable_value"] * scored["sustainable_value"] + social_w["local_economy"] * scored["local_economy"] + social_w["distance"] * scored["distance_score"]
        personal = personal_w["interest"] * scored["interest_match"] + personal_w["budget"] * scored["budget_score"] + personal_w["distance"] * scored["distance_score"] + personal_w["outdoor"] * scored["outdoor_match"] + personal_w["popularity"] * scored["popularity"] + personal_w["culture"] * scored["culture"]
        alpha = rule_config["sustainable"]["alpha_base"] + rule_config["sustainable"]["alpha_user"] * tourist["sustainability_sensitivity"]
        scored["score"] = (1 - alpha) * personal + alpha * social
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    ordered = scored.sort_values("score", ascending=False)

    if strategy == "sustainable" and rule_config["sustainable"].get("diversity_rule", True):
        diverse = ordered.drop_duplicates("neighbourhood").head(k)
        ordered = pd.concat([diverse, ordered[~ordered["poi_id"].isin(diverse["poi_id"])].head(k - len(diverse))])

    return ordered.head(k)["poi_id"].astype(int).tolist(), scored


def tourist_utility(recommendations, pois, tourist, current_crowd):
    """Estimate which recommendation the tourist actually chooses."""
    scored = add_common_scores(pois[pois["poi_id"].isin(recommendations)], tourist, current_crowd, pd.Series(dtype=float))
    utility = 0.46 * scored["interest_match"] + 0.13 * scored["popularity"] + 0.13 * scored["budget_score"] + 0.10 * scored["distance_score"] + (0.05 + 0.13 * tourist["crowd_aversion"]) * scored["crowd_score"] + 0.08 * tourist["sustainability_sensitivity"] * scored["sustainable_value"] + 0.05 * scored["outdoor_match"]
    if tourist["with_kids"]:
        utility += 0.04 * scored["family"] - 0.05 * scored["nightlife"]
    scored["utility"] = utility.clip(0, 1)
    return scored


def choose_one_poi(scored, rng):
    """Sample a visit from the recommended list with softmax choice."""
    utility = scored["utility"].values
    probabilities = np.exp((utility - utility.max()) / 0.11)
    probabilities = probabilities / probabilities.sum()
    return scored.iloc[rng.choice(len(scored), p=probabilities)]


def recommendation_quality(recommendations, pois, tourist, scored_candidates):
    """Measure simulated recommendation relevance and diversity."""
    relevance = 0.58 * scored_candidates["interest_match"] + 0.17 * scored_candidates["budget_score"] + 0.10 * scored_candidates["distance_score"] + 0.08 * scored_candidates["outdoor_match"] + 0.07 * scored_candidates["culture"]
    threshold = relevance.quantile(0.72)
    relevant = set(scored_candidates.loc[relevance >= threshold, "poi_id"])
    rec_rows = pois[pois["poi_id"].isin(recommendations)]
    categories = rec_rows["categories"].apply(lambda value: set(str(value).split(","))).tolist()

    similarities = []
    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            union = categories[i] | categories[j]
            similarities.append(len(categories[i] & categories[j]) / len(union) if union else 0)

    return {
        "precision_at_5": len(set(recommendations) & relevant) / len(recommendations),
        "recall_at_5": len(set(recommendations) & relevant) / max(len(relevant), 1),
        "diversity": 1 - np.mean(similarities) if similarities else 0,
        "constraint_respect": (rec_rows["cost"] <= tourist["max_cost"] * 1.15 + 1).mean(),
        "mean_recommendation_sustainability": rec_rows["sustainable_value"].mean()}


def estimate_co2(row, tourist):
    """Use a simple mobility-dependent CO2 proxy."""
    if tourist["mobility"] in ["walk", "bike"]:
        return 0.0
    if tourist["mobility"] == "transit":
        return 0.0 if row["distance_km"] <= 1.2 else row["distance_km"] * 0.035
    if tourist["mobility"] == "mixed":
        return 0.0 if row["distance_km"] <= tourist["max_distance"] else row["distance_km"] * 0.060
    return row["distance_km"] * 0.180


def run_simulation(strategy, pois, tourists, steps=5, seed=42, rule_config=None):
    """Run a complete scenario for one recommender strategy."""
    rng = np.random.default_rng(seed)
    rule_config = rule_config or DEFAULT_RULE_CONFIG
    tourists = tourists.copy(deep=True)
    tourists["visited"] = tourists["visited"].apply(lambda visited: set(visited))
    visit_rows, quality_rows, crowd_rows = [], [], []
    neighbourhood_visits = pd.Series(0, index=sorted(pois["neighbourhood"].unique()))
    for step in range(1, steps + 1):
        current_crowd = np.zeros(len(pois), dtype=int)
        for tourist_index in rng.permutation(tourists.index):
            tourist = tourists.loc[tourist_index]
            recs, scored_candidates = recommend_pois(strategy, pois, tourist, current_crowd, neighbourhood_visits, rule_config, k=5)
            quality = recommendation_quality(recs, pois, tourist, scored_candidates)
            quality.update({"strategy": strategy, "step": step, "tourist_id": int(tourist["tourist_id"])})
            rec_rows = pois.set_index("poi_id").loc[recs]

            quality["recommended_poi_ids"] = "|".join(map(str, recs))
            quality["recommended_poi_names"] = " | ".join(rec_rows["poi_name"].astype(str))
            quality["recommended_neighbourhoods"] = " | ".join(rec_rows["neighbourhood"].astype(str))
            quality_rows.append(quality)

            chosen = choose_one_poi(tourist_utility(recs, pois, tourist, current_crowd), rng)
            poi_id = int(chosen["poi_id"])
            current_crowd[poi_id] += 1

            neighbourhood_visits.loc[chosen["neighbourhood"]] += 1
            tourists.at[tourist_index, "current_lat"] = chosen["lat"]
            tourists.at[tourist_index, "current_lon"] = chosen["lon"]
            tourists.at[tourist_index, "visited"].add(poi_id)

            visit = {"strategy": strategy, "step": step, "tourist_id": int(tourist["tourist_id"]), "segment": tourist["segment"], "poi_id": poi_id, "poi_name": chosen["poi_name"], "neighbourhood": chosen["neighbourhood"], "is_central": chosen["is_central"], "satisfaction": chosen["utility"], "interest_match": chosen["interest_match"], "distance_km": chosen["distance_km"], "cost": chosen["cost"], "crowd_ratio_after_visit": current_crowd[poi_id] / chosen["capacity"], "sustainable_value": chosen["sustainable_value"], "local_economy": chosen["local_economy"], "green": chosen["green"], "baseline_pressure": chosen["baseline_pressure"]}
            visit["co2_kg"] = estimate_co2(visit, tourist)
            visit_rows.append(visit)

        for _, poi in pois.iterrows():
            crowd_rows.append({"strategy": strategy, "step": step, "poi_id": poi["poi_id"], "poi_name": poi["poi_name"], "neighbourhood": poi["neighbourhood"], "visits_this_step": current_crowd[int(poi["poi_id"])], "capacity": poi["capacity"], "crowd_ratio": current_crowd[int(poi["poi_id"])] / poi["capacity"]})
    return pd.DataFrame(visit_rows), pd.DataFrame(quality_rows), pd.DataFrame(crowd_rows)


def summarise_results(strategy, pois, visits, quality, crowd):
    """Create the main evaluation row for one strategy."""
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
        "visit_over_capacity_share": (visits["crowd_ratio_after_visit"] > 1).mean()}
    for metric in ["precision_at_5", "recall_at_5", "diversity", "constraint_respect", "mean_recommendation_sustainability"]:
        summary[f"avg_{metric}"] = quality[metric].mean()
    return pd.DataFrame([summary])


def create_detail_tables(strategy, pois, visits, crowd):
    """Create POI-level and neighbourhood-level tables."""

    poi_table = pois[["poi_id", "poi_name", "neighbourhood", "popularity", "capacity", "baseline_pressure", "sustainable_value"]].copy()
    poi_table = poi_table.merge(visits.groupby("poi_id").size().rename("visits"), on="poi_id", how="left")
    poi_table = poi_table.merge(crowd.groupby("poi_id")["crowd_ratio"].max().rename("max_slot_crowd_ratio"), on="poi_id", how="left")
    poi_table["visits"] = poi_table["visits"].fillna(0).astype(int)
    poi_table["strategy"] = strategy

    neighbourhood_table = visits.groupby("neighbourhood").agg(visits=("poi_id", "size"), avg_satisfaction=("satisfaction", "mean"), central=("is_central", "max")).reset_index()
    neighbourhood_table["visit_share"] = neighbourhood_table["visits"] / neighbourhood_table["visits"].sum()
    neighbourhood_table["strategy"] = strategy

    return poi_table.sort_values("visits", ascending=False), neighbourhood_table.sort_values("visits", ascending=False)


def clean_axes(ax):
    """Apply the visual style requested for the seminar plots."""
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_results(summary, neighbourhood_table, poi_table, output_dir):
    """Save blue, grid-free figures with straight labels."""

    plt.rcParams.update({"axes.grid": False, "font.size": 10})

    metrics = [("avg_satisfaction", "Mean satisfaction"), ("max_slot_crowd_ratio", "Maximum crowd ratio"), ("neighbourhood_entropy", "Neighbourhood entropy"), ("top_5_poi_visit_share", "Top-5 POI share"), ("central_visit_share", "Central visit share"), ("avg_diversity", "Recommendation diversity")]
    
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    for ax, (metric, title) in zip(axes.flat, metrics):
        values = [summary.loc[summary["strategy"] == strategy, metric].iloc[0] for strategy in STRATEGIES]
        bars = ax.bar(STRATEGIES, values, color=[STRATEGY_COLORS[strategy] for strategy in STRATEGIES], width=0.62)
        ax.set_title(title.upper(), fontsize=12, weight="bold")
        ax.tick_params(axis="x", rotation=0)
        clean_axes(ax)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(output_dir / "strategy_comparison.png", dpi=180)
    plt.close(fig)

    top_neighbourhoods = neighbourhood_table.groupby("neighbourhood")["visits"].sum().sort_values(ascending=False).head(12).index
    pivot = neighbourhood_table[neighbourhood_table["neighbourhood"].isin(top_neighbourhoods)].pivot_table(index="neighbourhood", columns="strategy", values="visit_share", fill_value=0).reindex(columns=STRATEGIES)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values().index]
    
    fig, ax = plt.subplots(figsize=(10, 7))
    y_positions, bar_height = np.arange(len(pivot)), 0.24
    for offset, strategy in zip([-bar_height, 0, bar_height], STRATEGIES):
        ax.barh(y_positions + offset, pivot[strategy], height=bar_height, color=STRATEGY_COLORS[strategy], label=strategy)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Share of visits")
    ax.set_title("DISTRIBUTION OF VISITS BY NEIGHBOURHOOD", fontsize=12, weight="bold")
    ax.legend(frameon=False)
    clean_axes(ax)
    fig.tight_layout()
    fig.savefig(output_dir / "neighbourhood_distribution.png", dpi=180)
    plt.close(fig)

    top_pois = poi_table.groupby("poi_name")["visits"].sum().sort_values(ascending=False).head(12).index
    pivot = poi_table[poi_table["poi_name"].isin(top_pois)].pivot_table(index="poi_name", columns="strategy", values="max_slot_crowd_ratio", fill_value=0).reindex(columns=STRATEGIES)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values().index]
    
    fig, ax = plt.subplots(figsize=(10, 7))
    y_positions = np.arange(len(pivot))
    for offset, strategy in zip([-bar_height, 0, bar_height], STRATEGIES):
        ax.barh(y_positions + offset, pivot[strategy], height=bar_height, color=STRATEGY_COLORS[strategy], label=strategy)
    ax.axvline(1.0, color="#C44E52", linestyle="--", linewidth=1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Maximum crowd / capacity")
    ax.set_title("PEAK CROWDING AT MAIN POIS", fontsize=12, weight="bold")
    ax.legend(frameon=False)
    clean_axes(ax)
    fig.tight_layout()
    fig.savefig(output_dir / "top_poi_crowding.png", dpi=180)
    plt.close(fig)
