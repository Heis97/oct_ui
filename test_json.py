import json
from dataclasses import dataclass, asdict

@dataclass
class Person:
    def __init__(self, name, value):
        self.name = name
        self.value = value


def save(_p1):    
    with open("my_object.json", "w", encoding="utf-8") as file:
        json.dump(_p1, file, indent=4) # indent для красивого форматирования

def load(file_name):
    with open("my_object.json", "r", encoding="utf-8") as file:
        loaded_dict = json.load(file)
    loaded_obj = Person(name=loaded_dict["name"], value=loaded_dict["value"])

    print(f"Имя: {loaded_obj.name}, Значение: {loaded_obj.value}")

obj = Person("Пример", 42)
obj_dict = obj.__dict__
save(obj_dict)

load("my_object.json")