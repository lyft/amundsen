// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';
import SanitizedHTML from 'react-sanitized-html';
import { shallow } from 'enzyme';

import globalState from 'fixtures/globalState';

import {
  AnnouncementPage,
  AnnouncementPageProps,
  mapDispatchToProps,
  mapStateToProps,
} from '.';

describe('AnnouncementPage', () => {
  let props: AnnouncementPageProps;
  let subject;

  beforeEach(() => {
    props = {
      announcementsGet: jest.fn(),
      posts: [
        {
          date: '12/31/1999',
          title: 'Y2K',
          html_content: '<div>The end of the world</div>',
        },
        {
          date: '01/01/2000',
          title: 'False Alarm',
          html_content: '<div>Just kidding</div>',
        },
      ],
    };
    subject = shallow(<AnnouncementPage {...props} />);
  });

  describe('componentDidMount', () => {
    it('calls props.announcementsGet', () => {
      expect(props.announcementsGet).toHaveBeenCalled();
    });
  });

  describe('createPost', () => {
    let content;
    beforeEach(() => {
      content = shallow(subject.instance().createPost(props.posts[0], 0));
    });
    it('renders the post title', () => {
      expect(content.children().at(0).children().at(0).text()).toEqual(
        props.posts[0].title
      );
    });

    it('renders the post date', () => {
      expect(content.children().at(0).children().at(1).text()).toEqual(
        props.posts[0].date
      );
    });

    it('renders SanitizedHTML with the post content', () => {
      expect(content.find(SanitizedHTML).props()).toMatchObject({
        html: props.posts[0].html_content,
      });
    });
  });

  describe('createPosts', () => {
    beforeEach(() => {
      subject.instance().createPost = jest.fn();
      subject.instance().createPosts();
    });
    it('call createPost() for each props.posts[] item', () => {
      expect(subject.instance().createPost).toHaveBeenCalledTimes(
        props.posts.length
      );
    });

    it('passes correct props to createPost()', () => {
      expect(subject.instance().createPost).toHaveBeenCalledWith(
        props.posts[0],
        0
      );
    });
  });

  describe('render', () => {
    let spy;
    beforeEach(() => {
      spy = jest.spyOn(AnnouncementPage.prototype, 'createPosts');
    });
    it('renders DocumentTitle w/ correct title', () => {
      expect(subject.find(DocumentTitle).props().title).toEqual(
        'Announcements - Amundsen'
      );
    });

    it('renders correct header', () => {
      expect(subject.find('#announcement-header').text()).toEqual(
        'Announcements'
      );
    });

    it('calls createPosts', () => {
      expect(spy).toHaveBeenCalled();
    });
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;

  beforeEach(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets announcementsGet on the props', () => {
    expect(result.announcementsGet).toBeInstanceOf(Function);
  });
});

describe('mapStateToProps', () => {
  let result;
  beforeEach(() => {
    result = mapStateToProps(globalState);
  });

  it('sets posts on the props', () => {
    expect(result.posts).toEqual(globalState.announcements.posts);
  });
});
