ALTER TABLE "registry_ip" ADD COLUMN "continent_id" integer REFERENCES "registry_continent" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "registry_ip" ADD COLUMN "country_id" integer REFERENCES "registry_country" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "registry_ip" ADD COLUMN "city_id" integer REFERENCES "registry_city" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "registry_ip" ADD COLUMN "organisation_id" integer REFERENCES "registry_organisation" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "registry_ip" ADD COLUMN "domain_id" integer REFERENCES "registry_domain" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "registry_ip" ADD COLUMN "host_id" integer REFERENCES "registry_host" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "registry_ip" ADD COLUMN "suffix_id" integer REFERENCES "registry_suffix" ("id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE registry_ip DROP COLUMN country;

UPDATE registry_ip
    SET ip = '0.0.0.0'
WHERE "registry_ip"."ip" = 'unknown';

ALTER TABLE "registry_ip" ALTER COLUMN "ip" type inet using ip::inet;

CREATE INDEX "registry_ip_city_id" ON "registry_ip" ("city_id");
CREATE INDEX "registry_ip_country_id" ON "registry_ip" ("country_id");
CREATE INDEX "registry_ip_continent_id" ON "registry_ip" ("continent_id");
CREATE INDEX "registry_ip_organisation_id" ON "registry_ip" ("organisation_id");
CREATE INDEX "registry_ip_domain_id" ON "registry_ip" ("domain_id");
CREATE INDEX "registry_ip_host_id" ON "registry_ip" ("host_id");
CREATE INDEX "registry_ip_suffix_id" ON "registry_ip" ("suffix_id");

CREATE INDEX "registry_ip_ip_regex" ON "registry_ip" ( host("ip")); 