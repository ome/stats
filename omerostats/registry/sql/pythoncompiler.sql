ALTER TABLE "registry_hit" ADD COLUMN "pythoncompiler_id" integer REFERENCES "registry_pythoncompiler" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "registry_hit_pythoncompiler_id" ON "registry_hit" ("pythoncompiler_id");

INSERT INTO registry_pythoncompiler (name)
    (SELECT distinct( registry_hit.python_compiler)
    FROM registry_hit
    WHERE registry_hit.python_compiler is not null);

UPDATE registry_hit
    SET pythoncompiler_id = registry_pythoncompiler.id
FROM registry_pythoncompiler
WHERE 
    registry_pythoncompiler.name = registry_hit.python_compiler;

CREATE UNIQUE INDEX registry_pythoncompiler_name_like_text ON registry_pythoncompiler (name text_pattern_ops);
