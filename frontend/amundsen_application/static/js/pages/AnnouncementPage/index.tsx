// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';
// TODO - Consider an alternative to react-sanitized-html (large filesize)
import SanitizedHTML from 'react-sanitized-html';

import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

// TODO: Use css-modules instead of 'import'
import './styles.scss';

import { GlobalState } from 'ducks/rootReducer';
import { GetAnnouncementsRequest } from 'ducks/announcements/types';
import { getAnnouncements } from 'ducks/announcements';
import { AnnouncementPost } from 'interfaces';

const ANNOUNCEMENTS_HEADER_TEXT = 'Announcements';

export interface StateFromProps {
  posts: AnnouncementPost[];
}

export interface DispatchFromProps {
  announcementsGet: () => GetAnnouncementsRequest;
}

export type AnnouncementPageProps = StateFromProps & DispatchFromProps;

export class AnnouncementPage extends React.Component<AnnouncementPageProps> {
  componentDidMount() {
    const { announcementsGet } = this.props;

    announcementsGet();
  }

  createPost(post: AnnouncementPost, postIndex: number) {
    return (
      <div key={`post:${postIndex}`} className="post-container">
        <div className="post-header">
          <h2 className="post-title title-2">{post.title}</h2>
          <div className="body-secondary-3">{post.date}</div>
        </div>
        <div className="post-content">
          <SanitizedHTML html={post.html_content} />
        </div>
      </div>
    );
  }

  createPosts() {
    const { posts } = this.props;

    return posts.map((post, index) => this.createPost(post, index));
  }

  render() {
    return (
      <DocumentTitle title="Announcements - Amundsen">
        <main className="container announcement-container">
          <div className="row">
            <div className="col-xs-12 col-md-10 col-md-offset-1">
              <h1 id="announcement-header" className="announcement-header">
                {ANNOUNCEMENTS_HEADER_TEXT}
              </h1>
              <hr />
              <div id="announcement-content" className="announcement-content">
                {this.createPosts()}
              </div>
            </div>
          </div>
        </main>
      </DocumentTitle>
    );
  }
}

export const mapStateToProps = (state: GlobalState) => ({
  posts: state.announcements.posts,
});

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators({ announcementsGet: getAnnouncements }, dispatch);

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(AnnouncementPage);
