import sys
import uuid
from colorama import Fore, Style, init
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from src.deep_agent import builder

# Initialize colorama and load environment
init(autoreset=True)
load_dotenv()


def print_banner():
    print(Fore.CYAN + Style.BRIGHT + """
╔═══════════════════════════════════════════════════════════════╗
║         🤖 LangGraph Multi-Agent Research Assistant           ║
║   Autonomous Persona Generation • Parallel Web Research      ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def run_cli():
    print_banner()

    # 1. User inputs
    default_topic = "The Future of Solid State Batteries in Electric Vehicles"
    print(Fore.YELLOW + f"Enter research topic (Press Enter for default: '{default_topic}'):")
    user_topic = input(Fore.WHITE + "> ").strip()
    topic = user_topic if user_topic else default_topic

    print(Fore.YELLOW + "\nEnter number of analyst perspectives to generate (Default: 2, Max: 5):")
    analyst_input = input(Fore.WHITE + "> ").strip()
    try:
        max_analysts = int(analyst_input) if analyst_input else 2
        max_analysts = max(1, min(max_analysts, 5))
    except ValueError:
        max_analysts = 2

    print(Fore.GREEN + f"\n[+] Starting Research Workflow for: \"{topic}\" with {max_analysts} analysts...\n")

    # 2. Compile graph with memory checkpointer to support interrupt/resume
    memory = MemorySaver()
    app = builder.compile(checkpointer=memory)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "topic": topic,
        "max_analysts": max_analysts,
        "sections": []
    }

    # 3. Step 1: Run until Human Feedback Interrupt
    print(Fore.BLUE + "[*] Step 1/3: Analyzing topic & generating expert analyst personas...")
    for event in app.stream(initial_state, config, stream_mode="updates"):
        for node_name in event.keys():
            if node_name == "create_analysts":
                print(Fore.GREEN + "  ✔ Analyst personas created successfully.")

    # 4. Human-in-the-Loop Review Loop
    while True:
        current_state = app.get_state(config)
        analysts = current_state.values.get("analysts", [])

        print(Fore.CYAN + Style.BRIGHT + "\n───────────────── 🧑‍🔬 Proposed Analyst Panel ─────────────────")
        for i, a in enumerate(analysts, start=1):
            name = getattr(a, "name", "Expert")
            role = getattr(a, "role", "")
            affiliation = getattr(a, "affiliation", "")
            desc = getattr(a, "description", "")
            print(Fore.WHITE + Style.BRIGHT + f"\n[{i}] {name}")
            print(Fore.YELLOW + f"    Role:        {role}")
            print(Fore.MAGENTA + f"    Affiliation: {affiliation}")
            print(Fore.WHITE + f"    Focus:       {desc}")
        print(Fore.CYAN + Style.BRIGHT + "─────────────────────────────────────────────────────────────\n")

        # Check if we are paused at interrupt
        if not current_state.next:
            break

        print(Fore.GREEN + Style.BRIGHT + "Do you approve these analysts?")
        print(Fore.WHITE + "  • Press [Enter] or type 'y' / 'perfect' to approve and start parallel interviews.")
        print(Fore.WHITE + "  • Or type your feedback/critique to regenerate:")
        feedback = input(Fore.YELLOW + "> ").strip()

        if feedback.lower() in {"", "y", "yes", "perfect", "continue", "approved"}:
            print(Fore.GREEN + "\n[+] Analysts approved! Initiating parallel web research interviews...\n")
            resume_command = Command(resume="perfect")
            break
        else:
            print(Fore.BLUE + f"\n[*] Incorporating your feedback: \"{feedback}\"")
            print(Fore.BLUE + "[*] Regenerating analysts...")
            resume_command = Command(resume=feedback)
            for event in app.stream(resume_command, config, stream_mode="updates"):
                for node_name in event.keys():
                    if node_name == "create_analysts":
                        print(Fore.GREEN + "  ✔ Analysts regenerated with your feedback.")

    # 5. Step 2 & 3: Run Parallel Research & Synthesis
    print(Fore.BLUE + "[*] Step 2/3: Conducting interviews & Tavily web research in parallel...")
    for event in app.stream(resume_command, config, stream_mode="updates"):
        for node_name in event.keys():
            if node_name == "conduct_interview":
                print(Fore.CYAN + "  ✔ Finished an interview subgraph & generated report section memo.")
            elif node_name == "write_report":
                print(Fore.MAGENTA + "  ✔ Synthesized core report narrative (Insights).")
            elif node_name == "write_introduction":
                print(Fore.YELLOW + "  ✔ Formulated executive introduction.")
            elif node_name == "write_conclusion":
                print(Fore.YELLOW + "  ✔ Formulated conclusion & implications.")
            elif node_name == "finalize_report":
                print(Fore.GREEN + Style.BRIGHT + "  ✔ Report assembly & source citation reduce completed!")

    # 6. Save & Display Final Report
    final_state = app.get_state(config)
    final_report = final_state.values.get("final_report", "")

    output_filename = "final_report.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_report)

    print(Fore.GREEN + Style.BRIGHT + f"\n🎉 Research Complete! Report successfully saved to: {output_filename}\n")
    print(Fore.CYAN + "─────────────────────────────────────────────────────────────")
    print(final_report[:1200] + ("\n\n[... Remaining content saved in final_report.md ...]" if len(final_report) > 1200 else ""))
    print(Fore.CYAN + "─────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n[!] Process cancelled by user. Exiting.")
        sys.exit(0)
