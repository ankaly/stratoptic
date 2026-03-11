"""
Stratoptic - Material Database
================================
Author      : Necmeddin
Institution : Gazi University, Department of Photonics
Version     : 0.1.0

Loads and queries optical materials from the JSON database.
Supports both literature values and Gazi Photonics Research Center samples.
"""

import json
import os
from typing import Optional
from tmm import Material


# =============================================================================
# DATABASE
# =============================================================================

class MaterialDatabase:
    """
    Optical material database manager.

    Loads materials from a JSON file and provides query methods.

    Usage
    -----
    db = MaterialDatabase()
    sio2 = db.get("SiO2")
    db.list_all()
    db.search("titanium")
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default: look for materials.json next to this file
            db_path = os.path.join(os.path.dirname(__file__), "materials.json")

        with open(db_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        self._materials   = self._data.get("materials", {})
        self._gazi        = self._data.get("gazi_photonics", {}).get("samples", {})

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, name: str) -> Material:
        """
        Retrieve a Material by name.

        Searches literature database first, then Gazi Photonics samples.

        Parameters
        ----------
        name : str — material key (e.g. 'SiO2', 'TiO2', 'Au')

        Returns
        -------
        Material

        Raises
        ------
        KeyError if material not found
        """
        if name in self._materials:
            entry = self._materials[name]
            return Material(
                name = entry["name"],
                n    = entry["n"],
                k    = entry.get("k", 0.0)
            )

        if name in self._gazi:
            entry = self._gazi[name]
            return Material(
                name = entry["name"],
                n    = entry["n"],
                k    = entry.get("k", 0.0)
            )

        available = list(self._materials.keys()) + list(self._gazi.keys())
        raise KeyError(
            f"Material '{name}' not found.\n"
            f"Available: {', '.join(sorted(available))}"
        )

    def list_all(self) -> None:
        """Print all available materials grouped by category."""
        categories = {}
        for key, entry in self._materials.items():
            cat = entry.get("category", "other")
            categories.setdefault(cat, []).append(entry)

        print(f"\n{'─'*60}")
        print(f"  Stratoptic Material Database — Literature Values")
        print(f"{'─'*60}")

        for cat, entries in sorted(categories.items()):
            print(f"\n  [{cat.upper()}]")
            for e in entries:
                k_str = f", k={e['k']}" if e.get("k", 0.0) > 0 else ""
                print(f"    {e['name']:<14} n={e['n']}{k_str}")
                print(f"               {e['full_name']}")

        if self._gazi:
            print(f"\n  [GAZI PHOTONICS RESEARCH CENTER]")
            for key, entry in self._gazi.items():
                print(f"    {entry['name']:<14} n={entry['n']}, k={entry.get('k',0.0)}")
        else:
            print(f"\n  [GAZI PHOTONICS RESEARCH CENTER]")
            print(f"    (No samples yet — to be added)")

        print(f"{'─'*60}\n")

    def search(self, query: str) -> list:
        """
        Search materials by name or full_name (case-insensitive).

        Parameters
        ----------
        query : str — search term

        Returns
        -------
        list of matching Material objects
        """
        q = query.lower()
        results = []
        for key, entry in self._materials.items():
            if q in entry["name"].lower() or q in entry.get("full_name", "").lower():
                results.append(self.get(key))
        return results

    def categories(self) -> list:
        """Return list of unique material categories."""
        cats = set(e.get("category", "other") for e in self._materials.values())
        return sorted(cats)

    def by_category(self, category: str) -> list:
        """
        Return all materials in a given category.

        Parameters
        ----------
        category : str — e.g. 'dielectric', 'metal', 'substrate', 'semiconductor'
        """
        return [
            self.get(key)
            for key, entry in self._materials.items()
            if entry.get("category") == category
        ]

    def info(self, name: str) -> None:
        """Print detailed info for a material including references."""
        sources = [self._materials, self._gazi]
        for src in sources:
            if name in src:
                e = src[name]
                print(f"\n{'─'*60}")
                print(f"  {e['name']} — {e.get('full_name', '')}")
                print(f"{'─'*60}")
                print(f"  n (@ {e.get('wavelength_ref','?')} nm) : {e['n']}")
                print(f"  k (@ {e.get('wavelength_ref','?')} nm) : {e.get('k', 0.0)}")
                print(f"  Category  : {e.get('category', '—')}")
                if e.get("notes"):
                    print(f"  Notes     : {e['notes']}")
                if e.get("references"):
                    print(f"  References:")
                    for ref in e["references"]:
                        print(f"    • {ref}")
                print(f"{'─'*60}\n")
                return
        print(f"Material '{name}' not found.")

    def __len__(self) -> int:
        return len(self._materials) + len(self._gazi)

    def __repr__(self) -> str:
        return (
            f"MaterialDatabase("
            f"{len(self._materials)} literature, "
            f"{len(self._gazi)} Gazi Photonics samples)"
        )
