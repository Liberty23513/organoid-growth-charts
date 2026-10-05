"""
Build the per-sample cell-type composition table used by the organoid growth-chart project.

Source: Human Neural Organoid Cell Atlas (HNOCA), He, Dony, Fleck et al., Nature 2024,
doi 10.1038/s41586-024-08172-8, public on CELLxGENE Discover (CC BY 4.0).

The atlas file is 18.8 GB. This script never downloads it. It reads only the `obs`
(per-cell metadata) columns it needs over HTTP range requests, which takes a few minutes
and well under 1 GB of memory. Expression values are never touched.

Output: hnoca_sample_composition.csv, one row per organoid sample:
    sample, n_cells, age, publication, protocol, protocol_type, cell_line,
    frac_NPC_IP, frac_neuron, frac_glia, frac_neuroepithelium_PSC,
    l2_<cell type> for each of the 17 annot_level_2 cell types

Usage:
    pip install remfile h5py pandas numpy
    python build_composition_table.py [--min-cells 100] [--out hnoca_sample_composition.csv]
"""
import argparse
import h5py
import pandas as pd
import remfile

URL = "https://datasets.cellxgene.cziscience.com/127a3c9a-7bcb-4362-a73e-e60fd67f5bae.h5ad"

COLUMNS = ["organoid_age_days", "bio_sample", "id", "publication",
           "assay_differentiation", "assay_type_differentiation", "cell_line", "annot_level_2"]

GROUPS = {
    "frac_NPC_IP": ["Dorsal Telencephalic NPC", "Ventral Telencephalic NPC",
                    "Non-telencephalic NPC", "Dorsal Telencephalic IP"],
    "frac_neuron": ["Dorsal Telencephalic Neuron", "Ventral Telencephalic Neuron",
                    "Non-telencephalic Neuron"],
    "frac_glia": ["Glioblast", "Astrocyte", "OPC"],
    "frac_neuroepithelium_PSC": ["Neuroepithelium", "PSC"],
}


def read_obs_column(obs, name):
    node = obs[name]
    if isinstance(node, h5py.Group):  # anndata categorical: codes + categories
        cats = [c.decode() if isinstance(c, bytes) else c for c in node["categories"][:]]
        return pd.Categorical.from_codes(node["codes"][:], categories=cats)
    return node[:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-cells", type=int, default=100)
    ap.add_argument("--out", default="hnoca_sample_composition.csv")
    args = ap.parse_args()

    with h5py.File(remfile.File(URL), "r") as f:
        cells = pd.DataFrame({c: read_obs_column(f["obs"], c) for c in COLUMNS})

    # bio_sample labels are not unique across datasets, so key samples on dataset id + bio_sample
    cells["sample"] = cells["id"].astype(str) + "|" + cells["bio_sample"].astype(str)
    cells["age"] = pd.to_numeric(cells["organoid_age_days"])

    per = cells.groupby("sample", observed=True).agg(
        n_cells=("age", "size"), age=("age", "first"),
        age_nuniq=("age", "nunique"), line_nuniq=("cell_line", "nunique"),
        publication=("publication", "first"), protocol=("assay_differentiation", "first"),
        protocol_type=("assay_type_differentiation", "first"), cell_line=("cell_line", "first"))
    assert (per.age_nuniq == 1).all(), "a sample has more than one age"
    assert (per.line_nuniq == 1).all(), "a sample has more than one cell line"
    per = per.drop(columns=["age_nuniq", "line_nuniq"])

    comp = pd.crosstab(cells["sample"], cells["annot_level_2"].astype(str), normalize="index")
    for name, types in GROUPS.items():
        per[name] = comp[[t for t in types if t in comp.columns]].sum(axis=1)
    table = per.join(comp.add_prefix("l2_"))
    table = table[table.n_cells >= args.min_cells]
    table.reset_index().to_csv(args.out, index=False)
    print(f"{len(cells):,} cells -> {len(per)} samples -> {len(table)} kept "
          f"(>= {args.min_cells} cells), written to {args.out}")


if __name__ == "__main__":
    main()
