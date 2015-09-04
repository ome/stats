ALTER TABLE "registry_hit" ADD COLUMN "osarch_id" integer REFERENCES "registry_osarch" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_osarch_id" ON "registry_hit" ("osarch_id");

INSERT INTO registry_osarch (name)
    (SELECT distinct( registry_hit.os_arch)
    FROM registry_hit
    WHERE registry_hit.os_arch is not null);

UPDATE registry_hit
    SET osarch_id = registry_osarch.id
FROM registry_osarch
WHERE 
    registry_osarch.name = registry_hit.os_arch;

CREATE UNIQUE INDEX registry_osarch_name_like_text ON registry_osarch (name text_pattern_ops);
