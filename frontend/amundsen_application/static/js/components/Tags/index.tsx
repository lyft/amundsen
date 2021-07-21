// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { Tag } from 'interfaces';

import { GlobalState } from 'ducks/rootReducer';
import { getAllTags } from 'ducks/tags/reducer';
import { GetAllTagsRequest } from 'ducks/tags/types';
import { getCuratedTags } from 'config/config-utils';
import TagsList from './TagsList';

import { POPULAR_TAGS_NUMBER } from './constants';

export interface StateFromProps {
  curatedTags: Tag[];
  popularTags: Tag[];
  otherTags: Tag[];
  isLoading: boolean;
}

interface OwnProps {
  shortTagsList: boolean;
}

export interface DispatchFromProps {
  getAllTags: () => GetAllTagsRequest;
}

export type TagsListContainerProps = StateFromProps &
  DispatchFromProps &
  OwnProps;

export class TagsListContainer extends React.Component<TagsListContainerProps> {
  componentDidMount() {
    this.props.getAllTags();
  }

  render() {
    const {
      isLoading,
      curatedTags,
      popularTags,
      otherTags,
      shortTagsList,
    } = this.props;
    return (
      <article className="tag-list">
        <TagsList
          curatedTags={curatedTags}
          popularTags={popularTags}
          otherTags={otherTags}
          isLoading={isLoading}
          shortTagsList={shortTagsList}
        />
      </article>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => {
  // TODO: These functions are selectors, consider moving them into the ducks
  const allTags = state.tags.allTags.tags;

  const allTagsNoZeros = allTags.filter(
    (tag) => tag.tag_count !== undefined && tag.tag_count > 0
  );

  const curatedTagsList = getCuratedTags();

  let curatedTags: Tag[] = [];
  let popularTags: Tag[] = [];
  let otherTags: Tag[] = [];

  if (curatedTagsList.length > 0) {
    // keeping curated tags with zero usage count
    curatedTags = allTags.filter(
      (tag) => curatedTagsList.indexOf(tag.tag_name) !== -1
    );
    otherTags = allTagsNoZeros
      .filter((tag) => curatedTagsList.indexOf(tag.tag_name) === -1)
      .sort((a, b) => {
        if (a.tag_name < b.tag_name) return -1;
        if (a.tag_name > b.tag_name) return 1;
        return 0;
      });
  } else {
    const tagsByUsage = allTagsNoZeros
      .sort((a, b) => {
        if (a.tag_count === undefined || b.tag_count === undefined) {
          return 0;
        }
        return a.tag_count - b.tag_count;
      })
      .reverse();
    popularTags = tagsByUsage.slice(0, POPULAR_TAGS_NUMBER).sort((a, b) => {
      if (a.tag_name < b.tag_name) return -1;
      if (a.tag_name > b.tag_name) return 1;
      return 0;
    });
    otherTags = tagsByUsage
      .slice(POPULAR_TAGS_NUMBER, tagsByUsage.length)
      .sort((a, b) => {
        if (a.tag_name < b.tag_name) return -1;
        if (a.tag_name > b.tag_name) return 1;
        return 0;
      });
  }

  return {
    curatedTags,
    popularTags,
    otherTags,
    isLoading: state.tags.allTags.isLoading,
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ getAllTags }, dispatch);

export default connect<StateFromProps, DispatchFromProps, OwnProps>(
  mapStateToProps,
  mapDispatchToProps
)(TagsListContainer);
