import copy
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from utils import STRATEGIES, STRATEGY_COLORS, create_tourists, load_pois_from_file, load_rule_config, load_tourist_profiles, run_simulation, summarise_results

METRICS = ["avg_satisfaction", "max_slot_crowd_ratio", "central_visit_share", "hotspot_visit_share", "neighbourhood_entropy", "top_5_poi_visit_share"]
BLUE = "#1F4E79"
LIGHT_BLUE = "#73A9C2"
DARK_BLUE = "#0B2E4A"
ACCENT = "#8DBBD3"


def renormalise(group):
    """Rescale a weight group after removing one component."""
    total = sum(group.values())
    if total <= 0:
        return group
    for key in group:
        group[key] = round(group[key] / total, 4)
    return group


def run_one(strategy, pois, tourists, rule_config, seed, steps):
    """Run one strategy and return only the summary row."""
    visits, quality, crowd = run_simulation(strategy, pois, tourists, steps=steps, seed=seed, rule_config=rule_config)
    return summarise_results(strategy, pois, visits, quality, crowd)


def run_seed_robustness(pois, profiles, rule_config, seeds, n_tourists, steps, output_dir):
    """Evaluate all strategies under several random seeds."""
    rows = []
    for seed in seeds:
        print(f"Robustness seed {seed}...", flush=True)
        tourists = create_tourists(n_tourists, profiles, seed=seed)
        for offset, strategy in enumerate(STRATEGIES):
            row = run_one(strategy, pois, tourists, rule_config, seed + 100 * offset, steps)
            row["seed"] = seed
            rows.append(row)
    runs = pd.concat(rows, ignore_index=True)
    runs.to_csv(output_dir / "multi_seed_runs.csv", index=False)

    summary_rows = []
    for strategy, group in runs.groupby("strategy"):
        row = {"strategy": strategy}
        for metric in METRICS[:4]:
            row[f"{metric}_mean"] = group[metric].mean()
            row[f"{metric}_std"] = group[metric].std(ddof=1)
        summary_rows.append(row)
    seed_summary = pd.DataFrame(summary_rows).sort_values("strategy")
    seed_summary.to_csv(output_dir / "multi_seed_summary.csv", index=False)
    return runs, seed_summary


def run_alpha_sensitivity(pois, profiles, rule_config, alpha_values, seed, n_tourists, steps, output_dir):
    """Evaluate the sustainable recommender under different alpha values."""
    tourists = create_tourists(n_tourists, profiles, seed=seed)
    rows = []
    for alpha in alpha_values:
        print(f"Alpha sensitivity {alpha:.2f}...", flush=True)
        cfg = copy.deepcopy(rule_config)
        cfg["sustainable"]["alpha_base"] = alpha
        cfg["sustainable"]["alpha_user"] = 0.0
        row = run_one("sustainable", pois, tourists, cfg, seed + int(alpha * 1000), steps)
        row["alpha_base"] = alpha
        row["expected_effect"] = {
            0.20: "More personalization, less sustainability impact",
            0.40: "Balanced trade-off",
            0.60: "Stronger sustainability, possible satisfaction loss",
            0.80: "Aggressive redistribution",
        }.get(round(alpha, 2), "Sensitivity setting")
        rows.append(row)
    sensitivity = pd.concat(rows, ignore_index=True)
    sensitivity.to_csv(output_dir / "alpha_sensitivity.csv", index=False)
    return sensitivity


def run_ablation(pois, profiles, rule_config, seed, n_tourists, steps, output_dir):
    """Remove one sustainable component at a time."""
    tourists = create_tourists(n_tourists, profiles, seed=seed)
    variants = {}

    variants["Full sustainable"] = copy.deepcopy(rule_config)

    no_crowd = copy.deepcopy(rule_config)
    no_crowd["sustainable"]["social"]["crowd"] = 0.0
    renormalise(no_crowd["sustainable"]["social"])
    variants["Without crowd term"] = no_crowd

    no_relief = copy.deepcopy(rule_config)
    no_relief["sustainable"]["social"]["neighbourhood_relief"] = 0.0
    renormalise(no_relief["sustainable"]["social"])
    variants["Without neighbourhood relief"] = no_relief

    no_diversity = copy.deepcopy(rule_config)
    no_diversity["sustainable"]["diversity_rule"] = False
    variants["Without diversity rule"] = no_diversity

    no_local = copy.deepcopy(rule_config)
    no_local["sustainable"]["social"]["local_economy"] = 0.0
    renormalise(no_local["sustainable"]["social"])
    variants["Without local economy term"] = no_local

    rows = []
    for idx, (variant, cfg) in enumerate(variants.items()):
        print(f"Ablation: {variant}...", flush=True)
        row = run_one("sustainable", pois, tourists, cfg, seed + 500 + idx, steps)
        row["variant"] = variant
        rows.append(row)
    ablation = pd.concat(rows, ignore_index=True)
    ablation.to_csv(output_dir / "ablation_study.csv", index=False)
    return ablation


def value_label(ax, bars, fmt="{:.2f}", horizontal=False):
    """Add small value labels to bar plots."""
    for bar in bars:
        if horizontal:
            value = bar.get_width()
            ax.text(value + 0.01, bar.get_y() + bar.get_height() / 2, fmt.format(value), va="center", fontsize=8)
        else:
            value = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.01, fmt.format(value), ha="center", fontsize=8)


def plot_improved_main_figures(summary, neighbourhood_table, poi_table, figures_dir):
    """Regenerate the main figures with cleaner labels and value annotations."""
    figures_dir.mkdir(parents=True, exist_ok=True)
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
        bars = ax.bar(STRATEGIES, values, color=[STRATEGY_COLORS[strategy] for strategy in STRATEGIES], width=0.60)
        value_label(ax, bars)
        ax.set_title(title.upper(), fontsize=13, weight="bold")
        ax.set_ylim(0, max(values) * 1.22)
        ax.tick_params(axis="x", rotation=0, labelsize=10)
        ax.tick_params(axis="y", labelsize=9)
    fig.tight_layout()
    fig.savefig(figures_dir / "strategy_comparison.png", dpi=220)
    plt.close(fig)

    top_neighbourhoods = neighbourhood_table.groupby("neighbourhood")["visits"].sum().sort_values(ascending=False).head(10).index
    plot_data = neighbourhood_table[neighbourhood_table["neighbourhood"].isin(top_neighbourhoods)]
    pivot = plot_data.pivot_table(index="neighbourhood", columns="strategy", values="visit_share", fill_value=0).reindex(columns=STRATEGIES)
    pivot = pivot.sort_values("popularity", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    y_positions = np.arange(len(pivot))
    bar_height = 0.24
    for offset, strategy in zip([-bar_height, 0, bar_height], STRATEGIES):
        bars = ax.barh(y_positions + offset, pivot[strategy], height=bar_height, color=STRATEGY_COLORS[strategy], label=strategy)
        value_label(ax, bars, fmt="{:.2f}", horizontal=True)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(pivot.index, fontsize=9)
    ax.set_title("TOP NEIGHBOURHOODS BY VISIT SHARE", fontsize=13, weight="bold")
    ax.set_xlabel("Share of visits")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures_dir / "neighbourhood_distribution.png", dpi=220)
    plt.close(fig)

    top_pois = poi_table.groupby("poi_name")["visits"].sum().sort_values(ascending=False).head(10).index
    plot_data = poi_table[poi_table["poi_name"].isin(top_pois)]
    pivot = plot_data.pivot_table(index="poi_name", columns="strategy", values="max_slot_crowd_ratio", fill_value=0).reindex(columns=STRATEGIES)
    pivot = pivot.sort_values("popularity", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    for offset, strategy in zip([-bar_height, 0, bar_height], STRATEGIES):
        bars = ax.barh(y_positions[:len(pivot)] + offset, pivot[strategy], height=bar_height, color=STRATEGY_COLORS[strategy], label=strategy)
        value_label(ax, bars, fmt="{:.2f}", horizontal=True)
    ax.set_yticks(np.arange(len(pivot)))
    ax.set_yticklabels(pivot.index, fontsize=9)
    ax.axvline(1.0, color="#C44E52", linestyle="--", linewidth=1)
    ax.set_title("PEAK CROWDING AT MAIN POIS", fontsize=13, weight="bold")
    ax.set_xlabel("Maximum crowd / capacity")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures_dir / "top_poi_crowding.png", dpi=220)
    plt.close(fig)


def plot_extended_figures(main_summary, sensitivity, figures_dir):
    """Create sensitivity and trade-off figures."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sensitivity["alpha_base"], sensitivity["avg_satisfaction"], marker="o", color=DARK_BLUE, label="Satisfaction")
    ax.plot(sensitivity["alpha_base"], sensitivity["central_visit_share"], marker="o", color=BLUE, label="Central share")
    ax.plot(sensitivity["alpha_base"], sensitivity["hotspot_visit_share"], marker="o", color=LIGHT_BLUE, label="Hotspot share")
    ax.plot(sensitivity["alpha_base"], sensitivity["max_slot_crowd_ratio"], marker="o", color=ACCENT, label="Max crowd ratio")
    ax.set_xlabel("Sustainability weight alpha")
    ax.set_ylabel("Metric value")
    ax.set_title("SENSITIVITY TO SUSTAINABILITY WEIGHT", fontsize=13, weight="bold")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures_dir / "alpha_sensitivity.png", dpi=220)
    plt.close(fig)

    y_metrics = [("central_visit_share", "Central visit share"), ("hotspot_visit_share", "Hotspot visit share"), ("max_slot_crowd_ratio", "Max crowd ratio")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, (metric, title) in zip(axes, y_metrics):
        for _, row in main_summary.iterrows():
            strategy = row["strategy"]
            ax.scatter(row["avg_satisfaction"], row[metric], s=120, color=STRATEGY_COLORS[strategy])
            ax.text(row["avg_satisfaction"] + 0.002, row[metric], strategy, fontsize=9, va="center")
        ax.set_xlabel("Satisfaction")
        ax.set_ylabel(title)
        ax.set_title(title.upper(), fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(figures_dir / "tradeoff_space.png", dpi=220)
    plt.close(fig)


def latex_mean_std(seed_summary, tables_dir):
    """Write multi-seed table in mean ± std format."""
    labels = {
        "avg_satisfaction": "Satisfaction",
        "max_slot_crowd_ratio": "Max crowd ratio",
        "central_visit_share": "Central share",
        "hotspot_visit_share": "Hotspot share",
    }
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\scriptsize",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        "Strategy & Satisfaction & Max crowd ratio & Central share & Hotspot share \\\\",
        "\\hline",
    ]
    for _, row in seed_summary.iterrows():
        values = []
        for metric in labels:
            values.append(f"{row[f'{metric}_mean']:.4f} $\\pm$ {row[f'{metric}_std']:.4f}")
        lines.append(f"{row['strategy'].capitalize()} & " + " & ".join(values) + r" \\")
    lines += ["\\hline", "\\end{tabular}", "}", "\\caption{Robustness across ten stochastic seeds.}", "\\label{tab:multi_seed}", "\\end{table*}"]
    (tables_dir / "multi_seed_results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_sensitivity(sensitivity, tables_dir):
    """Write alpha sensitivity table."""
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\scriptsize",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{llrrrr}",
        "\\hline",
        "Alpha base & Expected effect & Satisfaction & Max crowd ratio & Central share & Hotspot share \\\\",
        "\\hline",
    ]
    for _, row in sensitivity.sort_values("alpha_base").iterrows():
        lines.append(f"{row['alpha_base']:.2f} & {row['expected_effect']} & {row['avg_satisfaction']:.4f} & {row['max_slot_crowd_ratio']:.4f} & {row['central_visit_share']:.4f} & {row['hotspot_visit_share']:.4f} " + r"\\")
    lines += ["\\hline", "\\end{tabular}", "}", "\\caption{Sensitivity analysis of the sustainability weight $\\alpha$.}", "\\label{tab:alpha_sensitivity}", "\\end{table*}"]
    (tables_dir / "alpha_sensitivity.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_ablation(ablation, tables_dir):
    """Write ablation table."""
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\scriptsize",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        "Model variant & Max crowd ratio & Neighbourhood entropy & Central share & Satisfaction \\\\",
        "\\hline",
    ]
    for _, row in ablation.iterrows():
        lines.append(f"{row['variant']} & {row['max_slot_crowd_ratio']:.4f} & {row['neighbourhood_entropy']:.4f} & {row['central_visit_share']:.4f} & {row['avg_satisfaction']:.4f} " + r"\\")
    lines += ["\\hline", "\\end{tabular}", "}", "\\caption{Ablation study of the sustainable recommender components.}", "\\label{tab:ablation}", "\\end{table*}"]
    (tables_dir / "ablation_study.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_new_figures(figures_dir):
    """Write wrappers for new figures."""
    specs = {
        "alpha_sensitivity": ("alpha_sensitivity.png", "Sensitivity of the sustainable recommender to the sustainability weight $\\alpha$.", "fig:alpha_sensitivity"),
        "tradeoff_space": ("tradeoff_space.png", "Trade-off between tourist satisfaction and urban-pressure indicators.", "fig:tradeoff_space"),
    }
    for stem, (image, caption, label) in specs.items():
        text = "\n".join([
            "\\begin{figure*}[t]",
            "\\centering",
            f"\\includegraphics[width=0.95\\textwidth]{{figures/{image}}}",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            "\\end{figure*}",
            "",
        ])
        (figures_dir / f"{stem}.tex").write_text(text, encoding="utf-8")


def main():
    root = Path(__file__).resolve().parents[1]
    output_dir = root / "outputs" / "extended"
    figures_dir = root / "figures"
    tables_dir = root / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    pois = load_pois_from_file(root / "data" / "poi_catalogue.csv")
    profiles = load_tourist_profiles(root / "data" / "tourist_profiles.json")
    rule_config = load_rule_config(root / "data" / "rule_config_input.json")

    main_summary = pd.read_csv(root / "outputs" / "summary.csv")
    neighbourhood_table = pd.read_csv(root / "outputs" / "neighbourhood_metrics.csv")
    poi_table = pd.read_csv(root / "outputs" / "poi_metrics.csv")
    plot_improved_main_figures(main_summary, neighbourhood_table, poi_table, figures_dir)

    seeds = [10, 20, 30, 40, 42, 50, 60, 70, 80, 90]
    extended_tourists = 600
    runs, seed_summary = run_seed_robustness(pois, profiles, rule_config, seeds, n_tourists=extended_tourists, steps=5, output_dir=output_dir)
    sensitivity = run_alpha_sensitivity(pois, profiles, rule_config, [0.20, 0.40, 0.60, 0.80], seed=42, n_tourists=extended_tourists, steps=5, output_dir=output_dir)
    ablation = run_ablation(pois, profiles, rule_config, seed=42, n_tourists=extended_tourists, steps=5, output_dir=output_dir)

    plot_extended_figures(main_summary, sensitivity, figures_dir)
    latex_mean_std(seed_summary, tables_dir)
    latex_sensitivity(sensitivity, tables_dir)
    latex_ablation(ablation, tables_dir)
    latex_new_figures(figures_dir)

    metadata = {
        "robustness_seeds": seeds,
        "n_tourists": extended_tourists,
        "steps": 5,
        "note": "Extended experiments use 600 agents to test robustness while keeping the additional analysis computationally manageable.",
    }
    (output_dir / "extended_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("Extended analysis completed.")
    print(seed_summary.round(4).to_string(index=False))
    print(sensitivity[["alpha_base", "avg_satisfaction", "max_slot_crowd_ratio", "central_visit_share", "hotspot_visit_share"]].round(4).to_string(index=False))
    print(ablation[["variant", "max_slot_crowd_ratio", "neighbourhood_entropy", "central_visit_share", "avg_satisfaction"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
