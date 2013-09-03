ALTER TABLE "registry_hit" ADD COLUMN "agentversion_id" integer REFERENCES "registry_agentversion" ("id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE registry_hit DROP COLUMN header;
ALTER TABLE registry_hit DROP COLUMN parsed_version;
ALTER TABLE registry_hit DROP COLUMN poll;

CREATE INDEX "registry_hit_agentversion_id" ON "registry_hit" ("agentversion_id");

INSERT INTO registry_agentversion (version)
    (SELECT distinct( registry_hit.agent_version)
    FROM registry_hit
    WHERE registry_hit.agent_version is not null);

UPDATE registry_hit
    SET agentversion_id = registry_agentversion.id
FROM registry_agentversion
WHERE 
    registry_agentversion.version = registry_hit.agent_version;

CREATE UNIQUE INDEX registry_agentversion_version_like_text ON registry_agentversion (version text_pattern_ops);
