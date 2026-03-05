#!/usr/bin/env python3
import re

# regex patterns
game_pattern = re.compile(r"game=([^ ]+)")
eval_pattern = re.compile(r"eval=([-0-9]+)")
ply_pattern = re.compile(r"ply=([0-9]+)")

# standard chess starting position (expanded FEN)
START_POSITION = "rnbqkbnr/pppppppp/--------/--------/--------/--------/PPPPPPPP/RNBQKBNR"


def parse_fasta_positions(path):
    """Yield (header, board sequence) from FASTA-like file."""
    header = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                header = line
            else:
                yield header, line.split(" ")[0]


def parse_metadata(header):
    """Extract game, ply, and evaluation from FASTA header."""
    game = game_pattern.search(header).group(1)
    ply = int(ply_pattern.search(header).group(1))
    eval = int(eval_pattern.search(header).group(1))
    # print(eval)
    return game, ply, eval


def build_position_graph(fasta_file, max_depth=None):
    """
    Build DAG of positions.
    - Identical boards merge into one node.
    - Evaluation comes directly from FASTA.
    """
    nodes = {}
    prev_position = None
    prev_game = None

    for header, pos in parse_fasta_positions(fasta_file):
        game, ply, eval_score = parse_metadata(header)

        if max_depth and ply > max_depth:
            continue

        # reset at new game
        if game != prev_game:
            prev_position = START_POSITION

        # create or update node
        if pos not in nodes:
            nodes[pos] = {
                "children": set(),
                "visits": 0,
                "eval": eval_score
            }
        else:
            # always assign evaluation from FASTA
            if nodes[pos]["eval"] != eval_score:
                print(f"Warning: conflicting eval for position {pos}")
            nodes[pos]["eval"] = eval_score

        nodes[pos]["visits"] += 1

        # link parent -> child
        if prev_position:
            if prev_position not in nodes:
                nodes[prev_position] = {
                    "children": set(),
                    "visits": 0,
                    "eval": None  # unknown until we see it directly
                }
            nodes[prev_position]["children"].add(pos)

        # stop branch if forced mate
        if abs(eval_score) >= 10000:
            prev_position = None
        else:
            prev_position = pos

        prev_game = game

    return nodes


def evaluation_to_color(eval_score):
    """Map evaluation to color: green=white winning, red=black winning, yellow=balanced."""
    if eval_score is None:
        return "#dddddd"
    if eval_score > 200:
        return "#88ff88"  # green
    elif eval_score < -200:
        return "#ff8888"  # red
    else:
        return "#fff2a8"  # yellow


def export_graphviz(nodes, output_file="chess_tree.dot", min_visits=1):
    """Export DAG to Graphviz DOT file."""
    with open(output_file, "w") as f:
        f.write("digraph chess_tree {\n")
        f.write("rankdir=LR;\n")
        f.write("node [shape=box fontname=Courier style=filled];\n")

        # write nodes
        for pos, data in nodes.items():
            visits = data["visits"]
            if visits < min_visits:
                continue
            eval_score = data["eval"]
            color = evaluation_to_color(eval_score)
            size = 0.5 + (visits ** 0.4)
            label = f"{pos}\\nvisits={visits}\\neval={eval_score}"
            f.write(
                f"\"{pos}\" "
                f"[label=\"{label}\" fillcolor=\"{color}\" "
                f"width={size} height={size}];\n"
            )

        # write edges
        for parent, data in nodes.items():
            if data["visits"] < min_visits:
                continue
            for child in data["children"]:
                if child not in nodes:
                    continue
                if nodes[child]["visits"] < min_visits:
                    continue
                f.write(f"\"{parent}\" -> \"{child}\";\n")

        f.write("}\n")


def main():
    fasta_file = "lichess_EisWolf_LH_2026-03-05.fasta"
    output_file = "lichess_EisWolf_LH_2026-03-05.dot"

    MAX_DEPTH = 50
    MIN_VISITS = 1

    print("Building position graph...")
    nodes = build_position_graph(fasta_file, max_depth=MAX_DEPTH)

    print("Unique positions:", len(nodes))
    nonzero_eval = sum(1 for n in nodes.values() if n["eval"] not in (0, None))
    print("Positions with non-zero eval:", nonzero_eval)

    print("Exporting Graphviz DOT file...")
    export_graphviz(nodes, output_file, min_visits=MIN_VISITS)

    print("Done.")
    print("Render with:")
    print("dot -Tpng chess_tree.dot -o chess_tree.png")


if __name__ == "__main__":
    main()
