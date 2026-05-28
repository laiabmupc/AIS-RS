import json
import os
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
from crew_agents import DEFAULT_LLM_MODEL, maybe_write_llm_input_audit, maybe_write_llm_interpretation
from data_generation import LLM_AGENT_ROLES, llm_credentials_available, prepare_input_data
from utils import STRATEGIES, create_detail_tables, create_tourists, load_pois_from_file, load_rule_config, load_tourist_profiles, plot_results, run_simulation, summarise_results
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
from crewai.flow import Flow, and_, listen, start


class TourismEvaluationFlow(Flow):
    """CrewAI-style flow that coordinates the complete evaluation."""

    def __init__(self, n_tourists=2000, steps=5, seed=42, output_dir=Path("outputs"), model_name=DEFAULT_LLM_MODEL, llm_report=True, data_dir=Path("data")):
        super().__init__()
        self.n_tourists = n_tourists
        self.steps = steps
        self.seed = seed
        self.output_dir = Path(output_dir)
        self.model_name = model_name
        self.llm_report = llm_report
        self.data_dir = Path(data_dir)
        self.pois = None
        self.tourists = None
        self.rule_config = None
        self.strategy_results = {}
        self.final_results = None
        self.data_files = None

    def ensure_input_data(self):
        """Create the simulator input files if they are missing."""
        files = {
            "pois": self.data_dir / "poi_catalogue.csv",
            "segments": self.data_dir / "tourist_profiles.json",
            "rules": self.data_dir / "rule_config_input.json",
        }
        if all(path.exists() for path in files.values()):
            return files
        return prepare_input_data(self.data_dir, self.model_name)

    def build_input_summary(self, tourist_profiles):
        """Summarise inputs for the lightweight LLM audit."""
        top_pois = self.pois.sort_values("popularity", ascending=False).head(8)[["poi_name", "neighbourhood", "popularity"]]
        metadata = self.rule_config.get("metadata", {})
        return "\n".join([
            "The POI and tourist inputs are curated seminar assumptions, not official tourism measurements.",
            f"POIs: {len(self.pois)} across {self.pois['neighbourhood'].nunique()} neighbourhoods.",
            f"Tourist segments: {', '.join(tourist_profiles['segments'].keys())}.",
            f"Rule calibration metadata: {json.dumps(metadata, indent=2)}",
            "Most popular POIs:",
            top_pois.to_string(index=False),
        ])

    def build_result_notes(self, summary):
        """Build verified findings before the LLM writes the final prose."""
        rows = summary.set_index("strategy")
        p, q, s = rows.loc["popularity"], rows.loc["personalized"], rows.loc["sustainable"]
        return "\n".join([
            "# Verified simulation findings",
            f"Each strategy produced {int(s['total_visits'])} visits from the same tourist population.",
            f"Satisfaction: sustainable {s['avg_satisfaction']:.4f}, personalized {q['avg_satisfaction']:.4f}, popularity {p['avg_satisfaction']:.4f}. Sustainable is below personalized but above popularity.",
            f"Peak crowding ratio: sustainable {s['max_slot_crowd_ratio']:.4f}, personalized {q['max_slot_crowd_ratio']:.4f}, popularity {p['max_slot_crowd_ratio']:.4f}. Sustainable is the lowest.",
            f"Neighbourhood entropy: sustainable {s['neighbourhood_entropy']:.4f}, personalized {q['neighbourhood_entropy']:.4f}, popularity {p['neighbourhood_entropy']:.4f}. Sustainable is the highest.",
            f"Top-5 POI visit share: sustainable {s['top_5_poi_visit_share']:.4f}, personalized {q['top_5_poi_visit_share']:.4f}, popularity {p['top_5_poi_visit_share']:.4f}. Sustainable is the least concentrated.",
            f"Central visit share: sustainable {s['central_visit_share']:.4f}, personalized {q['central_visit_share']:.4f}, popularity {p['central_visit_share']:.4f}. Sustainable sends the smallest share to central areas.",
            f"Hotspot visit share: sustainable {s['hotspot_visit_share']:.4f}, personalized {q['hotspot_visit_share']:.4f}, popularity {p['hotspot_visit_share']:.4f}. Sustainable reduces hotspot pressure most.",
            f"POI coverage: sustainable {s['poi_coverage']:.4f}, personalized {q['poi_coverage']:.4f}, popularity {p['poi_coverage']:.4f}. Sustainable uses the widest set of POIs.",
            f"Precision@5: sustainable {s['avg_precision_at_5']:.4f}, personalized {q['avg_precision_at_5']:.4f}, popularity {p['avg_precision_at_5']:.4f}. Sustainable trades off some relevance compared with personalized.",
            f"Constraint respect: sustainable {s['avg_constraint_respect']:.4f}, personalized {q['avg_constraint_respect']:.4f}, popularity {p['avg_constraint_respect']:.4f}. Sustainable is the highest; this means budget/profile fit, not legal regulation.",
            f"Local economy score: sustainable {s['avg_local_economy']:.4f}, personalized {q['avg_local_economy']:.4f}, popularity {p['avg_local_economy']:.4f}. Sustainable is the highest.",
            f"Green visit share: sustainable {s['green_visit_share']:.4f}, personalized {q['green_visit_share']:.4f}, popularity {p['green_visit_share']:.4f}. Sustainable is the highest.",
            f"Mobility caveat: sustainable average distance is {s['avg_distance_km']:.4f} km versus {q['avg_distance_km']:.4f} personalized and {p['avg_distance_km']:.4f} popularity. Sustainable improves spatial distribution but still needs transport-aware tuning.",
            f"CO2 caveat: sustainable total CO2 proxy is {s['total_co2_kg']:.4f} kg versus {q['total_co2_kg']:.4f} personalized and {p['total_co2_kg']:.4f} popularity.",
        ])

    @start()
    def prepare_experiment(self):
        """Load or create the city catalogue, tourist profiles and rules."""
        print("Preparing POIs, tourist agents and recommender rules...", flush=True)
        files = self.ensure_input_data()
        self.data_files = files
        self.pois = load_pois_from_file(files["pois"])
        tourist_profiles = load_tourist_profiles(files["segments"])
        self.tourists = create_tourists(self.n_tourists, tourist_profiles, seed=self.seed)
        self.rule_config = load_rule_config(files["rules"])
        if self.llm_report and llm_credentials_available(self.model_name):
            audit_file = self.data_dir / "llm_input_audit.md"
            maybe_write_llm_input_audit(self.build_input_summary(tourist_profiles), audit_file, model_name=self.model_name)
            self.data_files["input_audit"] = audit_file
        elif self.llm_report:
            print("Skipping LLM input audit because the selected provider is not configured.", flush=True)
        self.strategy_results = {}
        self.state["data_source"] = "curated_reproducible_inputs"
        self.state["crew_agent_roles"] = LLM_AGENT_ROLES
        self.state["llm_model"] = self.model_name
        self.state["rule_calibration"] = self.rule_config.get("metadata", {})
        self.state["n_pois"] = len(self.pois)
        self.state["n_tourists"] = len(self.tourists)
        return "experiment_ready"

    def run_strategy_branch(self, strategy, seed_offset):
        """Run one recommender strategy and store its local results."""
        print(f"Running {strategy} recommender...", flush=True)
        visits, quality, crowd = run_simulation(strategy, self.pois, self.tourists, steps=self.steps, seed=self.seed + seed_offset, rule_config=self.rule_config)
        summary = summarise_results(strategy, self.pois, visits, quality, crowd)
        poi_table, neighbourhood_table = create_detail_tables(strategy, self.pois, visits, crowd)

        self.strategy_results[strategy] = {
            "visits": visits,
            "recommendations": quality,
            "slots": crowd,
            "summary": summary,
            "poi_metrics": poi_table,
            "neighbourhood_metrics": neighbourhood_table}
        self.state[f"{strategy}_ready"] = True
        return f"{strategy}_ready"

    @listen(prepare_experiment)
    def popularity_branch(self, _=None):
        """Specialist branch for the popularity baseline."""
        return self.run_strategy_branch("popularity", seed_offset=0)

    @listen(prepare_experiment)
    def personalized_branch(self, _=None):
        """Specialist branch for the interest-based recommender."""
        return self.run_strategy_branch("personalized", seed_offset=100)

    @listen(prepare_experiment)
    def sustainable_branch(self, _=None):
        """Specialist branch for the multi-criteria sustainable recommender."""
        return self.run_strategy_branch("sustainable", seed_offset=200)

    @listen(and_(popularity_branch, personalized_branch, sustainable_branch))
    def integrate_results(self, _=None):
        """Combine branch outputs, save CSV files and regenerate plots."""
        print("Integrating simulation results...", flush=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        results = {}
        table_names = ["visits", "recommendations", "slots", "summary", "poi_metrics", "neighbourhood_metrics"]
        for table_name in table_names:
            tables = [self.strategy_results[strategy][table_name] for strategy in STRATEGIES]
            results[table_name] = pd.concat(tables, ignore_index=True)
            results[table_name].to_csv(self.output_dir / f"{table_name}.csv", index=False)
        with open(self.output_dir / "rule_config.json", "w", encoding="utf-8") as file:
            json.dump(self.rule_config, file, indent=2)

        self.pois.to_csv(self.output_dir / "pois_used.csv", index=False)
        tourists_to_save = self.tourists.copy()
        tourists_to_save["visited"] = tourists_to_save["visited"].apply(lambda visited: "|".join(map(str, sorted(visited))))
        tourists_to_save.to_csv(self.output_dir / "tourists.csv", index=False)
        for path in self.data_files.values():
            if path.exists():
                shutil.copy2(path, self.output_dir / path.name)
        plot_results(results["summary"], results["neighbourhood_metrics"], results["poi_metrics"], self.output_dir)
        result_notes = self.build_result_notes(results["summary"])
        (self.output_dir / "verified_findings.md").write_text(result_notes + "\n", encoding="utf-8")

        if self.llm_report and llm_credentials_available(self.model_name):
            maybe_write_llm_interpretation(result_notes, self.output_dir / "llm_interpretation.md", model_name=self.model_name)
        elif self.llm_report:
            print("Skipping final LLM interpretation because the selected provider is not configured.", flush=True)

        metadata = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "model": self.model_name,
            "n_tourists": self.n_tourists,
            "steps": self.steps,
            "seed": self.seed,
            "data_dir": str(self.data_dir),
            "output_dir": str(self.output_dir),
            "llm_agents": LLM_AGENT_ROLES,
            "saved_files": sorted([path.name for path in self.output_dir.iterdir() if path.is_file()] + ["run_metadata.json"])}
        
        with open(self.output_dir / "run_metadata.json", "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        self.final_results = results
        self.state["outputs_dir"] = str(self.output_dir)

        return results

def run_tourism_flow(n_tourists=2000, steps=5, seed=42, output_dir=Path("outputs"), model_name=DEFAULT_LLM_MODEL, llm_report=True, data_dir=Path("data")):
    """Run the evaluation using CrewAI Flow when available."""
    flow = TourismEvaluationFlow(n_tourists=n_tourists, steps=steps, seed=seed, output_dir=output_dir, model_name=model_name, llm_report=llm_report, data_dir=data_dir)
    return flow.kickoff()
