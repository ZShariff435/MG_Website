class Mission:
    def __init__(self, mission_type, payout, gem_list=None, gem_count=0):
        self.mission_type = mission_type
        self.payout = payout
        self.gem_list = gem_list
        self.gem_count = gem_count

    def __repr__(self):
        if(self.mission_type == "same"):
            return f"OBTAIN {self.gem_count} OF THE SAME GEM FOR {self.payout}"
        elif(self.mission_type == "different"):
            return f"OBTAIN {self.gem_count} DIFFERENT GEMS FOR {self.payout}"
        elif(self.mission_type == "pairs"):
            return f"OBTAIN {self.gem_count} DIFFERENT PAIRS OF GEMS FOR {self.payout}"
        elif(self.mission_type == "specific"):
            return f"OBTAIN THE FOLLOWING {self.gem_list} FOR {self.payout}"
        
    def get_obs(self):
        obs = [0, 0, 0, 0, 0, 0, 0]
        if(self.mission_type == "specific"):
            obs[0] = 0
            mission_amount = {"Pink": 0, "Green": 0, "Blue": 0, "Purple": 0, "Yellow": 0}
            for gem in self.gem_list:
                mission_amount[gem] += 1
            obs[1] = mission_amount["Pink"]
            obs[2] = mission_amount["Green"]
            obs[3] = mission_amount["Blue"]
            obs[4] = mission_amount["Purple"]
            obs[5] = mission_amount["Yellow"]
            obs[6] = self.payout
        elif(self.mission_type == "same"):
            obs[0] = 1
            obs[1] = obs[2] = obs[3] = obs[4] = obs[5] = self.gem_count
            obs[6] = self.payout
        elif(self.mission_type == "different"):
            obs[0] = 2
            obs[1] = obs[2] = obs[3] = obs[4] = obs[5] = self.gem_count
            obs[6] = self.payout
        elif(self.mission_type == "pairs"):
            obs[0] = 3
            obs[1] = obs[2] = obs[3] = obs[4] = obs[5] = self.gem_count
            obs[6] = self.payout
        return obs


        

        

    