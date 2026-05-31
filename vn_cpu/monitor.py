"""VN-CPU ANSI Cognitive Monitor

A real-time dashboard for the Unified Neural Organism using the Rich library.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich import box

console = Console()

class CognitiveMonitor:
    def __init__(self, organism):
        self.organism = organism
        self.layout = Layout()
        self._setup_layout()

    def _setup_layout(self):
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        self.layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        self.layout["left"].split_column(
            Layout(name="cpu_state"),
            Layout(name="registers")
        )
        self.layout["right"].split_column(
            Layout(name="metabolism"),
            Layout(name="acoustics")
        )

    def generate_view(self):
        # 1. Header
        self.layout["header"].update(Panel(
            f"🧠 [bold cyan]VN-CPU v0.4[/bold cyan] | [bold green]UNIFIED NEURAL ORGANISM[/bold green] | [yellow]MODE: {self.organism.mode.upper()}[/yellow]",
            border_style="blue", box=box.ROUNDED
        ))

        # 2. CPU State
        cpu_info = (
            f"Instruction Count: {self.organism.cpu.runtime.instruction_count}\n"
            f"Last Pulse: {self.organism.cpu.runtime.history[-1]['inst'] if self.organism.cpu.runtime.history else 'N/A'}"
        )
        self.layout["cpu_state"].update(Panel(cpu_info, title="Neural Core Pulse", border_style="cyan"))

        # 3. Registers
        reg_table = Table(title="Context Registers", box=box.MINIMAL)
        reg_table.add_column("Reg", justify="right", style="cyan")
        reg_table.add_column("Content", style="white")
        for k, v in list(self.organism.cpu.runtime.ctx.items())[:8]:
            reg_table.add_row(f"#{k}", str(v)[:40] + "...")
        self.layout["registers"].update(Panel(reg_table, title="Memory State", border_style="magenta"))

        # 4. Metabolism
        enzyme_list = "\n".join([f"✨ Active: {e.name}" for e in self.organism.sel.enzymes])
        self.layout["metabolism"].update(Panel(enzyme_list, title="Metabolic Soup (SEL)", border_style="green"))

        # 5. Acoustics
        res_list = "\n".join([f"🎵 {r.name}: Tuning Fork @ {r.threshold}" for r in self.organism.crl.resonators])
        self.layout["acoustics"].update(Panel(res_list, title="Acoustic Resonance (CRL)", border_style="yellow"))

        return self.layout

    def render_loop(self):
        with Live(self.generate_view(), refresh_per_second=2) as live:
            # The actual execution is driven externally, this just shows the snapshot
            while True:
                live.update(self.generate_view())
