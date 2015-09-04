ALTER TABLE "registry_hit" ADD COLUMN "pythonversion_id" integer REFERENCES "registry_pythonversion" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_pythonversion_id" ON "registry_hit" ("pythonversion_id");

INSERT INTO registry_pythonversion (version)
    (SELECT distinct( registry_hit.python_version)
    FROM registry_hit
    WHERE registry_hit.python_version is not null);


UPDATE registry_hit
    SET pythonversion_id = registry_pythonversion.id
FROM registry_pythonversion
WHERE 
    registry_pythonversion.version = registry_hit.python_version;

CREATE UNIQUE INDEX registry_pythonversion_version_like_text ON registry_pythonversion (version text_pattern_ops);