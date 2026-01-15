from pathlib import Path

from cw_config import load_cfg, resolve_paths
from cw_pipeline import build_assets


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    cfg = load_cfg(base_dir / "run.cfg")
    paths = resolve_paths(cfg["paths"], base_dir)
    out = build_assets(cfg, paths)
    print("Wrote:", out["npz"])
    print("Wrote:", out["svg_raw"])
    print("Wrote:", out["svg_clean"])


if __name__ == "__main__":
    main()
