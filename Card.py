class Card:
    def __init__(self, type, amount=0, gem_type="NONE"):
        self.type = type
        self.amount = amount
        self.gem_type = gem_type

    def __repr__(self):
        if(self.type == "Gem"):
            return f"{self.gem_type}"
        elif(self.type == "Treasure"):
            return f"Auction {self.amount} Gems"
        else:
            return f"Card: {self.type} Value: {self.amount}"
        
    def get_obs(self):
        obs = [0, 0]
        if(self.type == "Gem"):
            if(self.gem_type == "Pink"):
                obs[0] = 0
            elif(self.gem_type == "Green"):
                obs[0] = 1
            elif(self.gem_type == "Blue"):
                obs[0] = 2
            elif(self.gem_type == "Purple"):
                obs[0] = 3
            elif(self.gem_type == "Yellow"):
                obs[0] = 4
        elif(self.type == "Loan"):
            obs[0] = -1
            obs[1] = self.amount
        elif(self.type == "Invest"):
            obs[0] = -1
            obs[1] = -1*self.amount
        elif(self.type == "Treasure"):
            obs[0] = -2
            obs[1] = self.amount
            
        return obs

    