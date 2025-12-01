class Parent:
    def __init__(self):
        self.setup()

    def setup(self):
        print("Parent setup")


class Child(Parent):
    def setup(self):
        print("Child setup")


c = Child()
