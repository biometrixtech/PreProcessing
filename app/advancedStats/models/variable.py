class categorization_variable(object):
    
    def __init__(self, name,  green_low, green_high,yellow_low, yellow_high,red_low, red_high,low_to_high_scale ):
        self.name = name
        self.green_low = green_low
        self.green_high = green_high
        self.yellow_low = yellow_low
        self.yellow_high = yellow_high
        self.red_low = red_low
        self.red_high = red_high
        self.invereted= (low_to_high_scale==True)
        


