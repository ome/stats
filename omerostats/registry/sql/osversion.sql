ALTER TABLE "registry_hit" ADD COLUMN "osversion_id" integer REFERENCES "registry_osversion" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_osversion_id" ON "registry_hit" ("osversion_id");

INSERT INTO registry_osversion (version)
    (SELECT distinct( registry_hit.os_version)
    FROM registry_hit
    WHERE registry_hit.os_version is not null);

UPDATE registry_hit
    SET osversion_id = registry_osversion.id
FROM registry_osversion
WHERE 
    registry_osversion.version = registry_hit.os_version;

CREATE UNIQUE INDEX registry_osversion_version_like_text ON registry_osversion (version text_pattern_ops);
