ALTER TABLE "registry_hit" ADD COLUMN "javaversion_id" integer REFERENCES "registry_javaversion" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_javaversion_id" ON "registry_hit" ("javaversion_id");

INSERT INTO registry_javaversion (version)
    (SELECT distinct( registry_hit.java_version)
    FROM registry_hit
    WHERE registry_hit.java_version is not null);

UPDATE registry_hit
    SET javaversion_id = registry_javaversion.id
FROM registry_javaversion
WHERE 
    registry_javaversion.version = registry_hit.java_version;

CREATE UNIQUE INDEX registry_javaversion_version_like_text ON registry_javaversion (version text_pattern_ops);
