let sessionId = null;
let gameState = null;

const GEM_COLORS = {
    Pink:   "gem-pink",
    Green:  "gem-green",
    Blue:   "gem-blue",
    Purple: "gem-purple",
    Yellow: "gem-yellow",
};

function showScreen(id) {
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    document.getElementById(id).classList.add("active");
}

/* ── API Helpers ── */

async function apiFetch(url, options) {
    const resp = await fetch(url, options);
    const data = await resp.json();
    if (!resp.ok) {
        alert(data.error || "Something went wrong");
        return null;
    }
    return data;
}

/* ── Game Lifecycle ── */

async function newGame(difficulty) {
    showScreen("screen-loading");
    const data = await apiFetch("/api/new_game", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({mode: "difficulty", difficulty}),
    });
    if (!data) { showScreen("screen-menu"); return; }
    sessionId = data.session_id;
    gameState = data;
    showScreen("screen-game");
    renderGame();
}

let botsLoaded = false;

async function toggleFreeplay() {
    const panel = document.getElementById("freeplay-panel");
    if (panel.style.display === "none") {
        panel.style.display = "block";
        if (!botsLoaded) {
            const bots = await apiFetch("/api/bots");
            if (!bots) return;
            const sel1 = document.getElementById("freeplay-bot1");
            const sel2 = document.getElementById("freeplay-bot2");
            sel1.innerHTML = "";
            sel2.innerHTML = "";
            bots.forEach(b => {
                const label = b.name !== b.id ? `${b.name} (${b.id})` : b.id;
                sel1.innerHTML += `<option value="${b.id}">${label}</option>`;
                sel2.innerHTML += `<option value="${b.id}">${label}</option>`;
            });
            if (bots.length > 1) sel2.selectedIndex = 1;
            botsLoaded = true;
        }
    } else {
        panel.style.display = "none";
    }
}

async function startFreeplay() {
    const bot1 = document.getElementById("freeplay-bot1").value;
    const bot2 = document.getElementById("freeplay-bot2").value;
    showScreen("screen-loading");
    const data = await apiFetch("/api/new_game", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({mode: "freeplay", bot_name: bot1, bot_name_2: bot2}),
    });
    if (!data) { showScreen("screen-menu"); return; }
    sessionId = data.session_id;
    gameState = data;
    showScreen("screen-game");
    renderGame();
}

function backToMenu() {
    sessionId = null;
    gameState = null;
    botsLoaded = false;
    showScreen("screen-menu");
}

/* ── Master Render ── */

function renderGame() {
    const s = gameState;
    document.getElementById("round-display").textContent = `Round ${s.round_number}`;
    const diffBadge = document.getElementById("difficulty-display");
    diffBadge.textContent = s.difficulty;
    diffBadge.className = `difficulty-badge ${s.difficulty}`;

    renderMissions(s.missions);
    renderGemMarket(s);
    renderAuctionArea(s);
    renderRoundLog(s);
    renderOpponent(s.opponents[0], "opponent-1", s.bot_names["1"]);
    renderOpponent(s.opponents[1], "opponent-2", s.bot_names["2"]);
    renderHumanPlayer(s);
}

/* ── Missions ── */

function renderMissions(missions) {
    const row = document.getElementById("missions-row");
    row.innerHTML = "";
    if (missions.length === 0) {
        row.innerHTML = '<div class="mission-card" style="opacity:0.5">No missions remaining</div>';
        return;
    }
    missions.forEach(m => {
        const card = document.createElement("div");
        card.className = "mission-card";

        let typeLabel = "";
        let detail = "";
        let gemsHtml = "";

        if (m.mission_type === "same") {
            typeLabel = "Collection";
            detail = `${m.gem_count} of the same gem`;
        } else if (m.mission_type === "different") {
            typeLabel = "Collection";
            detail = `${m.gem_count} different gems`;
        } else if (m.mission_type === "pairs") {
            typeLabel = "Collection";
            detail = `${m.gem_count} different pairs`;
        } else if (m.mission_type === "specific") {
            typeLabel = "Specific";
            detail = "Collect:";
            gemsHtml = '<div class="mission-gems">' +
                m.gem_list.map(g => `<span class="mission-gem-chip ${GEM_COLORS[g] || ''}">${g}</span>`).join("") +
                '</div>';
        }

        card.innerHTML = `
            <div class="mission-type">${typeLabel}</div>
            <div class="mission-detail">${detail}</div>
            ${gemsHtml}
            <div class="mission-payout">+${m.payout} coins</div>
        `;
        row.appendChild(card);
    });
}

/* ── Gem Market ── */

function renderGemMarket(s) {
    const el = document.getElementById("gem-market");
    let html = '<div class="gem-market-title">Gem Market</div>';
    html += '<div class="gem-market-cards">';

    if (s.gems_available.length > 0) {
        const primary = s.gems_available[0];
        html += makeGemCard(primary.gem_type, "gem-card-market-primary");
    }
    if (s.gems_available.length > 1) {
        const secondary = s.gems_available[1];
        html += makeGemCard(secondary.gem_type, "gem-card-market-secondary");
    }
    if (s.gems_available.length === 0) {
        html += '<div style="color:#666;font-style:italic">Empty</div>';
    }

    html += '</div>';
    html += `<div class="gem-market-remaining">${s.gem_deck_remaining} gems remaining in deck</div>`;

    el.innerHTML = html;
}

/* ── Auction Area ── */

function renderAuctionArea(s) {
    const el = document.getElementById("auction-area");
    let html = '<div class="auction-title">Auction</div>';

    if (s.auction_card) {
        const ac = s.auction_card;
        const typeClass = ac.type.toLowerCase();
        let amountText = "";
        if (ac.type === "Treasure") {
            amountText = `×${ac.amount}`;
        } else {
            amountText = `${ac.amount}`;
        }

        html += `
            <div class="auction-card-display ${typeClass}">
                <div class="auction-card-type">${ac.type}</div>
                <div class="auction-card-amount">${amountText}</div>
            </div>
        `;
    }

    if (s.phase === "bid") {
        html += `
            <div class="bid-controls">
                <div class="bid-input-group">
                    <input type="number" id="bid-input" class="bid-input" min="0" max="${s.max_bid}" value="0">
                    <span class="bid-max-label">/ ${s.max_bid}</span>
                </div>
                <button class="btn btn-bid" onclick="submitBid()">Place Bid</button>
            </div>
        `;
    } else if (s.phase === "reveal") {
        html += '<div class="reveal-banner">You won the auction! Click a card in your hand to reveal it.</div>';
    }

    el.innerHTML = html;

    const inp = document.getElementById("bid-input");
    if (inp) {
        inp.addEventListener("keydown", (e) => {
            if (e.key === "Enter") submitBid();
        });
    }
}

/* ── Round Log ── */

function renderRoundLog(s) {
    const el = document.getElementById("round-log");
    if (!s.last_round) {
        el.innerHTML = "";
        return;
    }
    const lr = s.last_round;
    const names = ["You", s.bot_names["1"], s.bot_names["2"]];
    const winnerName = names[lr.winner_player_no];
    const isHumanWin = lr.winner_player_no === 0;

    let bidsHtml = lr.bids.map((b, i) => {
        const isWinner = i === lr.winner_player_no;
        return `<span class="log-bid ${isWinner ? 'log-bid-winner' : ''}">${names[i]}: <strong>${b}</strong></span>`;
    }).join("");

    let extrasHtml = "";
    if (lr.gems_collected && lr.gems_collected.length > 0) {
        const gemChips = lr.gems_collected.map(g =>
            `<span class="log-gem-chip ${GEM_COLORS[g] || ''}">${g}</span>`
        ).join(" ");
        extrasHtml += `<div class="log-extra">${winnerName} collected ${gemChips}</div>`;
    }
    if (lr.missions_completed && lr.missions_completed.length > 0) {
        lr.missions_completed.forEach(m => {
            extrasHtml += `<div class="log-extra log-mission">Mission completed: ${m}</div>`;
        });
    }

    el.innerHTML = `
        <div class="log-winner ${isHumanWin ? 'log-winner-you' : ''}">${winnerName} won with ${lr.winning_bid} coins</div>
        <div class="log-bids">${bidsHtml}</div>
        ${extrasHtml}
    `;
}

/* ── Opponent Panels ── */

function renderOpponent(opp, containerId, label) {
    const el = document.getElementById(containerId);
    const revealedCount = opp.hand.filter(c => c.revealed).length;
    const hiddenCount = opp.hand.length - revealedCount;

    let html = `
        <div class="player-header">
            <span class="player-name">${label} (Player ${opp.player_no})</span>
            <div class="player-stats">
                <span class="stat"><span class="stat-icon">&#x1FA99;</span> <span class="stat-value">${opp.coins}</span></span>
                <span class="stat stat-deferred ${opp.deferred_income > 0 ? 'positive' : opp.deferred_income < 0 ? 'negative' : 'zero'}">
                    Deferred: ${opp.deferred_income >= 0 ? "+" : ""}${opp.deferred_income}
                </span>
            </div>
        </div>
    `;

    html += '<div class="cards-section"><div class="cards-label">Hand (' + hiddenCount + ' hidden, ' + revealedCount + ' revealed)</div><div class="cards-row">';
    opp.hand.forEach(c => {
        if (c.revealed && c.gem_type) {
            html += makeGemCard(c.gem_type, "gem-card-hand");
        } else {
            html += '<div class="gem-card gem-card-hand gem-unknown">?</div>';
        }
    });
    html += '</div></div>';

    html += '<div class="cards-section"><div class="cards-label">Collection (' + opp.collection.length + ')</div><div class="cards-row">';
    if (opp.collection.length === 0) {
        html += '<span style="color:#555;font-size:0.8rem;font-style:italic">None yet</span>';
    } else {
        opp.collection.forEach(c => {
            html += makeGemCard(c.gem_type, "gem-card-collection");
        });
    }
    html += '</div></div>';

    el.innerHTML = html;
}

/* ── Human Player Panel ── */

function renderHumanPlayer(s) {
    const el = document.getElementById("human-area");
    const p = s.human_player;
    const isRevealPhase = s.phase === "reveal";

    let html = `
        <div class="player-header">
            <span class="player-name">Your Hand</span>
            <div class="player-stats">
                <span class="stat"><span class="stat-icon">&#x1FA99;</span> <span class="stat-value">${p.coins}</span></span>
                <span class="stat stat-deferred ${p.deferred_income > 0 ? 'positive' : p.deferred_income < 0 ? 'negative' : 'zero'}">
                    Deferred: ${p.deferred_income >= 0 ? "+" : ""}${p.deferred_income}
                </span>
            </div>
        </div>
    `;

    html += '<div class="cards-section"><div class="cards-label">Hand</div><div class="cards-row">';
    p.hand.forEach(c => {
        const colorClass = GEM_COLORS[c.gem_type] || "gem-unknown";
        const clickable = isRevealPhase && !c.revealed;
        const dimmed = isRevealPhase && c.revealed;
        let classes = `gem-card gem-card-hand ${colorClass}`;
        if (clickable) classes += " clickable";
        if (dimmed) classes += " dimmed";

        let badge = "";
        if (c.revealed) {
            badge = '<span class="revealed-badge">R</span>';
        }

        const onclick = clickable ? `onclick="submitReveal(${c.index})"` : "";
        html += `<div class="${classes}" ${onclick}>${c.gem_type}${badge}</div>`;
    });
    html += '</div></div>';

    html += '<div class="cards-section"><div class="cards-label">Collection (' + p.collection.length + ')</div><div class="cards-row">';
    if (p.collection.length === 0) {
        html += '<span style="color:#555;font-size:0.8rem;font-style:italic">None yet</span>';
    } else {
        p.collection.forEach(c => {
            html += makeGemCard(c.gem_type, "gem-card-collection");
        });
    }
    html += '</div></div>';

    el.innerHTML = html;
}

/* ── Card Helpers ── */

function makeGemCard(gemType, sizeClass) {
    const colorClass = GEM_COLORS[gemType] || "gem-unknown";
    const label = gemType || "?";
    return `<div class="gem-card ${sizeClass} ${colorClass}">${label}</div>`;
}

/* ── Actions ── */

async function submitBid() {
    const inp = document.getElementById("bid-input");
    if (!inp) return;
    const bidVal = parseInt(inp.value, 10);
    if (isNaN(bidVal) || bidVal < 0 || bidVal > gameState.max_bid) {
        alert(`Bid must be between 0 and ${gameState.max_bid}`);
        return;
    }

    const data = await apiFetch(`/api/bid/${sessionId}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({bid: bidVal}),
    });
    if (!data) return;

    gameState = data;
    if (data.phase === "game_over") {
        renderGameOver();
    } else {
        renderGame();
    }
}

async function submitReveal(cardIndex) {
    const data = await apiFetch(`/api/reveal/${sessionId}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({card_index: cardIndex}),
    });
    if (!data) return;

    gameState = data;
    if (data.phase === "game_over") {
        renderGameOver();
    } else {
        renderGame();
    }
}

/* ── Game Over ── */

function renderGameOver() {
    const s = gameState;
    const title = document.getElementById("gameover-title");
    const scoresEl = document.getElementById("final-scores");

    const humanScore = s.scores.find(sc => sc.player_no === 0);
    if (humanScore && humanScore.rank === 1) {
        title.textContent = "You Win!";
        title.className = "gameover-title win";
    } else {
        title.textContent = "Game Over";
        title.className = "gameover-title lose";
    }

    let html = "";
    const sorted = [...s.scores].sort((a, b) => a.rank - b.rank);
    sorted.forEach(sc => {
        const name = sc.player_no === 0 ? "You" : s.bot_names[String(sc.player_no)];
        const rankClass = sc.rank === 1 ? "gold" : sc.rank === 2 ? "silver" : "bronze";
        const firstClass = sc.rank === 1 ? "first" : "";
        html += `
            <div class="score-row ${firstClass}">
                <span class="score-rank ${rankClass}">#${sc.rank}</span>
                <span class="score-name">${name}</span>
                <span class="score-coins">${sc.final_coins} coins</span>
            </div>
        `;
    });

    scoresEl.innerHTML = html;
    showScreen("screen-gameover");
}
