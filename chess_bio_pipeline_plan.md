### Chess Bioinformatics Pipeline Implementation Plan - Canvas

#### 1. Data Ingestion
* **Source:** Lichess API or local PGN files.
* **Task:** Fetch PGN data from a player, tournament, or opening line.
* **Implementation:**
  * Use Python `requests` or `berserk` API for Lichess.
  * Save PGN locally with standardized filename.
  * Optionally store raw PGNs in a Raspberry Pi Zero 2 W for offline processing.
  * **Real-time Integration:**
    * Poll Lichess API periodically for new games.
    * Example API URL: `https://lichess.org/api/games/user/EisWolf_LH?tags=true&clocks=false&evals=true&opening=true&literate=true&perfType=ultraBullet%2Cbullet%2Cblitz%2Crapid%2Cclassical%2Ccorrespondence%2Cstandard`

#### 2. PGN → FASTA Conversion
* **Goal:** Convert PGN games to bioinformatics-like FASTA format.
* **Actions:**
  * Use `FASTAFENfromPGN.py` script.
  * Extract: board positions (expanded FEN), eval, ply, side, game ID.
  * Store as FASTA for downstream pipeline.
  * **Automation:**
    * Automatically trigger conversion when new PGNs are fetched from API.

#### 3. Position Graph / DAG Construction
* **Goal:** Build a directed acyclic graph (DAG) representing all positions.
* **Actions:**
  * Use `GameTree.py` `build_position_graph` function.
  * Merge identical positions across games.
  * Store node metadata: eval, visits, depth.
  * Handle forced mates (eval >= 10000) by branch termination.
  * **Incremental Updates:**
    * Update existing DAG with new positions without rebuilding from scratch.

#### 4. Database Integration
* **Goal:** Persist all processed data for efficient storage, queries, and incremental updates.
* **Recommended DB:** SQLite for initial deployment (lightweight, file-based, Pi-compatible). Future migration to Neo4j or PostgreSQL if graph queries or multi-user access become important.
* **Schema Design:**
  * `positions` table: `node_id` (PK), `fen` (expanded), `eval`, `visits`, `depth`.
  * `games` table: `game_id` (PK), `result`, `player`, `timestamp`.
  * `edges` table: `parent_id`, `child_id` (relationships between positions).
  * `motifs` table: `motif_seq`, `frequency`, `game_refs`.
* **Integration:**
  * DAG builder inserts/updates nodes and edges.
  * Motif analyzer updates motifs table.
  * Queries allow fast retrieval of positions, evaluation stats, and motif occurrences.

#### 5. Visualization - Graphviz & Evaluation Landscape
* **Goal:** Visualize evolution of positions and evaluations.
* **Actions:**
  * Export DOT file via `export_graphviz`.
  * Color nodes based on evaluation.
  * Scale node size by visit count.
  * Optional: generate ply vs eval plots using `matplotlib` or `seaborn`.
  * **Raspberry Pi Use:**
    * Lightweight visualizations and previews can be rendered on Pi Zero 2 W for remote monitoring.

#### 6. Motif Detection in Board States
* **Goal:** Identify recurring tactical or positional patterns.
* **Actions:**
  * Represent each board as 64-character sequence.
  * Use sliding windows (k-mers) to detect frequent motifs.
  * Count frequency across all games.
  * Store motifs in DB table and/or CSV.

#### 7. Modular Pipeline Structure
* **Modules:**
  1. Parser (FASTA reader, metadata extraction)
  2. Graph Builder (DAG construction, node merging, incremental updates)
  3. Database Interface (CRUD for positions, edges, motifs, games)
  4. Exporter (Graphviz DOT, optional Newick)
  5. Visualizer (evaluation landscape, plots)
  6. Motif Analyzer (recurring patterns)
  7. Real-time Fetcher (Lichess API stream integration)

#### 8. Dataflow Diagram (Sketch)
```
[ Lichess API (EisWolf_LH) ]
            |
            v
      [ PGN Fetcher / Stream ]
            |
            v
     [ PGN → FASTA Converter ]
            |
            v
  +---------------------------+
  |   Database (SQLite)       |
  |---------------------------|
  | positions | games | edges |
  | motifs                    |
  +---------------------------+
   |             |           |
   v             v           v
[ DAG Builder ] [ Motif Analyzer ] [ Queries / Analytics ]
   |             |           |
   +-------------+-----------+
                 |
                 v
           [ Visualizer (DOT, plots) ]
                 |
                 v
          [ Raspberry Pi / Web Dashboard ]
```
* **Description:**
  * PGNs are fetched from the Lichess API.
  * FASTA converter processes and expands boards.
  * Data is inserted into the database.
  * DAG builder and motif analyzer read from DB.
  * Visualization module generates DOT/plots.
  * Raspberry Pi hosts dashboard or previews for monitoring.

#### 9. Performance & Storage Considerations
* Use integer IDs and hashed FENs for node keys.
* Limit max ply depth or min visits to reduce graph size.
* Cache intermediate results using `pickle` or `HDF5`.
* Raspberry Pi Zero 2 W can handle smaller datasets locally for testing and live monitoring.
* Database allows efficient incremental updates and queries without full graph rebuild.

#### 10. Future Extensions
* Dynamic coloring by evaluation changes along paths.
* Cluster similar positions based on piece distribution.
* Compare opening repertoires across players.
* Machine learning for predictive opening evaluation.
* Real-time streaming from Lichess API to update DAG dynamically.
* Optional web dashboard on Raspberry Pi for live visualization of games and motif trends.

