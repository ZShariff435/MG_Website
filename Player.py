import random
class Player:

    def __init__(self, player_no, starting_coins, starting_cards):
        self.player_no = player_no
        self.coins = starting_coins
        self.hand = []
        self.collection = []
        for x in starting_cards:
            self.hand.append((x, False))
            #(Card, Revealed)
        self.amount_to_add = 0
        #Amount to add at the end of the game based on Missions+Loans/Investments

    def bid(self, loan_amount=0):
        return random.randint(0, self.coins+loan_amount)
    
    def reveal_card(self):
        unrevealed_indices = [i for i, card in enumerate(self.hand) if card[1] == False]
        if(len(unrevealed_indices) == 0): return
        to_reveal = random.randint(0, len(unrevealed_indices)-1)
        index = unrevealed_indices[to_reveal]
        tuple = self.hand.pop(index)
        self.hand.append((tuple[0], True))

    #this is for the bot
    def reveal_card_by_color(self, card_color):
        mapping = {0: "Pink", 1:"Green", 2:"Blue", 3:"Purple", 4:"Yellow"}
        unrevealed_indices = [(i, card) for i, card in enumerate(self.hand) if card[1] == False]
        index = None
        if(0 <= card_color <=4):
            card_color = mapping[card_color]
            index = next((x[0] for i, x in enumerate(unrevealed_indices) if x[1][0].gem_type == card_color), None)
        if(index is None):
            print("I SCREWED UP THE REVEAL")
            index = unrevealed_indices[0][0]
        tuple = self.hand.pop(index)
        self.hand.append((tuple[0], True))

    
    def get_revealed_cards(self):
        revealed = [card for card in self.hand if card[1] == True]
        return revealed

    def get_value_display(self):
        return [card for card in self.hand if card[1] == True]
    
    def add_to_collection(self, card):
        self.collection.append(card)

    def __repr__(self):
        return f"""PLAYER NO {self.player_no} INFO:
                   REVEALED CARDS: {self.get_revealed_cards()}
                   COLLECTION: {self.collection}
                   PLAYER WEALTH: {self.coins}
                   PLAYER DEFERRED INCOME: {self.amount_to_add}"""

    def get_obs(self):
        obs = []
        revealed_obs = [0, 0, 0, 0, 0]
        revealed_amount = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
        for (gem, _) in self.get_revealed_cards():
            revealed_amount[gem.gem_type] += 1
        revealed_obs[0] = revealed_amount["Pink"]
        revealed_obs[1] = revealed_amount["Green"]
        revealed_obs[2] = revealed_amount["Blue"]
        revealed_obs[3] = revealed_amount["Purple"]
        revealed_obs[4] = revealed_amount["Yellow"]

        obs.append(revealed_obs)

        collection_obs = [0, 0, 0, 0, 0]
        collected_amount = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
        for gem in self.collection:
            collected_amount[gem.gem_type] += 1
        collection_obs[0] = collected_amount["Pink"]
        collection_obs[1] = collected_amount["Green"]
        collection_obs[2] = collected_amount["Blue"]
        collection_obs[3] = collected_amount["Purple"]
        collection_obs[4] = collected_amount["Yellow"]

        obs.append(collection_obs)

        wealth_obs = [self.coins]
        obs.append(wealth_obs)

        deferred_income = [self.amount_to_add]
        obs.append(deferred_income)

        obs = [x for sublist in obs for x in sublist]
        return obs

        
        

