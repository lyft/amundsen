# FAQ

## How to select between Neo4j and Atlas as backend for Amundsen?

### Why Neo4j?
1. Amundsen has direct influence over the data model if you use neo4j. This, at least initially, will benefit the speed by which new features in amundsen can arrive.
2. Neo4j for it is the market leader in Graph database and also was proven by Airbnb’s Data portal on their Data discovery tool.

### Why Atlas?
1. Atlas has lineage support already available. It's been tried and tested.
2. Tag/Badge propagation is supported.
3. It has a robust authentication and authorization system.
4. Atlas does data governance adding Amundsen for discovery makes it best of both worlds.
5. Apache Atlas is the only proxy in Amundsen supporting both push and pull approaches for collecting metadata:
    - `Push` method by leveraging Apache Atlas Hive Hook. It's an event listener running alongside Hive Metastore, translating Hive Metastore events into Apache Atlas entities and `pushing` them to Kafka topic, from which Apache Atlas ingests the data by internal processes.
    - `Pull` method by leveraging Amundsen Databuilder integration with Apache Atlas. It means that extractors available in Databuilder can be used to collect metadata about external systems (like PostgresMetadataExtractor) and sending them to Apache Atlas in a shape consumable by Amundsen.
    Amundsen <> Atlas integration is prepared in such way that you can use both push and pull models at the same time.
6. The free version of Neo4j does not have authorization support (Enterprise version does). Your question should actually be why use "neo4j over janusgraph" cause that is the right level of comparison. Atlas adds a whole bunch on top of the graph database.

#### Why not Atlas?
1. Atlas seems to have a slow development cycle and it's community is not very responsive although some small improvements have been made.
2. Atlas integration has less community support meaning new features might land slightly later for Atlas in comparison to Neo4j

##  What are the prerequisites to use Apache Atlas as backend for Amundsen?
To run Amundsen with Atlas, latest versions of following components should be used:
1. [Apache Atlas](https://github.com/apache/atlas/) - built from `master` branch. Ref [`103e867cc126ddb84e64bf262791a01a55bee6e5`](https://github.com/apache/atlas/commit/103e867cc126ddb84e64bf262791a01a55bee6e5) (or higher).
2. [amundsenatlastypes](https://pypi.org/project/amundsenatlastypes/) - library for installing Atlas entity definitions specific to Amundsen integration. Version `1.3.0` (or higher).

## How to migrate from Amundsen 1.x -> 2.x?

v2.0 renames a handful of fields in the services to be more consistent. Unfortunately one side effect is that the 2.0 versions of the services will need to be deployed simultaneously, as they are not interoperable with the 1.x versions.

Additionally, some indexed field names in the elasticsearch document change as well, so if you're using elasticsearch, you'll need to republish Elasticsearch index via Databuilder job.

The data in the metadata store, however, can be preserved when migrating from 1.x to 2.0.

v2.0 deployments consists of deployment of all three services along with republishing Elasticsearch document on Table with v2.0 Databuilder.

Keep in mind there is likely to be some downtime as v2.0.0, between deploying 3 services and re-seeding the elasticsearch indexes, so it might be ideal to stage a rollout by datacenter/environment if uptime is key

## How to avoid certain metadatas in Amundsen got erased by databuilder ingestion?

By default, databuilder always upserts the metadata. If you want to prevent that happens on certain type of metadata, you could add the following
config to your databuilder job's config

```python
'publisher.neo4j.{}'.format(neo4j_csv_publisher.NEO4J_CREATE_ONLY_NODES): [DESCRIPTION_NODE_LABEL],
```

This config means that databuilder will only update the table / column description if it doesn't exist before which could be the table is newly created.
This is useful when we treat Amundsen graph as the source of truth for certain types of metadata (e.g description).

## How to capture all Google Analytics?

Users are likely to have some sort of adblocker installed, making your Google Analytics less accurate.

To put a proxy in place to bypass any adblockers and capture all analytics, follow these steps:

1. Follow https://github.com/ZitRos/save-analytics-from-content-blockers#setup to set up your own proxy server.
2. In the same repository, run `npm run mask www.googletagmanager.com/gtag/js?id=UA-XXXXXXXXX` and save the output.
3. In your custom frontend, override https://github.com/amundsen-io/amundsenfrontendlibrary/blob/master/amundsen_application/static/templates/fragments/google-analytics-loader.html#L6 to <script async src="https://my-proxy-domain/MASKEDGOOGLETAGAMANAGERURL"></script>
4. Now, note that network requests to www.googletagmanager.com will be sent from behind your masked proxy endpoint, saving your analytics from content blockers!
