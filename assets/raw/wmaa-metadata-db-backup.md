

## Surviving MWAA Metadata Loss: Hard Lessons in Terraform and Airflow Migrations (Tech Blog)

If you manage infrastructure as code, you know the feeling. A seemingly innocuous pull request to update a resource name and bump a version number gets approved, merged, and applied. But in the world of Amazon Managed Workflows for Apache Airflow (MWAA), that simple rename can trigger a catastrophic data loss event.

**The Incident: When a Rename Becomes a Wipe**
Recently, we attempted to rename our MWAA environment (from `edr-sit-251` to `edr-sit-2112`) while simultaneously upgrading the Airflow version to v2.11.2 via Terraform. The deployment succeeded, the new webserver spun up, but the Airflow UI was completely empty. All historical DAG execution runs, task instance records, audit logs, and environment metadata were gone.

**What happened?** In AWS CloudFormation (and by extension, Terraform), the `Name` property of an `AWS::MWAA::Environment` is immutable. Changing it triggers a *Replacement* update behavior. CloudFormation provisions a brand-new environment, updates dependencies, and then **deletes the old environment**, taking its managed Aurora PostgreSQL metadata database with it.

Because AWS does not expose the underlying database snapshots to customers once an environment is deleted, the data is unrecoverable.

**The Right Way: Blue/Green Metadata Migration**
To safely navigate environment renames, cross-region disaster recovery, or massive version jumps, you must separate your operations and utilize a Blue/Green deployment strategy combined with metadata extraction.

**1. The Export Phase**
Before destroying the old environment, you must extract its state. Using the [official AWS migration guide](https://docs.aws.amazon.com/mwaa/latest/migrationguide/migrating-to-new-mwaa.html), you can deploy a custom DAG (`mwaa_export_data.py`). This DAG:

* Pauses all active workflows to ensure database consistency.
* Executes SQL queries to dump critical tables (`dag_run`, `task_instance`, `log`, `job`, `slot_pool`, `variable`, `connection`).
* Streams the output as CSV files to an encrypted Amazon S3 bucket.

**2. The Import Phase**
Once the new environment is fully provisioned, you deploy the `mwaa_import_data.py` DAG. This DAG pulls the CSVs from S3 and uses PostgreSQL's `COPY FROM STDIN` command to rapidly populate the fresh metadata database. Finally, it unpauses your workflows.

**Crucial Gotchas and Limitations**
Even with the official scripts, migrating Airflow metadata isn't seamless. Here are the risks you must plan for:

| Limitation | Details & Workarounds |
| --- | --- |
| **CloudWatch Logs Disconnect** | Historical task logs are stored in `airflow-{old_env_name}-Task`. The new environment will look for logs in a new log group. You will lose UI access to old logs, so you must query them directly in CloudWatch Logs Insights or export them separately. |
| **Fernet Encryption Issues** | Starting in Airflow 2.9.0, the `trigger` table uses a per-environment Fernet key. Importing triggers into a new environment will crash the scheduler. The latest AWS export/import scripts intentionally exclude this table. |
| **Dataset Tables** | In Airflow 2.9.2+, dataset tables are auto-generated and must be excluded from imports to avoid primary key collisions. |

When working with managed services like MWAA, infrastructure-as-code requires a deep understanding of resource lifecycles. An "in-place" upgrade only happens if the environment name remains completely untouched. For anything else, treat the database as ephemeral, implement robust S3-based backup DAGs, and always test your Terraform changes in a sandbox environment before touching production.