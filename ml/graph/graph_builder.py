"""
Graph Builder — NetworkX Transaction Graph — Phase 9.

Builds directed multi-graphs (nx.MultiDiGraph / nx.DiGraph) representing
financial networks where:
  - Nodes: Bank Accounts (with balance, risk flags, registration date attributes)
  - Directed Edges: Transactions (with transaction_id, amount, timestamp, channel, type)
"""

import logging
from typing import Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger("GraphBuilder")


class TransactionGraphBuilder:
    """
    Constructs and indexes NetworkX graphs from transaction and account DataFrames.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.simple_graph = nx.DiGraph()
        self.is_built: bool = False

    def build_graph(
        self,
        transactions_df: pd.DataFrame,
        accounts_df: Optional[pd.DataFrame] = None
    ) -> nx.MultiDiGraph:
        """
        Constructs a directed graph from transaction rows.
        Attaches edge attributes (amount, timestamp, transaction_id) and node metadata.
        """
        logger.info("Building NetworkX transaction graph from %d transactions...", len(transactions_df))
        self.graph = nx.MultiDiGraph()
        self.simple_graph = nx.DiGraph()

        # 1. Add account nodes with profile metadata if available
        if accounts_df is not None and not accounts_df.empty:
            for _, acc in accounts_df.iterrows():
                acc_id = str(acc["account_id"])
                self.graph.add_node(
                    acc_id,
                    account_type=acc.get("account_type", "INDIVIDUAL"),
                    country=acc.get("country", "India"),
                    city=acc.get("city", "UNKNOWN"),
                    is_flagged=bool(acc.get("is_flagged", False)),
                )

        # 2. Add transaction edges
        for _, txn in transactions_df.iterrows():
            snd = str(txn["sender_account"])
            rcv = str(txn["receiver_account"])

            # Ensure nodes exist
            if not self.graph.has_node(snd):
                self.graph.add_node(snd, account_type="UNKNOWN", is_flagged=False)
            if not self.graph.has_node(rcv):
                self.graph.add_node(rcv, account_type="UNKNOWN", is_flagged=False)

            edge_data = {
                "transaction_id": str(txn["transaction_id"]),
                "amount": float(txn["amount"]),
                "timestamp": str(txn["timestamp"]),
                "transaction_type": str(txn.get("transaction_type", "TRANSFER")),
                "channel": str(txn.get("channel", "ONLINE")),
                "is_suspicious": bool(txn.get("is_suspicious", False)),
            }

            # Add to MultiDiGraph (captures multiple transfers between same accounts)
            self.graph.add_edge(snd, rcv, key=str(txn["transaction_id"]), **edge_data)

            # Also maintain simple aggregated DiGraph for cycle & flow algorithms
            if self.simple_graph.has_edge(snd, rcv):
                self.simple_graph[snd][rcv]["weight"] += float(txn["amount"])
                self.simple_graph[snd][rcv]["tx_count"] += 1
            else:
                self.simple_graph.add_edge(
                    snd,
                    rcv,
                    weight=float(txn["amount"]),
                    tx_count=1,
                    first_timestamp=str(txn["timestamp"]),
                    last_timestamp=str(txn["timestamp"]),
                )

        self.is_built = True
        logger.info(
            "Graph construction complete: %d nodes (accounts), %d edges (transactions).",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
        )
        return self.graph

    def get_subgraph(self, account_id: str, radius: int = 2) -> nx.MultiDiGraph:
        """
        Extracts a localized ego-subgraph centered around a suspect account within N hops.
        Crucial for low-latency visual network inspection without traversing the full graph.
        """
        if not self.is_built:
            raise RuntimeError("Graph must be built before calling get_subgraph().")

        if not self.graph.has_node(account_id):
            return nx.MultiDiGraph()

        # Convert to undirected temporarily to find all connected neighbors within radius
        undir = self.graph.to_undirected(as_view=True)
        sub_nodes = nx.single_source_shortest_path_length(undir, account_id, cutoff=radius).keys()
        return self.graph.subgraph(sub_nodes).copy()
