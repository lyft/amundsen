# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import textwrap

# Specifying default mapping for elasticsearch index
# Documentation: https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html
# Setting type to "text" for all fields that would be used in search
# Using Simple Analyzer to convert all text into search terms
# https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-simple-analyzer.html
# Standard Analyzer is used for all text fields that don't explicitly specify an analyzer
# https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-standard-analyzer.html
TABLE_INDEX_MAP = textwrap.dedent(
    """
    {
    "settings": {
      "analysis": {
        "normalizer": {
          "column_names_normalizer": {
            "type": "custom",
            "filter": ["lowercase"]
          }
        }
      }
    },
    "mappings":{
        "table":{
          "properties": {
            "name": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "schema": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "display_name": {
              "type": "keyword"
            },
            "last_updated_timestamp": {
              "type": "date",
              "format": "epoch_second"
            },
            "description": {
              "type": "text",
              "analyzer": "simple"
            },
            "column_names": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword",
                  "normalizer": "column_names_normalizer"
                }
              }
            },
            "column_descriptions": {
              "type": "text",
              "analyzer": "simple"
            },
            "tags": {
              "type": "keyword"
            },
            "badges": {
              "type": "keyword"
            },
            "cluster": {
              "type": "text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "database": {
              "type": "text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "key": {
              "type": "keyword"
            },
            "total_usage":{
              "type": "long"
            },
            "unique_usage": {
              "type": "long"
            },
            "programmatic_descriptions": {
              "type": "text",
              "analyzer": "simple"
            }
          }
        }
      }
    }
    """
)

DASHBOARD_ELASTICSEARCH_INDEX_MAPPING = textwrap.dedent(
    """
    {
        "settings": {
          "analysis": {
            "normalizer": {
              "lowercase_normalizer": {
                "type": "custom",
                "char_filter": [],
                "filter": ["lowercase", "asciifolding"]
              }
            }
          }
        },
        "mappings":{
            "dashboard":{
              "properties": {
                "group_name": {
                  "type":"text",
                  "analyzer": "simple",
                  "fields": {
                    "raw": {
                      "type": "keyword",
                      "normalizer": "lowercase_normalizer"
                    }
                  }
                },
                "name": {
                  "type":"text",
                  "analyzer": "simple",
                  "fields": {
                    "raw": {
                      "type": "keyword",
                      "normalizer": "lowercase_normalizer"
                    }
                  }
                },
                "description": {
                  "type":"text",
                  "analyzer": "simple",
                  "fields": {
                    "raw": {
                      "type": "keyword"
                    }
                  }
                },
                "group_description": {
                  "type":"text",
                  "analyzer": "simple",
                  "fields": {
                    "raw": {
                      "type": "keyword"
                    }
                  }
                },
                "query_names": {
                  "type":"text",
                  "analyzer": "simple",
                  "fields": {
                    "raw": {
                      "type": "keyword"
                    }
                  }
                },
                "chart_names": {
                  "type":"text",
                  "analyzer": "simple",
                  "fields": {
                    "raw": {
                      "type": "keyword"
                    }
                  }
                },
                "tags": {
                  "type": "keyword"
                },
                "badges": {
                  "type": "keyword"
                }
              }
            }
          }
        }
    """
)

USER_INDEX_MAP = textwrap.dedent(
    """
    {
    "mappings":{
        "user":{
          "properties": {
            "email": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "first_name": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "last_name": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "full_name": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "total_read":{
              "type": "long"
            },
            "total_own": {
              "type": "long"
            },
            "total_follow": {
              "type": "long"
            }
          }
        }
      }
    }
    """
)

FEATURE_INDEX_MAP = textwrap.dedent(
    """
    {
    "settings": {
      "analysis": {
        "normalizer": {
          "lowercase_normalizer": {
            "type": "custom",
            "filter": ["lowercase"]
          }
        }
      }
    },
    "mappings":{
        "feature":{
          "properties": {
            "feature_group": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword",
                  "normalizer": "lowercase_normalizer"
                }
              }
            },
            "feature_name": {
              "type":"text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword",
                  "normalizer": "lowercase_normalizer"
                }
              }
            },
            "version": {
              "type": "keyword",
              "normalizer": "lowercase_normalizer"
            },
            "key": {
              "type": "keyword"
            },
            "total_usage":{
              "type": "long"
            },
            "status": {
              "type": "keyword"
            },
            "entity": {
              "type": "keyword"
            },
            "description": {
              "type": "text"
            },
            "availability": {
              "type": "text",
              "analyzer": "simple",
              "fields": {
                "raw": {
                  "type": "keyword"
                }
              }
            },
            "badges": {
              "type": "keyword"
            },
            "tags": {
              "type": "keyword"
            },
            "last_updated_timestamp": {
              "type": "date",
              "format": "epoch_second"
            }
          }
        }
      }
    }
    """
)
