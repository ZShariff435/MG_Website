from typing import Optional
import numpy as np
import gymnasium as gym
from Game import Game
import random

class GameEnvTest(gym.Env):

    def __init__(self, player_no=0, opponents=None, bot1=None, bot2=None, recurrent=False):
        if(recurrent):
            self.observation_space = gym.spaces.Box(low=-1000, high=1000, shape=(80,))
        else:
            self.observation_space = gym.spaces.Box(low=-1000, high=1000, shape=(77,))
        self.action_space = gym.spaces.Discrete(n=101, start=0, dtype=int) #0-95 coins, 96-100 reveal
        self.player_no = player_no
        self.phase = 0
        self.opponents = opponents
        self.bot1 = bot1
        self.bot2 = bot2
        self.recurrent = recurrent

    def _get_obs(self, central, mode):
        self.phase = mode
        return central.get_obs(self.player_no, mode, recurrent=self.recurrent)
    
    def reset(self, seed=None, options=None):
        #print("I AM RESETTING")
        super().reset(seed = seed)
        if(self.opponents != None):
            #bot1 = self.opponents[random.randint(0, len(self.opponents)-1)]
            #REMEMBER TO UNCOMMENT THE ABOVE LATER
            bot1="megagem_agentv4_4"
            bot2 = self.opponents[random.randint(0, len(self.opponents)-1)]
        elif(self.bot1 != None and self.bot2 != None):
            bot1 = self.bot1
            bot2 = self.bot2
        else:
            bot1 = "megagem_agentv4_3"
            bot2 = "megagem_agentv5"
        print(f"Playing against {bot1} and {bot2}")
        self.central = Game(3, bot=True, bot_name=bot1, bot_name_2=bot2)
        self.phase = 0
        return self.central.get_obs(player_no=self.player_no, mode=0, recurrent=self.recurrent), {}
    
    def step(self, action):
        if(len(self.central.gems_available) == 0):
            reward = 0
            terminated = True
            scores = self.central.compute_scores()
            reward += 0.5*scores[self.player_no][1]
            ranked = sorted(scores, key=lambda x: x[1], reverse=True)
            for i in range(3):
                if(ranked[i][0] == self.player_no):
                    if(i == 0):
                        print("Bot Won!")
                        reward += 50
                    elif(i == 1):
                        print("Bot got 2nd...")
                        reward += 20
                    elif(i == 2):
                        print("Bot lost :(")
                        reward -= 10
            return self.central.get_obs(player_no=self.player_no, mode=0, recurrent=self.recurrent), reward, terminated, False, {}
        if(self.phase == 0): #bidding phase
            reward = 0
            central = self.central
            #RECALL THAT THE TOP OF THE AUCTION DECK IS THE OBSERVATION
            current_auction_card = central.auction_deck[0]
            loan_amount = 0
            if(current_auction_card.type == "Loan"):
                loan_amount = current_auction_card.amount
            bids = []
            for player in central.players:
                if(player.player_no == self.player_no):
                    if(action < 0 or action > player.coins + loan_amount):
                        print("I SCREWED UP THE BID")
                        action = 0
                        reward -= 10
                    bids.append(action)
                else:
                    bids.append(player.bid(loan_amount))
            central.bids = bids
            winner, bid = central.get_winner(bids)
            botwon = (winner.player_no == self.player_no)
            winner.coins -= bid
            #print(f"UP FOR AUCTION: {len(central.gems_available)}")

            count = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
            for curr_player in central.players:
                for (gem, revealed) in curr_player.hand:
                    if(curr_player.player_no == self.player_no):
                        count[gem.gem_type] +=1
                    elif(revealed): 
                        count[gem.gem_type] += 1

            curr_player = self.central.players[self.player_no]

            if(current_auction_card.type == "Loan"):
                if(botwon):
                    reward += 0.1*(current_auction_card.amount - bid)
                winner.coins += current_auction_card.amount
                winner.amount_to_add -= current_auction_card.amount
            elif(current_auction_card.type == "Invest"):
                winner.amount_to_add += bid + current_auction_card.amount
            elif(current_auction_card.type == "Treasure"):
                if(current_auction_card.amount == 1):
                    gem = central.gems_available.pop(0)
                    if(botwon): 
                        reward += 0.02*curr_player.coins
                        reward += 0.5*central.value_chart[count[gem.gem_type]]
                    winner.add_to_collection(gem)
                    central.draw_gem()
                elif(current_auction_card.amount == 2):
                    gem = central.gems_available.pop(0)
                    if(botwon):
                        reward += 0.02*curr_player.coins 
                        reward += 0.5*central.value_chart[count[gem.gem_type]]
                    winner.add_to_collection(gem)
                    central.draw_gem()
                    if(len(central.gems_available) > 0):
                        gem = central.gems_available.pop(0)
                        if(botwon): 
                            reward += 0.5*central.value_chart[count[gem.gem_type]]
                        winner.add_to_collection(gem)
                        central.draw_gem()
                missions_done = central.complete_possible_missions(winner)
                if(botwon):
                    for mission in missions_done:
                        reward += 1*mission.payout
            
            #curr_player = self.central.players[self.player_no]
            #reward += 0.01*curr_player.coins #+ 0.01*curr_player.amount_to_add
            if(winner.player_no == self.player_no and len(winner.get_revealed_cards()) != 5):
                return self.central.get_obs(player_no=self.player_no, mode=1, recurrent=self.recurrent), reward, False, False, {}
            else:
                central.draw_auction()
                if(winner.player_no != self.player_no): 
                    winner.reveal_card()
                terminated = False
                if(len(central.gems_available) == 0):
                    #print("This is running")
                    terminated = True
                #reward = 0
                if(terminated):
                    scores = central.compute_scores()
                    reward += 0.5*scores[self.player_no][1]
                    ranked = sorted(scores, key=lambda x: x[1], reverse=True)
                    for i in range(3):
                        if(ranked[i][0] == self.player_no):
                            if(i == 0):
                                print("Bot Won!")
                                reward += 50
                            elif(i == 1):
                                print("Bot got 2nd...")
                                reward += 20
                            elif(i == 2):
                                print("Bot lost :(")
                                reward -= 10
                return self.central.get_obs(player_no=self.player_no, mode=0, recurrent=self.recurrent), reward, terminated, False, {}

        elif(self.phase == 1): #Revealing phase
            central = self.central
            central.draw_auction()
            player = self.central.players[self.player_no]
            #print(f"I AM TRYING TO REVEAL {action}")
            player.reveal_card_by_color(action-96)
            self.phase = 0
            terminated = False
            if(len(central.gems_available) == 0):
                #print("This is running but the other one")
                terminated = True
            reward = 0
            if(action < 96 or action > 100):
                reward -= 10
            if(terminated):
                scores = central.compute_scores()
                reward += 0.5*scores[self.player_no][1]
                ranked = sorted(scores, key=lambda x: x[1], reverse=True)
                for i in range(3):
                    if(ranked[i][0] == self.player_no):
                        if(i == 0):
                            print("Bot Won!")
                            reward += 50
                        elif(i == 1):
                            print("Bot got 2nd...")
                            reward += 20
                        elif(i == 2):
                            print("Bot lost :(")
                            reward -= 10
            return self.central.get_obs(player_no=self.player_no, mode=0, recurrent=self.recurrent), reward, terminated, False, {}

    def action_masks(self):
        #print(f"action_masks called, phase={self.phase}, action will be applied next")
        curr_player = self.central.players[self.player_no]
        if(self.phase == 0):
            max_bid = curr_player.coins
            if(self.central.auction_deck[0].type == "Loan"):
                max_bid += self.central.auction_deck[0].amount
            mask = [True if i <= max_bid else False for i in range(101)]
            mask[0] = True #double check
            return mask
        elif(self.phase == 1):
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
        

