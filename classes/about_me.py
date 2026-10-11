class AboutMe:
    def __init__(self, first_name: str, last_name: str, age: int, height: float) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.height = height
        self.is_happy = True

    def greet(self) -> None:
        happiness_status = "happy" if self.is_happy else "not happy"
        print(f"Hello, my name is {self.first_name} {self.last_name}. I am {self.age} years old and {self.height} meters tall.")