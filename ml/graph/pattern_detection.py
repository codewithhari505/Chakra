"""
Graph Pattern Detection — Phase 9.

Detects complex structural AML typologies in transaction graphs:
  1. Circular Fund Transfers / Cycles (A -> B -> C -> A)
  2. Multi-hop Layering Chains (A -> B -> C -> D -> E)
  3. Fan-out Dispersion Hubs (One-to-Many rapid outflows)
  4. Fan-in Aggregation Funnels (Many-to-One pooling)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger("GraphPatternDetection")


@dataclass
class DetectedCycle:
    cycle_nodes: List[str]
    cycle_length: int
    total_amount: float
    transactions: List[str]
    time_span_hours: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_nodes": self.cycle_nodes,
            "cycle_length": self.cycle_length,
            "total_amount": round(self.total_amount, 2),
            "transactions": self.transactions,
            "time_span_hours": round(self.time_span_hours, 2) if self.time_span_hours else None,
        }


@dataclass
class DetectedLayeringChain:
    chain_nodes: List[str]
    hops: int
    initial_amount: float
    final_amount: float
    retained_slippage_pct: float
    transactions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_nodes": self.chain_nodes,
            "hops": self.hops,
            "initial_amount": round(self.initial_amount, 2),
            "final_amount": round(self.final_amount, 2),
            "retained_slippage_pct": round(self.retained_slippage_pct, 2),
            "transactions": self.transactions,
        }


class AMLGraphPatternDetector:
    """
    Scans NetworkX transaction graphs for circular and layered topological patterns.
    """

    def __init__(
        self,
        max_cycle_length: int = 5,
        min_cycle_length: int = 3,
        min_layering_hops: int = 3,
        max_layering_hops: int = 6,
    ):
        self.max_cycle_length = max_cycle_length
        self.min_cycle_length = min_cycle_length
        self.min_layering_hops = min_layering_hops
        self.max_layering_hops = max_layering_hops

    def find_cycles(
        self,
        simple_graph: nx.DiGraph,
        max_cycles: int = 200
    ) -> List[DetectedCycle]:
        """
        Detects directed cycles using simple cycles algorithm within bounded length.
        """
        logger.info("Scanning graph for directed cycles (length %d to %d)...", self.min_cycle_length, self.max_cycle_length)
        detected: List[DetectedCycle] = []

        try:
            cycles_gen = nx.simple_cycles(simple_graph)
            for cycle in cycles_gen:
                c_len = len(cycle)
                if self.min_cycle_length <= c_len <= self.max_cycle_length:
                    cycle_nodes = list(cycle) + [cycle[0]]
                    total_amt = 0.0
                    for u, v in zip(cycle_nodes[:-1], cycle_nodes[1:]):
                        if simple_graph.has_edge(u, v):
                            total_amt += simple_graph[u][v].get("weight", 0.0)

                    detected.append(DetectedCycle(
                        cycle_nodes=cycle,
                        cycle_length=c_len,
                        total_amount=total_amt,
                        transactions=[]
                    ))
                    if len(detected) >= max_cycles:
                        break
        except Exception as e:
            logger.warning("Error during cycle search: %s", e)

        logger.info("Detected %d suspicious transaction cycles.", len(detected))
        return detected

    def find_layering_chains(
        self,
        simple_graph: nx.DiGraph,
        max_chains: int = 200,
        amount_tolerance_ratio: float = 0.25,
    ) -> List[DetectedLayeringChain]:
        """
        Detects directed path chains (A -> B -> C -> D -> E) where funds flow
        sequentially with small fee deductions (< 25% total drop across chain).
        Prioritizes maximal length paths to capture the entire layering journey.
        """
        logger.info("Scanning for sequential layering chains...")
        chains: List[DetectedLayeringChain] = []

        # Target nodes that serve as intermediary conduits
        conduits = [n for n in simple_graph.nodes() if simple_graph.in_degree(n) >= 1 and simple_graph.out_degree(n) >= 1]

        visited_starts: Set[str] = set()
        for conduit in conduits[:500]:
            preds = list(simple_graph.predecessors(conduit))
            if not preds:
                continue
            start_node = preds[0]
            if start_node in visited_starts:
                continue
            visited_starts.add(start_node)

            try:
                paths = nx.single_source_shortest_path(simple_graph, start_node, cutoff=self.max_layering_hops)
                # Sort candidate paths by descending length so maximal chains are evaluated first
                sorted_paths = sorted(paths.values(), key=len, reverse=True)

                for path in sorted_paths:
                    hops = len(path) - 1
                    if hops >= self.min_layering_hops:
                        edge_weights = []
                        valid_flow = True
                        for u, v in zip(path[:-1], path[1:]):
                            if simple_graph.has_edge(u, v):
                                edge_weights.append(simple_graph[u][v].get("weight", 0.0))
                            else:
                                valid_flow = False
                                break

                        if valid_flow and edge_weights:
                            init_amt = edge_weights[0]
                            fin_amt = edge_weights[-1]
                            if init_amt > 0:
                                slippage = (init_amt - fin_amt) / init_amt
                                if 0.0 <= slippage <= amount_tolerance_ratio:
                                    chains.append(DetectedLayeringChain(
                                        chain_nodes=path,
                                        hops=hops,
                                        initial_amount=init_amt,
                                        final_amount=fin_amt,
                                        retained_slippage_pct=slippage * 100.0,
                                        transactions=[]
                                    ))
                                    # Found longest valid chain for this root
                                    break

                    if len(chains) >= max_chains:
                        return chains
            except Exception:
                continue

        logger.info("Detected %d layering chains.", len(chains))
        return chains

    def find_fan_out_hubs(
        self,
        simple_graph: nx.DiGraph,
        min_out_degree: int = 4,
        max_in_degree: int = 2
    ) -> List[Dict[str, Any]]:
        """Identifies rapid dispersion hub accounts (high out-degree, low in-degree)."""
        hubs = []
        for node in simple_graph.nodes():
            out_d = simple_graph.out_degree(node)
            in_d = simple_graph.in_degree(node)
            if out_d >= min_out_degree and in_d <= max_in_degree:
                total_dispersion = sum(simple_graph[node][tgt].get("weight", 0.0) for tgt in simple_graph.successors(node))
                hubs.append({
                    "account_id": node,
                    "fan_out_degree": out_d,
                    "fan_in_degree": in_d,
                    "total_dispersion_amount": round(total_dispersion, 2),
                })
        return sorted(hubs, key=lambda x: x["fan_out_degree"], reverse=True)
