-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP DATABASE IF EXISTS "tournament";

CREATE DATABASE "tournament";
\c "tournament";

-- tables
-- Table: matches
CREATE TABLE matches (
    id serial  NOT NULL,
    winner_id int  NOT NULL,
    loser_id int  NOT NULL,
    tournament_id int  NOT NULL,
    CONSTRAINT matches_pk PRIMARY KEY (id)
);


-- Table: players
CREATE TABLE players (
    id serial  NOT NULL,
    tournament_id int  NOT NULL,
    name text  NOT NULL,
    nickname text  NULL,
    CONSTRAINT players_pk PRIMARY KEY (id)
);


-- Table: tournaments
CREATE TABLE tournaments (
    id serial  NOT NULL,
    name text  NOT NULL,
    information text  NULL,
    CONSTRAINT tournaments_pk PRIMARY KEY (id)
);


-- views
-- View: played_matches
CREATE VIEW played_matches AS
select players.id, players.name, count(matches.id) as total_count
        from players left join matches
            on matches.winner_id = players.id
                or matches.loser_id = players.id
        group by players.id;


-- View: won_matches
CREATE VIEW won_matches AS
select players.id, players.name, count(matches.id) as win_count
        from players left join matches
             on matches.winner_id = players.id
        group by players.id;


-- foreign keys
-- Reference:  match_winner (table: matches)
ALTER TABLE matches ADD CONSTRAINT match_winner
    FOREIGN KEY (winner_id)
    REFERENCES players (id)
    NOT DEFERRABLE
;


-- Reference:  match_loser (table: matches)
ALTER TABLE matches ADD CONSTRAINT match_loser
    FOREIGN KEY (loser_id)
    REFERENCES players (id)
    NOT DEFERRABLE
;


-- Reference:  player_tournament (table: players)
ALTER TABLE players ADD CONSTRAINT player_tournament
    FOREIGN KEY (tournament_id)
    REFERENCES tournaments (id)
    NOT DEFERRABLE
;

-- Reference:  match_tournament (table: matches)
ALTER TABLE matches ADD CONSTRAINT match_tournament
    FOREIGN KEY (tournament_id)
    REFERENCES tournaments (id)
    NOT DEFERRABLE
;
-- End of file.