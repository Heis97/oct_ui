from functools import reduce

def checksum(command:str):
        return reduce(lambda x, y: x ^ y, map(ord, command))
        
def gcodeCom(lineno:int,_command:str)->str:
    prefix = "N" + str(lineno) + " " + _command 
    command = prefix + "*" + str(checksum(prefix))
    return command


    

    

    
