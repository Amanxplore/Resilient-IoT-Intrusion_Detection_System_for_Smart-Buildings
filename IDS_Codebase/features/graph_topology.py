from __future__ import annotations

from typing import Dict, List, Set, Tuple

class BuildingGraphTopology:
    """
    Graph Neural Network (GNN) Building Topology Simulator.
    Models HVAC duct connections and adjacent room spatial graph adjacency matrix
    to trace cascade attack propagation across smart building zones.
    """
    def __init__(self) -> None:
        self.adjacency: Dict[str, Set[str]] = {}

    def add_zone_connection(self, zone_a: str, zone_b: str) -> None:
        if zone_a not in self.adjacency:
            self.adjacency[zone_a] = set()
        if zone_b not in self.adjacency:
            self.adjacency[zone_b] = set()
        self.adjacency[zone_a].add(zone_b)
        self.adjacency[zone_b].add(zone_a)

    def trace_attack_propagation(self, compromised_zone: str, max_depth: int = 2) -> List[str]:
        if compromised_zone not in self.adjacency:
            return [compromised_zone]

        visited: Set[str] = {compromised_zone}
        queue: List[Tuple[str, int]] = [(compromised_zone, 0)]
        at_risk: List[str] = []

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for neighbor in self.adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    at_risk.append(neighbor)
                    queue.append((neighbor, depth + 1))

        return at_risk
