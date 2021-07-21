// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { ResourceType, Tag, SearchType } from 'interfaces';

import { updateSearchState } from 'ducks/search/reducer';
import { UpdateSearchStateRequest } from 'ducks/search/types';
import { logClick } from 'utils/analytics';

import './styles.scss';

interface OwnProps {
  data: Tag;
  compact?: boolean;
}

export interface DispatchFromProps {
  searchTag: (tagName: string) => UpdateSearchStateRequest;
}

export type TagInfoProps = OwnProps & DispatchFromProps;

export class TagInfo extends React.Component<TagInfoProps> {
  static defaultProps = {
    compact: true,
  };

  onClick = (e) => {
    const name = this.props.data.tag_name;
    logClick(e, {
      target_type: 'tag',
      label: name,
    });
    this.props.searchTag(name);
  };

  render() {
    const name = this.props.data.tag_name;

    return (
      <button
        id={`tag::${name}`}
        className={'btn tag-button' + (this.props.compact ? ' compact' : '')}
        onClick={this.onClick}
      >
        <span className="tag-name">{name}</span>
        {!this.props.compact && (
          <span className="tag-count">{this.props.data.tag_count}</span>
        )}
      </button>
    );
  }
}

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      searchTag: (tagName: string) =>
        updateSearchState({
          filters: {
            [ResourceType.dashboard]: { tag: tagName },
            [ResourceType.table]: { tag: tagName },
          },
          submitSearch: true,
        }),
    },
    dispatch
  );

export default connect<null, DispatchFromProps, OwnProps>(
  null,
  mapDispatchToProps
)(TagInfo);
