// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';
import * as DocumentTitle from 'react-document-title';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { RouteComponentProps } from 'react-router';

import { GlobalState } from 'ducks/rootReducer';
import { getTableData } from 'ducks/tableMetadata/reducer';
import { getTableLineage } from 'ducks/lineage/reducer';
import { openRequestDescriptionDialog } from 'ducks/notification/reducer';
import { updateSearchState } from 'ducks/search/reducer';
import { GetTableDataRequest } from 'ducks/tableMetadata/types';
import { GetTableLineageRequest } from 'ducks/lineage/types';
import { OpenRequestAction } from 'ducks/notification/types';
import { UpdateSearchStateRequest } from 'ducks/search/types';

import {
  getDescriptionSourceDisplayName,
  getMaxLength,
  getSourceIconClass,
  getResourceNotices,
  getTableSortCriterias,
  indexDashboardsEnabled,
  issueTrackingEnabled,
  isTableListLineageEnabled,
  notificationsEnabled,
} from 'config/config-utils';

import BadgeList from 'features/BadgeList';
import ColumnList from 'features/ColumnList';

import BookmarkIcon from 'components/Bookmark/BookmarkIcon';
import Breadcrumb from 'components/Breadcrumb';
import TabsComponent, { TabInfo } from 'components/TabsComponent';
import TagInput from 'components/Tags/TagInput';
import EditableText from 'components/EditableText';
import LoadingSpinner from 'components/LoadingSpinner';
import EditableSection from 'components/EditableSection';
import Alert from 'components/Alert';

import { logAction, logClick } from 'utils/analytics';
import { formatDateTimeShort } from 'utils/dateUtils';
import { getLoggingParams } from 'utils/logUtils';
import { buildTableKey } from 'utils/navigationUtils';

import {
  ProgrammaticDescription,
  ResourceType,
  TableMetadata,
  RequestMetadataType,
  SortCriteria,
  Lineage,
} from 'interfaces';

import DataPreviewButton from './DataPreviewButton';
import ExploreButton from './ExploreButton';
import LineageButton from './LineageButton';
import FrequentUsers from './FrequentUsers';
import LineageLink from './LineageLink';
import LineageList from './LineageList';
import TableOwnerEditor from './TableOwnerEditor';
import SourceLink from './SourceLink';
import TableDashboardResourceList from './TableDashboardResourceList';
import TableDescEditableText from './TableDescEditableText';
import TableHeaderBullets from './TableHeaderBullets';
import TableIssues from './TableIssues';
import WatermarkLabel from './WatermarkLabel';
import WriterLink from './WriterLink';
import TableReportsDropdown from './ResourceReportsDropdown';
import RequestDescriptionText from './RequestDescriptionText';
import RequestMetadataForm from './RequestMetadataForm';
import ListSortingDropdown from './ListSortingDropdown';

import * as Constants from './constants';

import './styles.scss';

const SERVER_ERROR_CODE = 500;
const DASHBOARDS_PER_PAGE = 10;
const TABLE_SOURCE = 'table_page';
const SORT_CRITERIAS = {
  ...getTableSortCriterias(),
};

export interface PropsFromState {
  isLoading: boolean;
  isLoadingDashboards: boolean;
  numRelatedDashboards: number;
  statusCode: number | null;
  tableData: TableMetadata;
  tableLineage: Lineage;
}
export interface DispatchFromProps {
  getTableData: (
    key: string,
    searchIndex?: string,
    source?: string
  ) => GetTableDataRequest;
  getTableLineageDispatch: (key: string) => GetTableLineageRequest;
  openRequestDescriptionDialog: (
    requestMetadataType: RequestMetadataType,
    columnName: string
  ) => OpenRequestAction;
  searchSchema: (schemaText: string) => UpdateSearchStateRequest;
}

export interface MatchProps {
  cluster: string;
  database: string;
  schema: string;
  table: string;
}

export type TableDetailProps = PropsFromState &
  DispatchFromProps &
  RouteComponentProps<MatchProps>;

const ErrorMessage = () => (
  <div className="container error-label">
    <Breadcrumb />
    <label>{Constants.ERROR_MESSAGE}</label>
  </div>
);

export interface StateProps {
  sortedBy: SortCriteria;
  currentTab: string;
}

export class TableDetail extends React.Component<
  TableDetailProps & RouteComponentProps<any>,
  StateProps
> {
  private key: string;

  private didComponentMount: boolean = false;

  state = {
    sortedBy: SORT_CRITERIAS.sort_order,
    currentTab: Constants.TABLE_TAB.COLUMN,
  };

  componentDidMount() {
    const { location, getTableData, getTableLineageDispatch } = this.props;
    const { index, source } = getLoggingParams(location.search);
    const {
      match: { params },
    } = this.props;
    this.key = buildTableKey(params);
    getTableData(this.key, index, source);

    if (isTableListLineageEnabled()) {
      getTableLineageDispatch(this.key);
    }
    this.didComponentMount = true;
  }

  componentDidUpdate() {
    const {
      location,
      getTableData,
      getTableLineageDispatch,
      match: { params },
    } = this.props;
    const newKey = buildTableKey(params);

    if (this.key !== newKey) {
      const { index, source } = getLoggingParams(location.search);

      this.key = newKey;
      getTableData(this.key, index, source);

      if (isTableListLineageEnabled()) {
        getTableLineageDispatch(this.key);
      }
    }
  }

  getDisplayName() {
    const { match } = this.props;
    const { params } = match;

    return `${params.schema}.${params.table}`;
  }

  handleClick = (e) => {
    const { match, searchSchema } = this.props;
    const { params } = match;
    const schemaText = params.schema;

    logClick(e, {
      target_type: 'schema',
      label: schemaText,
    });
    searchSchema(schemaText);
  };

  renderProgrammaticDesc = (
    descriptions: ProgrammaticDescription[] | undefined
  ) => {
    if (!descriptions) {
      return null;
    }

    return descriptions.map((d) => (
      <EditableSection key={`prog_desc:${d.source}`} title={d.source} readOnly>
        <EditableText maxLength={999999} value={d.text} editable={false} />
      </EditableSection>
    ));
  };

  handleSortingChange = (sortValue) => {
    this.toggleSort(SORT_CRITERIAS[sortValue]);
  };

  toggleSort = (sorting: SortCriteria) => {
    const { sortedBy } = this.state;

    if (sorting !== sortedBy) {
      this.setState({
        sortedBy: sorting,
      });
    }
  };

  renderTabs(editText, editUrl) {
    const tabInfo: TabInfo[] = [];
    const {
      isLoadingDashboards,
      numRelatedDashboards,
      tableData,
      openRequestDescriptionDialog,
      tableLineage,
    } = this.props;
    const { sortedBy } = this.state;

    // Default Column content
    tabInfo.push({
      content: (
        <ColumnList
          openRequestDescriptionDialog={openRequestDescriptionDialog}
          columns={tableData.columns}
          database={tableData.database}
          tableKey={tableData.key}
          editText={editText}
          editUrl={editUrl}
          sortBy={sortedBy}
        />
      ),
      key: Constants.TABLE_TAB.COLUMN,
      title: `Columns (${tableData.columns.length})`,
    });

    if (indexDashboardsEnabled()) {
      const loadingTitle = (
        <div className="tab-title">
          Dashboards <LoadingSpinner />
        </div>
      );

      tabInfo.push({
        content: (
          <TableDashboardResourceList
            itemsPerPage={DASHBOARDS_PER_PAGE}
            source={TABLE_SOURCE}
          />
        ),
        key: Constants.TABLE_TAB.DASHBOARD,
        title: isLoadingDashboards
          ? loadingTitle
          : `Dashboards (${numRelatedDashboards})`,
      });
    }

    if (isTableListLineageEnabled()) {
      if (tableLineage.upstream_entities.length > 0) {
        tabInfo.push({
          content: (
            <LineageList
              items={tableLineage.upstream_entities}
              direction="upstream"
            />
          ),
          key: Constants.TABLE_TAB.UPSTREAM,
          title: `Upstream (${tableLineage.upstream_entities.length})`,
        });
      }
      if (tableLineage.downstream_entities.length > 0) {
        tabInfo.push({
          content: (
            <LineageList
              items={tableLineage.downstream_entities}
              direction="downstream"
            />
          ),
          key: Constants.TABLE_TAB.DOWNSTREAM,
          title: `Downstream (${tableLineage.downstream_entities.length})`,
        });
      }
    }

    return (
      <TabsComponent
        tabs={tabInfo}
        defaultTab={Constants.TABLE_TAB.COLUMN}
        onSelect={(key) => {
          this.setState({ currentTab: key });
          logAction({
            command: 'click',
            target_id: 'table_detail_tab',
            label: key,
          });
        }}
      />
    );
  }

  render() {
    const { isLoading, statusCode, tableData } = this.props;
    const { currentTab } = this.state;
    let innerContent;

    // We want to avoid rendering the previous table's metadata before new data is fetched in componentDidMount
    if (isLoading || !this.didComponentMount) {
      innerContent = <LoadingSpinner />;
    } else if (statusCode === SERVER_ERROR_CODE) {
      innerContent = <ErrorMessage />;
    } else {
      const data = tableData;
      const editText = data.source
        ? `${Constants.EDIT_DESC_TEXT} ${getDescriptionSourceDisplayName(
            data.source.source_type
          )}`
        : '';
      const ownersEditText = data.source
        ? // TODO rename getDescriptionSourceDisplayName to more generic since
          // owners also edited on the same file?
          `${Constants.EDIT_OWNERS_TEXT} ${getDescriptionSourceDisplayName(
            data.source.source_type
          )}`
        : '';
      const editUrl = data.source ? data.source.source : '';
      const tableNotice = getResourceNotices(
        ResourceType.table,
        `${data.cluster}.${data.database}.${data.schema}.${data.name}`
      );

      innerContent = (
        <div className="resource-detail-layout table-detail">
          {notificationsEnabled() && <RequestMetadataForm />}
          <header className="resource-header">
            <div className="header-section">
              <Breadcrumb />
              <span
                className={
                  'icon icon-header ' +
                  getSourceIconClass(data.database, ResourceType.table)
                }
              />
            </div>
            <div className="header-section header-title">
              <h1
                className="header-title-text truncated"
                title={`${data.schema}.${data.name}`}
              >
                <Link to="/search" onClick={this.handleClick}>
                  {data.schema}
                </Link>
                .{data.name}
              </h1>
              <BookmarkIcon
                bookmarkKey={data.key}
                resourceType={ResourceType.table}
              />
              <div className="body-2">
                <TableHeaderBullets
                  database={data.database}
                  cluster={data.cluster}
                  isView={data.is_view}
                />
                {data.badges.length > 0 && <BadgeList badges={data.badges} />}
              </div>
            </div>
            <div className="header-section header-links">
              <WriterLink tableWriter={data.table_writer} />
              <LineageLink tableData={data} />
              <SourceLink tableSource={data.source} />
            </div>
            <div className="header-section header-buttons">
              <LineageButton tableData={data} />
              <TableReportsDropdown resourceReports={data.resource_reports} />
              <DataPreviewButton modalTitle={this.getDisplayName()} />
              <ExploreButton tableData={data} />
            </div>
          </header>
          <div className="column-layout-1">
            <aside className="left-panel">
              {!!tableNotice && (
                <Alert
                  message={tableNotice.messageHtml}
                  severity={tableNotice.severity}
                />
              )}
              <EditableSection
                title={Constants.DESCRIPTION_TITLE}
                readOnly={!data.is_editable}
                editText={editText}
                editUrl={editUrl || undefined}
              >
                <TableDescEditableText
                  maxLength={getMaxLength('tableDescLength')}
                  value={data.description}
                  editable={data.is_editable}
                />
                <span>
                  {notificationsEnabled() && <RequestDescriptionText />}
                </span>
              </EditableSection>
              {issueTrackingEnabled() && (
                <section className="metadata-section">
                  <TableIssues
                    tableKey={this.key}
                    tableName={this.getDisplayName()}
                  />
                </section>
              )}
              <section className="column-layout-2">
                <section className="left-panel">
                  {!!data.last_updated_timestamp && (
                    <section className="metadata-section">
                      <div className="section-title">
                        {Constants.LAST_UPDATED_TITLE}
                      </div>
                      <time className="body-2">
                        {formatDateTimeShort({
                          epochTimestamp: data.last_updated_timestamp,
                        })}
                      </time>
                    </section>
                  )}
                  <section className="metadata-section">
                    <div className="section-title">
                      {Constants.DATE_RANGE_TITLE}
                    </div>
                    <WatermarkLabel watermarks={data.watermarks} />
                  </section>
                  <EditableSection title={Constants.TAG_TITLE}>
                    <TagInput
                      resourceType={ResourceType.table}
                      uriKey={tableData.key}
                    />
                  </EditableSection>
                  {this.renderProgrammaticDesc(
                    data.programmatic_descriptions.left
                  )}
                </section>
                <section className="right-panel">
                  <EditableSection
                    title={Constants.OWNERS_TITLE}
                    readOnly={!data.is_editable}
                    editText={ownersEditText}
                    editUrl={editUrl || undefined}
                  >
                    <TableOwnerEditor resourceType={ResourceType.table} />
                  </EditableSection>
                  <section className="metadata-section">
                    <div className="section-title">
                      {Constants.FREQ_USERS_TITLE}
                    </div>
                    <FrequentUsers readers={data.table_readers} />
                  </section>
                  {this.renderProgrammaticDesc(
                    data.programmatic_descriptions.right
                  )}
                </section>
              </section>
              {this.renderProgrammaticDesc(
                data.programmatic_descriptions.other
              )}
            </aside>
            <main className="right-panel">
              {currentTab === Constants.TABLE_TAB.COLUMN && (
                <ListSortingDropdown
                  options={SORT_CRITERIAS}
                  onChange={this.handleSortingChange}
                />
              )}
              {this.renderTabs(editText, editUrl)}
            </main>
          </div>
        </div>
      );
    }

    return (
      <DocumentTitle
        title={`${this.getDisplayName()} - Amundsen Table Details`}
      >
        {innerContent}
      </DocumentTitle>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  isLoading: state.tableMetadata.isLoading,
  statusCode: state.tableMetadata.statusCode,
  tableData: state.tableMetadata.tableData,
  tableLineage: state.lineage.lineageTree,
  numRelatedDashboards: state.tableMetadata.dashboards
    ? state.tableMetadata.dashboards.dashboards.length
    : 0,
  isLoadingDashboards: state.tableMetadata.dashboards
    ? state.tableMetadata.dashboards.isLoading
    : true,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getTableData,
      getTableLineageDispatch: getTableLineage,
      openRequestDescriptionDialog,
      searchSchema: (schemaText: string) =>
        updateSearchState({
          filters: {
            [ResourceType.table]: { schema: schemaText },
          },
          submitSearch: true,
        }),
    },
    dispatch
  );

export default connect<PropsFromState, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(TableDetail);
