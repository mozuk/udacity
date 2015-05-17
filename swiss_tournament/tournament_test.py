#!/usr/bin/env python
#
# Test cases for tournament.py

from tournament import *


# noinspection PyPep8Naming
def testDeleteMatches():
    deleteMatches()
    print("1. Old matches can be deleted.")


# noinspection PyPep8Naming
def testDelete():
    deleteMatches()
    deletePlayers()
    deleteTournaments()
    print("2. Player records can be deleted.")


# noinspection PyPep8Naming
def testCount():
    deleteMatches()
    deletePlayers()
    c = countPlayers()
    if c == '0':
        raise TypeError(
            "countPlayers() should return numeric zero, not string '0'.")
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print("3. After deleting, countPlayers() returns zero.")


# noinspection PyPep8Naming
def testRegister():
    deleteMatches()
    deletePlayers()
    deleteTournaments()
    # Create a bogus tournament for testing
    createTournament(name="WT 2015", info="The one and only Wombat tossing tournament of the gods (TM)")
    registerPlayer("Chandra Nalaar")
    c = countPlayers()
    if c != 1:
        raise ValueError(
            "After one player registers, countPlayers() should be 1.")
    print("4. After registering a player, countPlayers() returns 1.")


# noinspection PyPep8Naming
def testRegisterCountDelete():
    deleteMatches()
    deletePlayers()
    deleteTournaments()
    # Create a bogus tournament for testing
    createTournament(name="WT 2015", info="The one and only Wombat tossing tournament of the gods (TM)")
    registerPlayer("Markov Chaney")
    registerPlayer("Joe Malik")
    registerPlayer("Mao Tsu-hsi")
    registerPlayer("Atlanta Hope")
    c = countPlayers()
    if c != 4:
        raise ValueError(
            "After registering four players, countPlayers should be 4.")
    deletePlayers()
    c = countPlayers()
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print("5. Players can be registered and deleted.")


# noinspection PyPep8Naming
def testStandingsBeforeMatches():
    deleteMatches()
    deletePlayers()
    deleteTournaments()
    # Create a bogus tournament for testing
    createTournament(name="WT 2015", info="The one and only Wombat tossing tournament of the gods (TM)")
    registerPlayer("Melpomene Murray")
    registerPlayer("Randy Schwartz")
    standings = playerStandings()
    if len(standings) < 2:
        raise ValueError("Players should appear in playerStandings even before "
                         "they have played any matches.")
    elif len(standings) > 2:
        raise ValueError("Only registered players should appear in standings.")
    if len(standings[0]) != 4:
        raise ValueError("Each playerStandings row should have four columns.")
    [(id1, name1, wins1, matches1), (id2, name2, wins2, matches2)] = standings
    if matches1 != 0 or matches2 != 0 or wins1 != 0 or wins2 != 0:
        raise ValueError(
            "Newly registered players should have no matches or wins.")
    if {name1, name2} != {"Melpomene Murray", "Randy Schwartz"}:
        raise ValueError("Registered players' names should appear in standings, "
                         "even if they have no matches played.")
    print("6. Newly registered players appear in the standings with no matches.")


# noinspection PyPep8Naming
def testReportMatches():
    deleteMatches()
    deletePlayers()
    deleteTournaments()
    # Create a bogus tournament for testing
    createTournament(name="WT 2015", info="The one and only Wombat tossing tournament of the gods (TM)")
    registerPlayer("Bruno Walton")
    registerPlayer("Boots O'Neal")
    registerPlayer("Cathy Burton")
    registerPlayer("Diane Grant")
    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3, id4)
    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3) and w != 1:
            raise ValueError("Each match winner should have one win recorded.")
        elif i in (id2, id4) and w != 0:
            raise ValueError("Each match loser should have zero wins recorded.")
    print("7. After a match, players have updated standings.")


# noinspection PyPep8Naming
def testPairings():
    deleteMatches()
    deletePlayers()
    deleteTournaments()
    # Create a bogus tournament for testing
    createTournament(name="WT 2015", info="The one and only Wombat tossing tournament of the gods (TM)")
    registerPlayer("Twilight Sparkle")
    registerPlayer("Fluttershy")
    registerPlayer("Applejack")
    registerPlayer("Pinkie Pie")
    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2)
    reportMatch(id3, id4)
    pairings = swissPairings()
    if len(pairings) != 2:
        raise ValueError(
            "For four players, swissPairings should return two pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings
    correct_pairs = {frozenset([id1, id3]), frozenset([id2, id4])}
    actual_pairs = {frozenset([pid1, pid2]), frozenset([pid3, pid4])}
    if correct_pairs != actual_pairs:
        raise ValueError(
            "After one match, players with one win should be paired.")
    print("8. After one match, players with one win are paired.")


if __name__ == '__main__':
    testDeleteMatches()
    testDelete()
    testCount()
    testRegister()
    testRegisterCountDelete()
    testStandingsBeforeMatches()
    testReportMatches()
    testPairings()
    print("Success!  All tests pass!")


