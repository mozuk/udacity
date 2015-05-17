# Class to help sorting of player stats data into min_heap
class PlayerStats:
    def __init__(self, wins, matches, player_id, name):
        self.matches = matches
        self.wins = wins
        self.win_percent = (wins / matches) * 100
        self.player_id = player_id
        self.player_name = name

    def __lt__(self, other):
        return self.win_percent < other.win_percent

    def player_info(self):
        return "%s-%s: %.2f" % (self.player_id, self.player_name, self.win_percent)

    def __str__(self):
        return self.player_info()
