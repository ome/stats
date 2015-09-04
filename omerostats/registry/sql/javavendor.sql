ALTER TABLE "registry_hit" ADD COLUMN "javavendor_id" integer REFERENCES "registry_javavendor" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_javavendor_id" ON "registry_hit" ("javavendor_id");

INSERT INTO registry_javavendor (name)
    (SELECT distinct( registry_hit.java_vendor)
    FROM registry_hit
    WHERE registry_hit.java_vendor is not null);

UPDATE registry_hit
    SET javavendor_id = registry_javavendor.id
FROM registry_javavendor
WHERE 
    registry_javavendor.name = registry_hit.java_vendor;

CREATE UNIQUE INDEX registry_javavendor_name_like_text ON registry_javavendor (name text_pattern_ops);
