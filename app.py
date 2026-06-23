import uuid
import os
from threading import Lock

from flask import Flask, request, jsonify, render_template

from Game import Game
from WebsitePlayer import WebsitePlayer

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

sessions = {}
sessions_lock = Lock()

BOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bots")

DIFFICULTY_MAP = {
    "easy": {
        "bot_name": "bots/megagem_agentv3_2",
        "bot_name_2": "bots/megagem_agentv2_3",
        "recurrent": False,
        "recurrent2": False,
    },
    "medium": {
        "bot_name": "bots/megagem_agentv4_5",
        "bot_name_2": "bots/megagem_agentv4_4",
        "recurrent": False,
        "recurrent2": False,
    },
    "hard": {
        "bot_name": "bots/megagem_agentv5_2_6",
        "bot_name_2": "bots/megagem_agent_antiv5_6",
        "recurrent": False,
        "recurrent2": False,
    },
}


BOT_DISPLAY_NAMES = {
    "megagem_agentv3_2": "Phil",
    "megagem_agentv2_3": "Onizuka",
    "megagem_agentv4_5": "Geto",
    "megagem_agentv4_4": "Gojo",
    "megagem_agentv5_2_6": "Apex",
    "megagem_agent_antiv5_6": "Zenith",
}


def get_available_bots():
    bots = []
    for f in os.listdir(BOTS_DIR):
        if f.endswith(".zip"):
            name = f[:-4]
            if "vR" not in name:
                bots.append(name)
    bots.sort()
    return bots


class SessionState:
    def __init__(self, central, difficulty, bot_names):
        self.central = central
        self.difficulty = difficulty
        self.bot_names = bot_names
        self.phase = "bid"
        self.round_number = 1
        self.current_auction_card = central.auction_deck[0]
        self.last_round_result = None
        self.scores = None


def swap_human_player(central):
    old = central.players[0]
    wp = WebsitePlayer.__new__(WebsitePlayer)
    wp.player_no = old.player_no
    wp.coins = old.coins
    wp.hand = old.hand
    wp.collection = old.collection
    wp.amount_to_add = old.amount_to_add
    central.players[0] = wp
    return wp


def serialize_state(session_id, session):
    central = session.central
    human = central.players[0]

    missions = []
    for m in central.active_missions:
        missions.append({
            "mission_type": m.mission_type,
            "payout": m.payout,
            "gem_list": m.gem_list,
            "gem_count": m.gem_count,
            "description": str(m),
        })

    gems_avail = [{"gem_type": g.gem_type} for g in central.gems_available]

    ac = session.current_auction_card
    auction_card = None
    if ac:
        auction_card = {
            "type": ac.type,
            "amount": ac.amount,
            "gem_type": ac.gem_type,
        }

    loan_amount = 0
    if ac and ac.type == "Loan":
        loan_amount = ac.amount
    max_bid = human.coins + loan_amount

    human_hand = []
    for i, (card, revealed) in enumerate(human.hand):
        human_hand.append({
            "gem_type": card.gem_type,
            "revealed": revealed,
            "index": i,
        })

    human_data = {
        "player_no": 0,
        "coins": human.coins,
        "deferred_income": human.amount_to_add,
        "hand": human_hand,
        "collection": [{"gem_type": c.gem_type} for c in human.collection],
    }

    opponents = []
    for p in central.players[1:]:
        opp_hand = []
        for i, (card, revealed) in enumerate(p.hand):
            opp_hand.append({
                "gem_type": card.gem_type if revealed else None,
                "revealed": revealed,
            })
        opponents.append({
            "player_no": p.player_no,
            "coins": p.coins,
            "deferred_income": p.amount_to_add,
            "hand": opp_hand,
            "collection": [{"gem_type": c.gem_type} for c in p.collection],
        })

    scores = None
    if session.phase == "game_over" and session.scores is not None:
        raw_scores = session.scores
        ranked = sorted(raw_scores, key=lambda x: x[1], reverse=True)
        scores = []
        for rank, (pno, coins) in enumerate(ranked):
            scores.append({"player_no": pno, "final_coins": coins, "rank": rank + 1})

    return {
        "session_id": session_id,
        "phase": session.phase,
        "round_number": session.round_number,
        "difficulty": session.difficulty,
        "missions": missions,
        "gems_available": gems_avail,
        "gem_deck_remaining": len(central.gem_deck),
        "auction_card": auction_card,
        "auction_deck_remaining": len(central.auction_deck),
        "max_bid": max_bid,
        "human_player": human_data,
        "opponents": opponents,
        "bot_names": session.bot_names,
        "last_round": session.last_round_result,
        "scores": scores,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/bots")
def list_bots():
    bots = get_available_bots()
    return jsonify([{"id": b, "name": BOT_DISPLAY_NAMES.get(b, b)} for b in bots])


@app.route("/api/new_game", methods=["POST"])
def new_game():
    data = request.get_json()
    mode = data.get("mode", "difficulty")

    if mode == "freeplay":
        bot1 = data.get("bot_name")
        bot2 = data.get("bot_name_2")
        available = get_available_bots()
        if bot1 not in available or bot2 not in available:
            return jsonify({"error": "Invalid bot name"}), 400
        bot_name = f"bots/{bot1}"
        bot_name_2 = f"bots/{bot2}"
        difficulty = "freeplay"
        bot1_display = BOT_DISPLAY_NAMES.get(bot1, bot1)
        bot2_display = BOT_DISPLAY_NAMES.get(bot2, bot2)
    else:
        difficulty = data.get("difficulty", "easy")
        if difficulty not in DIFFICULTY_MAP:
            return jsonify({"error": "Invalid difficulty"}), 400
        config = DIFFICULTY_MAP[difficulty]
        bot_name = config["bot_name"]
        bot_name_2 = config["bot_name_2"]
        raw1 = bot_name.replace("bots/", "")
        raw2 = bot_name_2.replace("bots/", "")
        bot1_display = BOT_DISPLAY_NAMES.get(raw1, raw1)
        bot2_display = BOT_DISPLAY_NAMES.get(raw2, raw2)

    central = Game(
        3,
        human=True,
        bot_name=bot_name,
        bot_name_2=bot_name_2,
        recurrent=False,
        recurrent2=False,
    )
    swap_human_player(central)

    session_id = str(uuid.uuid4())
    bot_names = {1: bot1_display, 2: bot2_display}
    session = SessionState(central, difficulty, bot_names)

    with sessions_lock:
        sessions[session_id] = session

    return jsonify(serialize_state(session_id, session))


@app.route("/api/state/<session_id>")
def get_state(session_id):
    with sessions_lock:
        session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(serialize_state(session_id, session))


@app.route("/api/bid/<session_id>", methods=["POST"])
def bid(session_id):
    with sessions_lock:
        session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    if session.phase != "bid":
        return jsonify({"error": f"Cannot bid in phase '{session.phase}'"}), 400

    central = session.central
    human_player = central.players[0]
    data = request.get_json()
    human_bid = data.get("bid")

    if human_bid is None or not isinstance(human_bid, int):
        return jsonify({"error": "Bid must be an integer"}), 400

    current_auction_card = session.current_auction_card
    loan_amount = 0
    if current_auction_card.type == "Loan":
        loan_amount = current_auction_card.amount
    max_bid = human_player.coins + loan_amount

    if human_bid < 0 or human_bid > max_bid:
        return jsonify({"error": f"Bid must be between 0 and {max_bid}"}), 400

    bids = []
    for player in central.players:
        if player.player_no == 0:
            bids.append(human_bid)
        else:
            bids.append(player.bid(loan_amount))

    winner, bid_amount = central.get_winner(bids)
    winner.coins -= bid_amount

    gems_collected = []
    missions_completed = []

    if current_auction_card.type == "Loan":
        winner.coins += current_auction_card.amount
        winner.amount_to_add -= current_auction_card.amount
    elif current_auction_card.type == "Invest":
        winner.amount_to_add += bid_amount + current_auction_card.amount
    elif current_auction_card.type == "Treasure":
        if current_auction_card.amount >= 1:
            gem = central.gems_available.pop(0)
            gems_collected.append(gem.gem_type)
            winner.add_to_collection(gem)
            central.draw_gem()
        if current_auction_card.amount >= 2:
            if len(central.gems_available) > 0:
                gem = central.gems_available.pop(0)
                gems_collected.append(gem.gem_type)
                winner.add_to_collection(gem)
                central.draw_gem()
        missions_won = central.complete_possible_missions(winner)
        missions_completed = [str(m) for m in missions_won]

    human_won = (winner.player_no == 0)
    human_has_unrevealed = any(not revealed for (_, revealed) in human_player.hand)

    if human_won and human_has_unrevealed:
        session.phase = "reveal"
    else:
        if not human_won:
            winner.reveal_card()

        if len(central.gems_available) == 0:
            session.phase = "game_over"
            session.scores = central.compute_scores()
        else:
            central.draw_auction()
            session.current_auction_card = central.auction_deck[0] if len(central.auction_deck) > 0 else None
            session.phase = "bid"
            session.round_number += 1

    session.last_round_result = {
        "round_number": session.round_number,
        "auction_card_type": current_auction_card.type,
        "auction_card_amount": current_auction_card.amount,
        "bids": bids,
        "winner_player_no": winner.player_no,
        "winning_bid": bid_amount,
        "gems_collected": gems_collected,
        "missions_completed": missions_completed,
    }

    return jsonify(serialize_state(session_id, session))


@app.route("/api/reveal/<session_id>", methods=["POST"])
def reveal(session_id):
    with sessions_lock:
        session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    if session.phase != "reveal":
        return jsonify({"error": f"Cannot reveal in phase '{session.phase}'"}), 400

    central = session.central
    human_player = central.players[0]
    data = request.get_json()
    card_index = data.get("card_index")

    if card_index is None or not isinstance(card_index, int):
        return jsonify({"error": "card_index must be an integer"}), 400
    if card_index < 0 or card_index >= len(human_player.hand):
        return jsonify({"error": "Invalid card index"}), 400
    if human_player.hand[card_index][1]:
        return jsonify({"error": "Card already revealed"}), 400

    human_player.reveal_card_by_index(card_index)

    if len(central.gems_available) == 0:
        session.phase = "game_over"
        session.scores = central.compute_scores()
    else:
        central.draw_auction()
        session.current_auction_card = central.auction_deck[0] if len(central.auction_deck) > 0 else None
        session.phase = "bid"
        session.round_number += 1

    return jsonify(serialize_state(session_id, session))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
