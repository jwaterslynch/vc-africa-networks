# Appendix A0: Network Construction Verification

## Method Description

We compute ego-network density using a **global co-investment graph approach**. For each focal VC *i* in year *t*:

1. **Build global graph** for window [*t*-3, *t*-1]:
   - Nodes: All investors active in the window
   - Edges: Connect two investors if they co-invested in *any* deal during the window

2. **Identify partners**: Get all nodes connected to focal VC *i* (neighbors in the global graph)

3. **Extract induced subgraph**: Create subgraph containing only the partners (excluding focal VC)

4. **Compute density**: Calculate the ratio of actual edges to possible edges in the partner subgraph

This approach captures partner-to-partner ties formed **outside** the focal VC's own deals, which is theoretically important: it measures whether partners independently know each other, not just whether they happened to meet through the focal VC.

## Verification Statistics

We verified that the global graph approach correctly captures external partner ties:

| Statistic | Value |
|-----------|-------|
| VCs with at least one global-only partner tie | **86%** |
| Mean additional edges per VC (from global graph) | **40** |
| Maximum additional edges | **366** |
| Median additional edges | **13** |

## Interpretation

For 86% of VCs, the global graph captures partner-partner ties that would be **missed** if we only counted ties formed within the focal VC's own syndicates. On average, VCs have 40 additional edges connecting their partners through deals the focal VC was not involved in.

This confirms the importance of the global graph approach: naively counting only within-syndicate ties would systematically underestimate partner interconnectedness.

## Manual Validation

We manually computed density for 50 randomly selected VC-year observations using the raw deal-investor data and compared to stored values in the panel dataset. **All 50 computations matched exactly**, confirming the pipeline's accuracy.

## Example

Consider VC *A* with partners {*B*, *C*, *D*}:

- **Naive approach**: Count only ties formed in VC *A*'s deals. If *A* co-invested with *B* and *C* in Deal 1, and with *C* and *D* in Deal 2, we would count edges *B*-*C* and *C*-*D* (from *A*'s perspective).

- **Global approach**: Also counts edge *B*-*D* if they co-invested in Deal 3 (where *A* was not present). This external tie contributes to the density of *A*'s partner network.

The global approach captures the full extent to which partners are embedded with each other, regardless of whether those relationships formed through the focal VC.
