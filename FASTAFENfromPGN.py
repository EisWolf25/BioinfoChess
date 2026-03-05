import re
import chess
import chess.pgn

# regex to capture [%eval ...]
eval_pattern = re.compile(r"\[%eval\s+([^\]]+)\]")


def extract_eval(comment):
    """Extract evaluation from PGN comment."""
    m = eval_pattern.search(comment)
    if not m:
        return None

    val = m.group(1)

    # convert mate scores
    if val.startswith("#"):
        if "-" in val:
            return -10000
        return 10000

    return float(val)


def expand_fen_board(fen):
    """
    Convert compressed FEN board like:
    5p2 -> -----p--
    """
    board, rest = fen.split(" ", 1)

    expanded_rows = []

    for row in board.split("/"):
        expanded = ""
        for c in row:
            if c.isdigit():
                expanded += "-" * int(c)
            else:
                expanded += c
        expanded_rows.append(expanded)

    expanded_board = "/".join(expanded_rows)

    return expanded_board + " " + rest


def pgn_to_fasta_stream(pgn_path, out_path):

    with open(pgn_path) as pgn, open(out_path, "w") as out:

        while True:
            game = chess.pgn.read_game(pgn)

            if game is None:
                break

            game_id = game.headers.get("GameId", "unknown")
            result = game.headers.get("Result", "*")

            board = game.board()
            ply = 0

            for node in game.mainline():

                move = node.move
                board.push(move)

                ply += 1

                fen = board.fen()
                fen_expanded = expand_fen_board(fen)

                eval_score = extract_eval(node.comment)

                if eval_score is None:
                    continue

                side = "w" if board.turn else "b"

                header = (
                    f">game={game_id} "
                    f"ply={ply} "
                    f"side={side} "
                    f"eval={eval_score} "
                    f"result={result}"
                )

                out.write(header + "\n")
                out.write(fen_expanded + "\n\n")


if __name__ == "__main__":
    pgn_to_fasta_stream("lichess_EisWolf_LH_2026-03-05.pgn", "lichess_EisWolf_LH_2026-03-05.fasta")
