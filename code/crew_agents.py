import os
from pathlib import Path
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
DEFAULT_LLM_MODEL = os.getenv("AIS_LLM_MODEL", "ollama/qwen2.5:7b")
try:
    from crewai import Agent, Crew, LLM, Process, Task
    CREWAI_AGENT_AVAILABLE = True
except ModuleNotFoundError:
    CREWAI_AGENT_AVAILABLE = False


def build_llm(model_name=DEFAULT_LLM_MODEL):
    """Create the LLM configuration used by CrewAI agents."""
    return LLM(model=model_name, temperature=0.0, timeout=240, max_tokens=2048)


def save_crew_output(result, output_file):
    """Persist CrewAI output even when this CrewAI version skips output_file."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    text = (getattr(result, "raw", None) or str(result)).strip()
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        text = "\n".join(lines[1:-1]).strip()
    output_file.write_text(text + "\n", encoding="utf-8")
    return result


def maybe_write_llm_interpretation(summary_text, output_file, model_name=DEFAULT_LLM_MODEL):
    """Ask the evaluation agent to write a short interpretation."""
    if not CREWAI_AGENT_AVAILABLE:
        raise RuntimeError("CrewAI is not installed in this environment.")

    analyst = Agent(
        role="Sustainable tourism evaluator",
        goal="Interpret crowding, neighbourhood spread, satisfaction, diversity and constraint respect.",
        backstory="You are a responsible-tourism analyst. Explain trade-offs without inventing numbers.",
        llm=build_llm(model_name),
        verbose=False,
    )
    task = Task(
        description=(
            "Rewrite the following verified findings as a concise Markdown interpretation. Keep the same meaning and numbers. Do not calculate new metrics, "
            "do not add claims that are not in the notes, and do not say that a value is higher/lower unless the notes already say so. Constraint respect "
            "means respecting tourist budget/profile constraints, not legal regulations.\n\n"
            f"{summary_text}"
        ),
        expected_output="A concise Markdown interpretation of the simulation results.",
        agent=analyst,
        output_file=str(output_file),
    )
    crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=False)
    return save_crew_output(crew.kickoff(), output_file)


def maybe_write_llm_input_audit(input_summary, output_file, model_name=DEFAULT_LLM_MODEL):
    """Ask a small CrewAI agent to audit the prepared simulator inputs."""
    if not CREWAI_AGENT_AVAILABLE:
        raise RuntimeError("CrewAI is not installed in this environment.")

    auditor = Agent(
        role="Input assumptions auditor",
        goal="Check whether the prepared POI, tourist and rule inputs are coherent for a seminar simulation.",
        backstory="You review structured tourism simulation assumptions. You are concise and do not invent facts.",
        llm=build_llm(model_name),
        verbose=False,
    )
    task = Task(
        description=(
            "Given this simulator input summary, write a short Markdown audit with: main assumptions, why the inputs are acceptable for a seminar "
            "experiment, and the main limitations. Do not invent new POIs or numbers. Do not call the inputs official or real-world measurements; "
            "describe them as curated seminar inputs. Avoid the phrase 'real-world'.\n\n"
            f"{input_summary}"
        ),
        expected_output="A concise Markdown audit of the prepared simulation inputs.",
        agent=auditor,
        output_file=str(output_file),
    )
    crew = Crew(agents=[auditor], tasks=[task], process=Process.sequential, verbose=False)
    return save_crew_output(crew.kickoff(), output_file)
