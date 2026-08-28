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
    with open(file_name, "r", encoding="utf-8") as file:
        loaded_dict = json.load(file)
    return loaded_dict


obj = load("data_main7.json")

with open('my_file.txt', 'w') as file:
    num_st = 60
    alias = (obj[num_st][0]-obj[num_st-1][0])
    for i in range(num_st,len(obj)-num_st):
        res = (obj[i][0]-obj[i-1][0]) -  alias
        #if abs(res)<2500000:
        file.write(str(res)+'\n')


