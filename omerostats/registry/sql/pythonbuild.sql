ALTER TABLE "registry_hit" ADD COLUMN "pythonbuild_id" integer REFERENCES "registry_pythonbuild" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_pythonbuild_id" ON "registry_hit" ("pythonbuild_id");

INSERT INTO registry_pythonbuild (name)
    (SELECT distinct( registry_hit.python_build)
    FROM registry_hit
    WHERE registry_hit.python_build is not null);

UPDATE registry_hit
    SET pythonbuild_id = registry_pythonbuild.id
FROM registry_pythonbuild
WHERE 
    registry_pythonbuild.name = registry_hit.python_build;

CREATE UNIQUE INDEX registry_pythonbuild_name_like_text ON registry_pythonbuild (name text_pattern_ops);
