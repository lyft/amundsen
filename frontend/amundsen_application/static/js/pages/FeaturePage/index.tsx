// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { RouteComponentProps } from 'react-router';

import TabsComponent, { TabInfo } from 'components/TabsComponent';
import Breadcrumb from 'components/Breadcrumb';
import EditableSection from 'components/EditableSection';
import TagInput from 'components/Tags/TagInput';
import BadgeList from 'features/BadgeList';
import LineageList from 'pages/TableDetailPage/LineageList';
import {
  getDisplayNameByResource,
  getMaxLength,
  getSourceDisplayName,
  isFeatureListLineageEnabled,
} from 'config/config-utils';
import { GlobalState } from 'ducks/rootReducer';
import {
  FeatureCodeState,
  FeaturePreviewDataState,
  getFeature,
  getFeatureCode,
  getFeatureLineage,
  FeatureLineageState,
  getFeaturePreviewData,
} from 'ducks/feature/reducer';
import {
  GetFeatureCodeRequest,
  GetFeaturePreviewDataRequest,
  GetFeatureRequest,
} from 'ducks/feature/types';
import { GetFeatureLineageRequest } from 'ducks/lineage/types';
import { PreviewDataTable } from 'features/PreviewData';
import { FeatureMetadata, FeaturePreviewQueryParams } from 'interfaces/Feature';
import { ResourceType } from 'interfaces/Resources';
import { logAction } from 'utils/analytics';
import { getLoggingParams } from 'utils/logUtils';
import { formatDateTimeShort } from 'utils/dateUtils';

import FeatureDescEditableText from './FeatureDescEditableText';
import FeatureOwnerEditor from './FeatureOwnerEditor';
import { GenerationCode } from './GenerationCode';

import {
  PREVIEW_DATA_TAB_TITLE,
  DATA_TYPE_TITLE,
  DESCRIPTION_TITLE,
  ENTITY_TITLE,
  FEATURE_GROUP_TITLE,
  FEATURE_TAB,
  GEN_CODE_TAB_TITLE,
  LAST_UPDATED_TITLE,
  OWNERS_TITLE,
  PARTITION_KEY_TITLE,
  SOURCE_TITLE,
  TAG_TITLE,
  VERSION_TITLE,
  UPSTREAM_TAB_TITLE,
} from './constants';

import './styles.scss';

interface StateFromProps {
  isLoading: boolean;
  statusCode: number | null;
  feature: FeatureMetadata;
  featureCode: FeatureCodeState;
  featureLineage: FeatureLineageState;
  preview: FeaturePreviewDataState;
}

export interface DispatchFromProps {
  getFeatureDispatch: (
    key: string,
    index: string,
    source: string
  ) => GetFeatureRequest;
  getFeatureCodeDispatch: (key: string) => GetFeatureCodeRequest;
  getFeatureLineageDispatch: (key: string) => GetFeatureLineageRequest;
  getFeaturePreviewDispatch: (
    payload: FeaturePreviewQueryParams
  ) => GetFeaturePreviewDataRequest;
}

interface FeatureRouteParams {
  group: string;
  name: string;
  version: string;
}

export type FeaturePageProps = RouteComponentProps<FeatureRouteParams> &
  StateFromProps &
  DispatchFromProps;

export const FeaturePageLoader: React.FC = () => (
  <div className="resource-detail-layout feature-page">
    <header className="resource-header">
      <section className="header-section">
        <div className="shimmer-page-title is-shimmer-animated" />
        <div className="shimmer-page-subtitle is-shimmer-animated" />
      </section>
    </header>
    <article className="column-layout-1">
      <aside className="left-panel">
        <section className="metadata-section">
          <div className="shimmer-section-title is-shimmer-animated" />
          <div className="shimmer-section-content is-shimmer-animated" />
        </section>
        <section className="column-layout-2">
          <section className="left-panel">
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
          </section>
          <section className="right-panel">
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
            <section className="metadata-section">
              <div className="shimmer-section-title is-shimmer-animated" />
              <div className="shimmer-section-content is-shimmer-animated" />
            </section>
          </section>
        </section>
      </aside>
      <main className="right-panel">
        <section className="metadata-section">
          <div className="shimmer-tab-title">
            <div className="shimmer-tab is-shimmer-animated" />
            <div className="shimmer-tab is-shimmer-animated" />
            <div className="shimmer-tab is-shimmer-animated" />
          </div>
          <div className="shimmer-tab-content is-shimmer-animated" />
          <div className="shimmer-tab-content is-shimmer-animated" />
          <div className="shimmer-tab-content is-shimmer-animated" />
          <div className="shimmer-tab-content is-shimmer-animated" />
          <div className="shimmer-tab-content is-shimmer-animated" />
        </section>
      </main>
    </article>
  </div>
);

export function renderTabs(featureCode, featureLineage, preview) {
  const tabInfo: TabInfo[] = [];
  tabInfo.push({
    content: (
      <PreviewDataTable
        isLoading={preview.isLoading}
        previewData={preview.previewData}
      />
    ),
    key: FEATURE_TAB.PREVIEW_DATA,
    title: PREVIEW_DATA_TAB_TITLE,
  });
  if (isFeatureListLineageEnabled()) {
    const upstreamItems = featureLineage.featureLineage.upstream_entities;
    if (upstreamItems.length) {
      tabInfo.push({
        content: <LineageList items={upstreamItems} direction="upstream" />,
        key: FEATURE_TAB.UPSTREAM,
        title: `${UPSTREAM_TAB_TITLE} (${upstreamItems.length})`,
      });
    }
  }
  tabInfo.push({
    content: (
      <GenerationCode
        isLoading={featureCode.isLoading}
        featureCode={featureCode.featureCode}
      />
    ),
    key: FEATURE_TAB.GEN_CODE,
    title: GEN_CODE_TAB_TITLE,
  });

  return (
    <TabsComponent
      tabs={tabInfo}
      defaultTab={FEATURE_TAB.PREVIEW_DATA}
      onSelect={(key) => {
        logAction({
          command: 'click',
          target_id: 'feature_page_tab',
          label: key,
        });
      }}
    />
  );
}

export const getFeatureKey = (group: string, name: string, version: string) =>
  `${group}/${name}/${version}`;

export const FeaturePage: React.FC<FeaturePageProps> = ({
  isLoading,
  feature,
  featureCode,
  featureLineage,
  preview,
  getFeatureLineageDispatch,
  getFeatureDispatch,
  getFeatureCodeDispatch,
  getFeaturePreviewDispatch,
  location,
  match,
}: FeaturePageProps) => {
  const [key, setKey] = React.useState('');
  React.useEffect(() => {
    const { group, name, version } = match.params;
    const newKey = getFeatureKey(group, name, version);
    if (key !== newKey) {
      const { index, source } = getLoggingParams(location.search);
      setKey(newKey);
      getFeatureDispatch(newKey, index, source);
      getFeatureCodeDispatch(newKey);
      getFeatureLineageDispatch(newKey);
      getFeaturePreviewDispatch({
        version,
        feature_group: group,
        feature_name: name,
      });
    }
  });

  if (isLoading) {
    return <FeaturePageLoader />;
  }
  const sourcesWithDisplay = feature.availability.map((source) =>
    getSourceDisplayName(source, ResourceType.feature)
  );
  return (
    <div className="resource-detail-layout feature-page">
      <header className="resource-header">
        <section className="header-section">
          <Breadcrumb />
          <span className="icon icon-header icon-database" />
        </section>
        <section className="header-section">
          <h1
            className="header-title-text text-headline-w2 truncated"
            title={feature.name}
          >
            {feature.feature_group}.{feature.name}
          </h1>
          <p className="header-subtitle text-body-w3">
            {getDisplayNameByResource(ResourceType.feature)}
            {sourcesWithDisplay.length > 0 && '&bull;&nbsp;'}
            {sourcesWithDisplay.join(', ')}
            {feature.badges.length > 0 && <BadgeList badges={feature.badges} />}
          </p>
        </section>
      </header>
      <article className="column-layout-1">
        <aside className="left-panel">
          <EditableSection title={DESCRIPTION_TITLE}>
            <FeatureDescEditableText
              maxLength={getMaxLength('tableDescLength')}
              value={feature.description}
              editable
            />
          </EditableSection>
          <section className="column-layout-2">
            <section className="left-panel">
              <section className="metadata-section">
                <h3 className="section-title text-title-w3">{ENTITY_TITLE}</h3>
                {feature.entity}
              </section>
              <section className="metadata-section">
                <h3 className="section-title text-title-w3">
                  {DATA_TYPE_TITLE}
                </h3>
                {feature.data_type}
              </section>
              <section className="metadata-section">
                <h3 className="section-title text-title-w3">{SOURCE_TITLE}</h3>
                {feature.availability}
              </section>
              <section className="metadata-section">
                <h3 className="section-title text-title-w3">
                  {LAST_UPDATED_TITLE}
                </h3>
                <time>
                  {formatDateTimeShort({
                    epochTimestamp: feature.last_updated_timestamp,
                  })}
                </time>
              </section>
              <EditableSection title={TAG_TITLE}>
                <TagInput
                  resourceType={ResourceType.feature}
                  uriKey={feature.key}
                />
              </EditableSection>
            </section>
            <section className="right-panel">
              <EditableSection title={OWNERS_TITLE}>
                <FeatureOwnerEditor resourceType={ResourceType.feature} />
              </EditableSection>
              {feature.partition_column !== null &&
                feature.partition_column !== undefined && (
                  <section className="metadata-section">
                    <h3 className="section-title text-title-w3">
                      {PARTITION_KEY_TITLE}
                    </h3>
                    {feature.partition_column}
                  </section>
                )}
              <section className="metadata-section">
                <h3 className="section-title text-title-w3">{VERSION_TITLE}</h3>
                {feature.version}
              </section>
              <section className="metadata-section">
                <h3 className="section-title text-title-w3">
                  {FEATURE_GROUP_TITLE}
                </h3>
                {feature.feature_group}
              </section>
            </section>
          </section>
        </aside>
        <main className="right-panel">
          {renderTabs(featureCode, featureLineage, preview)}
        </main>
      </article>
    </div>
  );
};

export const mapStateToProps = (state: GlobalState) => ({
  isLoading: state.feature.isLoading,
  statusCode: state.feature.statusCode,
  feature: state.feature.feature,
  featureCode: state.feature.featureCode,
  featureLineage: state.feature.featureLineage,
  preview: state.feature.preview,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      getFeatureDispatch: getFeature,
      getFeatureCodeDispatch: getFeatureCode,
      getFeatureLineageDispatch: getFeatureLineage,
      getFeaturePreviewDispatch: getFeaturePreviewData,
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(FeaturePage);
