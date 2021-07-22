# Amundsen Databuilder

[![PyPI version](https://badge.fury.io/py/amundsen-databuilder.svg)](https://badge.fury.io/py/amundsen-databuilder)
[![License](http://img.shields.io/:license-Apache%202-blue.svg)](LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/amundsen-databuilder.svg)](https://pypi.org/project/amundsen-databuilder/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
[![Slack Status](https://img.shields.io/badge/slack-join_chat-white.svg?logo=slack&style=social)](https://amundsenworkspace.slack.com/join/shared_invite/enQtNTk2ODQ1NDU1NDI0LTc3MzQyZmM0ZGFjNzg5MzY1MzJlZTg4YjQ4YTU0ZmMxYWU2MmVlMzhhY2MzMTc1MDg0MzRjNTA4MzRkMGE0Nzk)

Amundsen Databuilder is a data ingestion library, which is inspired by [Apache Gobblin](https://gobblin.apache.org/). It could be used in an orchestration framework(e.g. Apache Airflow) to build data from Amundsen. You could use the library either with an adhoc python script([example](https://github.com/amundsen-io/amundsendatabuilder/blob/master/example/scripts/sample_data_loader.py)) or inside an Apache Airflow DAG([example](https://github.com/amundsen-io/amundsendatabuilder/blob/master/example/dags/hive_sample_dag.py)).

For information about Amundsen and our other services, visit the [main repository](https://github.com/amundsen-io/amundsen#amundsen) `README.md` . Please also see our instructions for a [quick start](https://github.com/amundsen-io/amundsen/blob/master/docs/installation.md#bootstrap-a-default-version-of-amundsen-using-docker) setup  of Amundsen with dummy data, and an [overview of the architecture](https://github.com/amundsen-io/amundsen/blob/master/docs/architecture.md#architecture).

## Requirements
- Python >= 3.6.x
- elasticsearch 6.x (currently it doesn't support 7.x)

## Doc
- https://www.amundsen.io/amundsen/

## Concept
ETL job consists of extraction of records from the source, transform records, if necessary, and load records into the sink. Amundsen Databuilder is a ETL framework for Amundsen and there are corresponding components for ETL called Extractor, Transformer, and Loader that deals with record level operation. A component called task controls all these three components.
Job is the highest level component in Databuilder that controls task and publisher and is the one that client use to launch the ETL job.

In Databuilder, each components are highly modularized and each components are using namespace based config, HOCON config, which makes it highly reusable and pluggable. (e.g: transformer can be reused within extractor, or extractor can be reused within extractor)
(Note that concept on components are highly motivated by [Apache Gobblin](https://gobblin.apache.org/ "Apache Gobblin"))

![Databuilder components](docs/assets/AmundsenDataBuilder.png?raw=true "Title")


### [Extractor](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/extractor "Extractor")
Extractor extracts record from the source. This does not neccessarily mean that it only supports [pull pattern](https://blogs.sap.com/2013/12/09/to-push-or-pull-that-is-the-question/ "pull pattern") in ETL. For example, extracting record from messaging bus make it a push pattern in ETL.

### [Transformer](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/transformer "Transformer")
Transfomer takes record from either extractor or from transformer itself (via ChainedTransformer) to transform record.

### [Loader](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/loader "Loader")
A loader takes record from transformer or from extractor directly and load it to sink, or staging area. As loader is operated in record level, it's not capable of supporting atomicity.

### [Task](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/task "Task")
A task orchestrates extractor, transformer, and loader to perform record level operation.

### [Record](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/models "Record")
A record is represented by one of [models](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/models "models").

### [Publisher](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/publisher "Publisher")
A publisher is an optional component. It's common usage is to support atomicity in job level and/or to easily support bulk load into the sink.

### [Job](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/job "Job")
Job is the highest level component in Databuilder, and it orchestrates task, and publisher.

## [Model](docs/models.md)
Models are abstractions representing the domain.

## List of extractors
#### [DBAPIExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/db_api_extractor.py "DBAPIExtractor")
An extractor that uses [Python Database API](https://www.python.org/dev/peps/pep-0249/ "Python Database API") interface. DBAPI requires three information, connection object that conforms DBAPI spec, a SELECT SQL statement, and a [model class](https://github.com/amundsen-io/amundsendatabuilder/tree/master/databuilder/models "model class") that correspond to the output of each row of SQL statement.

```python
job_config = ConfigFactory.from_dict({
        'extractor.dbapi{}'.format(DBAPIExtractor.CONNECTION_CONFIG_KEY): db_api_conn,
        'extractor.dbapi.{}'.format(DBAPIExtractor.SQL_CONFIG_KEY ): select_sql_stmt,
        'extractor.dbapi.model_class': 'package.module_name.class_name'
        })

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=DBAPIExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [GenericExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/generic_extractor.py "GenericExtractor")
An extractor that takes list of dict from user through config.

#### [HiveTableLastUpdatedExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/hive_table_last_updated_extractor.py "HiveTableLastUpdatedExtractor")
An extractor that extracts last updated time from Hive metastore and underlying file system. Although, hive metastore has a parameter called "last_modified_time", but it cannot be used as it provides DDL timestamp not DML timestamp.
For this reason, HiveTableLastUpdatedExtractor is utilizing underlying file of Hive to fetch latest updated date. However, it is not efficient to poke all files in Hive, and it only pokes underlying storage for non-partitioned table. For partitioned table, it will fetch partition created timestamp, and it's close enough for last updated timestamp.

As getting metadata from files could be time consuming there're several features to increase performance.
1. Support of multithreading to parallelize metadata fetching. Although, cpython's multithreading is not true multithreading as it's bounded by single core, getting metadata of file is mostly IO bound operation. Note that number of threads should be less or equal to number of connections.
1. User can pass where clause to only include certain schema and also remove certain tables. For example, by adding something like `TBL_NAME NOT REGEXP '(tmp|temp)` would eliminate unncecessary computation.

```python
job_config = ConfigFactory.from_dict({
    'extractor.hive_table_last_updated.partitioned_table_where_clause_suffix': partitioned_table_where_clause,
    'extractor.hive_table_last_updated.non_partitioned_table_where_clause_suffix'): non_partitioned_table_where_clause,
    'extractor.hive_table_last_updated.extractor.sqlalchemy.{}'.format(
            SQLAlchemyExtractor.CONN_STRING): connection_string,
    'extractor.hive_table_last_updated.extractor.fs_worker_pool_size': pool_size,
    'extractor.hive_table_last_updated.filesystem.{}'.format(FileSystem.DASK_FILE_SYSTEM): s3fs.S3FileSystem(
        anon=False,
        config_kwargs={'max_pool_connections': pool_size})})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=HiveTableLastUpdatedExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [HiveTableMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/hive_table_metadata_extractor.py "HiveTableMetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from Hive metastore database.
```python
job_config = ConfigFactory.from_dict({
    'extractor.hive_table_metadata.{}'.format(HiveTableMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.hive_table_metadata.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=HiveTableMetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [CassandraExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/cassandra_extractor.py "CassandraExtractor")
An extractor that extracts table and column metadata including keyspace, table name, column name and column type from Apache Cassandra databases

```python
job_config = ConfigFactory.from_dict({
    'extractor.cassandra.{}'.format(CassandraExtractor.CLUSTER_KEY): cluster_identifier_string,
    'extractor.cassandra.{}'.format(CassandraExtractor.IPS_KEY): [127.0.0.1],
    'extractor.cassandra.{}'.format(CassandraExtractor.KWARGS_KEY): {},
    'extractor.cassandra.{}'.format(CassandraExtractor.FILTER_FUNCTION_KEY): my_filter_function,

})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=CassandraExtractor(),
        loader=AnyLoader()))
job.launch()
```

If using the function filter options here is the function description
```python
def filter(keytab, table):
  # return False if you don't want to add that table and True if you want to add
  return True
```

If needed to define more args on the cassandra cluster you can pass through kwargs args
```python
config = ConfigFactory.from_dict({
    'extractor.cassandra.{}'.format(CassandraExtractor.IPS_KEY): [127.0.0.1],
    'extractor.cassandra.{}'.format(CassandraExtractor.KWARGS_KEY): {'port': 9042}
})
# it will call the cluster constructor like this
Cluster([127.0.0.1], **kwargs)
```

#### [GlueExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/glue_extractor.py "GlueExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from AWS Glue metastore.

Before running make sure you have a working AWS profile configured and have access to search tables on Glue
```python
job_config = ConfigFactory.from_dict({
    'extractor.glue.{}'.format(GlueExtractor.CLUSTER_KEY): cluster_identifier_string,
    'extractor.glue.{}'.format(GlueExtractor.FILTER_KEY): []})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=GlueExtractor(),
        loader=AnyLoader()))
job.launch()
```

If using the filters option here is the input format
```
[
  {
    "Key": "string",
    "Value": "string",
    "Comparator": "EQUALS"|"GREATER_THAN"|"LESS_THAN"|"GREATER_THAN_EQUALS"|"LESS_THAN_EQUALS"
  }
  ...
]
```

#### [Delta-Lake-MetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/delta_lake_metadata_extractor.py)
An extractor that runs on a spark cluster and obtains delta-lake metadata using spark sql commands.
This custom solution is currently necessary because the hive metastore does not contain all metadata information for delta-lake tables.
For simplicity, this extractor can also be used for all hive tables as well.

Because it must run on a spark cluster,
it is required that you have an operator (for example a [databricks submit run operator](https://airflow.apache.org/docs/stable/_modules/airflow/contrib/operators/databricks_operator.html))
that calls the configuration code on a spark cluster.
```python
spark = SparkSession.builder.appName("Amundsen Delta Lake Metadata Extraction").getOrCreate()
job_config = create_delta_lake_job_config()
dExtractor = DeltaLakeMetadataExtractor()
dExtractor.set_spark(spark)
job = DefaultJob(conf=job_config,
                 task=DefaultTask(extractor=dExtractor, loader=FsNeo4jCSVLoader()),
                 publisher=Neo4jCsvPublisher())
job.launch()
```
The delta lake extractor supports extraction of complex data types to be indexed and searchable. 
```
struct<a:int,b:string,c:array<struct<d:int,e:string>>,f:map<int,<struct<g:int,h:string>>>

Will be extracted as:
a     int
b     string
c     array<struct<d:int,e:string>>
c.d   int
c.e   string
f     map<int,<struct<g:int,h:string>>
f.g   int
f.h   string
```
This functionality is behind a configuration value. Simply set EXTRACT_NESTED_COLUMNS to True in the job config.

You can check out the sample deltalake metadata script for a full example.


#### [DremioMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/dremio_metadata_extractor.py)
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from [Dremio](https://www.dremio.com).

Before running make sure that you have the Dremio ODBC driver installed. Default config values assume the default driver name for the [MacBook install](https://docs.dremio.com/drivers/mac-odbc.html).
```python
job_config = ConfigFactory.from_dict({
    'extractor.dremio.{}'.format(DremioMetadataExtractor.DREMIO_USER_KEY): DREMIO_USER,
    'extractor.dremio.{}'.format(DremioMetadataExtractor.DREMIO_PASSWORD_KEY): DREMIO_PASSWORD,
    'extractor.dremio.{}'.format(DremioMetadataExtractor.DREMIO_HOST_KEY): DREMIO_HOST})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=DremioMetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [DruidMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/druid_metadata_extractor.py)
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from a [Druid](https://druid.apache.org/) DB.

The `where_clause_suffix` could be defined, normally you would like to filter out the in `INFORMATION_SCHEMA`.

You could specify the following job config
```python
conn_string = "druid+https://{host}:{port}/druid/v2/sql/".format(
        host=druid_broker_host,
        port=443
)
job_config = ConfigFactory.from_dict({
    'extractor.druid_metadata.{}'.format(PostgresMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
  'extractor.druid_metadata.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): conn_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=DruidMetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [OracleMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/oracle_metadata_extractor.py "OracleMetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from the Oracle database.

By default, the Oracle database name is used as the cluster name. To override this, set `USE_CATALOG_AS_CLUSTER_NAME` to `False`, and `CLUSTER_KEY` to what you wish to use as the cluster name.

The `where_clause_suffix` below should define which schemas you'd like to query. The SQL query driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/oracle_metadata_extractor.py)

```python
job_config = ConfigFactory.from_dict({
    'extractor.oracle_metadata.{}'.format(OracleMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.oracle_metadata.{}'.format(OracleMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME): True,
    'extractor.oracle_metadata.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=OracleMetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [PostgresMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/postgres_metadata_extractor.py "PostgresMetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from a Postgres or Redshift database.

By default, the Postgres/Redshift database name is used as the cluster name. To override this, set `USE_CATALOG_AS_CLUSTER_NAME`
to `False`, and `CLUSTER_KEY` to what you wish to use as the cluster name.

The `where_clause_suffix` below should define which schemas you'd like to query (see [the sample dag](https://github.com/amundsen-io/amundsendatabuilder/blob/master/example/dags/postgres_sample_dag.py) for an example).

The SQL query driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/postgres_metadata_extractor.py)

```python
job_config = ConfigFactory.from_dict({
    'extractor.postgres_metadata.{}'.format(PostgresMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.postgres_metadata.{}'.format(PostgresMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME): True,
    'extractor.postgres_metadata.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=PostgresMetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [MSSQLMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/mssql_metadata_extractor.py "PostgresMetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from a Microsoft SQL database.

By default, the Microsoft SQL Server Database name is used as the cluster name. To override this, set `USE_CATALOG_AS_CLUSTER_NAME`
to `False`, and `CLUSTER_KEY` to what you wish to use as the cluster name.

The `where_clause_suffix` below should define which schemas you'd like to query (`"('dbo','sys')"`).

The SQL query driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/mssql_metadata_extractor.py)

This extractor is highly derived from [PostgresMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/postgres_metadata_extractor.py "PostgresMetadataExtractor").
```python
job_config = ConfigFactory.from_dict({
    'extractor.mssql_metadata.{}'.format(MSSQLMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.mssql_metadata.{}'.format(MSSQLMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME): True,
    'extractor.mssql_metadata.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=MSSQLMetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [MysqlMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/mysql_metadata_extractor.py "MysqlMetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from a MYSQL database.

By default, the MYSQL database name is used as the cluster name. To override this, set `USE_CATALOG_AS_CLUSTER_NAME`
to `False`, and `CLUSTER_KEY` to what you wish to use as the cluster name.

The `where_clause_suffix` below should define which schemas you'd like to query.

The SQL query driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/mysql_metadata_extractor.py)

```python
job_config = ConfigFactory.from_dict({
    'extractor.mysql_metadata.{}'.format(MysqlMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.mysql_metadata.{}'.format(MysqlMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME): True,
    'extractor.mysql_metadata.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(conf=job_config,
                                 task=DefaultTask(extractor=MysqlMetadataExtractor(), loader=FsNeo4jCSVLoader()),
                                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### [Db2MetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/db2_metadata_extractor.py "Db2MetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from a Unix, Windows or Linux Db2 database or BigSQL.

The `where_clause_suffix` below should define which schemas you'd like to query or those that you would not (see [the sample data loader](https://github.com/amundsen-io/amundsendatabuilder/blob/master/example/sample_db2_data_loader.py) for an example).

The SQL query driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/db2_metadata_extractor.py)

```python
job_config = ConfigFactory.from_dict({
    'extractor.db2_metadata.{}'.format(Db2MetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.db2_metadata.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=Db2MetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [SnowflakeMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/snowflake_metadata_extractor.py "SnowflakeMetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from a Snowflake database.

By default, the Snowflake database name is used as the cluster name. To override this, set `USE_CATALOG_AS_CLUSTER_NAME`
to `False`, and `CLUSTER_KEY` to what you wish to use as the cluster name.

By default, the Snowflake database is set to `PROD`. To override this, set `DATABASE_KEY`
to `WhateverNameOfYourDb`.

By default, the Snowflake schema is set to `INFORMATION_SCHEMA`. To override this, set `SCHEMA_KEY`
to `WhateverNameOfYourSchema`.

Note that `ACCOUNT_USAGE` is a separate schema which allows users to query a wider set of data at the cost of latency.
Differences are defined [here](https://docs.snowflake.com/en/sql-reference/account-usage.html#differences-between-account-usage-and-information-schema)

The `where_clause_suffix` should define which schemas you'd like to query (see [the sample dag](https://github.com/amundsen-io/amundsendatabuilder/blob/master/example/scripts/sample_snowflake_data_loader.py) for an example).

The SQL query driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/snowflake_metadata_extractor.py)

```python
job_config = ConfigFactory.from_dict({
    'extractor.snowflake.{}'.format(SnowflakeMetadataExtractor.SNOWFLAKE_DATABASE_KEY): 'YourDbName',
    'extractor.snowflake.{}'.format(SnowflakeMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.snowflake.{}'.format(SnowflakeMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME): True,
    'extractor.snowflake.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=SnowflakeMetadataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [GenericUsageExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/generic_usage_extractor.py "GenericUsageExtractor")
An extractor that extracts table popularity metadata from a custom created Snowflake table (created by a script that may look like [this scala script](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/example/scripts/sample_snowflake_table_usage.scala "sample_snowflake_table_usage")). You can create a DAG using the [Databricks Operator](https://github.com/apache/airflow/blob/main/airflow/providers/databricks/operators/databricks.py) and run this script within Databricks or wherever you are able to run Scala.

By default, `snowflake` is used as the database name. `ColumnReader` has the datasource as its `database` input, and database as its `cluster` input.

The following inputs are related to where you create your Snowflake popularity table.

By default, the Snowflake popularity database is set to `PROD`. To override this, set `POPULARITY_TABLE_DATABASE`
to `WhateverNameOfYourDb`.

By default, the Snowflake popularity schema is set to `SCHEMA`. To override this, set `POPULARTIY_TABLE_SCHEMA`
to `WhateverNameOfYourSchema`.

By default, the Snowflake popularity table is set to `TABLE`. To override this, set `POPULARITY_TABLE_NAME`
to `WhateverNameOfYourTable`.

The `where_clause_suffix` should define any filtering you'd like to include in your query. For example, this may include `user_email`s that you don't want to include in your popularity definition.

```python
job_config = ConfigFactory.from_dict({
    f'extractor.generic_usage.extractor.sqlalchemy.{SQLAlchemyExtractor.CONN_STRING}': connection_string(),
    f'extractor.generic_usage.{GenericUsageExtractor.WHERE_CLAUSE_SUFFIX_KEY}': where_clause_suffix,
    f'extractor.generic_usage.{GenericUsageExtractor.POPULARITY_TABLE_DATABASE}': 'WhateverNameOfYourDb',
    f'extractor.generic_usage.{GenericUsageExtractor.POPULARTIY_TABLE_SCHEMA}': 'WhateverNameOfYourSchema',
    f'extractor.generic_usage.{GenericUsageExtractor.POPULARITY_TABLE_NAME}': 'WhateverNameOfYourTable',
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=GenericUsageExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [SnowflakeTableLastUpdatedExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/snowflake_table_last_updated_extractor.py "SnowflakeTableLastUpdatedExtractor")
An extractor that extracts table last updated timestamp from a Snowflake database.

It uses same configs as the `SnowflakeMetadataExtractor` described above.

The SQL query driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/snowflake_table_last_updated_extractor.py)

```python
job_config = ConfigFactory.from_dict({
    'extractor.snowflake_table_last_updated.{}'.format(SnowflakeTableLastUpdatedExtractor.SNOWFLAKE_DATABASE_KEY): 'YourDbName',
    'extractor.snowflake_table_last_updated.{}'.format(SnowflakeTableLastUpdatedExtractor.WHERE_CLAUSE_SUFFIX_KEY): where_clause_suffix,
    'extractor.snowflake_table_last_updated.{}'.format(SnowflakeTableLastUpdatedExtractor.USE_CATALOG_AS_CLUSTER_NAME): True,
    'extractor.snowflake_table_last_updated.extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string()})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=SnowflakeTableLastUpdatedExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [BigQueryMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/bigquery_metadata_extractor.py "BigQuery Metdata Extractor")
An extractor that extracts table and column metadata including database, schema, table name, table description, column name and column description from a Bigquery database.

The API calls driving the extraction is defined [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/bigquery_metadata_extractor.py)

You will need to create a service account for reading metadata and grant it "BigQuery Metadata Viewer" access to all of your datasets. This can all be done via the bigquery ui.

Download the creditials file and store it securely. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment varible to the location of your credtials files and your code should have access to everything it needs.

You can configure bigquery like this. You can optionally set a label filter if you only want to pull tables with a certain label.
```python
    job_config = {
        'extractor.bigquery_table_metadata.{}'.format(
            BigQueryMetadataExtractor.PROJECT_ID_KEY
            ): gcloud_project
    }
    if label_filter:
        job_config[
            'extractor.bigquery_table_metadata.{}'
            .format(BigQueryMetadataExtractor.FILTER_KEY)
            ] = label_filter
    task = DefaultTask(extractor=BigQueryMetadataExtractor(),
                       loader=csv_loader,
                       transformer=NoopTransformer())
    job = DefaultJob(conf=ConfigFactory.from_dict(job_config),
                     task=task,
                     publisher=Neo4jCsvPublisher())
job.launch()
```

#### [Neo4jEsLastUpdatedExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/neo4j_es_last_updated_extractor.py "Neo4jEsLastUpdatedExtractor")
An extractor that basically get current timestamp and passes it GenericExtractor. This extractor is basically being used to create timestamp for "Amundsen was last indexed on ..." in Amundsen web page's footer.

#### [Neo4jExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/neo4j_extractor.py "Neo4jExtractor")
An extractor that extracts records from Neo4j based on provided [Cypher query](https://neo4j.com/developer/cypher/ "Cypher query"). One example is to extract data from Neo4j so that it can transform and publish to Elasticsearch.
```python
job_config = ConfigFactory.from_dict({
    'extractor.neo4j.{}'.format(Neo4jExtractor.CYPHER_QUERY_CONFIG_KEY): cypher_query,
    'extractor.neo4j.{}'.format(Neo4jExtractor.GRAPH_URL_CONFIG_KEY): neo4j_endpoint,
    'extractor.neo4j.{}'.format(Neo4jExtractor.MODEL_CLASS_CONFIG_KEY): 'package.module.class_name',
    'extractor.neo4j.{}'.format(Neo4jExtractor.NEO4J_AUTH_USER): neo4j_user,
    'extractor.neo4j.{}'.format(Neo4jExtractor.NEO4J_AUTH_PW): neo4j_password},
    'extractor.neo4j.{}'.format(Neo4jExtractor.NEO4J_ENCRYPTED): True})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=Neo4jExtractor(),
        loader=AnyLoader()))
job.launch()
```
#### [Neo4jSearchDataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/neo4j_search_data_extractor.py "Neo4jSearchDataExtractor")
An extractor that is extracting Neo4j utilizing Neo4jExtractor where CYPHER query is already embedded in it.
```python
job_config = ConfigFactory.from_dict({
    'extractor.search_data.extractor.neo4j.{}'.format(Neo4jExtractor.GRAPH_URL_CONFIG_KEY): neo4j_endpoint,
    'extractor.search_data.extractor.neo4j.{}'.format(Neo4jExtractor.MODEL_CLASS_CONFIG_KEY): 'databuilder.models.neo4j_data.Neo4jDataResult',
    'extractor.search_data.extractor.neo4j.{}'.format(Neo4jExtractor.NEO4J_AUTH_USER): neo4j_user,
    'extractor.search_data.extractor.neo4j.{}'.format(Neo4jExtractor.NEO4J_AUTH_PW): neo4j_password},
    'extractor.search_data.extractor.neo4j.{}'.format(Neo4jExtractor.NEO4J_ENCRYPTED): False})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=Neo4jSearchDataExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [AtlasSearchDataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/atlas_search_data_extractor.py "AtlasSearchDataExtractor")
An extractor that is extracting Atlas Data to index compatible with Elasticsearch Search Proxy.
```python
entity_type = 'Table'
extracted_search_data_path = f'/tmp/{entity_type.lower()}_search_data.json'
process_pool_size = 5

# atlas config
atlas_url = 'localhost'
atlas_port = 21000
atlas_protocol = 'http'
atlas_verify_ssl = False
atlas_username = 'admin'
atlas_password = 'admin'
atlas_search_chunk_size = 200
atlas_details_chunk_size = 10

# elastic config
es = Elasticsearch([
    {'host': 'localhost'},
])

elasticsearch_client = es
elasticsearch_new_index_key = f'{entity_type.lower()}-' + str(uuid.uuid4())
elasticsearch_new_index_key_type = '_doc'
elasticsearch_index_alias = f'{entity_type.lower()}_search_index'

job_config = ConfigFactory.from_dict({
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_URL_CONFIG_KEY):
        atlas_url,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PORT_CONFIG_KEY):
        atlas_port,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PROTOCOL_CONFIG_KEY):
        atlas_protocol,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_VALIDATE_SSL_CONFIG_KEY):
        atlas_verify_ssl,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_USERNAME_CONFIG_KEY):
        atlas_username,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_PASSWORD_CONFIG_KEY):
        atlas_password,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_SEARCH_CHUNK_SIZE_KEY):
        atlas_search_chunk_size,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ATLAS_DETAILS_CHUNK_SIZE_KEY):
        atlas_details_chunk_size,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.PROCESS_POOL_SIZE_KEY):
        process_pool_size,
    'extractor.atlas_search_data.{}'.format(AtlasSearchDataExtractor.ENTITY_TYPE_KEY):
        entity_type,
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_PATH_CONFIG_KEY):
        extracted_search_data_path,
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_MODE_CONFIG_KEY):
        'w',
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.FILE_PATH_CONFIG_KEY):
        extracted_search_data_path,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.FILE_MODE_CONFIG_KEY):
        'r',
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_CLIENT_CONFIG_KEY):
        elasticsearch_client,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_NEW_INDEX_CONFIG_KEY):
        elasticsearch_new_index_key,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_DOC_TYPE_CONFIG_KEY):
        elasticsearch_new_index_key_type,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_ALIAS_CONFIG_KEY):
        elasticsearch_index_alias
})

if __name__ == "__main__":
    task = DefaultTask(extractor=AtlasSearchDataExtractor(),
                       transformer=NoopTransformer(),
                       loader=FSElasticsearchJSONLoader())

    job = DefaultJob(conf=job_config,
                     task=task,
                     publisher=ElasticsearchPublisher())

    job.launch()
```

#### [VerticaMetadataExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/vertica_metadata_extractor.py "MysqlMetadataExtractor")
An extractor that extracts table and column metadata including database, schema, table name, column name and column datatype from a Vertica database.

A sample loading script for Vertica is provided [here](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/databuilder/example/scripts/sample_vertica_loader.py)

By default, the Vertica database name is used as the cluster name. The `where_clause_suffix` in the example can be used to define which schemas you would like to query.



#### [SQLAlchemyExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/sql_alchemy_extractor.py "SQLAlchemyExtractor")
An extractor utilizes [SQLAlchemy](https://www.sqlalchemy.org/ "SQLAlchemy") to extract record from any database that support SQL Alchemy.
```python
job_config = ConfigFactory.from_dict({
    'extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.CONN_STRING): connection_string(),
    'extractor.sqlalchemy.{}'.format(SQLAlchemyExtractor.EXTRACT_SQL): sql,
    'extractor.sqlalchemy.model_class': 'package.module.class_name'})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=SQLAlchemyExtractor(),
        loader=AnyLoader()))
job.launch()
```

#### [DbtExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/dbt_extractor.py "SQLAlchemyExtractor")
This extractor utilizes the [dbt](https://www.getdbt.com/ "dbt") output files `catalog.json` and `manifest.json` to extract metadata and ingest it into Amundsen. The `catalog.json` and `manifest.json` can both be generated by running `dbt docs generate` in your dbt project. Visit the [dbt artifacts page](https://docs.getdbt.com/reference/artifacts/dbt-artifacts "dbt artifacts") for more information.

The `DbtExtractor` can currently create the following:

- Tables and their definitions
- Columns and their definitions
- Table level lineage
- dbt tags (as Amundsen badges or tags)
- Table Sources (e.g. link to GitHib where the dbt template resides)

```python
job_config = ConfigFactory.from_dict({
    # Required args
    f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': 'snowflake',
    f'extractor.dbt.{DbtExtractor.MANIFEST_JSON}': catalog_file_loc,  # File location
    f'extractor.dbt.{DbtExtractor.DATABASE_NAME}': json.dumps(manifest_data),  # JSON Dumped object
    # Optional args
    f'extractor.dbt.{DbtExtractor.SOURCE_URL}': 'https://github.com/your-company/your-repo/tree/main',
    f'extractor.dbt.{DbtExtractor.EXTRACT_TABLES}': True,
    f'extractor.dbt.{DbtExtractor.EXTRACT_DESCRIPTIONS}': True,
    f'extractor.dbt.{DbtExtractor.EXTRACT_TAGS}': True,
    f'extractor.dbt.{DbtExtractor.IMPORT_TAGS_AS}': 'badges',
    f'extractor.dbt.{DbtExtractor.EXTRACT_LINEAGE}': True,
})
job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=DbtExtractor(),
        loader=AnyLoader()))
job.launch()
```

### [RestAPIExtractor](./databuilder/extractor/restapi/rest_api_extractor.py)
A extractor that utilizes [RestAPIQuery](#rest-api-query) to extract data. RestAPIQuery needs to be constructed ([example](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_extractor.py#L40)) and needs to be injected to RestAPIExtractor.

### Mode Dashboard Extractor
Here are extractors that extracts metadata information from Mode via Mode's REST API.

Prerequisite:

 1. You will need to [create API access token](https://mode.com/developer/api-reference/authentication/) that has admin privilege.
 2. You will need organization code. This is something you can easily get by looking at one of Mode report's URL.
     `https://app.mode.com/<organization code>/reports/report_token`

#### [ModeDashboardExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_extractor.py)
A Extractor that extracts core metadata on Mode dashboard. https://app.mode.com/

It extracts list of reports that consists of:
Dashboard group name (Space name)
Dashboard group id (Space token)
Dashboard group description (Space description)
Dashboard name (Report name)
Dashboard id (Report token)
Dashboard description (Report description)

Other information such as report run, owner, chart name, query name is in separate extractor.

It calls two APIs ([spaces API](https://mode.com/developer/discovery-api/analytics/spaces/) and [reports API](https://mode.com/developer/discovery-api/analytics/reports/)) joining together.

You can create Databuilder job config like this.
```python
task = DefaultTask(extractor=ModeDashboardExtractor(),
                   loader=FsNeo4jCSVLoader(), )

tmp_folder = '/var/tmp/amundsen/mode_dashboard_metadata'
node_files_folder = '{tmp_folder}/nodes'.format(tmp_folder=tmp_folder)
relationship_files_folder = '{tmp_folder}/relationships'.format(tmp_folder=tmp_folder)

job_config = ConfigFactory.from_dict({
    'extractor.mode_dashboard.{}'.format(ORGANIZATION): organization,
    'extractor.mode_dashboard.{}'.format(MODE_BEARER_TOKEN): mode_bearer_token,
    'extractor.mode_dashboard.{}'.format(DASHBOARD_GROUP_IDS_TO_SKIP): [space_token_1, space_token_2, ...],
    'loader.filesystem_csv_neo4j.{}'.format(FsNeo4jCSVLoader.NODE_DIR_PATH): node_files_folder,
    'loader.filesystem_csv_neo4j.{}'.format(FsNeo4jCSVLoader.RELATION_DIR_PATH): relationship_files_folder,
    'loader.filesystem_csv_neo4j.{}'.format(FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR): True,
    'task.progress_report_frequency': 100,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NODE_FILES_DIR): node_files_folder,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.RELATION_FILES_DIR): relationship_files_folder,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_END_POINT_KEY): neo4j_endpoint,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_USER): neo4j_user,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_PASSWORD): neo4j_password,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_ENCRYPTED): True,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_CREATE_ONLY_NODES): [DESCRIPTION_NODE_LABEL],
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.JOB_PUBLISH_TAG): job_publish_tag
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```


#### [ModeDashboardOwnerExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_owner_extractor.py)
An Extractor that extracts Dashboard owner. Mode itself does not have concept of owner and it will use creator as owner. Note that if user left the organization, it would skip the dashboard.

You can create Databuilder job config like this. (configuration related to loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#ModeDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = ModeDashboardOwnerExtractor()
task = DefaultTask(extractor=extractor,
                   loader=FsNeo4jCSVLoader(), )

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_BEARER_TOKEN): mode_bearer_token,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### [ModeDashboardLastSuccessfulExecutionExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_last_successful_executions_extractor.py)
A Extractor that extracts Mode dashboard's last successful run (execution) timestamp.

You can create Databuilder job config like this. (configuration related to loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#ModeDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = ModeDashboardLastSuccessfulExecutionExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_BEARER_TOKEN): mode_bearer_token,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### [ModeDashboardExecutionsExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_executions_extractor.py)
A Extractor that extracts last run (execution) status and timestamp.

You can create Databuilder job config like this. (configuration related to loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#ModeDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = ModeDashboardExecutionsExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_BEARER_TOKEN): mode_bearer_token,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### [ModeDashboardLastModifiedTimestampExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_last_modified_timestamp_extractor.py)
A Extractor that extracts Mode dashboard's last modified timestamp.

You can create Databuilder job config like this. (configuration related to loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#ModeDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = ModeDashboardLastModifiedTimestampExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_BEARER_TOKEN): mode_bearer_token,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### [ModeDashboardQueriesExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_queries_extractor.py)
A Extractor that extracts Mode's query information.

You can create Databuilder job config like this. (configuration related to loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#ModeDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = ModeDashboardQueriesExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_BEARER_TOKEN): mode_bearer_token,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### [ModeDashboardChartsBatchExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_charts_batch_extractor.py)
A Extractor that extracts Mode Dashboard charts metadata.

You can create Databuilder job config like this. (configuration related to loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#ModeDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = ModeDashboardChartsBatchExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_BEARER_TOKEN): mode_bearer_token,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```


#### [ModeDashboardUserExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_user_extractor.py)
A Extractor that extracts Mode user_id and then update User node.

You can create Databuilder job config like this. (configuration related to loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#ModeDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = ModeDashboardUserExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_ACCESS_TOKEN): mode_token,
    '{}.{}'.format(extractor.get_scope(), MODE_PASSWORD_TOKEN): mode_password,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### [ModeDashboardUsageExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_usage_extractor.py)

A Extractor that extracts Mode dashboard's accumulated view count.

Note that this provides accumulated view count which does [not effectively show relevancy](./docs/dashboard_ingestion_guide.md#21-ingest-dashboard-usage-data-and-decorate-neo4j-over-base-data). Thus, fields from this extractor is not directly compatible with [DashboardUsage](./docs/models.md#dashboardusage) model.

If you are fine with `accumulated usage`, you could use TemplateVariableSubstitutionTransformer to transform Dict payload from [ModeDashboardUsageExtractor](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_usage_extractor.py) to fit [DashboardUsage](./docs/models.md#dashboardusage) and transform Dict to  [DashboardUsage](./docs/models.md#dashboardusage) by [TemplateVariableSubstitutionTransformer](./databuilder/transformer/template_variable_substitution_transformer.py), and [DictToModel](./databuilder/transformer/dict_to_model.py) transformers. ([Example](./databuilder/extractor/dashboard/mode_analytics/mode_dashboard_queries_extractor.py#L36) on how to combining these two transformers)


### [RedashDashboardExtractor](./databuilder/extractor/dashboard/redash/redash_dashboard_extractor.py)

The included `RedashDashboardExtractor` provides support for extracting basic metadata for Redash dashboards (dashboard name, owner, URL, created/updated timestamps, and a generated description) and their associated queries (query name, URL, and raw query). It can be extended with a configurable table parser function to also support extraction of `DashboardTable` metadata. (See below for example usage.)

Note: `DashboardUsage` and `DashboardExecution` metadata are not supported in this extractor, as these concepts are not supported by the Redash API.

The `RedashDashboardExtractor` depends on the following Redash API endpoints: `GET /api/dashboards`, `GET /api/dashboards/<dashboard-slug>`. It has been tested against Redash 8 and is also expected to work with Redash 9.

```python
extractor = RedashDashboardExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    'extractor.redash_dashboard.redash_base_url': redash_base_url, # ex: https://redash.example.org
    'extractor.redash_dashboard.api_base_url': api_base_url, # ex: https://redash.example.org/api
    'extractor.redash_dashboard.api_key': api_key, # ex: abc1234
    'extractor.redash_dashboard.table_parser': table_parser, # ex: my_library.module.parse_tables
    'extractor.redash_dashboard.redash_version': redash_version # ex: 8. optional, default=9
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

#### RedashDashboardExtractor: table_parser

The `RedashDashboardExtractor` extracts raw queries from each dashboard. You may optionally use these queries to parse out relations to tables in Amundsen. A table parser can be provided in the configuration for the `RedashDashboardExtractor`, as seen above. This function should have type signature `(RedashVisualizationWidget) -> Iterator[TableRelationData]`. For example:

```python
def parse_tables(viz_widget: RedashVisualizationWidget) -> Iterator[TableRelationData]:
    # Each viz_widget corresponds to one query.
    # viz_widget.data_source_id is the ID of the target DB in Redash.
    # viz_widget.raw_query is the raw query (e.g., SQL).
    if viz_widget.data_source_id == 123:
        table_names = some_sql_parser(viz_widget.raw_query)
        return [TableRelationData('some_db', 'prod', 'some_schema', tbl) for tbl in table_names]
    return []
```

### [TableauDashboardExtractor](./databuilder/extractor/dashboard/tableau/tableau_dashboard_extractor.py)

The included `TableauDashboardExtractor` provides support for extracting basic metadata for Tableau workbooks. All Tableau extractors including this one use the [Tableau Metadata GraphQL API](https://help.tableau.com/current/api/metadata_api/en-us/index.html) to gather the metadata. Tableau "workbooks" are mapped to Amundsen dashboards, and the top-level project in which these workbooks preside is the dashboard group. The metadata it gathers is as follows:
- Dashboard name (Workbook name)
- Dashboard description (Workbook description)
- Dashboard creation timestamp (Workbook creation timestamp)
- Dashboard group name (Workbook top-level folder name)
- Dashboard and dashboard group URL

If you wish to exclude top-level projects from being loaded, specify their names in the `tableau_excluded_projects` list and workbooks from any of those projects will not be indexed.

Tableau's concept of "owners" does not map cleanly into Amundsen's understanding of owners, as the owner of a Tableau workbook is simply whoever updated it last, even if they made a very small change. This can prove problematic in determining the true point of contact for a workbook, so it's simply omitted for now. Similarly, the hierachy of `dashboard/query/chart` in Amundsen does not map into Tableau, where `charts` have only an optional relation to queries and vice versa. For these reasons, there are not extractors for either entity.

The Tableau Metadata API also does not support usage or execution statistics, so there are no extractors for these entities either.

Sample job config:
```python
extractor = TableauDashboardExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    'extractor.tableau_dashboard_metadata.tableau_host': tableau_host,
    'extractor.tableau_dashboard_metadata.api_version': tableau_api_version,
    'extractor.tableau_dashboard_metadata.site_name': tableau_site_name,
    'extractor.tableau_dashboard_metadata.tableau_personal_access_token_name': tableau_personal_access_token_name,
    'extractor.tableau_dashboard_metadata.tableau_personal_access_token_secret': tableau_personal_access_token_secret,
    'extractor.tableau_dashboard_metadata.excluded_projects': tableau_excluded_projects,
    'extractor.tableau_dashboard_metadata.cluster': tableau_dashboard_cluster,
    'extractor.tableau_dashboard_metadata.database': tableau_dashboard_database,
    'extractor.tableau_dashboard_metadata.transformer.timestamp_str_to_epoch.timestamp_format': "%Y-%m-%dT%H:%M:%SZ",
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

### [TableauDashboardTableExtractor](./databuilder/extractor/dashboard/tableau/tableau_dashboard_table_extractor.py)

The included `TableauDashboardTableExtractor` provides support for extracting table metadata from Tableau workbooks. The extractor assumes all the table entities have already been created; if you are interested in using the provided `TableauExternalTableExtractor`, make sure that job runs before this one, as it will create the tables required by this job. It also assumes that the dashboards are using their names as the primary ID.

A sample job config is shown below. Configuration related to the loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#TableauDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = TableauDashboardTableExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    'extractor.tableau_dashboard_table.tableau_host': tableau_host,
    'extractor.tableau_dashboard_table.api_version': tableau_api_version,
    'extractor.tableau_dashboard_table.site_name': tableau_site_name,
    'extractor.tableau_dashboard_table.tableau_personal_access_token_name': tableau_personal_access_token_name,
    'extractor.tableau_dashboard_table.tableau_personal_access_token_secret': tableau_personal_access_token_secret,
    'extractor.tableau_dashboard_table.excluded_projects': tableau_excluded_projects,
    'extractor.tableau_dashboard_table.cluster': tableau_dashboard_cluster,
    'extractor.tableau_dashboard_table.database': tableau_dashboard_database,
    'extractor.tableau_dashboard_table.external_cluster_name': tableau_external_table_cluster,
    'extractor.tableau_dashboard_table.external_schema_name': tableau_external_table_schema,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

### [TableauDashboardQueryExtractor](./databuilder/extractor/dashboard/tableau/tableau_dashboard_query_extractor.py)

The included `TableauDashboardQueryExtractor` provides support for extracting query metadata from Tableau workbooks. It retrives the name and query text for each custom SQL query.

A sample job config is shown below. Configuration related to the loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#TableauDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = TableauDashboardQueryExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    'extractor.tableau_dashboard_query.tableau_host': tableau_host,
    'extractor.tableau_dashboard_query.api_version': tableau_api_version,
    'extractor.tableau_dashboard_query.site_name': tableau_site_name,
    'extractor.tableau_dashboard_query.tableau_personal_access_token_name': tableau_personal_access_token_name,
    'extractor.tableau_dashboard_query.tableau_personal_access_token_secret': tableau_personal_access_token_secret,
    'extractor.tableau_dashboard_query.excluded_projects': tableau_excluded_projects,
    'extractor.tableau_dashboard_query.cluster': tableau_dashboard_cluster,
    'extractor.tableau_dashboard_query.database': tableau_dashboard_database,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

### [TableauDashboardLastModifiedExtractor](./databuilder/extractor/dashboard/tableau/tableau_dashboard_last_modified_extractor.py)

The included `TableauDashboardLastModifiedExtractor` provides support for extracting the last updated timestamp for Tableau workbooks.

A sample job config is shown below. Configuration related to the loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#TableauDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = TableauDashboardQueryExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    'extractor.tableau_dashboard_last_modified.tableau_host': tableau_host,
    'extractor.tableau_dashboard_last_modified.api_version': tableau_api_version,
    'extractor.tableau_dashboard_last_modified.site_name': tableau_site_name,
    'extractor.tableau_dashboard_last_modified.tableau_personal_access_token_name': tableau_personal_access_token_name,
    'extractor.tableau_dashboard_last_modified.tableau_personal_access_token_secret': tableau_personal_access_token_secret,
    'extractor.tableau_dashboard_last_modified.excluded_projects': tableau_excluded_projects,
    'extractor.tableau_dashboard_last_modified.cluster': tableau_dashboard_cluster,
    'extractor.tableau_dashboard_last_modified.database': tableau_dashboard_database,
    'extractor.tableau_dashboard_last_modified.transformer.timestamp_str_to_epoch.timestamp_format': "%Y-%m-%dT%H:%M:%SZ",
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

### [TableauExternalTableExtractor](./databuilder/extractor/dashboard/tableau/tableau_external_table_extractor.py)

The included `TableauExternalTableExtractor` provides support for extracting external table entities referenced by Tableau workbooks. In this context, "external" tables are "tables" that are not from a typical database, and are loaded using some other data format, like CSV files.
This extractor has been tested with the following types of external tables; feel free to add others, but it's recommended
to test them in a non-production instance first to be safe.
- Excel spreadsheets
- Text files (including CSV files)
- Salesforce connections
- Google Sheets connections

Use the `external_table_types` list config option to specify which external connection types you would like to index;
refer to your Tableau instance for the exact formatting of each connection type string.

Excel spreadsheets, Salesforce connections, and Google Sheets connections are all classified as
"databases" in terms of Tableau's Metadata API, with their "subsheets" forming their "tables" when
present. However, these tables are not assigned a schema, this extractor chooses to use the name
of the parent sheet as the schema, and assign a new table to each subsheet. The connection type is
always used as the database, and for text files, the schema is set using the `external_schema_name`
config option. Since these external tables are usually named for human consumption only and often
contain a wider range of characters, all inputs are sanitized to remove any problematic
occurences before they are inserted: see the `sanitize` methods `TableauDashboardUtils` for specifics.

A more concrete example: if one had a Google Sheet titled "Growth by Region" with 2 subsheets called
"FY19 Report" and "FY20 Report", two tables would be generated with the following keys:
`googlesheets://external.growth_by_region/FY_19_Report`
`googlesheets://external.growth_by_region/FY_20_Report`

A sample job config is shown below. Configuration related to the loader and publisher is omitted as it is mostly the same. Please take a look at this [example](#TableauDashboardExtractor) for the configuration that holds loader and publisher.

```python
extractor = TableauExternalTableExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    'extractor.tableau_external_table.tableau_host': tableau_host,
    'extractor.tableau_external_table.api_version': tableau_api_version,
    'extractor.tableau_external_table.site_name': tableau_site_name,
    'extractor.tableau_external_table.tableau_personal_access_token_name': tableau_personal_access_token_name,
    'extractor.tableau_external_table.tableau_personal_access_token_secret': tableau_personal_access_token_secret,
    'extractor.tableau_external_table.excluded_projects': tableau_excluded_projects,
    'extractor.tableau_external_table.cluster': tableau_dashboard_cluster,
    'extractor.tableau_external_table.database': tableau_dashboard_database,
    'extractor.tableau_external_table.external_cluster_name': tableau_external_table_cluster,
    'extractor.tableau_external_table.external_schema_name': tableau_external_table_schema,
    'extractor.tableau_external_table.external_table_types': tableau_external_table_types
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

### [ApacheSupersetMetadataExtractor](./databuilder/extractor/dashboard/apache_superset/apache_superset_metadata_extractor.py)

The included `ApacheSupersetMetadataExtractor` provides support for extracting basic metadata for Apache Superset dashboards.

All Apache Superset extractors including this one use Apache Superset REST API (`/api/v1`) and were developed based on Apache Superset version `1.1`.

##### Caution!

Apache Superset does not contain metadata fulfilling the concept of `DashboardGroup`. For that reasons, when configuring extractor following parameters must be provided:
- dashboard_group_id (required)
- dashboard_group_name (required)
- cluster (required)
- dashboard_group_description (optional)

#### DashboardMetadata

`ApacheSupersetMetadataExtractor` extracts metadata into `DashboardMetadata` model.

##### Metadata available in REST API

- Dashboard id (id)
- Dashboard name (dashboard_title)
- Dashboard URL (url)

##### Metadata not available in Apache Superset REST API

- Dashboard description
- Dashboard creation timestamp

#### DashboardLastModifiedTimestamp

`ApacheSupersetLastModifiedTimestampExtractor` extracts metadata into `DashboardLastModifiedTimestamp` model.

##### Available in REST API

- Dashboard last modified timestamp (changed_on property of dashboard)

###### Caution!

`changed_on` value does not provide timezone info so we assume it's UTC.

#### Sample job config

```python
tmp_folder = f'/tmp/amundsen/dashboard'

dict_config = {
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': f'{tmp_folder}/nodes',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': f'{tmp_folder}/relationships',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_ID}': '1',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_NAME}': 'dashboard group',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_DESCRIPTION}': 'dashboard group description',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.CLUSTER}': 'gold',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.APACHE_SUPERSET_SECURITY_SETTINGS_DICT}': dict(
        username='admin',
        password='admin',
        provider='db')
}

job_config = ConfigFactory.from_dict(dict_config)

task = DefaultTask(extractor=ApacheSupersetMetadataExtractor(), loader=FsNeo4jCSVLoader())

job = DefaultJob(conf=job_config,
                 task=task)

job.launch()
```

### [ApacheSupersetTableExtractor](./databuilder/extractor/dashboard/apache_superset/apache_superset_table_extractor.py)

The included `ApacheSupersetTableExtractor` provides support for extracting relationships between dashboards and tables. All Apache Superset extractors including this one use Apache Superset REST API (`api/v1`).

##### Caution!

As table information in Apache Superset is minimal, following configuration options enable parametrization required to achieve proper relationship information:
- `driver_to_database_mapping` - mapping between sqlalchemy `drivername` and actual `database` property of `TableMetadata` model.
- `database_to_cluster_mapping` - mapping between Apache Superset Database ID and `cluster` from `TableMedata` model (defaults to `cluster` config of `extractor.apache_superset`)

#### DashboardTable

##### Metadata available in REST API

- Table keys

#### Sample job config

```python
tmp_folder = f'/tmp/amundsen/dashboard'

dict_config = {
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': f'{tmp_folder}/nodes',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': f'{tmp_folder}/relationships',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_ID}': '1',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_NAME}': 'dashboard group',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_DESCRIPTION}': 'dashboard group description',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.CLUSTER}': 'gold',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.APACHE_SUPERSET_SECURITY_SETTINGS_DICT}': dict(
        username='admin',
        password='admin',
        provider='db')
}

job_config = ConfigFactory.from_dict(dict_config)

task = DefaultTask(extractor=ApacheSupersetTableExtractor(), loader=FsNeo4jCSVLoader())

job = DefaultJob(conf=job_config,
                 task=task)

job.launch()
```

### [ApacheSupersetChartExtractor](./databuilder/extractor/dashboard/apache_superset/apache_superset_chart_extractor.py)

The included `ApacheSupersetChartExtractor` provides support for extracting information on charts connected to given dashboard.

##### Caution!

Currently there is no way to connect Apache Superset `Query` model to neither `Chart` nor `Dashboard` model. For that reason, to comply with Amundsen
Databuilder data model, we register single `DashboardQuery` node serving as a bridge to which all the `DashboardChart` nodes are connected.

#### DashboardChart

##### Metadata available in REST API

- Chart id (id)
- Chart name (chart_name)
- Chart type (viz_type)

##### Metadata not available in REST API

- Chart url

#### Sample job config

```python
tmp_folder = f'/tmp/amundsen/dashboard'

dict_config = {
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': f'{tmp_folder}/nodes',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': f'{tmp_folder}/relationships',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_ID}': '1',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_NAME}': 'dashboard group',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.DASHBOARD_GROUP_DESCRIPTION}': 'dashboard group description',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.CLUSTER}': 'gold',
    f'extractor.apache_superset.{ApacheSupersetBaseExtractor.APACHE_SUPERSET_SECURITY_SETTINGS_DICT}': dict(
        username='admin',
        password='admin',
        provider='db')
}

job_config = ConfigFactory.from_dict(dict_config)

task = DefaultTask(extractor=ApacheSupersetChartExtractor(), loader=FsNeo4jCSVLoader())

job = DefaultJob(conf=job_config,
                 task=task)

job.launch()
```

### [PandasProfilingColumnStatsExtractor](./databuilder/extractor/pandas_profiling_column_stats_extractor.py)

[Pandas profiling](https://github.com/pandas-profiling/pandas-profiling) is a library commonly used by Data Engineer and Scientists to calculate advanced data profiles on data.
It is run on pandas dataframe and results in json file containing (amongst other things) descriptive and quantile statistics on columns.

#### Required input parameters
- `FILE_PATH` - file path to pandas-profiling **json** report
- `TABLE_NAME` - name of the table for which report was calculated
- `SCHEMA_NAME` - name of the schema from which table originates
- `DATABASE_NAME` - name of database technology from which table originates
- `CLUSTER_NAME` - name of the cluster from which table originates

#### Optional input parameters

- `PRECISION` - precision for metrics of `float` type. Defaults to `3` meaning up to 3 digits after decimal point.
- `STAT_MAPPINGS` - if you wish to collect only selected set of metrics configure this option with dictionary of following format:
    - key - raw name of the stat in pandas-profiling
    - value - tuple of 2 elements:
        - first value of the tuple - full name of the stat (this influences what will be rendered for user in UI)
        - second value of the tuple - function modifying the stat (by default we just do type casting)

Such dictionary should in that case contain only keys of metrics you wish to collect.

For example - if you want only min and max value of a column, provide extractor with configuration option:

```python
PandasProfilingColumnStatsExtractor.STAT_MAPPINGS = {'max': ('Maximum', float), 'min': ('Minimum', float)}
```

Complete set of available metrics is defined as DEFAULT_STAT_MAPPINGS attribute of PandasProfilingColumnStatsExtractor.

#### Common usage patterns

As pandas profiling is executed on top of pandas dataframe, it is up to the user to populate the dataframe before running
the report calculation (and subsequently the extractor). While doing so remember that it might not be a good idea to run the
report on a complete set of rows if your tables are very sparse. In such case it is recommended to dump a subset of rows
to pandas dataframe beforehand and calculate the report on just a sample of original data.

##### Spark support

Support for native execution of pandas-profiling on Spark Dataframe is currently worked on and should come in the future.

#### Sample job config

```python
import pandas as pd
import pandas_profiling
from pyhocon import ConfigFactory
from sqlalchemy import create_engine

from databuilder.extractor.pandas_profiling_column_stats_extractor import PandasProfilingColumnStatsExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.task.task import DefaultTask

table_name = 'video_game_sales'
schema_name = 'superset'

# Load table contents to pandas dataframe
db_uri = f'postgresql://superset:superset@localhost:5432/{schema_name}'
engine = create_engine(db_uri, echo=True)

df = pd.read_sql_table(
    table_name,
    con=engine
)

# Calculate pandas-profiling report on a table
report_file = '/tmp/table_report.json'

report = df.profile_report(sort=None)
report.to_file(report_file)

# Run PandasProfilingColumnStatsExtractor on calculated report
tmp_folder = f'/tmp/amundsen/column_stats'

dict_config = {
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': f'{tmp_folder}/nodes',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': f'{tmp_folder}/relationships',
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR}': False,
    'extractor.pandas_profiling.table_name': table_name,
    'extractor.pandas_profiling.schema_name': schema_name,
    'extractor.pandas_profiling.database_name': 'postgres',
    'extractor.pandas_profiling.cluster_name': 'dev',
    'extractor.pandas_profiling.file_path': report_file
}

job_config = ConfigFactory.from_dict(dict_config)

task = DefaultTask(extractor=PandasProfilingColumnStatsExtractor(), loader=FsNeo4jCSVLoader())

job = DefaultJob(conf=job_config,
                 task=task)

job.launch()
```

### [ElasticsearchMetadataExtractor](./databuilder/extractor/es_metadata_extractor.py)

The included `ElasticsearchMetadataExtractor` provides support for extracting basic metadata for Elasticsearch indexes.

It extracts index metadata into `TableMetadata` model so the results are retrievable the same way as table metadata.

Index properties (fields) are treated as `ColumnMetadata`.

#### Technical indexes

This extractor will collect metadata for all indexes of your Elasticsearch instance except for technical indices (which names start with `.`)

#### Configuration

Following configuration options are supported under `extractor.es_metadata` scope:
- `cluster` (required) - name of the cluster of Elasticsearch instance we are extracting metadata from.
- `schema` (required) - name of the schema of Elasticsearch instance we are extracting metadata from.
- `client` (required) - object containing `Elasticsearch` class instance for connecting to Elasticsearch.
- `extract_technical_details` (defaults to `False`) - if `True` index `aliases` and `settings` will be extracted as `Programmatic Descriptions`.

#### Sample job config

```python3
import os

from elasticsearch import Elasticsearch
from pyhocon import ConfigFactory

from databuilder.extractor.es_metadata_extractor import ElasticsearchMetadataExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.task.task import DefaultTask

tmp_folder = '/tmp/es_metadata'

node_files_folder = f'{tmp_folder}/nodes'
relationship_files_folder = f'{tmp_folder}/relationships'

dict_config = {
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': node_files_folder,
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': relationship_files_folder,
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
    f'extractor.es_metadata.{ElasticsearchMetadataExtractor.CLUSTER}': 'demo',
    f'extractor.es_metadata.{ElasticsearchMetadataExtractor.SCHEMA}': 'dev',
    f'extractor.es_metadata.{ElasticsearchMetadataExtractor.ELASTICSEARCH_CLIENT_CONFIG_KEY}': Elasticsearch()
}

job_config = ConfigFactory.from_dict(dict_config)

task = DefaultTask(extractor=ElasticsearchMetadataExtractor(), loader=FsNeo4jCSVLoader())

job = DefaultJob(conf=job_config,
                 task=task)
```

### [ElasticsearchColumnStatsExtractor](./databuilder/extractor/es_column_stats_extractor.py)

The included `ElasticsearchColumnStatsExtractor` provides support for extracting basic statistics on numerical properties of Elasticsearch indexes.

It extracts statistics using [Elasticsearch aggregation `matrix_stats`](https://www.elastic.co/guide/en/elasticsearch/reference/master/search-aggregations-matrix-stats-aggregation.html). It disregards statistics named `covariance` and `correlation`.

#### Technical indexes

This extractor will collect metadata for all indexes of your Elasticsearch instance except for technical indices (which names start with `.`)

#### Configuration

Following configuration options are supported under `extractor.es_column_stats` scope:
- `cluster` (required) - name of the cluster of Elasticsearch instance we are extracting metadata from.
- `schema` (required) - name of the schema of Elasticsearch instance we are extracting metadata from.
- `client` (required) - object containing `Elasticsearch` class instance for connecting to Elasticsearch.
- `extract_technical_details` (defaults to `False`) - if `True` index `aliases` and `settings` will be extracted as `Programmatic Descriptions`.

#### Sample job config

```python3
import os

from elasticsearch import Elasticsearch
from pyhocon import ConfigFactory

from databuilder.extractor.es_column_stats_extractor import ElasticsearchColumnStatsExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.task.task import DefaultTask

tmp_folder = '/tmp/es_column_stats'

node_files_folder = f'{tmp_folder}/nodes'
relationship_files_folder = f'{tmp_folder}/relationships'

dict_config = {
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.NODE_DIR_PATH}': node_files_folder,
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.RELATION_DIR_PATH}': relationship_files_folder,
    f'loader.filesystem_csv_neo4j.{FsNeo4jCSVLoader.SHOULD_DELETE_CREATED_DIR}': True,
    f'extractor.es_column_stats.{ElasticsearchColumnStatsExtractor.CLUSTER}': 'demo',
    f'extractor.es_column_stats.{ElasticsearchColumnStatsExtractor.SCHEMA}': 'dev',
    f'extractor.es_column_stats.{ElasticsearchColumnStatsExtractor.ELASTICSEARCH_CLIENT_CONFIG_KEY}': Elasticsearch()
}

job_config = ConfigFactory.from_dict(dict_config)

task = DefaultTask(extractor=ElasticsearchColumnStatsExtractor(), loader=FsNeo4jCSVLoader())

job = DefaultJob(conf=job_config,
                 task=task)
```

### [BamboohrUserExtractor](./databuilder/extractor/user/bamboohr/bamboohr_user_extractor.py)

The included `BamboohrUserExtractor` provides support for extracting basic user metadata from [BambooHR](https://www.bamboohr.com/).  For companies and organizations that use BambooHR to store employee information such as email addresses, first names, last names, titles, and departments, use the `BamboohrUserExtractor` to populate Amundsen user data.

A sample job config is shown below.

```python
extractor = BamboohrUserExtractor()
task = DefaultTask(extractor=extractor, loader=FsNeo4jCSVLoader())

job_config = ConfigFactory.from_dict({
    'extractor.bamboohr_user.api_key': api_key,
    'extractor.bamboohr_user.subdomain': subdomain,
})

job = DefaultJob(conf=job_config,
                 task=task,
                 publisher=Neo4jCsvPublisher())
job.launch()
```

## List of transformers

Transformers are implemented by subclassing [Transformer](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/transformer/base_transformer.py#L12 "Transformer") and implementing `transform(self, record)`. A transformer can:

- Modify a record and return it,
- Return `None` to filter a record out,
- Yield multiple records. This is useful for e.g. inferring metadata (such as ownership) from table descriptions.

#### [ChainedTransformer](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/transformer/base_transformer.py#L41 "ChainedTransformer")
A chanined transformer that can take multiple transformers, passing each record through the chain.

#### [RegexStrReplaceTransformer](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/transformer/regex_str_replace_transformer.py "RegexStrReplaceTransformer")
Generic string replacement transformer using REGEX. User can pass list of tuples where tuple contains regex and replacement pair.
```python
job_config = ConfigFactory.from_dict({
    'transformer.regex_str_replace.{}'.format(REGEX_REPLACE_TUPLE_LIST): [(',', ' '), ('"', '')],
    'transformer.regex_str_replace.{}'.format(ATTRIBUTE_NAME): 'instance_field_name',})

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=AnyExtractor(),
        transformer=RegexStrReplaceTransformer(),
        loader=AnyLoader()))
job.launch()
```

#### [TemplateVariableSubstitutionTransformer](./databuilder/transformer/template_variable_substitution_transformer.py)
Adds or replaces field in Dict by string.format based on given template and provide record Dict as a template parameter.

#### [DictToModel](./databuilder/transformer/dict_to_model.py)
Transforms dictionary into model.

#### [TimestampStringToEpoch](./databuilder/transformer/timestamp_string_to_epoch.py)
Transforms string timestamp into int epoch.

#### [RemoveFieldTransformer](./databuilder/transformer/remove_field_transformer.py)
Remove fields from the Dict.

#### [TableTagTransformer](./databuilder/transformer/table_tag_transformer.py)
Adds the same set of tags to all tables produced by the job.

#### [GenericTransformer](./databuilder/transformer/generic_transformer.py)
Transforms dictionary based on callback function that user provides.

## List of loader
#### [FsNeo4jCSVLoader](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/loader/file_system_neo4j_csv_loader.py "FsNeo4jCSVLoader")
Write node and relationship CSV file(s) that can be consumed by Neo4jCsvPublisher. It assumes that the record it consumes is instance of Neo4jCsvSerializable.

```python
job_config = ConfigFactory.from_dict({
    'loader.filesystem_csv_neo4j.{}'.format(FsNeo4jCSVLoader.NODE_DIR_PATH): node_files_folder,
    'loader.filesystem_csv_neo4j.{}'.format(FsNeo4jCSVLoader.RELATION_DIR_PATH): relationship_files_folder},)

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=AnyExtractor(),
        loader=FsNeo4jCSVLoader()),
    publisher=Neo4jCsvPublisher())
job.launch()
```

#### [GenericLoader](./databuilder/loader/generic_loader.py)
Loader class that calls user provided callback function with record as a parameter

Example that pushes Mode Dashboard accumulated usage via GenericLoader where callback_function expected to insert record to data warehouse.

```python
extractor = ModeDashboardUsageExtractor()
task = DefaultTask(extractor=extractor,
                   loader=GenericLoader(), )

job_config = ConfigFactory.from_dict({
    '{}.{}'.format(extractor.get_scope(), ORGANIZATION): organization,
    '{}.{}'.format(extractor.get_scope(), MODE_BEARER_TOKEN): mode_bearer_token,
    'loader.generic.callback_function': callback_function
})

job = DefaultJob(conf=job_config, task=task)
job.launch()

```


#### [FSElasticsearchJSONLoader](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/loader/file_system_elasticsearch_json_loader.py "FSElasticsearchJSONLoader")
Write Elasticsearch document in JSON format which can be consumed by ElasticsearchPublisher. It assumes that the record it consumes is instance of ElasticsearchDocument.

```python
data_file_path = '/var/tmp/amundsen/search_data.json'

job_config = ConfigFactory.from_dict({
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_PATH_CONFIG_KEY): data_file_path,
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_MODE_CONFIG_KEY): 'w',})

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=AnyExtractor(),
        loader=FSElasticsearchJSONLoader()),
    publisher=ElasticsearchPublisher())
job.launch()
```

#### [FsAtlasCSVLoader](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/loader/file_system_atlas_csv_loader.py "FileSystemCSVLoader")
Write node and relationship CSV file(s) that can be consumed by AtlasCsvPublisher. It assumes that the record it
 consumes is instance of AtlasSerializable.

```python
from pyhocon import ConfigFactory
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_atlas_csv_loader import FsAtlasCSVLoader
from databuilder.task.task import DefaultTask

tmp_folder = f'/tmp/amundsen/dashboard'

job_config = ConfigFactory.from_dict({
    f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': f'{tmp_folder}/entities',
    f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': f'{tmp_folder}/relationships'
})

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=AnyExtractor(),
        loader=FsAtlasCSVLoader()),
    publisher=AnyPublisher())
job.launch()
```

## List of publisher
#### [Neo4jCsvPublisher](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/publisher/neo4j_csv_publisher.py "Neo4jCsvPublisher")
A Publisher takes two folders for input and publishes to Neo4j.
One folder will contain CSV file(s) for Node where the other folder will contain CSV file(s) for Relationship. Neo4j follows Label Node properties Graph and refer to [here](https://neo4j.com/docs/developer-manual/current/introduction/graphdb-concepts/ "here") for more information

```python
node_files_folder = '{tmp_folder}/nodes/'.format(tmp_folder=tmp_folder)
relationship_files_folder = '{tmp_folder}/relationships/'.format(tmp_folder=tmp_folder)

job_config = ConfigFactory.from_dict({
    'loader.filesystem_csv_neo4j.{}'.format(FsNeo4jCSVLoader.NODE_DIR_PATH): node_files_folder,
    'loader.filesystem_csv_neo4j.{}'.format(FsNeo4jCSVLoader.RELATION_DIR_PATH): relationship_files_folder,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NODE_FILES_DIR): node_files_folder,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.RELATION_FILES_DIR): relationship_files_folder,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_END_POINT_KEY): neo4j_endpoint,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_USER): neo4j_user,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_PASSWORD): neo4j_password,
    'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_ENCRYPTED): True,
})

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=AnyExtractor(),
        loader=FsNeo4jCSVLoader()),
    publisher=Neo4jCsvPublisher())
job.launch()
```

#### [ElasticsearchPublisher](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/publisher/elasticsearch_publisher.py "ElasticsearchPublisher")
Elasticsearch Publisher uses Bulk API to load data from JSON file. Elasticsearch publisher supports atomic operation by utilizing alias in Elasticsearch.
A new index is created and data is uploaded into it. After the upload is complete, index alias is swapped to point to new index from old index and traffic is routed to new index.
```python
data_file_path = '/var/tmp/amundsen/search_data.json'

job_config = ConfigFactory.from_dict({
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_PATH_CONFIG_KEY): data_file_path,
    'loader.filesystem.elasticsearch.{}'.format(FSElasticsearchJSONLoader.FILE_MODE_CONFIG_KEY): 'w',
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.FILE_PATH_CONFIG_KEY): data_file_path,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.FILE_MODE_CONFIG_KEY): 'r',
    'publisher.elasticsearch{}'.format(ElasticsearchPublisher.ELASTICSEARCH_CLIENT_CONFIG_KEY): elasticsearch_client,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_NEW_INDEX_CONFIG_KEY): elasticsearch_new_index,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_DOC_TYPE_CONFIG_KEY): elasticsearch_doc_type,
    'publisher.elasticsearch.{}'.format(ElasticsearchPublisher.ELASTICSEARCH_ALIAS_CONFIG_KEY): elasticsearch_index_alias,
})

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=AnyExtractor(),
        loader=FSElasticsearchJSONLoader()),
    publisher=ElasticsearchPublisher())
job.launch()
```
#### [AtlasCsvPublisher](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/publisher/atlas_csv_publisher.py "AtlasCsvPublisher")
A Publisher takes two folders for input and publishes to Atlas.
One folder will contain CSV file(s) for Entity where the other folder will contain CSV file(s) for Relationship.

##### Amundsen <> Atlas Types
Atlas publisher requires registering appropriate entity types in Atlas. This can be achieved in two ways:

###### Register entity types directly in publisher
By default publisher will register proper entity types for you. This is achieved with `register_entity_types` configuration option of the publisher, which defaults to `True`.

If your metadata synchronization job consists of several extractors leveraging `AtlasCSVPublisher` it is recommended to have this option turned on only for the first extractor.

###### Register entity types using standalone script
You can register entity types separately - below script might serve as a baseline and will probably need adjusting AtlasClient to your environment.
```python3
from apache_atlas.client.base_client import AtlasClient

from databuilder.types.atlas import AtlasEntityInitializer

client = AtlasClient('http://localhost:21000', ('admin', 'admin'))

init = AtlasEntityInitializer(client)

init.create_required_entities()
```

###### Caution!
Whenever you upgrade your databuilder version it is important to re-run `AtlasEntityInitializer` as there might be new changes to entity types required for Atlas integration to work properly.

##### Sample script
```python
from apache_atlas.client.base_client import AtlasClient
from pyhocon import ConfigFactory
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_atlas_csv_loader import FsAtlasCSVLoader
from databuilder.publisher.atlas_csv_publisher import AtlasCSVPublisher
from databuilder.task.task import DefaultTask

tmp_folder = f'/tmp/amundsen/dashboard'

job_config = ConfigFactory.from_dict({
    f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.ENTITY_DIR_PATH}': f'{tmp_folder}/entities',
    f'loader.filesystem_csv_atlas.{FsAtlasCSVLoader.RELATIONSHIP_DIR_PATH}': f'{tmp_folder}/relationships',
    f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_CLIENT}': AtlasClient('http://localhost:21000', ('admin', 'admin')) ,
    f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ENTITY_DIR_PATH}': f'{tmp_folder}/entities',
    f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.RELATIONSHIP_DIR_PATH}': f'{tmp_folder}/relationships',
    f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.ATLAS_ENTITY_CREATE_BATCH_SIZE}': 10,
    f'publisher.atlas_csv_publisher.{AtlasCSVPublisher.REGISTER_ENTITY_TYPES}': True
})

job = DefaultJob(
    conf=job_config,
    task=DefaultTask(
        extractor=AnyExtractor(),
        loader=FsAtlasCSVLoader()),
    publisher=AtlasCSVPublisher())
job.launch()
```


#### [Callback](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/callback/call_back.py "Callback")
Callback interface is built upon a [Observer pattern](https://en.wikipedia.org/wiki/Observer_pattern "Observer pattern") where the participant want to take any action when target's state changes.

Publisher is the first one adopting Callback where registered Callback will be called either when publish succeeded or when publish failed. In order to register callback, Publisher provides [register_call_back](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/publisher/base_publisher.py#L50 "register_call_back") method.

One use case is for Extractor that needs to commit when job is finished (e.g: Kafka). Having Extractor register a callback to Publisher to commit when publish is successful, extractor can safely commit by implementing commit logic into [on_success](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/callback/call_back.py#L18 "on_success") method.

### REST API Query
Databuilder now has a generic REST API Query capability that can be joined each other.
Most of the cases of extraction is currently from Database or Datawarehouse that is queryable via SQL. However, not all metadata sources provide our access to its Database and they mostly provide REST API to consume their metadata.

The challenges come with REST API is that:

 1. there's no explicit standard in REST API. Here, we need to conform to majority of cases (HTTP call with JSON payload & response) but open for extension for different authentication scheme, and different way of pagination, etc.
 2. It is hardly the case that you would get what you want from one REST API call. It is usually the case that you need to snitch (JOIN) multiple REST API calls together to get the information you want.

To solve this challenges, we introduce [RestApiQuery](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/rest_api/rest_api_query.py)

RestAPIQuery is:
 1. Assuming that REST API is using HTTP(S) call with GET method -- RestAPIQuery intention's is **read**, not write -- where basic HTTP auth is supported out of the box. There's extension point on other authentication scheme such as Oauth, and pagination, etc. (See [ModePaginatedRestApiQuery](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/rest_api/mode_analytics/mode_paginated_rest_api_query.py) for pagination)
 2. Usually, you want the subset of the response you get from the REST API call -- value extraction. To extract the value you want, RestApiQuery uses [JSONPath](https://goessner.net/articles/JsonPath/) which is similar product as XPATH of XML.
 3. You can JOIN multiple RestApiQuery together.

More detail on JOIN operation in RestApiQuery:
 1. It joins multiple RestApiQuery together by accepting prior RestApiQuery as a constructor -- a [Decorator pattern](https://en.wikipedia.org/wiki/Decorator_pattern)
 2. In REST API, URL is the one that locates the resource we want. Here, JOIN simply means we need to find resource **based on the identifier that other query's result has**. In other words, when RestApiQuery forms URL, it uses previous query's result to compute the URL `e.g: Previous record: {"dashboard_id": "foo"}, URL before: http://foo.bar/dashboard/{dashboard_id} URL after compute: http://foo.bar/dashboard/foo`
With this pattern RestApiQuery supports 1:1 and 1:N JOIN relationship.
(GROUP BY or any other aggregation, sub-query join is not supported)

To see in action, take a peek at [ModeDashboardExtractor](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/extractor/dashboard/mode_analytics/mode_dashboard_extractor.py)
Also, take a look at how it extends to support pagination at [ModePaginatedRestApiQuery](./databuilder/rest_api/mode_analytics/mode_paginated_rest_api_query.py).

### Removing stale data in Neo4j -- [Neo4jStalenessRemovalTask](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/task/neo4j_staleness_removal_task.py):

As Databuilder ingestion mostly consists of either INSERT OR UPDATE, there could be some stale data that has been removed from metadata source but still remains in Neo4j database. Neo4jStalenessRemovalTask basically detects staleness and removes it.

In [Neo4jCsvPublisher](https://github.com/amundsen-io/amundsen/blob/main/databuilder/databuilder/publisher/neo4j_csv_publisher.py), it adds attributes "published_tag" and "publisher_last_updated_epoch_ms" on every nodes and relations. You can use either of these two attributes to detect staleness and remove those stale node or relation from the database.

#### Using "published_tag" to remove stale data
Use *published_tag* to remove stale data, when it is certain that non-matching tag is stale once all the ingestion is completed. For example, suppose that you use current date (or execution date in Airflow) as a *published_tag*, "2020-03-31". Once Databuilder ingests all tables and all columns, all table nodes and column nodes should have *published_tag* as "2020-03-31". It is safe to assume that table nodes and column nodes whose *published_tag* is different -- such as "2020-03-30" or "2020-02-10" -- means that it is deleted from the source metadata. You can use Neo4jStalenessRemovalTask to delete those stale data.

    task = Neo4jStalenessRemovalTask()
    job_config_dict = {
        'job.identifier': 'remove_stale_data_job',
        'task.remove_stale_data.neo4j_endpoint': neo4j_endpoint,
        'task.remove_stale_data.neo4j_user': neo4j_user,
        'task.remove_stale_data.neo4j_password': neo4j_password,
        'task.remove_stale_data.staleness_max_pct': 10,
        'task.remove_stale_data.target_nodes': ['Table', 'Column'],
        'task.remove_stale_data.job_publish_tag': '2020-03-31'
    }
    job_config = ConfigFactory.from_dict(job_config_dict)
    job = DefaultJob(conf=job_config, task=task)
    job.launch()

Note that there's protection mechanism, **staleness_max_pct**, that protect your data being wiped out when something is clearly wrong. "**staleness_max_pct**" basically first measure the proportion of elements that will be deleted and if it exceeds threshold per type ( 10% on the configuration above ), the deletion won't be executed and the task aborts.

#### Using "publisher_last_updated_epoch_ms" to remove stale data
You can think this approach as TTL based eviction. This is particularly useful when there are multiple ingestion pipelines and you cannot be sure when all ingestion is done. In this case, you might still can say that if specific node or relation has not been published past 3 days, it's stale data.

    task = Neo4jStalenessRemovalTask()
    job_config_dict = {
        'job.identifier': 'remove_stale_data_job',
        'task.remove_stale_data.neo4j_endpoint': neo4j_endpoint,
        'task.remove_stale_data.neo4j_user': neo4j_user,
        'task.remove_stale_data.neo4j_password': neo4j_password,
        'task.remove_stale_data.staleness_max_pct': 10,
        'task.remove_stale_data.target_relations': ['READ', 'READ_BY'],
        'task.remove_stale_data.milliseconds_to_expire': 86400000 * 3
    }
    job_config = ConfigFactory.from_dict(job_config_dict)
    job = DefaultJob(conf=job_config, task=task)
    job.launch()

Above configuration is trying to delete stale usage relation (READ, READ_BY), by deleting READ or READ_BY relation that has not been published past 3 days. If number of elements to be removed is more than 10% per type, this task will be aborted without executing any deletion.

#### Dry run
Deletion is always scary and it's better to perform dryrun before put this into action. You can use Dry run to see what sort of Cypher query will be executed.

    task = Neo4jStalenessRemovalTask()
    job_config_dict = {
        'job.identifier': 'remove_stale_data_job',
        'task.remove_stale_data.neo4j_endpoint': neo4j_endpoint,
        'task.remove_stale_data.neo4j_user': neo4j_user,
        'task.remove_stale_data.neo4j_password': neo4j_password,
        'task.remove_stale_data.staleness_max_pct': 10,
        'task.remove_stale_data.target_relations': ['READ', 'READ_BY'],
        'task.remove_stale_data.milliseconds_to_expire': 86400000 * 3
        'task.remove_stale_data.dry_run': True
    }
    job_config = ConfigFactory.from_dict(job_config_dict)
    job = DefaultJob(conf=job_config, task=task)
    job.launch()
