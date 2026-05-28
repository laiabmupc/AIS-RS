import argparse
from pathlib import Path
from crew_agents import DEFAULT_LLM_MODEL
from crew_flow import run_tourism_flow
from utils import RANDOM_SEED


def parse_args():
    parser = argparse.ArgumentParser(description="Run the sustainable POI recommender ABM simulation.")
    parser.add_argument("--tourists", type=int, default=2000, help="Number of tourist agents.")
    parser.add_argument("--steps", type=int, default=5, help="Number of POI decisions per tourist.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for reproducibility.")
    parser.add_argument("--outdir", type=Path, default=Path("outputs"), help="Folder for CSV tables and plots.")
    parser.add_argument("--model", default=DEFAULT_LLM_MODEL, help="CrewAI LLM model used by the audit and interpretation agents.")
    parser.add_argument("--no-llm-report", action="store_true", help="Skip the optional LLM audit and interpretation files.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Folder for prepared POI/profile/rule files.")
    return parser.parse_args()


def print_summary(summary):
    columns_to_print = [
        "strategy",
        "avg_satisfaction",
        "max_slot_crowd_ratio",
        "neighbourhood_entropy",
        "top_5_poi_visit_share",
        "central_visit_share",
        "avg_precision_at_5",
        "avg_diversity",
        "avg_constraint_respect",
    ]
    print("\nSummary")
    print(summary[columns_to_print].round(4).to_string(index=False))


def main():
    args = parse_args()
    print("CrewAI Flow available: running the multi-agent evaluation flow.", flush=True)
    print(f"Configured CrewAI LLM model: {args.model}", flush=True)
    try:
        results = run_tourism_flow(args.tourists, args.steps, args.seed, args.outdir, model_name=args.model, llm_report=not args.no_llm_report, data_dir=args.data_dir)
    except RuntimeError as error:
        raise SystemExit(f"ERROR: {error}") from error
    print_summary(results["summary"])
    print(f"\nFiles saved in: {args.outdir.resolve()}")


if __name__ == "__main__":
    main()
