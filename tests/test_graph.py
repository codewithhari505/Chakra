"""
Unit tests for Phase 9: NetworkX Transaction Graph & Pattern Detection.
"""

from pathlib import Path
import sys
import networkx as nx
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.graph.graph_builder import TransactionGraphBuilder
from ml.graph.pattern_detection import AMLGraphPatternDetector
from ml.graph.graph_analysis import GraphMetricsAnalyzer


@pytest.fixture
def circular_transaction_data():
    """Generates explicit circular transfer loop: A -> B -> C -> A."""
    return pd.DataFrame({
        "transaction_id": ["TX1", "TX2", "TX3"],
        "sender_account": ["ACC_A", "ACC_B", "ACC_C"],
        "receiver_account": ["ACC_B", "ACC_C", "ACC_A"],
        "amount": [50000.0, 49500.0, 49000.0],
        "timestamp": ["2025-01-01 10:00:00", "2025-01-01 10:30:00", "2025-01-01 11:00:00"],
        "is_suspicious": [True, True, True]
    })


@pytest.fixture
def layering_chain_data():
    """Generates sequential layering chain: A -> B -> C -> D -> E."""
    return pd.DataFrame({
        "transaction_id": ["TX10", "TX11", "TX12", "TX13"],
        "sender_account": ["ACC_A", "ACC_B", "ACC_C", "ACC_D"],
        "receiver_account": ["ACC_B", "ACC_C", "ACC_D", "ACC_E"],
        "amount": [100000.0, 99000.0, 98000.0, 97000.0],
        "timestamp": ["2025-02-01 08:00:00", "2025-02-01 08:20:00", "2025-02-01 08:40:00", "2025-02-01 09:00:00"],
        "is_suspicious": [True, True, True, True]
    })


def test_graph_builder_nodes_and_edges(circular_transaction_data):
    builder = TransactionGraphBuilder()
    g = builder.build_graph(circular_transaction_data)

    assert g.number_of_nodes() == 3
    assert g.number_of_edges() == 3
    assert g.has_node("ACC_A")
    assert g.has_edge("ACC_A", "ACC_B")
    assert builder.simple_graph.has_edge("ACC_C", "ACC_A")


def test_cycle_detection(circular_transaction_data):
    builder = TransactionGraphBuilder()
    builder.build_graph(circular_transaction_data)

    detector = AMLGraphPatternDetector(min_cycle_length=3, max_cycle_length=4)
    cycles = detector.find_cycles(builder.simple_graph)

    assert len(cycles) >= 1
    c = cycles[0]
    assert c.cycle_length == 3
    assert set(c.cycle_nodes) == {"ACC_A", "ACC_B", "ACC_C"}
    assert c.total_amount >= 140000.0


def test_layering_detection(layering_chain_data):
    builder = TransactionGraphBuilder()
    builder.build_graph(layering_chain_data)

    detector = AMLGraphPatternDetector(min_layering_hops=3, max_layering_hops=5)
    chains = detector.find_layering_chains(builder.simple_graph)

    assert len(chains) >= 1
    ch = chains[0]
    assert ch.hops >= 3
    assert ch.chain_nodes[0] == "ACC_A"
    assert ch.chain_nodes[-1] == "ACC_E"
    assert ch.retained_slippage_pct <= 10.0


def test_graph_metrics_calculation(circular_transaction_data):
    builder = TransactionGraphBuilder()
    builder.build_graph(circular_transaction_data)

    analyzer = GraphMetricsAnalyzer()
    df_metrics = analyzer.compute_account_metrics(builder.simple_graph)

    assert len(df_metrics) == 3
    assert "pagerank" in df_metrics.columns
    assert "degree" in df_metrics.columns
    assert "betweenness_centrality" in df_metrics.columns
    assert (df_metrics["degree"] == 2).all()  # In cycle, in=1, out=1 => total=2
