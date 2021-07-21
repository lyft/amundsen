# Amundsen K8s Helm Charts

Source code can be found [here](https://github.com/amundsen-io/amundsen)

## What is this?

This is setup templates for deploying [amundsen](https://github.com/amundsen-io/amundsen) on [k8s (kubernetes)](https://kubernetes.io/), using [helm.](https://helm.sh/)

## How do I get started?

1. Make sure you have the following command line clients setup:
    - k8s (kubectl)
    - helm
2. Build out a cloud based k8s cluster, such as [Amazon EKS](https://aws.amazon.com/eks/)
3. Ensure you can connect to your cluster with cli tools in step 1.

## Prerequisites

1. Helm 2.14+
2. Kubernetes 1.14+

## Chart Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://charts.helm.sh/stable | elasticsearch | 1.32.0 |

## Chart Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| LONG_RANDOM_STRING | int | `1234` | A long random string. You should probably provide your own. This is needed for OIDC. |
| affinity | object | `{}` | amundsen application wide configuration of affinity. This applies to search, metadata, frontend and neo4j. Elasticsearch has it's own configuation properties for this. [ref](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity) |
| dnsZone | string | `"teamname.company.com"` | **DEPRECATED - its not standard to pre construct urls this way.** The dns zone (e.g. group-qa.myaccount.company.com) the app is running in. Used to construct dns hostnames (on aws only). |
| dockerhubImagePath | string | `"amundsendev"` | **DEPRECATED - this is not useful, it would be better to just allow the whole image to be swapped instead.** The image path for dockerhub. |
| elasticsearch.client.replicas | int | `1` | only running amundsen on 1 client replica |
| elasticsearch.cluster.env.EXPECTED_MASTER_NODES | int | `1` | required to match master.replicas |
| elasticsearch.cluster.env.MINIMUM_MASTER_NODES | int | `1` | required to match master.replicas |
| elasticsearch.cluster.env.RECOVER_AFTER_MASTER_NODES | int | `1` | required to match master.replicas |
| elasticsearch.data.replicas | int | `1` | only running amundsen on 1 data replica |
| elasticsearch.enabled | bool | `true` | set this to false, if you want to provide your own ES instance. |
| elasticsearch.master.replicas | int | `1` | only running amundsen on 1 master replica |
| environment | string | `"dev"` | **DEPRECATED - its not standard to pre construct urls this way.** The environment the app is running in. Used to construct dns hostnames (on aws only) and ports. |
| frontEnd.OIDC_AUTH_SERVER_ID **(DEPRECATED)** | string | `nil` | The authorization server id for OIDC. |
| frontEnd.OIDC_CLIENT_ID **(DEPRECATED)** | string | `nil` | The client id for OIDC. |
| frontEnd.OIDC_CLIENT_SECRET **(DEPRECATED)** | string | `""` | The client secret for OIDC. |
| frontEnd.OIDC_ORG_URL **(DEPRECATED)** | string | `nil` | The organization URL for OIDC. |
| frontEnd.OVERWRITE_REDIRECT_URI **(DEPRECATED)** | string | `nil` | The redirect uri for OIDC. |
| frontEnd.affinity | object | `{}` | Frontend pod specific affinity. |
| frontEnd.annotations | object | `{}` | Frontend service specific tolerations. |
| frontEnd.baseUrl | string | `"http://localhost"` | used by notifications util to provide links to amundsen pages in emails. |
| frontEnd.createOidcSecret | bool | `false` | OIDC needs some configuration. If you want the chart to make your secrets, set this to true and set the next four values. If you don't want to configure your secrets via helm, you can still use the amundsen-oidc-config.yaml as a template |
| frontEnd.image | string | `"amundsendev/amundsen-frontend"` | The image of the frontend container. |
| frontEnd.envVars | object | `{}` |Everything set under "envVars" during helm install/upgrade will be parsed as environment variable for this service. |
| frontEnd.imagePullSecrets | list | `[]` | Optional pod imagePullSecrets [ref](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) |
| frontEnd.imageTag | string | `"2.3.0"` | The image tag of the frontend container. |
| frontEnd.nodeSelector | object | `{}` | Frontend pod specific nodeSelector. |
| frontEnd.oidcEnabled **(DEPRECATED)** | bool | `false` | *Use `oidc.enabled` instead.* To enable auth via OIDC, set this to true. |
| frontEnd.podAnnotations | object | `{}` | Frontend pod specific annotations. |
| frontEnd.replicas | int | `1` | How many replicas of the frontend service to run. |
| frontEnd.resources | object | `{}` | See pod resourcing [ref](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/) |
| frontEnd.serviceName | string | `"frontend"` | The frontend service name. |
| frontEnd.servicePort | int | `80` | The port the frontend service will be exposed on via the loadbalancer. |
| frontEnd.serviceType | string | `"ClusterIP"` | The frontend service type. See service types [ref](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) |
| frontEnd.tolerations | list | `[]` | Frontend pod specific tolerations. |
| metadata.affinity | object | `{}` | Metadata pod specific affinity. |
| metadata.annotations | object | `{}` | Metadata service specific tolerations. |
| metadata.envVars | object | `{}` |Everything set under "envVars" during helm install/upgrade will be parsed as environment variable for this service. |
| metadata.image | string | `"amundsendev/amundsen-metadata"` | The image of the metadata container. |
| metadata.imagePullSecrets | list | `[]` | Optional pod imagePullSecrets [ref](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) |
| metadata.imageTag | string | `"2.5.5"` | The image tag of the metadata container. |
| metadata.neo4jEndpoint **(DEPRECATED)** | string | `nil` | *Use `metadata.proxy.host` & `metadata.proxy.port` instead.* The name of the service hosting neo4j on your cluster, if you bring your own. You should only need to change this, if you don't use the version in this chart. |
| metadata.nodeSelector | object | `{}` | Metadata pod specific nodeSelector. |
| metadata.podAnnotations | object | `{}` | Metadata pod specific annotations. |
| metadata.proxy.host | string | `nil` | Host name / URI of your proxy. |
| metadata.proxy.port | string | `nil` | Metadata Proxy Port on which the proxy is running. |
| metadata.proxy.user | string | `nil` | Credentials - Username of the Metadata proxy. |
| metadata.proxy.password | string | `nil` | Credentials - Password of the Metadata proxy. |
| metadata.replicas | int | `1` | How many replicas of the metadata service to run. |
| metadata.resources | object | `{}` | See pod resourcing [ref](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/) |
| metadata.serviceName | string | `"metadata"` | The metadata service name. |
| metadata.serviceType | string | `"ClusterIP"` | The metadata service type. See service types [ref](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) |
| metadata.tolerations | list | `[]` | Metadata pod specific tolerations. |
| neo4j.affinity | object | `{}` | neo4j specific affinity. |
| neo4j.annotations | object | `{}` | neo4j service specific tolerations. |
| neo4j.backup | object | `{"enabled":false,"podAnnotations":{},"s3Path":"s3://dev/null","schedule":"0 * * * *"}` | If enabled is set to true, make sure and set the s3 path as well. |
| neo4j.backup.s3Path | string | `"s3://dev/null"` | The s3path to write to for backups. |
| neo4j.backup.schedule | string | `"0 * * * *"` | The schedule to run backups on. Defaults to hourly. |
| neo4j.config | object | `{"dbms":{"heap_initial_size":"1G","heap_max_size":"2G","pagecache_size":"2G"}}` | Neo4j application specific configuration. This type of configuration is why the charts/stable version is not used. See [ref](https://github.com/helm/charts/issues/21439) |
| neo4j.config.dbms | object | `{"heap_initial_size":"1G","heap_max_size":"2G","pagecache_size":"2G"}` | dbms config for neo4j |
| neo4j.config.dbms.heap_initial_size | string | `"1G"` | the initial java heap for neo4j |
| neo4j.config.dbms.heap_max_size | string | `"2G"` | the max java heap for neo4j |
| neo4j.config.dbms.pagecache_size | string | `"2G"` | the page cache size for neo4j |
| neo4j.enabled | bool | `true` | If neo4j is enabled as part of this chart, or not. Set this to false if you want to provide your own version. |
| neo4j.nodeSelector | object | `{}` | neo4j specific nodeSelector. |
| neo4j.persistence | object | `{}` | Neo4j persistence. Turn this on to keep your data between pod crashes, etc. This is also needed for backups. |
| neo4j.podAnnotations | object | `{}` | neo4j pod specific annotations. |
| neo4j.resources | object | `{}` | See pod resourcing [ref](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/) |
| neo4j.tolerations | list | `[]` | neo4j specific tolerations. |
| neo4j.version | string | `"3.3.0"` | The neo4j application version used by amundsen. |
| nodeSelector | object | `{}` | amundsen application wide configuration of nodeSelector. This applies to search, metadata, frontend and neo4j. Elasticsearch has it's own configuation properties for this. [ref](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#nodeselector) |
| oidc.enabled | bool | `false` | Flag to enable/disable the OIDC. Once enabled, everything under oidc.configs will be parsed. Please make sure to set `frontend.config.class: amundsen_application.oidc_config.OidcConfig`, and following variables must also be set under `oidc.[frontend/metadata/search]`. `client_id`, `client_secret`.|
| oidc.configs | object | `{}` | Everything under oidc.configs will be parsed as environment variables for each service. More information on how to setup these variables can be found here: [verdan/flaskoidc](https://github.com/verdan/flaskoidc#configurations) |
| podAnnotations | object | `{}` | amundsen application wide configuration of podAnnotations. This applies to search, metadata, frontend and neo4j. Elasticsearch has it's own configuation properties for this. [ref](https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/) |
| provider | string | `"aws"` | The cloud provider the app is running in. Used to construct dns hostnames (on aws only). |
| search.affinity | object | `{}` | Search pod specific affinity. |
| search.annotations | object | `{}` | Search service specific tolerations. |
| search.elasticSearchCredentials **(DEPRECATED)** | object | `{}` | *Use `search.proxy.user` & `search.proxy.password` instead.* The elasticsearch user and password. This should only be set if you bring your own elasticsearch cluster in which case you must also set elasticsearch.enabled to false |
| search.elasticsearchEndpoint **(DEPRECATED)** | string | `nil` | *Use `search.proxy.endpoint` instead.* The name of the service hosting elasticsearch on your cluster, if you bring your own. You should only need to change this, if you don't use the version in this chart. |
| search.envVars | object | `{}` |Everything set under "envVars" during helm install/upgrade will be parsed as environment variable for this service. |
| search.image | string | `"amundsendev/amundsen-search"` | The image of the search container. |
| search.imagePullSecrets | list | `[]` | Optional pod imagePullSecrets [ref](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) |
| search.imageTag | string | `"2.4.0"` | The image tag of the search container. |
| search.nodeSelector | object | `{}` | Search pod specific nodeSelector. |
| search.podAnnotations | object | `{}` | Search pod specific annotations. |
| search.proxy.endpoint | string | `nil` | Endpoint of the search proxy (i.e., ES endpoint etc.). |
| search.proxy.user | string | `nil` | Credentials / Username to connect to proxy. |
| search.proxy.password | string | `nil` | Credentials / Password to connect to proxy. |
| search.replicas | int | `1` | How many replicas of the search service to run. |
| search.resources | object | `{}` | See pod resourcing [ref](https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/) |
| search.serviceName | string | `"search"` | The search service name. |
| search.serviceType | string | `"ClusterIP"` | The search service type. See service types [ref](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) |
| search.tolerations | list | `[]` | Search pod specific tolerations. |
| tolerations | list | `[]` | amundsen application wide configuration of tolerations. This applies to search, metadata, frontend and neo4j. Elasticsearch has it's own configuation properties for this. [ref](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#taints-and-tolerations-beta-feature) |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.5.0](https://github.com/norwoodj/helm-docs/releases/v1.5.0)


## Neo4j DBMS Config?

You may want to override the default memory usage for Neo4J. In particular, if you're just test-driving a deployment and your node exits with status 137, you should set the usage to smaller values:

``` yaml
config:
  dbms:
    heap_initial_size: 1G
    heap_max_size: 2G
    pagecache_size: 2G
```

With this values file, you can then install Amundsen using Helm 2 with:

``` shell
helm install ./templates/helm --values impl/helm/dev/values.yaml
```

For Helm 3 it's now mandatory to specify a [chart reference name](https://helm.sh/docs/intro/using_helm/#helm-install-installing-a-package) e.g. `my-amundsen`:

``` shell
helm install my-amundsen ./templates/helm --values impl/helm/dev/values.yaml
```

## Other Notes

- For aws setup, you will also need to setup the [external-dns plugin](https://github.com/kubernetes-incubator/external-dns)
- There is an existing helm chart for neo4j, but, it is missing some features necessary to for use such as:
  - [\[stable/neo4j\] make neo4j service definition more extensible](https://github.com/helm/charts/issues/21441); without this, it is not possible to setup external load balancers, external-dns, etc
  - [\[stable/neo4j\] allow custom configuration of neo4j](https://github.com/helm/charts/issues/21439); without this, custom configuration is not possible which includes setting configmap based settings, which also includes turning on apoc.
