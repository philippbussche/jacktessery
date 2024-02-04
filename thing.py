class Thing:
    def __init__(self, name):
        self.name = name
        self.metrics = []
    def __str__(self):
        return self.name
    
    def add_metric(self, metric):
        self.metrics.append(metric)
        
    def get_metrics(self):
        return self.metrics
    
    def get_name(self):
        return self.name