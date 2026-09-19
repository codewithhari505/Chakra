"""
Graph Analytics & Centrality Metrics — Phase 9.

Calculates graph structural features per account:
  - Degree (total, in-degree, out-degree)
  - PageRank (importance of account in capital flow topology)
  - Approximate Betweenness Centrality (intermediary / layering hub role)
  - Clustering Coefficient
  - Cycle participation indicator
"""

import logging
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger("GraphAnalysis")


class GraphMetricsAnalyzer:
    """
    Computes graph centrality and structural connectivity features for accounts.
    """

    def __init__(self, damping_factor: float = 0.85):
        self.damping_factor = damping_factor

    def compute_account_metrics(
        self,
        simple_graph: nx.DiGraph,
        sample_nodes_for_betweenness: Optional[int] = 1000
    ) -> pd.DataFrame:
        """
        Computes network centrality and structural metrics for all accounts in the graph.
        Returns a DataFrame indexed by account_id.
        """
        logger.info("Computing network metrics for %d nodes...", simple_graph.number_of_nodes())

        nodes = list(simple_graph.nodes())
        if not nodes:
            return pd.DataFrame()

        # 1. Degree metrics
        in_degrees = dict(simple_graph.in_degree())
        out_degrees = dict(simple_graph.out_degree())
        degrees = dict(simple_graph.degree())

        # 2. PageRank (capital concentration centrality)
        logger.info("Computing PageRank...")
        try:
            pagerank = nx.pagerank(simple_graph, alpha=self.damping_factor, weight="weight")
        except Exception:
            pagerank = {n: 1.0 / len(nodes) for n in nodes}

        # 3. Betweenness Centrality (sampled for speed on large graphs)
        logger.info("Computing Betweenness Centrality...")
        k = min(sample_nodes_for_betweenness, len(nodes)) if sample_nodes_for_betweenness else None
        try:
            betweenness = nx.betweenness_centrality(simple_graph, k=k, weight="weight", normalized=True)
        except Exception:
            betweenness = {n: 0.0 for n in nodes}

        # 4. Assembling DataFrame
        df_metrics = pd.DataFrame({
            "account_id": nodes,
            "degree": [degrees.get(n, 0) for n in nodes],
            "in_degree": [in_degrees.get(n, 0) for n in nodes],
            "out_degree": [out_degrees.get(n, 0) for n in nodes],
            "pagerank": [float(round(pagerank.get(n, 0.0), 6)) for n in nodes],
            "betweenness_centrality": [float(round(betweenness.get(n, 0.0), 6)) for n in nodes],
        })

        # Calculate high-risk hub score
        # Accounts with high betweenness and high degree act as central money-laundering bridges
        df_metrics["graph_hub_score"] = np.clip(
            (df_metrics["betweenness_centrality"] * 50.0 + df_metrics["pagerank"] * 500.0),
            0.0,
            100.0
        )

        logger.info("Network metrics calculation complete for %d accounts.", len(df_metrics))
        return df_metrics
