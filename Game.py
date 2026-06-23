from Card import Card
from Mission import Mission
from Player import Player
from BotPlayer import BotPlayer
from HumanPlayer import HumanPlayer
import random
import json
import numpy as np

class Game:

    @staticmethod
    def generate_gem_deck():
        gem_deck = []
        for i in range(30):
            x = i//6
            if(x == 0):
                gem_deck.append(Card("Gem", gem_type="Pink"))
            elif(x == 1):
                gem_deck.append(Card("Gem", gem_type="Green"))
            elif(x == 2):
                gem_deck.append(Card("Gem", gem_type="Blue"))
            elif(x == 3):
                gem_deck.append(Card("Gem", gem_type="Purple"))
            elif(x == 4):
                gem_deck.append(Card("Gem", gem_type="Yellow"))
        random.shuffle(gem_deck)
        return gem_deck
    
    @staticmethod
    def generate_auction_deck():
        auction_deck = []
        for i in range(25):
            if(0 <= i < 12):
                auction_deck.append(Card("Treasure", amount=1))
            elif(12 <= i < 17):
                auction_deck.append(Card("Treasure", amount=2))
            elif(17 <= i < 19):
                auction_deck.append(Card("Invest", amount=5))
            elif(19 <= i < 21):
                auction_deck.append(Card("Invest", amount=10))
            elif(21 <= i < 23):
                auction_deck.append(Card("Loan", amount=10))
            else:
                auction_deck.append(Card("Loan", amount=20))
        random.shuffle(auction_deck)
        return auction_deck
    
    @staticmethod
    def generate_missions():
        mission_deck = []
        with open("missions.json", "r") as f:
            missions_raw = json.load(f)
        for x in missions_raw:
            mission_deck.append(Mission(x["mission_type"], x["payout"], gem_list=x["gem_list"], gem_count=x["gem_count"]))
        random.shuffle(mission_deck)
        return mission_deck[0:4]

    def __init__(self, num_players=3, human=False, bot=False, bot_name="megagem_agentv3_2", bot_name_2=None, recurrent=False, recurrent2 = False):
        if(bot_name_2 == None): 
            bot_name_2 = bot_name
        self.gem_deck = self.generate_gem_deck()
        self.auction_deck = self.generate_auction_deck()
        self.active_missions = self.generate_missions()
        self.last_bid_winner = -1
        self.value_chart = {0: 0, 1:4, 2:8, 3:12, 4:16, 5:20, 6:20}
        value_chart = self.value_chart
        #make adjustable later
        self.human=human
        self.bids = [-1, -1, -1]

        starting_coins = 0
        hand_size = 0
        if(num_players == 3):
            starting_coins = 35
            hand_size = 5
        elif(num_players == 4):
            starting_coins = 25
            hand_size = 4
        elif(num_players == 5):
            starting_coins = 20
            hand_size = 3
        else:
            pass
            #invalid
        
        self.players = []
        amount = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
        for i in range(num_players):
            if(human and i == 0):
                self.players.append(HumanPlayer(i, starting_coins, self.gem_deck[0:hand_size]))
            elif(i == 1):
                if(bot_name == "random"):
                    self.players.append(Player(i, starting_coins, self.gem_deck[0:hand_size]))
                else: 
                    self.players.append(BotPlayer(i, starting_coins, self.gem_deck[0:hand_size], central=self, bot_name=bot_name, recurrent=recurrent))
            else:
                if(bot_name_2 == "random"):
                    self.players.append(Player(i, starting_coins, self.gem_deck[0:hand_size]))
                else: 
                    self.players.append(BotPlayer(i, starting_coins, self.gem_deck[0:hand_size], central=self, bot_name=bot_name_2, recurrent=recurrent2))
            for card in self.gem_deck[0:hand_size]:
                amount[card.gem_type]+=1
            del self.gem_deck[0:hand_size]
        
        value = {}
        for key, entry in amount.items():
            value[key] = value_chart[entry]

        self.gem_values = value
        
        self.gems_available = self.gem_deck[0:2]
        del self.gem_deck[0:2]

    def get_revealed_cards(self):
        revealed_cards = []
        for player in self.players:
            revealed_cards.append(player.get_revealed_cards())
        return list(enumerate(revealed_cards))
    
    def display_state(self):
        print("ACTIVE MISSION CARDS: ")
        for mission in self.active_missions:
            print(mission)
        for player in self.players:
            print(player)
            print()
    
    def get_obs(self, player_no, mode, recurrent=False):
        obs = []
        
        mode_obs = [mode]
        obs.append(mode_obs)

        mission_obs = [x.get_obs() for x in self.active_missions]
        while(len(mission_obs) < 4):
            mission_obs.append([-1, -1, -1, -1, -1, -1, -1])
        mission_obs = [x for sublist in mission_obs for x in sublist]
        obs.append(mission_obs)

        player_obs = [x.get_obs() for x in self.players]
        curr_player_info = player_obs.pop(player_no)
        player_obs.insert(0, curr_player_info)
        player_obs = [x for sublist in player_obs for x in sublist]
        obs.append(player_obs)

        active_gems_obs = [x.get_obs()[0] for x in self.gems_available]
        while(len(active_gems_obs) < 2):
            active_gems_obs.append(-1)
        obs.append(active_gems_obs)

        gems_left_obs = [len(self.gem_deck)]
        obs.append(gems_left_obs)
        
        #This is a little dangerous since in the main game loop we just draw the card
        #But here we treat the top of the deck as the current card
        #Well, maybe not dangerous, but something to keep in mind
        up_auction_obs = self.auction_deck[0].get_obs()
        obs.append(up_auction_obs)

        max_bid = self.players[player_no].coins
        if(up_auction_obs[1] > 0): 
            max_bid += up_auction_obs[1]
        max_bid_obs = [max_bid]
        obs.append(max_bid_obs)

        curr_player = self.players[player_no]
        hands_obs = [0, 0, 0, 0, 0]
        hand_amount = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
        for (gem, _) in curr_player.hand:
            hand_amount[gem.gem_type] += 1
        hands_obs[0] = hand_amount["Pink"]
        hands_obs[1] = hand_amount["Green"]
        hands_obs[2] = hand_amount["Blue"]
        hands_obs[3] = hand_amount["Purple"]
        hands_obs[4] = hand_amount["Yellow"]
        obs.append(hands_obs)

        last_bid_obs = [self.last_bid_winner]
        obs.append(last_bid_obs)

        if(recurrent):
            bids = self.bids.copy()
            bid = bids.pop(player_no)
            bids.insert(0, bid)
            obs.append(bids)

        obs = [x for sublist in obs for x in sublist]
        return np.array(obs, dtype=np.int32)



    
    def draw_auction(self):
        card = self.auction_deck.pop(0)
        return card
    
    def draw_gem(self):
        if(len(self.gem_deck) == 0):
            #print("I CANT DRAW!")
            return
        card = self.gem_deck.pop(0)
        self.gems_available.append(card)


    def get_winner(self, bids):
        bids = list(enumerate(bids))
        bids = sorted(bids, key=lambda x: x[1], reverse=True)
        winners = [bid for bid in bids if bid[1] == bids[0][1]]
        if(len(winners) == 1):
            self.last_bid_winner = winners[0][0]
            return ((self.players[winners[0][0]], winners[0][1]))
        else:
            if(self.human):
                print(f"TIE WITH FOLLOWING INFO: {winners}")
            return self.resolve_tie(winners)

    def resolve_tie(self, tied):
        if(self.last_bid_winner == -1):
            winner = tied[random.randint(0, len(tied)-1)]
            self.last_bid_winner = winner[0]
            return ((self.players[winner[0]], winner[1]))
        else:
            tied = [(player[0], player[1], player[0] - (self.last_bid_winner+1)) if player[0] - (self.last_bid_winner+1) >= 0 else (player[0], player[1], player[0] - (self.last_bid_winner+1) + len(self.players)) for player in tied]
            tied = sorted(tied, key=lambda x: x[2])
            self.last_bid_winner = tied[0][0]
            return ((self.players[tied[0][0]], tied[0][1]))
        
    def compute_scores(self):
        for player in self.players:
            player.coins += player.amount_to_add
            for gem in player.collection:
                player.coins += self.gem_values[gem.gem_type]
        
        #ranked = sorted(self.players, key=lambda x: x.coins, reverse=True)
        #return [(x.player_no, x.coins) for i, x in enumerate(ranked)]
        return [(x.player_no, x.coins) for x in self.players]
    
    def complete_possible_missions(self, winner):
        missions_won = []
        winner_amount = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
        for gem in winner.collection:
            winner_amount[gem.gem_type] += 1
        to_remove = []
        for index, mission in enumerate(self.active_missions):
            if(mission.mission_type == "same"):
                for key, entry in winner_amount.items():
                    if(entry >= mission.gem_count):
                        to_remove.append(index)
                        winner.amount_to_add += mission.payout
                        missions_won.append(mission)
                        break
            elif(mission.mission_type == "different"):
                unique = 0
                for key, entry in winner_amount.items():
                    if(entry > 0):
                        unique += 1
                if(unique >= mission.gem_count):
                    to_remove.append(index)
                    winner.amount_to_add += mission.payout
                    missions_won.append(mission)
            elif(mission.mission_type == "pairs"):
                pair_amount = 0
                for key, entry in winner_amount.items():
                    if(entry >= 2):
                        pair_amount += 1
                if(pair_amount >= mission.gem_count):
                    to_remove.append(index)
                    winner.amount_to_add += mission.payout
                    missions_won.append(mission)
            elif(mission.mission_type == "specific"):
                mission_amount = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
                for gem in mission.gem_list:
                    mission_amount[gem] += 1
                to_award = True

                for key, entry in mission_amount.items():
                    if(entry > winner_amount[key]):
                        to_award = False
                        break

                if(to_award):
                    to_remove.append(index)
                    winner.amount_to_add += mission.payout
                    missions_won.append(mission)
        self.active_missions = [m for i, m in enumerate(self.active_missions) if i not in to_remove]
        return missions_won

                    
                

                    










