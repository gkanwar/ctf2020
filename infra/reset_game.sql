-- Be VERY CAREFUL, this nukes all capture/tick/scoring data
DELETE FROM scoring_capture;
ALTER SEQUENCE scoring_capture_id_seq RESTART;
DELETE FROM scoring_flag;
ALTER SEQUENCE scoring_flag_id_seq RESTART;
DELETE FROM scoring_statuscheck;
ALTER SEQUENCE scoring_statuscheck_id_seq RESTART;
UPDATE scoring_gamecontrol SET current_tick=0;
REFRESH MATERIALIZED VIEW scoring_scoreboard;
