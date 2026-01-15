from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from cw_config import load_cfg, resolve_paths


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    cfg = load_cfg(base_dir / "run.cfg")
    paths = resolve_paths(cfg["paths"], base_dir)

    data = np.load(str(paths["npz"]))
    t_ms = data["t"] * 1000.0

    bot_nodes = sorted(
        [k for k in data.files if k.startswith("bot_")],
        key=lambda s: int(s.split("_")[1])
    )

    plt.figure(figsize=(10, 5))
    plt.plot(t_ms, data["vin"], label="Input", color="gray", alpha=0.5)
    for bn in bot_nodes:
        stage = bn.split("_")[1]
        plt.plot(t_ms, data[bn], label=f"Stage {stage}")
    plt.title(f"CW Multiplier - {len(bot_nodes)} Stages")
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage (V)")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
