CREATE TABLE IF NOT EXISTS teams (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    team_number TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

/* This table handles the many-to-many relation between teams and users */
CREATE TABLE IF NOT EXISTS users_teams (
    user_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    role    SMALLINT NOT NULL, -- 0: member, 1: admin - may add more
    PRIMARY KEY (user_id, team_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL  PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL, -- The password here is hashed
    salt        TEXT NOT NULL,
    team_id     INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scores (
    season               INTEGER NOT NULL,
    eventCode            TEXT NOT NULL,
    matchLevel           TEXT NOT NULL,
    matchSeries          INTEGER NOT NULL,
    matchNumber          INTEGER NOT NULL,
    alliance             TEXT,
    robot1Auto           TEXT NOT NULL,
    robot2Auto           TEXT NOT NULL,
    autoSampleNet        INTEGER NOT NULL,
    autoSampleLow        INTEGER NOT NULL,
    autoSampleHigh       INTEGER NOT NULL,
    autoSpecimenLow      INTEGER NOT NULL,
    autoSpecimenHigh     INTEGER NOT NULL,
    teleopSampleNet      INTEGER NOT NULL,
    teleopSampleLow      INTEGER NOT NULL,
    teleopSampleHigh     INTEGER NOT NULL,
    teleopSpecimenLow    INTEGER NOT NULL,
    teleopSpecimenHigh   INTEGER NOT NULL,
    robot1Teleop         TEXT NOT NULL,
    robot2Teleop         TEXT NOT NULL,
    minorFouls           INTEGER NOT NULL,
    majorFouls           INTEGER NOT NULL,
    autoSamplePoints     INTEGER NOT NULL,
    autoSpecimenPoints   INTEGER NOT NULL,
    teleopSamplePoints   INTEGER NOT NULL,
    teleopSpecimenPoints INTEGER NOT NULL,
    teleopParkPoints     INTEGER NOT NULL,
    teleopAscentPoints   INTEGER NOT NULL,
    autoPoints           INTEGER NOT NULL,
    teleopPoints         INTEGER NOT NULL,
    endGamePoints        INTEGER NOT NULL,
    foulPointsCommitted  INTEGER NOT NULL,
    preFoulTotal         INTEGER NOT NULL,
    totalPoints          INTEGER NOT NULL,
    team                 INTEGER NOT NULL,
    PRIMARY KEY (season, eventCode, matchLevel, matchSeries, matchNumber, alliance)
);

CREATE TABLE IF NOT EXISTS matches (
    season               INTEGER NOT NULL,
    eventCode            TEXT NOT NULL,
    actualStartTime      TEXT,
    description          TEXT,
    tournamentLevel      TEXT,
    series               INTEGER NOT NULL,
    matchNumber          INTEGER NOT NULL,
    scoreRedFinal        INTEGER NOT NULL,
    scoreRedFoul         INTEGER NOT NULL,
    scoreRedAuto         INTEGER NOT NULL,
    scoreBlueFinal       INTEGER NOT NULL,
    scoreBlueFoul        INTEGER NOT NULL,
    scoreBlueAuto        INTEGER NOT NULL,
    postResultTime       TEXT,
    teamNumber           INTEGER NOT NULL,
    station              TEXT,
    dq                   BOOLEAN NOT NULL,
    onField              BOOLEAN NOT NULL,
    modifiedOn           TEXT,
    PRIMARY KEY (season, eventCode, tournamentLevel, series, matchNumber, teamNumber, station, dq, onField)
);