class Asymmetry(object):
    """description of class"""
    def __init__(self, training_asymmetry=0, kinematic_asymmetry=0):
        self.training_asymmetry = 0
        self.kinematic_asymmetry = 0
        self.total_asymmetry = self.training_asymmetry+self.kinematic_asymmetry
        self.total_sum = 0

