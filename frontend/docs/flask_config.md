# Flask configuration

After modifying any variable in [config.py](https://github.com/lyft/amundsenfrontendlibrary/blob/master/amundsen_application/config.py) described in this document, be sure to rebuild your application with these changes.

**NOTE: This document is a work in progress and does not include 100% of features. We welcome PRs to complete this document**

## Custom Routes
In order to add any custom Flask endpoints to Amundsen's frontend application, configure a function on the `INIT_CUSTOM_ROUTES` variable. This function takes the created Flask application and can leverage Flask's [add_url_rule](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.add_url_rule) method to add custom routes.

Example: Setting `INIT_CUSTOM_ROUTES` to the `init_custom_routes` method below will expose a `/custom_route` endpoint on the frontend application.
```bash
def init_custom_routes(app: Flask) -> None:
  app.add_url_rule('/custom_route', 'custom_route', custom_route)

def custom_route():
  pass
```
## Dashboard Preview
This service provides an API to download preview image of dashboard resources, which currently only supports [Mode](https://app.mode.com/).

The dashboard preview image is cached in user's browser up to a day. In order to adjust this you can change the value of `DASHBOARD_PREVIEW_IMAGE_CACHE_MAX_AGE_SECONDS`

### How to configure Mode dashboard preview
Add the following environment variables:
```bash
    CREDENTIALS_MODE_ADMIN_TOKEN
    CREDENTIALS_MODE_ADMIN_PASSWORD
    MODE_ORGANIZATION
```

#### How to enable authorization on Mode dashboard
By default, Amundsen does not do any authorization on showing preview. By registering name of the Mode preview class in configuration, you can enable authorization.
```bash
    ACL_ENABLED_DASHBOARD_PREVIEW = {'ModePreview'}
```
Amundsen ingests Mode dashboards only from the shared space, which all registered Mode users are able to view. Therefore our authorization first validates if the current user is registered in Mode. This feature is dependent on Amundsen also ingesting Mode user information via the [ModeDashboardUserExtractor](https://github.com/lyft/amundsendatabuilder/blob/master/README.md#modedashboarduserextractor) and the metadata service version must be at least [v2.5.2](https://github.com/lyft/amundsenmetadatalibrary/releases/tag/v2.5.2).

### How to support preview of different product?
You can add preview support for different products by adding its preview class to [DefaultPreviewMethodFactory](https://github.com/lyft/amundsenfrontendlibrary/blob/master/amundsen_application/api/preview/dashboard/dashboard_preview/preview_factory_method.py#L27)
In order to develop new preview class, you need to implement the class that inherits [BasePreview](https://github.com/lyft/amundsenfrontendlibrary/blob/master/amundsen_application/base/base_preview.py#L4) class and [ModePreview](https://github.com/lyft/amundsenfrontendlibrary/blob/master/amundsen_application/api/preview/dashboard/dashboard_preview/mode_preview.py#L28) would be a great example.

## Mail Client Features
Amundsen has two features that leverage the custom mail client -- the feedback tool and notifications. For these features a custom implementation of [base_mail_client](https://github.com/lyft/amundsenfrontendlibrary/blob/master/amundsen_application/base/base_mail_client.py) must be mapped to the `MAIL_CLIENT` configuration variable.

To fully enable these features in the UI, the application configuration variables for these features must also be set to true. Please see this [entry](application_config.md#mail-client-features) in our application configuration doc for further information.

## Issue Tracking Integration Features
Amundsen has a feature to allow display of associated tickets within the table detail view. The feature both displays
open tickets and allows users to report new tickets associated with the table. These tickets must contain the
`table_uri` within the ticket text in order to be displayed; the `table_uri` is automatically added to tickets created
via the feature. Tickets are displayed from most recent to oldest, and currently only open tickets are displayed. Currently only
 [JIRA](https://www.atlassian.com/software/jira) is supported. The UI must also be enabled to use this feature, please
 see configuration notes [here](application_config.md#issue-tracking-features).

There are several configuration
settings in `config.py` that should be set in order to use this feature.

Here are the settings and what they should be set to
```python
    ISSUE_LABELS = []  # type: List[str] (Optional labels to be set on the created tickets)
    ISSUE_TRACKER_URL = None  # type: str (Your JIRA environment, IE 'https://jira.net')
    ISSUE_TRACKER_USER = None  # type: str (Recommended to be a service account)
    ISSUE_TRACKER_PASSWORD = None  # type: str
    ISSUE_TRACKER_PROJECT_ID = None  # type: int (Project ID for the project you would like JIRA tickets to be created in)
    ISSUE_TRACKER_CLIENT = None  # type: str (Fully qualified class name and path)
    ISSUE_TRACKER_CLIENT_ENABLED = False  # type: bool (Enabling the feature, must be set to True)
    ISSUE_TRACKER_MAX_RESULTS = None  # type: int (Max issues to display at a time)
    ISSUE_TRACKER_ISSUE_TYPE_ID = None # type: int (Jira only: Override default issue tracker ID whenever needed for cloud/hosted deployments)
```
## Programmatic Descriptions
Amundsen supports configuring other mark down supported non-editable description boxes on the table page.
This can be useful if you have multiple writers which want to write different pieces of information to Amundsen
that are either very company specific and thus would never be directly integrated into Amundsen or require long form text
to properly convey the information.

What are some more specific examples of what could be used for this?
- You have an existing process that generates quality reports for a dataset that you want to embed in the table page.
- You have a process that detects pii information (also adding the appropriate tag/badge) but also generates a simple
report to provide context.
- You have extended table information that is applicable to your datastore which you want to scrape and provide in the
table page

Programmatic descriptions are referred to by a "description source" which is a unique identifier.
In the UI, they will appear on the table page under structured metadata.

In config.py you can then configure the descriptions to have a custom order, as well as whether or not they should exist in the left column or right column.
```
PROGRAMMATIC_DISPLAY = {
    'RIGHT': {
      "test3" : {},
      "test2" : { "display_order": 0 }
    },
    'LEFT': {
      "test1" : { "display_order": 1 },
      "test0" : { "display_order": 0 },
    },
    'test4': {"display_order": 0},
}
```
Description sources not mentioned in the configuration will be alphabetically placed at the bottom of the list. If `PROGRAMMATIC_DISPLAY` is left at `None` all added fields will show up in the order in which they were returned from the backend. Here is a screenshot of what it would look like in the bottom left:

<img src='img/programmatic_descriptions.png' width='50%' />

## Uneditable Table Descriptions
Amundsen supports configuring table and column description to be non-editable for selective tables. You may want to make table
descriptions non-editable due to various reasons such as table already has table description from source of truth.
You can define matching rules in  [config.py](https://github.com/lyft/amundsenfrontendlibrary/blob/master/amundsen_application/config.py) for selecting tables. This configuration is useful as table selection criteria can
be company specific which will not directly integrated with Amundsen.
You can use different combinations of schema and table name for selecting tables.

Here are some examples when this feature can be used:
1. You want to set ALL tables in your application as un-editable
2. You want to set all tables with a given schema or schema pattern as un-editable.
3. You want to set all tables with a specific table name pattern in a given schema pattern as un-editable.
4. You want to set all tables with a given table name pattern as un-editable.

Amundsen has two variables in `config.py` file which can be used to define match rules:
1. `ALL_UNEDITABLE_SCHEMAS` : boolean on/off switch for ability to edit tables. This can also be set using the environment variable 'ALL_UNEDITABLE_SCHEMAS'
2. `UNEDITABLE_SCHEMAS` : Set of schemas where all tables should be un-editable. It takes exact schema name.
3. `UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES` : List of MatchRuleObject, where each MatchRuleObject consists of regex for
schema name or regex for table name or both.

Purpose of `ALL_UNEDITABLE_SCHEMAS` is to provide a blanket on/off switch for disabling editing schemas. This should be used if you plan to up
all of your schemas via databuilder rather then allow users to do it via the UI.

Purpose of `UNEDITABLE_SCHEMAS` can be fulfilled by `UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES` but we are keeping both
variables for backward compatibility.
If you want to restrict tables from a given schemas then you can use `UNEDITABLE_SCHEMAS` as follows:
```python
UNEDITABLE_SCHEMAS = set(['schema1', 'schema2'])
```
After above configuration, all tables in 'schema1' and 'schema2' will have non-editable table and column descriptions.

If you have more complex matching rules you can use `UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES`. It provides you more flexibility
and control as you can create multiple match rules and use regex for matching schema and table names.

You can configure your match rules in `config.py` as follow:
```python
UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES = [
        # match rule for all table in schema1
        MatchRuleObject(schema_regex=r"^(schema1)"),
        # macth rule for all tables in schema2 and schema3
        MatchRuleObject(schema_regex=r"^(schema2|schema3)"),
        # match rule for tables in schema4 with table name pattern 'noedit_*'
        MatchRuleObject(schema_regex=r"^(schema4)", table_name_regex=r"^noedit_([a-zA-Z_0-9]+)"),
        # match rule for tables in schema5, schema6 and schema7 with table name pattern 'noedit_*'
        MatchRuleObject(schema_regex=r"^(schema5|schema6|schema7)", table_name_regex=r"^noedit_([a-zA-Z_0-9]+)"),
        # match rule for all tables with table name pattern 'others_*'
        MatchRuleObject(table_name_regex=r"^others_([a-zA-Z_0-9]+)")
    ]
```

After configuring this, users will not be able to edit table and column descriptions of any table matching above match rules
from UI.
