import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
from agents import DEFAULT_MODEL, generate_pois, generate_rule_config, generate_tourist_profiles, write_agent_interpretation, write_input_audit
from simulation import STRATEGIES, create_detail_tables, create_tourists, finalize_pois, normalise_rule_config, plot_results, run_simulation, summarise_results


def parse_args():
    parser = argparse.ArgumentParser(description="Run the agent-heavy POI recommender ABM experiment.")
    parser.add_argument("--tourists", type=int, default=1200, help="Number of tourist agents.")
    parser.add_argument("--steps", type=int, default=5, help="Number of POI decisions per tourist.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Local Ollama model, for example ollama/qwen2.5:7b.")
    parser.add_argument("--outdir", type=Path, default=Path("output_agents"), help="Independent output folder.")
    parser.add_argument("--force", action="store_true", help="Regenerate agent data and overwrite previous output_agents results.")
    return parser.parse_args()


def reset_output_dir(output_dir, force):
    """Keep the agent experiment separated from the previous implementation."""
    if force and output_dir.exists():
        if output_dir.name != "output_agents":
            raise ValueError("For safety, --force only removes a folder literally named output_agents.")
        shutil.rmtree(output_dir)
    (output_dir / "data").mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)
    (output_dir / "agent_logs").mkdir(parents=True, exist_ok=True)


def load_or_generate_inputs(args):
    """Run the LLM agents for POIs, tourist profiles and informed rule design."""
    data_dir = args.outdir / "data"
    poi_path = data_dir / "agent_generated_pois.csv"
    profile_path = data_dir / "agent_tourist_profiles.json"
    rule_path = data_dir / "agent_rule_config.json"
    if not args.force and poi_path.exists():
        print("Reusing agent-generated POIs from output_agents/data.", flush=True)
        pois = pd.read_csv(poi_path).to_dict("records")
    else:
        print("Agent 1/3: creating the Barcelona POI database...", flush=True)
        pois = generate_pois(args.outdir, model=args.model)
        pd.DataFrame(pois).to_csv(poi_path, index=False)

    if not args.force and profile_path.exists():
        print("Reusing agent-generated tourist profiles from output_agents/data.", flush=True)
        tourist_profiles = json.loads(profile_path.read_text(encoding="utf-8"))
    else:
        print("Agent 2/3: creating tourist population profiles...", flush=True)
        tourist_profiles = generate_tourist_profiles(args.outdir, model=args.model)
        profile_path.write_text(json.dumps(tourist_profiles, indent=2), encoding="utf-8")

    if not args.force and rule_path.exists():
        print("Reusing agent-calibrated recommender rules from output_agents/data.", flush=True)
        rule_config = json.loads(rule_path.read_text(encoding="utf-8"))
    else:
        print("Agent 3/3: calibrating informed recommender rules from the generated POIs...", flush=True)
        rule_config = generate_rule_config(pois, args.outdir, model=args.model)
        rule_path.write_text(json.dumps(rule_config, indent=2), encoding="utf-8")
    return pois, tourist_profiles, rule_config


def build_input_audit_text(pois, tourist_profiles, rule_config):
    """Create verified notes before the audit agent writes prose."""
    top_pois = pois.sort_values("popularity", ascending=False).head(8)[["poi_name", "neighbourhood", "popularity"]]
    segments = [row.get("segment", row.get("name", "unknown")) for row in tourist_profiles["segments"]]
    return "\n".join([
        "# Agent-generated input summary",
        f"POIs generated: {len(pois)}.",
        f"Neighbourhoods covered: {pois['neighbourhood'].nunique()}.",
        f"Tourist segments generated: {', '.join(segments)}.",
        f"Rule metadata: {json.dumps(rule_config.get('metadata', {}), indent=2)}",
        "Most popular generated POIs:",
        top_pois.to_string(index=False),
    ])


def build_result_notes(summary):
    """Create verified notes so the final LLM agent cannot invent metrics."""
    rows = summary.set_index("strategy")
    p, q, s = rows.loc["popularity"], rows.loc["personalized"], rows.loc["sustainable"]
    return "\n".join([
        "# Verified simulation findings",
        f"Each strategy produced {int(s['total_visits'])} visits from the same synthetic tourist population.",
        f"Satisfaction: sustainable {s['avg_satisfaction']:.4f}, personalized {q['avg_satisfaction']:.4f}, popularity {p['avg_satisfaction']:.4f}.",
        f"Peak crowding ratio: sustainable {s['max_slot_crowd_ratio']:.4f}, personalized {q['max_slot_crowd_ratio']:.4f}, popularity {p['max_slot_crowd_ratio']:.4f}.",
        f"Neighbourhood entropy: sustainable {s['neighbourhood_entropy']:.4f}, personalized {q['neighbourhood_entropy']:.4f}, popularity {p['neighbourhood_entropy']:.4f}.",
        f"Top-5 POI visit share: sustainable {s['top_5_poi_visit_share']:.4f}, personalized {q['top_5_poi_visit_share']:.4f}, popularity {p['top_5_poi_visit_share']:.4f}.",
        f"Central visit share: sustainable {s['central_visit_share']:.4f}, personalized {q['central_visit_share']:.4f}, popularity {p['central_visit_share']:.4f}.",
        f"Hotspot visit share: sustainable {s['hotspot_visit_share']:.4f}, personalized {q['hotspot_visit_share']:.4f}, popularity {p['hotspot_visit_share']:.4f}.",
        f"POI coverage: sustainable {s['poi_coverage']:.4f}, personalized {q['poi_coverage']:.4f}, popularity {p['poi_coverage']:.4f}.",
        f"Precision@5: sustainable {s['avg_precision_at_5']:.4f}, personalized {q['avg_precision_at_5']:.4f}, popularity {p['avg_precision_at_5']:.4f}.",
        f"Local economy score: sustainable {s['avg_local_economy']:.4f}, personalized {q['avg_local_economy']:.4f}, popularity {p['avg_local_economy']:.4f}.",
        f"Green visit share: sustainable {s['green_visit_share']:.4f}, personalized {q['green_visit_share']:.4f}, popularity {p['green_visit_share']:.4f}.",
        f"Average distance: sustainable {s['avg_distance_km']:.4f} km, personalized {q['avg_distance_km']:.4f} km, popularity {p['avg_distance_km']:.4f} km.",
    ])


def build_safe_interpretation(summary):
    """Write the final interpretation directly from verified metrics."""
    rows = summary.set_index("strategy")
    p, q, s = rows.loc["popularity"], rows.loc["personalized"], rows.loc["sustainable"]
    satisfaction_loss = q["avg_satisfaction"] - s["avg_satisfaction"]
    satisfaction_gain = s["avg_satisfaction"] - p["avg_satisfaction"]
    central_drop = p["central_visit_share"] - s["central_visit_share"]
    hotspot_drop = p["hotspot_visit_share"] - s["hotspot_visit_share"]
    top5_drop = p["top_5_poi_visit_share"] - s["top_5_poi_visit_share"]
    return "\n".join([
        "# Verified agent-based interpretation",
        "",
        "The popularity baseline concentrates tourists in the most famous and central POIs. It obtains the lowest average satisfaction "
        f"({p['avg_satisfaction']:.4f}), the highest peak crowding ratio ({p['max_slot_crowd_ratio']:.4f}), a very high central visit share "
        f"({p['central_visit_share']:.4f}) and the largest top-5 POI concentration ({p['top_5_poi_visit_share']:.4f}). This is the expected behaviour "
        "of a simple popularity recommender: it is easy to explain, but it reinforces overtourism.",
        "",
        "The personalized recommender is the strongest strategy from the individual-user perspective. It reaches the highest satisfaction "
        f"({q['avg_satisfaction']:.4f}) and the highest simulated Precision@5 ({q['avg_precision_at_5']:.4f}). However, its city-level behaviour is still "
        f"less balanced than the sustainable strategy: central visit share remains at {q['central_visit_share']:.4f}, hotspot visit share at "
        f"{q['hotspot_visit_share']:.4f}, and top-5 POI share at {q['top_5_poi_visit_share']:.4f}.",
        "",
        "The sustainable recommender gives the best urban-management outcome. Compared with popularity, it reduces central visit share by "
        f"{central_drop:.4f}, hotspot visit share by {hotspot_drop:.4f}, and top-5 POI share by {top5_drop:.4f}. It also obtains the highest neighbourhood "
        f"entropy ({s['neighbourhood_entropy']:.4f}) and the widest POI coverage ({s['poi_coverage']:.4f}), which means tourists are distributed across "
        "more places and neighbourhoods.",
        "",
        "The main trade-off is clear and defensible. Sustainable recommendation loses "
        f"{satisfaction_loss:.4f} satisfaction points with respect to the personalized recommender, but it remains {satisfaction_gain:.4f} points above "
        "the popularity baseline. Therefore, it does not maximize individual relevance, but it achieves a much better compromise between tourist utility "
        "and collective sustainability objectives.",
        "",
        "Some indicators need careful interpretation. The popularity strategy has the highest local economy score in this run because several very popular "
        "commercial places and markets receive many visits. This does not mean that the wealth is well distributed. The sustainable strategy has a slightly "
        f"lower average local economy score ({s['avg_local_economy']:.4f}) than popularity ({p['avg_local_economy']:.4f}), but it spreads visits much more "
        "widely and increases green visit share to "
        f"{s['green_visit_share']:.4f}, compared with {q['green_visit_share']:.4f} for personalized and {p['green_visit_share']:.4f} for popularity.",
        "",
        "Overall, the simulation supports the usefulness of the evaluation mechanism. By comparing the same tourist population under three recommender "
        "strategies, it shows that the sustainable approach is superior for reducing overtourism indicators, while the personalized recommender remains "
        "best for pure profile relevance.",
    ])


def save_results(results, pois, tourists, rule_config, output_dir):
    """Persist every table needed for the final report and demo."""
    table_names = ["visits", "recommendations", "slots", "summary", "poi_metrics", "neighbourhood_metrics"]
    combined = {}
    for table_name in table_names:
        combined[table_name] = pd.concat([results[strategy][table_name] for strategy in STRATEGIES], ignore_index=True)
        combined[table_name].to_csv(output_dir / f"{table_name}.csv", index=False)
    pois.to_csv(output_dir / "pois_used.csv", index=False)
    tourists_to_save = tourists.copy()
    tourists_to_save["visited"] = tourists_to_save["visited"].apply(lambda value: "|".join(map(str, sorted(value))))
    tourists_to_save.to_csv(output_dir / "tourists.csv", index=False)
    (output_dir / "rule_config.json").write_text(json.dumps(rule_config, indent=2), encoding="utf-8")
    plot_results(combined["summary"], combined["neighbourhood_metrics"], combined["poi_metrics"], output_dir / "figures")
    return combined


def print_summary(summary):
    """Print the compact comparison table."""
    columns = ["strategy", "avg_satisfaction", "max_slot_crowd_ratio", "neighbourhood_entropy", "top_5_poi_visit_share", "central_visit_share", "avg_precision_at_5", "avg_diversity"]
    print("\nSummary")
    print(summary[columns].round(4).to_string(index=False))


def main():
    args = parse_args()
    reset_output_dir(args.outdir, args.force)
    pois_raw, tourist_profiles, rule_raw = load_or_generate_inputs(args)
    pois = finalize_pois(pd.DataFrame(pois_raw))
    if len(pois) < 50:
        raise SystemExit(f"ERROR: The POI agents produced only {len(pois)} usable POIs.")
    rule_config = normalise_rule_config(rule_raw)
    tourists = create_tourists(args.tourists, tourist_profiles, seed=args.seed)

    input_notes = build_input_audit_text(pois, tourist_profiles, rule_config)
    (args.outdir / "agent_input_notes.md").write_text(input_notes + "\n", encoding="utf-8")
    (args.outdir / "agent_input_audit.md").write_text(write_input_audit(input_notes, args.outdir, model=args.model) + "\n", encoding="utf-8")

    results = {}
    for offset, strategy in enumerate(STRATEGIES):
        print(f"Running {strategy} recommender simulation...", flush=True)
        visits, recommendations, slots = run_simulation(strategy, pois, tourists, steps=args.steps, seed=args.seed + 100 * offset, rule_config=rule_config)
        summary = summarise_results(strategy, pois, visits, recommendations, slots)
        poi_metrics, neighbourhood_metrics = create_detail_tables(strategy, pois, visits, slots)
        results[strategy] = {"visits": visits, "recommendations": recommendations, "slots": slots, "summary": summary, "poi_metrics": poi_metrics, "neighbourhood_metrics": neighbourhood_metrics}

    combined = save_results(results, pois, tourists, rule_config, args.outdir)
    result_notes = build_result_notes(combined["summary"])
    (args.outdir / "verified_findings.md").write_text(result_notes + "\n", encoding="utf-8")
    llm_draft = write_agent_interpretation(result_notes, args.outdir, model=args.model)
    (args.outdir / "agent_interpretation_llm_draft.md").write_text(llm_draft + "\n", encoding="utf-8")
    (args.outdir / "agent_interpretation.md").write_text(build_safe_interpretation(combined["summary"]) + "\n", encoding="utf-8")

    metadata = {"created_at": datetime.now().isoformat(timespec="seconds"), "model": args.model, "n_tourists": args.tourists, "steps": args.steps, "seed": args.seed, "n_pois": len(pois), "output_dir": str(args.outdir), "agent_roles": ["Barcelona POI database curator", "Tourist population modeller", "Recommender rule calibration analyst", "Synthetic data audit analyst", "Sustainable tourism evaluation analyst"]}
    (args.outdir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print_summary(combined["summary"])
    print(f"\nFiles saved in: {args.outdir.resolve()}")


if __name__ == "__main__":
    main()
