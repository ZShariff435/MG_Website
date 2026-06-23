from Player import Player


class WebsitePlayer(Player):

    def __init__(self, player_no, starting_coins, starting_cards):
        super().__init__(player_no, starting_coins, starting_cards)

    def bid(self, loan_amount=0):
        raise NotImplementedError("WebsitePlayer.bid() should not be called; use Flask routes.")

    def reveal_card(self):
        raise NotImplementedError("WebsitePlayer.reveal_card() should not be called; use Flask routes.")

    def reveal_card_by_index(self, hand_index):
        if hand_index < 0 or hand_index >= len(self.hand):
            return False
        card, revealed = self.hand[hand_index]
        if revealed:
            return False
        self.hand.pop(hand_index)
        self.hand.append((card, True))
        return True
