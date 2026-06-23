from Game import Game
from GameEnvTest import GameEnvTest
import gymnasium as gym
import numpy as np
import random

from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
import numpy as np
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.evaluation import evaluate_policy


def mask_fn(env: gym.Env) -> np.ndarray:
    # Do whatever you'd like in this function to return the action mask
    # for the current env. In this example, we assume the env has a
    # helpful method we can rely on.
    return env.action_masks()


env = GameEnvTest(bot1="megagem_agentv4_3", bot2="megagem_agentv4_4", recurrent=True)
#model = RecurrentPPO("MlpLstmPolicy", env=env, learning_rate=2.5e-4, verbose=1, gamma=0.99)
model = RecurrentPPO.load("megagem_agentvR2", env=env)
model.learning_rate = 2.5e-4
model.gamma = 0.99
model.learn(total_timesteps=200000)
model.save("megagem_agentvR2")

'''
opponents1 = ["megagem_agentv5_2_1"]
opponents2 = ["megagem_agent_antiv5_1"]
for i in range(10):
    if(i%2 == 0):
        env = GameEnvTest(opponents=opponents2)
        model = MaskablePPO.load(f"megagem_agentv5_2_{i//2 + 1}", env=env)
        model.learning_rate = 2.5e-4
        model.gamma = 0.99
        model.learn(total_timesteps=200000)
        model.save(f"megagem_agentv5_2_{i//2 + 2}")
        opponents1.append(f"megagem_agentv5_2_{i//2 + 2}")
    else:
        env = GameEnvTest(opponents=opponents1)
        model = MaskablePPO.load(f"megagem_agent_antiv5_{i//2 + 1}", env=env)
        model.learning_rate = 2.5e-4
        model.gamma = 0.99
        model.learn(total_timesteps=200000)
        model.save(f"megagem_agent_antiv5_{i//2 + 2}")
        opponents2.append(f"megagem_agent_antiv5_{i//2 + 2}")
'''


#opponents = ["random", "megagem_agentv2_4", "megagem_agentv3_1", "megagem_agentv4_1", "megagem_agentv4_3", "megagem_agentv4_4", "megagem_agentv4_5_3", "megagem_agentv4_5_4", "megagem_agentv4_6"]
#env = GameEnvTest(opponents=opponents)
#model = MaskablePPO("MlpPolicy", env, learning_rate=2.5e-4, verbose=1, gamma=0.99)
#model = MaskablePPO.load("megagem_agentv4_5_4", env=env)
#model.learning_rate = 2.5e-4
#model.gamma = 0.99
#model.learn(total_timesteps=600000)
#model.save("megagem_agentv5")


#for i in range(10):
    #print(f"Iteration {i}")
    #env = GameEnvTest()  # Initialize env
    ##model = MaskablePPO("MlpPolicy", env, learning_rate=2.5e-4, verbose=1, gamma=0.99)
    #model = MaskablePPO.load("megagem_agentv3_2", env=env)
    #model.learning_rate = 2.5e-4
    #model.gamma = 0.99
    #model.learn(total_timesteps=200000)
    #model.save("megagem_agentv3_2")

#v2_3 is easy (Overbids like crazy)
#v2_4 is easy-medium (still overbids, but not as much. It wins bids, but the overall game can be won easily)
#v2_5 is easy (underbids like crazy)
#v3_1 is 0.015*coin + 0.01*deferred_income trained off of v2_4. Became too conservative
#v3_2 is v2_4 with 0.01*coin and 1*mission, no deferred income signal. Then self-play a bunch of times
#It just bids 5 on everything, so it's really bad
#v4_1: Trains with V2_4 and an older version of itself. 0.02*coin only when a gem is won, 0.1*(loan amount - bid) when a loan is won (to curb overspending)
#Trained from V2_4. It is pretty conservative
#V4_2: Trained from scratch against V2_4 and V3_2 (which bids 5 on everything). Same reward model as V4_1
#Bids 6 on everything. LOL
#V4_3: Trained from scratch against V2_4 and V4_2. Same reward model as V4_1
#Bids 7 on Everything, with some exceptions
#V4_4: Trained from scratch against V2_4 and V2_3. Same reward model as V4_1
#Bids 8 on Everything, with some exceptions
#V4_5: Trained from V2_4 against V4_3 and V4_4. Same reward model as V4_1
#bids either 1 or 10, but seems to be learning which gems to value. Keep for further training
#V4_5_2: V4_5 with more training
#V4_5_3: V4_5_2 with more traininig at a 5e-4 learning rate. Trained x2
#V4_5_4: V4_5_3 with more training round at a 5e-4 learning rate. 
#V4_6: Trained from scratch against V4_3 and V4_4. Same reward model as V4_1
#unclear what its strategy is, seems to only bid between 6-8
#V5 - A new family of bots. trained from V4_5_4 against a diverse list of opponents to try and teach general strategy
#Same reward model as before.
#V5_2 - V5 trained against Anti-V5 in Fictitious self play
#Anti-V5 - Trained from scratch against V5 in Fictitious self play
#VR1 - Version 1 of RecurrentPPO. -10 penalty for invalid actions. Trained against V5 + Anti-V5 hard difficulty
#VR2 - RecurrentPPO. Trained from VR1 against V4_4 and V4_3 to teach it gem valuation (hopefully)
#Trained x2




