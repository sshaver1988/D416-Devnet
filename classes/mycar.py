class Car:
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year

    def display_car(self):
        return f"{self.year} {self.make} {self.model}"

    def start_engine(self):
        return "The engine is starting."

    def stop_engine(self):
        return "The engine is stopping."