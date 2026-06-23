from Player import Player
import random

class HumanPlayer(Player):
    def __init__(self, player_no, starting_coins, starting_cards):
        super().__init__(player_no, starting_coins, starting_cards)
    
    def bid(self, loan_amount=0):
        self.display_info()
        return int(input(f"How much do you want to bid? (Max is {self.coins+loan_amount})"))
    
    def reveal_card(self):
        unrevealed_indices = [(i, card[0]) for i, card in enumerate(self.hand) if card[1] == False]
        if(len(unrevealed_indices) == 0): return
        print(unrevealed_indices)
        to_reveal = int(input("Which card do you want to reveal?"))
        index = unrevealed_indices[to_reveal][0]
        tuple = self.hand.pop(index)
        self.hand.append((tuple[0], True))

    def display_info(self):
        print(f"YOUR HAND: {self.hand}")
        print(f"YOUR BALANCE: {self.coins}")
        print(f"YOUR DEFERRED INCOME: {self.amount_to_add}")
        print(f"YOUR COLLECTION:  {self.collection}")
        