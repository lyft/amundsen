// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { addBookmark, removeBookmark } from 'ducks/bookmark/reducer';
import {
  AddBookmarkRequest,
  RemoveBookmarkRequest,
} from 'ducks/bookmark/types';
import { GlobalState } from 'ducks/rootReducer';

import { ResourceType } from 'interfaces';

import './styles.scss';

interface StateFromProps {
  isBookmarked: boolean;
}

interface DispatchFromProps {
  addBookmark: (key: string, type: ResourceType) => AddBookmarkRequest;
  removeBookmark: (key: string, type: ResourceType) => RemoveBookmarkRequest;
}

interface OwnProps {
  bookmarkKey: string;
  large?: boolean;
  resourceType: ResourceType;
}

export type BookmarkIconProps = StateFromProps & DispatchFromProps & OwnProps;

export class BookmarkIcon extends React.Component<BookmarkIconProps> {
  public static defaultProps: Partial<OwnProps> = {
    large: false,
  };

  handleClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    event.preventDefault();

    if (this.props.isBookmarked) {
      this.props.removeBookmark(
        this.props.bookmarkKey,
        this.props.resourceType
      );
    } else {
      this.props.addBookmark(this.props.bookmarkKey, this.props.resourceType);
    }
  };

  render() {
    return (
      <div
        className={
          'bookmark-icon ' + (this.props.large ? 'bookmark-large' : '')
        }
        onClick={this.handleClick}
      >
        <img
          className={
            'icon ' +
            (this.props.isBookmarked ? 'icon-bookmark-filled' : 'icon-bookmark')
          }
          alt=""
        />
      </div>
    );
  }
}

export const mapStateToProps = (state: GlobalState, ownProps: OwnProps) => ({
  bookmarkKey: ownProps.bookmarkKey,
  isBookmarked: state.bookmarks.myBookmarks[ownProps.resourceType].some(
    (bookmark) => bookmark.key === ownProps.bookmarkKey
  ),
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ addBookmark, removeBookmark }, dispatch);

export default connect<StateFromProps, DispatchFromProps, OwnProps>(
  mapStateToProps,
  mapDispatchToProps
)(BookmarkIcon);
