// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import globalState from 'fixtures/globalState';

import { ResourceType } from 'interfaces';

import {
  BookmarkIcon,
  BookmarkIconProps,
  mapDispatchToProps,
  mapStateToProps,
} from '.';

describe('BookmarkIcon', () => {
  const setup = (propOverrides?: Partial<BookmarkIconProps>) => {
    const props: BookmarkIconProps = {
      bookmarkKey: 'someKey',
      isBookmarked: true,
      large: false,
      addBookmark: jest.fn(),
      removeBookmark: jest.fn(),
      resourceType: ResourceType.table,
      ...propOverrides,
    };
    const wrapper = shallow<BookmarkIcon>(<BookmarkIcon {...props} />);
    return { props, wrapper };
  };

  describe('handleClick', () => {
    const clickEvent = {
      preventDefault: jest.fn(),
      stopPropagation: jest.fn(),
    };
    it('stops propagation and prevents default', () => {
      const { wrapper } = setup();
      wrapper.find('div').simulate('click', clickEvent);
      expect(clickEvent.preventDefault).toHaveBeenCalled();
      expect(clickEvent.stopPropagation).toHaveBeenCalled();
    });

    it('bookmarks an unbookmarked resource', () => {
      const { props, wrapper } = setup({
        isBookmarked: false,
      });

      wrapper.find('div').simulate('click', clickEvent);
      expect(props.addBookmark).toHaveBeenCalledWith(
        props.bookmarkKey,
        props.resourceType
      );
    });

    it('unbookmarks a bookmarked resource', () => {
      const { props, wrapper } = setup({
        isBookmarked: true,
      });
      wrapper.find('div').simulate('click', clickEvent);
      expect(props.removeBookmark).toHaveBeenCalledWith(
        props.bookmarkKey,
        props.resourceType
      );
    });
  });

  describe('render', () => {
    it('renders an empty bookmark when not bookmarked', () => {
      const { wrapper } = setup({ isBookmarked: false });
      expect(wrapper.find('.icon-bookmark').exists()).toBe(true);
    });

    it('renders a filled star when bookmarked', () => {
      const { wrapper } = setup({ isBookmarked: true });
      expect(wrapper.find('.icon-bookmark-filled').exists()).toBe(true);
    });

    it('renders a large star when specified', () => {
      const { wrapper } = setup({ large: true });
      expect(wrapper.find('.bookmark-large').exists()).toBe(true);
    });
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let props;

  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    props = mapDispatchToProps(dispatch);
  });

  it('sets addBookmark on the props', () => {
    expect(props.addBookmark).toBeInstanceOf(Function);
  });

  it('sets removeBookmark on the props', () => {
    expect(props.removeBookmark).toBeInstanceOf(Function);
  });
});

describe('mapStateToProps', () => {
  it('sets the bookmarkKey on the props', () => {
    const ownProps = {
      bookmarkKey: 'test_bookmark_key',
      resourceType: ResourceType.table,
    };
    const result = mapStateToProps(globalState, ownProps);
    expect(result.bookmarkKey).toEqual(ownProps.bookmarkKey);
  });

  it('sets isBookmarked to false when the resource key is not bookmarked', () => {
    const ownProps = {
      bookmarkKey: 'not_bookmarked_key',
      resourceType: ResourceType.table,
    };
    const result = mapStateToProps(globalState, ownProps);
    expect(result.isBookmarked).toBe(false);
  });

  it('sets isBookmarked to true when the resource key is bookmarked', () => {
    const ownProps = {
      bookmarkKey: 'bookmarked_key',
      resourceType: ResourceType.table,
    };
    const result = mapStateToProps(globalState, ownProps);
    expect(result.isBookmarked).toBe(true);
  });
});
