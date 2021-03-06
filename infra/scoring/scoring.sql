DROP TABLE IF EXISTS "scoring_scoreboard";
DROP MATERIALIZED VIEW IF EXISTS "scoring_scoreboard";

-- Scoreboard
CREATE MATERIALIZED VIEW "scoring_scoreboard" AS
WITH
  -- Seems very difficult to implement
  -- attackcount AS (
  --   SELECT count(*) as num_captured,
  --          capturing_team_id,
  -- 	   protecting_team_id,
  -- 	   service_id
  --   FROM scoring_capture
  --   INNER JOIN scoring_flag ON scoring_capture.flag_id = scoring_flag.id
  --   GROUP BY capturing_team_id, protecting_team_id, service_id
  -- ),
  attack AS (
    SELECT capturing_team_id as team_id,
           service_id,
           1000 * (sqrt(count(*)+4) - 2) as attack,
           0 as bonus -- skip the bonus stuff
    FROM scoring_capture
    INNER JOIN scoring_flag ON scoring_capture.flag_id = scoring_flag.id
    GROUP BY capturing_team_id, service_id
  ),
  flagdefense AS (
    SELECT DISTINCT scoring_flag.id,
           count(*) as score,
           scoring_flag.protecting_team_id as team_id,
	   scoring_flag.service_id as service_id
    FROM scoring_capture
    INNER JOIN scoring_flag ON scoring_capture.flag_id = scoring_flag.id
    -- only lose points from functional services
    INNER JOIN scoring_statuscheck ON
        scoring_flag.service_id = scoring_statuscheck.service_id AND
        scoring_flag.protecting_team_id = scoring_statuscheck.team_id AND
        scoring_capture.tick = scoring_statuscheck.tick
    WHERE scoring_statuscheck.status = 0 OR scoring_statuscheck.status = 4
    GROUP BY scoring_flag.id, scoring_flag.service_id
  ),
  defense AS (
    SELECT -50 * sum(score) as defense,
           team_id,
           service_id
    FROM flagdefense
    GROUP BY team_id, service_id
  ),
  sla_ok AS (
    SELECT count(*) as sla_ok,
           team_id,
           service_id
    FROM scoring_statuscheck
    WHERE status = 0
    GROUP BY team_id, service_id
  ),
  sla_recover AS (
    SELECT count(*) as sla_recover,
           team_id,
           service_id
    FROM scoring_statuscheck
    WHERE status = 4
    GROUP BY team_id, service_id
  ),
  sla AS (
    SELECT 100 * (coalesce(sla_ok, 0) + coalesce(sla_recover, 0)) as sla,
           team_id,
           service_id
    FROM sla_ok
    NATURAL FULL OUTER JOIN sla_recover
  ),
  teams as (
    SELECT user_id as team_id
    FROM registration_team
    INNER JOIN auth_user ON auth_user.id = registration_team.user_id
    WHERE is_active = true
    	  AND nop_team = false
  ),
  fill AS (
    SELECT team_id, scoring_service.id AS service_id
    FROM teams, scoring_service
  )
SELECT team_id,
       service_id,
       coalesce(attack, 0)::double precision as attack,
       coalesce(bonus, 0) as bonus,
       coalesce(defense, 0) as defense,
       coalesce(sla, 0) as sla,
       coalesce(attack, 0) + coalesce(defense, 0) + coalesce(bonus, 0) + coalesce(sla, 0) as total
FROM attack
NATURAL FULL OUTER JOIN defense
NATURAL FULL OUTER JOIN sla
NATURAL INNER JOIN fill
ORDER BY team_id, service_id;

ALTER MATERIALIZED VIEW scoring_scoreboard OWNER TO ctf_controller;
GRANT SELECT on TABLE scoring_scoreboard TO ctf_web;
