"""
Network Construction Module

CORRECTED IMPLEMENTATION: Uses global co-investment graph approach.

For each focal VC i in year t:
1. Build GLOBAL co-investment graph for window [t-3, t-1]
   - Nodes: ALL investors active in window
   - Edges: connect two investors if they co-invested in ANY deal
2. Get focal VC's neighbors (partners) = nodes connected to VC i
3. Extract INDUCED SUBGRAPH on partners (excluding focal VC)
4. Compute density on this induced subgraph

This correctly captures partner-to-partner ties formed OUTSIDE
the focal VC's deals.
"""

import networkx as nx
import pandas as pd
import numpy as np
from itertools import combinations
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def build_global_coinvestment_graph(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    year: int,
    window: int = 3
) -> nx.Graph:
    """
    Build GLOBAL co-investment graph for all deals in [year-window, year-1].

    Parameters
    ----------
    deal_investors : DataFrame
        Junction table with deal_id, investor_id
    deals : DataFrame
        Deals table with deal_id, deal_year
    year : int
        Focal year t (network computed from t-window to t-1)
    window : int
        Lookback window in years (default 3)

    Returns
    -------
    nx.Graph
        Undirected graph where nodes are investors and edges indicate
        co-investment in at least one deal during the window.
        Edge weight = number of shared deals.
    """
    # Get deals in window [year-window, year-1]
    window_start = year - window
    window_end = year - 1

    window_deal_ids = deals[
        (deals['deal_year'] >= window_start) &
        (deals['deal_year'] <= window_end)
    ]['deal_id'].unique()

    if len(window_deal_ids) == 0:
        return nx.Graph()

    # Filter deal_investors to window
    di_window = deal_investors[deal_investors['deal_id'].isin(window_deal_ids)]

    # Build graph
    G = nx.Graph()

    # Add all investors as nodes
    all_investors = di_window['investor_id'].unique()
    G.add_nodes_from(all_investors)

    # For each deal, create edges between ALL co-investors
    for deal_id in window_deal_ids:
        participants = di_window[
            di_window['deal_id'] == deal_id
        ]['investor_id'].tolist()

        # Create edges between all pairs
        for inv1, inv2 in combinations(participants, 2):
            if G.has_edge(inv1, inv2):
                G[inv1][inv2]['weight'] += 1
            else:
                G.add_edge(inv1, inv2, weight=1)

    return G


def compute_ego_density(G_global: nx.Graph, focal_vc: str) -> Dict[str, float]:
    """
    Compute ego-network measures for focal VC.

    Density is computed on the INDUCED SUBGRAPH of the focal VC's
    neighbors (excluding the focal VC itself).

    Parameters
    ----------
    G_global : nx.Graph
        Global co-investment graph for the window
    focal_vc : str
        Investor ID of focal VC

    Returns
    -------
    dict with keys:
        - ego_size: number of unique partners (k)
        - ego_density: density of induced subgraph on partners
        - ego_edges: number of edges among partners
        - avg_clustering: average clustering coefficient of partners
        - n_components: number of connected components in ego network
    """
    if focal_vc not in G_global:
        return {
            'ego_size': 0,
            'ego_density': np.nan,
            'ego_edges': 0,
            'avg_clustering': np.nan,
            'n_components': 0,
            'in_giant_component': np.nan
        }

    # Get partners (neighbors of focal VC)
    partners = list(G_global.neighbors(focal_vc))
    k = len(partners)

    if k < 2:
        return {
            'ego_size': k,
            'ego_density': np.nan,  # Undefined for k < 2
            'ego_edges': 0,
            'avg_clustering': np.nan,
            'n_components': 1 if k == 1 else 0,
            'in_giant_component': np.nan
        }

    # Extract induced subgraph on partners (excluding focal VC)
    ego = G_global.subgraph(partners).copy()

    # Compute density
    density = nx.density(ego)
    n_edges = ego.number_of_edges()

    # Clustering
    avg_clustering = nx.average_clustering(ego)

    # Components
    components = list(nx.connected_components(ego))
    n_components = len(components)
    largest = max(len(c) for c in components) if components else 0
    in_giant = largest / k if k > 0 else np.nan

    return {
        'ego_size': k,
        'ego_density': density,
        'ego_edges': n_edges,
        'avg_clustering': avg_clustering,
        'n_components': n_components,
        'in_giant_component': in_giant
    }


def compute_weighted_density(G_global: nx.Graph, focal_vc: str) -> float:
    """
    Compute weighted density where edge weight = number of shared deals.

    Weighted density = sum(weights) / max_possible_edges
    """
    if focal_vc not in G_global:
        return np.nan

    partners = list(G_global.neighbors(focal_vc))
    k = len(partners)

    if k < 2:
        return np.nan

    ego = G_global.subgraph(partners)

    total_weight = sum(d.get('weight', 1) for _, _, d in ego.edges(data=True))
    max_edges = k * (k - 1) / 2

    return total_weight / max_edges if max_edges > 0 else np.nan


def get_partner_list(
    G_global: nx.Graph,
    focal_vc: str
) -> List[str]:
    """Get list of partner investor IDs for focal VC."""
    if focal_vc not in G_global:
        return []
    return list(G_global.neighbors(focal_vc))


def compute_network_measures_for_year(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    year: int,
    window: int = 3,
    min_ego_size: int = 2
) -> pd.DataFrame:
    """
    Compute network measures for all VCs active in the window.

    Parameters
    ----------
    deal_investors : DataFrame
    deals : DataFrame
    year : int
        Focal year t
    window : int
        Lookback window
    min_ego_size : int
        Minimum partners required (VCs with fewer are excluded)

    Returns
    -------
    DataFrame with one row per VC, columns for network measures
    """
    logger.info(f"Computing network measures for year {year} (window {year-window}-{year-1})")

    # Build global graph for this year's window
    G = build_global_coinvestment_graph(deal_investors, deals, year, window)

    logger.info(f"  Global graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Get all VCs (nodes in the graph)
    all_vcs = list(G.nodes())

    records = []
    for vc_id in all_vcs:
        measures = compute_ego_density(G, vc_id)

        # Skip if below minimum ego size
        if measures['ego_size'] < min_ego_size:
            continue

        # Add weighted density
        measures['ego_density_weighted'] = compute_weighted_density(G, vc_id)

        # Add identifiers
        measures['investor_id'] = vc_id
        measures['year'] = year

        records.append(measures)

    result = pd.DataFrame(records)
    logger.info(f"  VCs with ego_size >= {min_ego_size}: {len(result)}")

    return result


def build_network_panel(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    years: List[int],
    window: int = 3,
    min_ego_size: int = 2
) -> Tuple[pd.DataFrame, Dict[int, nx.Graph]]:
    """
    Build network measures panel for multiple years.

    Parameters
    ----------
    deal_investors : DataFrame
    deals : DataFrame
    years : list of int
        Years to compute measures for
    window : int
        Lookback window
    min_ego_size : int
        Minimum partners required

    Returns
    -------
    panel : DataFrame
        VC-year panel with network measures
    graphs : dict
        Year -> global graph mapping (for debugging/visualization)
    """
    logger.info(f"Building network panel for years {years}")

    panels = []
    graphs = {}

    for year in years:
        # Build and store graph
        G = build_global_coinvestment_graph(deal_investors, deals, year, window)
        graphs[year] = G

        # Compute measures
        year_panel = compute_network_measures_for_year(
            deal_investors, deals, year, window, min_ego_size
        )

        if len(year_panel) > 0:
            panels.append(year_panel)

    if panels:
        panel = pd.concat(panels, ignore_index=True)
    else:
        panel = pd.DataFrame()

    logger.info(f"Network panel: {len(panel)} VC-year observations")

    return panel, graphs
