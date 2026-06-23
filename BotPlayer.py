from Player import Player
import gymnasium as gym
import numpy as np

from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib import RecurrentPPO

class BotPlayer(Player):

    def __init__(self, player_no, starting_coins, starting_cards, central, bot_name="megagem_agentv3_2", recurrent=False):
        super().__init__(player_no, starting_coins, starting_cards)
        if(recurrent):
            self.model = RecurrentPPO.load(bot_name)
        else:
            self.model = MaskablePPO.load(bot_name)
        self.central = central
        self.recurrent = recurrent
        self.lstm_states = None
        self.episode_starts = np.array([True])

    def bid(self, loan_amount=0):
        obs = self.central.get_obs(self.player_no, 0, recurrent=self.recurrent)
        if(self.recurrent):
            answer, self.lstm_states = self.model.predict(obs, state=self.lstm_states, episode_start=self.episode_starts, deterministic=False)
            self.episode_starts = np.array([False])
            return int(answer)
        else:
            return int(self.model.predict(obs, action_masks=self.action_masks(0))[0])
    
    def reveal_card(self):
        unrevealed_indices = [i for i, card in enumerate(self.hand) if card[1] == False]
        if(len(unrevealed_indices) == 0): return
        obs = self.central.get_obs(self.player_no, 1, recurrent=self.recurrent)
        if(self.recurrent):
            answer, self.lstm_states = self.model.predict(obs, state=self.lstm_states, episode_start=self.episode_starts, deterministic=False)
            self.episode_starts = np.array([False])
            self.reveal_card_by_color(int(answer - 96))
        else:
            self.reveal_card_by_color(int(self.model.predict(obs, action_masks=self.action_masks(1))[0]) - 96)

    def action_masks(self, phase):
        curr_player = self.central.players[self.player_no]
        if(phase == 0):
            max_bid = curr_player.coins
            if(self.central.auction_deck[0].type == "Loan"):
                max_bid += self.central.auction_deck[0].amount
            mask = [True if i <= max_bid else False for i in range(101)]
            mask[0] = True #double check
            return mask
        elif(phase == 1):
            mask = [False for i in range(101)]
            count = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
            for (gem, revealed) in curr_player.hand:
                if(not revealed): 
                   count[gem.gem_type] += 1
            mask[96] = (count["Pink"] > 0)
            mask[97] = (count["Green"] > 0)
            mask[98] = (count["Blue"] > 0)
            mask[99] = (count["Purple"] > 0)
            mask[100] = (count["Yellow"] > 0)
            #print(f"phase 1 mask: {mask}")
            return mask
