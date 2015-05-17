#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import heapq # Needed for min_heap sorting of players by winning percentage
from pairing import PlayerStats


def connect():
    """Connect to the PostgresSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=swiss_tournament_db")


# noinspection PyPep8Naming
def createTournament(name, info):
    db = connect()
    cursor = db.cursor()
    cursor.execute("insert into tournaments (name,information) values(%(name)s,%(info)s)",
                   {'name': name, 'info': info})
    db.commit()
    db.close()


# noinspection PyPep8Naming
def deleteTournaments():
    """Remove all the tournament records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute("delete from tournaments")
    db.commit()
    db.close()


# noinspection PyPep8Naming
def deleteMatches():
    """Remove all the match records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute("delete from matches")
    db.commit()
    db.close()


# noinspection PyPep8Naming
def deletePlayers():
    """Remove all the player records from the database."""
    db = connect()
    cursor = db.cursor()
    cursor.execute("delete from players")
    db.commit()
    db.close()


# noinspection PyPep8Naming
def countPlayers():
    """Returns the number of players currently registered."""
    db = connect()
    cursor = db.cursor()
    cursor.execute("select count(*) as number from players")
    count = cursor.fetchone()[0]
    db.close()
    return count


# noinspection PyPep8Naming
def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    db = connect()
    cursor = db.cursor()

    # Get tournament id. We should have only now for this demo project
    cursor.execute("select id from tournaments")
    tournament_id = cursor.fetchone()[0]

    # Register player on DB
    cursor.execute("insert into players (tournament_id,name) values( %(id)s, %(name)s)",
                   {'id': tournament_id, 'name': name})
    db.commit()
    db.close()


# noinspection PyPep8Naming
def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    db = connect()
    cursor = db.cursor()
    # Get total matches count and won count from predefined views
    cursor.execute(
        """
        select played_matches.id, played_matches.name, won_matches.win_count, played_matches.total_count
        from played_matches, won_matches
        where played_matches.id = won_matches.id
        """
    )
    standings = cursor.fetchall()
    db.close()
    return standings


# noinspection PyPep8Naming
def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    db = connect()
    cursor = db.cursor()

    # Get tournament id. We should have only now for this demo project
    cursor.execute("select id from tournaments")
    tournament_id = cursor.fetchone()[0]

    # Store the match data now
    cursor.execute("""insert into matches (tournament_id, winner_id, loser_id)
                   values( %(tournament_id)s, %(winner_id)s, %(loser_id)s)""",
                   {'winner_id': winner, 'loser_id': loser, 'tournament_id': tournament_id})
    db.commit()
    db.close()


# noinspection PyPep8Naming
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairing.py.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    players = []
    pairings = []
    standings = playerStandings()

    # let's sort players by win percentage
    for player_id, name, wins, matches in standings:
        players.append(PlayerStats(wins, matches, player_id, name))

    # make a min heap to sort the players by ranking as best as possible
    heapq.heapify(players)

    # loop through the sorted pairings and push each 2 players to their own match
    for index in range(0, len(players), 2):
        pairings.append((players[index].player_id,
                         players[index].player_name,
                         players[index + 1].player_id,
                         players[index + 1].player_name,
                         ))

    return pairings