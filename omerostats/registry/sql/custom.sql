DO
$do$
BEGIN
IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_agentversion
            ON (registry_agentversion.id = registry_hit.agentversion_id)
        WHERE registry_hit.agent_version IS NOT NULL
            AND registry_hit.agent_version != registry_agentversion.version) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN agent_version;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_javaversion
            ON (registry_javaversion.id = registry_hit.javaversion_id)
        WHERE registry_hit.java_version IS NOT NULL
            AND registry_hit.java_version != registry_javaversion.version) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN java_version;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_javavendor
            ON (registry_javavendor.id = registry_hit.javavendor_id)
        WHERE registry_hit.java_vendor IS NOT NULL
            AND registry_hit.java_vendor != registry_javavendor.name) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN java_vendor;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_osarch
            ON (registry_osarch.id = registry_hit.osarch_id)
        WHERE registry_hit.os_arch IS NOT NULL
            AND registry_hit.os_arch != registry_osarch.name) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN os_arch;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_osname
            ON (registry_osname.id = registry_hit.osname_id)
        WHERE registry_hit.os_name IS NOT NULL
            AND registry_hit.os_name != registry_osname.name) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN os_name;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_osversion
            ON (registry_osversion.id = registry_hit.osversion_id)
        WHERE registry_hit.os_version IS NOT NULL
            AND registry_hit.os_version != registry_osversion.version) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN os_version;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_pythonbuild
            ON (registry_pythonbuild.id = registry_hit.pythonbuild_id)
        WHERE registry_hit.python_build IS NOT NULL
            AND registry_hit.python_build != registry_pythonbuild.name) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN python_build;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_pythoncompiler
            ON (registry_pythoncompiler.id = registry_hit.pythoncompiler_id)
        WHERE registry_hit.python_compiler IS NOT NULL
            AND registry_hit.python_compiler != registry_pythoncompiler.name) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN python_compiler;
END IF;

IF ((SELECT count(*)
        FROM registry_hit
        INNER JOIN registry_pythonversion
            ON (registry_pythonversion.id = registry_hit.pythonversion_id)
        WHERE registry_hit.python_version IS NOT NULL
            AND registry_hit.python_version != registry_pythonversion.name) = 0
    ) THEN
   ALTER TABLE registry_hit DROP COLUMN python_version;
END IF;

END
$do$;
