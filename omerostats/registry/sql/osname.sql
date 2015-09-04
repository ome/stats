ALTER TABLE "registry_hit" ADD COLUMN "osname_id" integer REFERENCES "registry_osname" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_osname_id" ON "registry_hit" ("osname_id");

INSERT INTO registry_osname (name)
    (SELECT distinct( registry_hit.os_name)
    FROM registry_hit
    WHERE registry_hit.os_name is not null);

UPDATE registry_hit
    SET osname_id = registry_osname.id
FROM registry_osname
WHERE 
    registry_osname.name = registry_hit.os_name;

CREATE UNIQUE INDEX registry_osname_name_like_text ON registry_osname (name text_pattern_ops);
