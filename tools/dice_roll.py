import random

def roll_dice():
    player_dice = random.randint(1, 6)
    twin_dice = random.randint(1, 6)
    if player_dice > twin_dice:
        result = f"The player won by rolling a {player_dice}, beating the digital twin's {twin_dice}."
    elif player_dice < twin_dice:
        result = f"The digital twin won by rolling a {twin_dice}, higher than the player's {player_dice}."
    else:
        result = f"Both rolled {player_dice}. Ask the player to play again."
    return f"The result of the game was: {result}"