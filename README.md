# AIS Sustainable POI Recommender Evaluation

This repository contains the code, generated data and results for an agent-based evaluation of sustainable tourism recommender systems for urban Points of Interest (POIs). The project compares three recommendation strategies:

- `popularity`: recommends mostly famous and popular POIs.
- `personalized`: recommends POIs that match the tourist profile.
- `sustainable`: combines tourist preferences with crowd reduction, neighbourhood redistribution, sustainability value and local economy criteria.

The repository contains two implementations of the same evaluation idea. The first one is a controlled low-LLM approach, where the POI catalogue and tourist profiles are curated and the simulator is mostly deterministic. The second one is an agent-heavy LLM approach, where local LLM agents generate the POIs, tourist segments and recommender rule configuration before running the same type of agent-based simulation.

## Repository Structure

```text
.
├── code/                    # Controlled low-LLM implementation
├── code_agents/             # Agent-heavy LLM implementation
├── data/                    # Curated input data for the controlled approach
├── outputs/                 # Results of the controlled approach
├── output_agents/           # Results of the agent-heavy approach
├── figures/                 # Report figures for the controlled approach and extended analyses
├── requirements.txt         # Python dependencies
```

## Approach 1: Controlled Low-LLM Simulator

The controlled implementation is located in `code/`. It uses curated POI and tourist-profile data stored in `data/`, then runs an agent-based simulation over three recommender strategies.

Main files:

- `code/main.py`: entry point for the controlled simulation.
- `code/utils.py`: simulator, recommender scoring, metrics and plotting utilities.
- `code/data_generation.py`: curated input preparation and lightweight LLM support.
- `code/extended_analysis.py`: multi-seed, sensitivity and ablation analyses.

Main results:

- `outputs/summary.csv`
- `outputs/visits.csv`
- `outputs/recommendations.csv`
- `outputs/poi_metrics.csv`
- `outputs/neighbourhood_metrics.csv`
- `outputs/extended/multi_seed_summary.csv`
- `outputs/extended/alpha_sensitivity.csv`
- `outputs/extended/ablation_study.csv`

## Approach 2: Agent-Heavy LLM Simulator

The agent-heavy implementation is located in `code_agents/`. It uses local role-based LLM agents to create the structured inputs, then runs a deterministic agent-based simulator using the generated data.

Main files:

- `code_agents/main.py`: entry point for the agent-heavy pipeline.
- `code_agents/agents.py`: local LLM agents for POI generation, tourist-profile generation, rule calibration and auditing.
- `code_agents/simulation.py`: simulator, recommender scoring, metrics and plotting utilities.

Main results:

- `output_agents/summary.csv`
- `output_agents/visits.csv`
- `output_agents/recommendations.csv`
- `output_agents/poi_metrics.csv`
- `output_agents/neighbourhood_metrics.csv`
- `output_agents/data/agent_generated_pois.csv`
- `output_agents/data/agent_tourist_profiles.json`
- `output_agents/data/agent_rule_config.json`
- `output_agents/agent_logs/`

## Installation

Create and activate a Python environment, then install the dependencies:

```bash
pip install -r requirements.txt
```

The agent-heavy implementation uses a local Ollama model. The final execution used:

```text
ollama/qwen2.5:3b
```

If Ollama is not installed or the model is not available, the controlled simulator can still be inspected through the saved results in `outputs/`.
For checking the agent-heavy simulator with the already generated agent data, the optional LLM-written audit and interpretation can be skipped with `--no-llm-text`.

## Running the Controlled Approach

From the repository root:

```bash
python code/main.py --tourists 2000 --steps 5 --seed 42 --outdir outputs --data-dir data
```

To run the extended analyses:

```bash
python code/extended_analysis.py
```

## Running the Agent-Heavy Approach

From the repository root:

```bash
python code_agents/main.py --tourists 1000 --steps 5 --seed 42 --outdir output_agents --no-llm-text
```

To regenerate the LLM-agent inputs from scratch:

```bash
python code_agents/main.py --tourists 1000 --steps 5 --seed 42 --outdir output_agents --force
```

Using `--force` removes and recreates `output_agents`, so it should only be used when the generated agent data need to be refreshed.

## Main Finding

Both implementations support the same conclusion. The personalized recommender obtains the highest individual relevance and satisfaction, while the sustainable recommender obtains the strongest city-level behaviour. In particular, the sustainable recommender reduces central pressure, hotspot concentration and top-POI dominance with only a small satisfaction loss relative to the personalized recommender.

In the controlled approach:

- Sustainable satisfaction: `0.6700`
- Personalized satisfaction: `0.6950`
- Sustainable central visit share: `0.3131`
- Popularity central visit share: `0.8598`

In the agent-heavy approach:

- Sustainable satisfaction: `0.6774`
- Personalized satisfaction: `0.7036`
- Sustainable central visit share: `0.2734`
- Popularity central visit share: `0.9072`
