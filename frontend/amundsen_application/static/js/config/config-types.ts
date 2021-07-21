import { FilterType, ResourceType, SortCriteria } from '../interfaces';

/**
 * AppConfig and AppConfigCustom should share the same definition, except each field in AppConfigCustom
 * is optional. If you choose to override one of the configs, you must provide the full type definition
 * for that section.
 */

export interface AppConfig {
  analytics: AnalyticsConfig;
  badges: BadgeConfig;
  browse: BrowseConfig;
  date: DateFormatConfig;
  editableText: EditableTextConfig;
  indexDashboards: IndexDashboardsConfig;
  indexUsers: IndexUsersConfig;
  indexFeatures: IndexFeaturesConfig;
  userIdLabel?: string /* Temporary configuration due to lacking string customization/translation support */;
  issueTracking: IssueTrackingConfig;
  logoPath: string | null;
  logoTitle: string;
  documentTitle: string;
  numberFormat: NumberFormatConfig | null;
  mailClientFeatures: MailClientFeaturesConfig;
  announcements: AnnoucementsFeaturesConfig;
  navLinks: Array<LinkConfig>;
  resourceConfig: ResourceConfig;
  featureLineage: FeatureLineageConfig;
  tableLineage: TableLineageConfig;
  columnLineage: ColumnLineageConfig;
  tableProfile: TableProfileConfig;
}

export interface AppConfigCustom {
  analytics?: AnalyticsConfig;
  badges?: BadgeConfig;
  browse?: BrowseConfig;
  date?: DateFormatConfig;
  editableText?: EditableTextConfig;
  indexDashboards?: IndexDashboardsConfig;
  indexUsers?: IndexUsersConfig;
  indexFeatures?: IndexFeaturesConfig;
  userIdLabel?: string /* Temporary configuration due to lacking string customization/translation support */;
  issueTracking?: IssueTrackingConfig;
  logoPath?: string;
  logoTitle?: string;
  documentTitle?: string;
  numberFormat?: NumberFormatConfig | null;
  mailClientFeatures?: MailClientFeaturesConfig;
  announcements?: AnnoucementsFeaturesConfig;
  navLinks?: Array<LinkConfig>;
  resourceConfig?: ResourceConfig;
  featureLineage?: FeatureLineageConfig;
  tableLineage?: TableLineageConfig;
  columnLineage?: ColumnLineageConfig;
  tableProfile?: TableProfileConfig;
}

/**
 * AnalyticsConfig - Configure a single analytics destination
 *
 * plugins - array of AnalyticsPlugin functions (upstream doesn't expose this type, so any).
 */
export interface AnalyticsConfig {
  plugins: Array<any>;
}

/**
 * BrowseConfig - Customize the 'browse' page.
 *
 * curatedTags - An array of tags to show in a separate section at the top.
 * showAllTags - Shows all tags when true, or only curated tags if false
 */
interface BrowseConfig {
  curatedTags: Array<string>;
  showAllTags: boolean;
}

/**
 * The data shape of MultiSelectFilterCategory.options
 *
 * displaName - The display name of the multi-select filter option
 * value - The value the option represents
 */
interface MultiSelectFilterOptions {
  displayName?: string;
  value: string;
}

/**
 * Base interface for all possible FilterConfig objects
 *
 * categoryId - The filter category that this config represents, e.g. 'database' or 'badges'
 * displayName - The displayName for the filter category
 * helpText - An option string of text that will render in the filter UI for the filter category
 * type - The FilterType for this filter category
 */
interface BaseFilterCategory {
  categoryId: string;
  displayName: string;
  helpText?: string;
  type: FilterType;
}

/**
 * Interface for filter categories which allow multiple values to be selected by the user
 */
interface MultiSelectFilterCategory extends BaseFilterCategory {
  type: FilterType.CHECKBOX_SELECT;
  options: MultiSelectFilterOptions[];
}

/**
 * Interface for filter categories which allow only one value to be entered by the user
 */
interface SingleFilterCategory extends BaseFilterCategory {
  type: FilterType.INPUT_SELECT;
}

/**
 * Configures filter categories for each resource
 */
export type FilterConfig = (MultiSelectFilterCategory | SingleFilterCategory)[];

/**
 * Configures the UI for a given entity source
 */
type SourcesConfig = {
  [id: string]: {
    displayName?: string;
    iconClass?: string;
  };
};

/**
 * Configures the UI for a given table description source
 */
type DescriptionSourceConfig = {
  [id: string]: { displayName: string; iconPath: string };
};

/**
 * Shows criterias to sort tables
 */
type SortCriteriaConfig = {
  [key: string]: SortCriteria;
};

export enum NoticeSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ALERT = 'alert',
}
export interface NoticeType {
  severity: NoticeSeverity;
  messageHtml: string | ((resourceName: string) => string);
}
/**
 * Stats configuration options
 */
type StatsConfig = {
  uniqueValueTypeName: string;
};

/**
 * A list of notices where the key is the 'schema.name' of the table and the value
 * a Notice
 */
type NoticesConfigType = Record<string, NoticeType>;

/**
 * Base interface for all possible ResourceConfig objects
 *
 * displayName - The name displayed throughout the application to refer to this resource type
 * filterCategories - Optional configuration for any filters that can be applied to this resource
 */
interface BaseResourceConfig {
  displayName: string;
  filterCategories?: FilterConfig;
  supportedSources?: SourcesConfig;
  notices?: NoticesConfigType;
}

interface TableResourceConfig extends BaseResourceConfig {
  supportedDescriptionSources?: DescriptionSourceConfig;
  sortCriterias?: SortCriteriaConfig;
  stats?: StatsConfig;
}

export enum BadgeStyle {
  DANGER = 'negative',
  DEFAULT = 'neutral',
  INFO = 'info',
  PRIMARY = 'primary',
  SUCCESS = 'positive',
  WARNING = 'warning',
}

export interface BadgeStyleConfig {
  style: BadgeStyle;
  displayName?: string;
}

/**
 * BadgeConfig - Configure badge colors
 *
 * An object that maps badges to BadgeStyleConfigs
 */
interface BadgeConfig {
  [badge: string]: BadgeStyleConfig;
}

/**
 * DateConfig - Configure various date formats
 *
 */
interface DateFormatConfig {
  default: string;
  dateTimeLong: string;
  dateTimeShort: string;
}

/** ResourceConfig - For customizing values related to how various resources
 *                   are displayed in the UI.
 *
 * A map of each resource type to its configuration
 */
interface ResourceConfig {
  [ResourceType.dashboard]: BaseResourceConfig;
  [ResourceType.table]: TableResourceConfig;
  [ResourceType.user]: BaseResourceConfig;
  [ResourceType.feature]: BaseResourceConfig;
}

/**
 * MailClientFeaturesConfig - Enable/disable UI features with a dependency on
 *                            configuring a custom mail client.
 *
 * feedbackEnabled - Enables the feedback feature UI
 * notificationsEnabled - Enables any UI related to sending notifications to users
 */
interface MailClientFeaturesConfig {
  feedbackEnabled: boolean;
  notificationsEnabled: boolean;
}

/**
 * AnnoucementsFeaturesConfig - Enable/disable UI features related to the announcements
 *
 * enabled - Enables the announcements feature
 */
interface AnnoucementsFeaturesConfig {
  enabled: boolean;
}

/**
 * TableProfileConfig - Customize the "Table Profile" section of the "Table Details" page.
 *
 * isBeta - Adds a "beta" tag to the "Table Profile" section header.
 * isExploreEnabled - Enables the third party SQL explore feature.
 * exploreUrlGenerator - Generates a URL to a third party SQL explorable website.
 */
interface TableProfileConfig {
  isBeta: boolean;
  isExploreEnabled: boolean;
  exploreUrlGenerator: (
    database: string,
    cluster: string,
    schema: string,
    table: string,
    partitionKey?: string,
    partitionValue?: string
  ) => string;
}

/**
 * FeatureLineageConfig - enable upstream lineage tab for features
 */
interface FeatureLineageConfig {
  inAppListEnabled: boolean;
}

/**
 * TableLineageConfig - Customize the "Table Lineage" links of the "Table Details" page.
 * This feature is intended to link to an external lineage provider.
 *
 * iconPath - Path to an icon image to display next to the lineage URL.
 * isBeta - Adds a "beta" tag to the section header.
 * isEnabled - Whether to show or hide this section
 * urlGenerator - Generate a URL to the third party lineage website
 * inAppListEnabled - Enable the in app Upstream/Downstream tabs for table lineage. Requires backend support.
 */
interface TableLineageConfig {
  iconPath: string;
  isBeta: boolean;
  urlGenerator: (
    database: string,
    cluster: string,
    schema: string,
    table: string
  ) => string;
  externalEnabled: boolean;
  inAppListEnabled: boolean;
  inAppPageEnabled: boolean;
}

/**
 * ColumnLineageConfig - Configure column level lineage features in Amundsen.
 *
 * inAppListEnabled
 */
interface ColumnLineageConfig {
  inAppListEnabled: boolean;
  inAppPageEnabled: boolean;
  urlGenerator: (
    database: string,
    cluster: string,
    schema: string,
    table: string,
    column: string
  ) => string;
}

export interface LinkConfig {
  href: string;
  id: string;
  label: string;
  target?: string;
  use_router: boolean;
}

/**
 * IndexDashboardsConfig - When enabled, dashboards will be avaialable as searchable resources. This requires
 * dashboards objects to be ingested via Databuilder and made available in the metadata and serch services.
 *
 * enabled - Enables/disables this feature in the frontend only
 */
interface IndexDashboardsConfig {
  enabled: boolean;
}

/**
 * IndexUsersConfig - When enabled, users will be avaialable as searchable resources. This requires
 * user objects to bed ingested via Databuilder and made available in the metadata and serch services.
 *
 * enabled - Enables/disables this feature in the frontend only
 */
interface IndexUsersConfig {
  enabled: boolean;
}

/**
 * IndexFeaturesConfig - When enabled, ML features will be avaialable as searchable resources. This requires
 * feature objects to be ingested via Databuilder and made available in the metadata and serch services.
 *
 * enabled - Enables/disables this feature in the frontend only
 */
interface IndexFeaturesConfig {
  enabled: boolean;
}

/**
 * EditableTextConfig - Configure max length limits for editable fields
 *
 * tableDescLength - maxlength for table descriptions
 * columnDescLength - maxlength for column descriptions
 */
interface EditableTextConfig {
  tableDescLength: number;
  columnDescLength: number;
}
/**
 * IssueTrackingConfig - configures whether to display the issue tracking feature
 * that allows users to display tickets associated with a table and create ones
 * linked to a table
 */
interface IssueTrackingConfig {
  enabled: boolean;
}

export enum NumberStyle {
  DECIMAL = 'decimal',
  CURRENCY = 'currency',
  PERCENT = 'percent',
  UNIT = 'unit',
}

export interface NumberStyleConfig {
  style: NumberStyle;
  config: string;
}

/**
 * NumberFormatConfig - configurations for formatting different type of numbers like currency, percentage,number system
 * this allows users to display numbers in desired format
 */
export interface NumberFormatConfig {
  numberSystem: string | null;
  [NumberStyle.DECIMAL]?: NumberStyleConfig;
}
