// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0
import * as React from 'react';

import { shallow } from 'enzyme';

import { allTestTags } from 'fixtures/metadata/tagsList';
import TagsList, { TagsListProps } from '.';

const POPULAR_TAGS_NUMBER = 20;

const popularTags = allTestTags.slice(0, POPULAR_TAGS_NUMBER).sort((a, b) => {
  if (a.tag_name < b.tag_name) return -1;
  if (a.tag_name > b.tag_name) return 1;
  return 0;
});

const otherTags = allTestTags
  .slice(POPULAR_TAGS_NUMBER, allTestTags.length)
  .sort((a, b) => {
    if (a.tag_name < b.tag_name) return -1;
    if (a.tag_name > b.tag_name) return 1;
    return 0;
  });

const setup = (propOverrides?: Partial<TagsListProps>) => {
  const props = {
    curatedTags: [],
    popularTags: [],
    otherTags: [],
    ...propOverrides,
  };
  const wrapper = shallow<typeof TagsList>(<TagsList {...props} />).dive();
  return { props, wrapper };
};

describe('TagsList', () => {
  describe('render shimmer loader whe isLoading is true', () => {
    const { wrapper } = setup({
      popularTags,
      otherTags,
      isLoading: true,
      shortTagsList: true,
    });

    it('should render ShimmeringTagListLoader', () => {
      const expected = 1;
      const actual = wrapper.find('.shimmer-tag-list-loader').length;

      expect(actual).toEqual(expected);
    });
  });

  describe('render shortTagsList with popular tags', () => {
    const { wrapper } = setup({
      popularTags,
      otherTags,
      isLoading: false,
      shortTagsList: true,
    });

    it('should render shortTagsList', () => {
      const expected = 1;
      const actual = wrapper.find('.short-tag-list').length;

      expect(actual).toEqual(expected);
    });

    it('should render TagsListTitle', () => {
      wrapper.children();
      const expected = 1;
      const actual = wrapper.childAt(0).shallow().find('.tag-list-title')
        .length;

      expect(actual).toEqual(expected);
    });

    it('should render TagsListBlock', () => {
      const expected = 1;
      const actual = wrapper.childAt(1).shallow().find('.tags-list').length;

      expect(actual).toEqual(expected);
    });

    it('should render Browse more tags link', () => {
      const expected = 1;
      const actual = wrapper.find('.browse-tags-link').length;

      expect(actual).toEqual(expected);
    });
  });

  describe('render longTagsList with popular tags', () => {
    const { wrapper } = setup({
      popularTags,
      otherTags,
      isLoading: false,
      shortTagsList: false,
    });

    const allChildren = wrapper.children().map((child) => child.shallow());

    it('should render longTagsList', () => {
      const expected = 1;
      const actual = wrapper.find('.full-tag-list').length;

      expect(actual).toEqual(expected);
    });

    it('should render TagsListTitle', () => {
      const expected = 1;
      let actual = 0;

      allChildren.forEach((comp) => {
        if (comp.find('#browse-header').exists()) {
          actual++;
        }
      });

      expect(actual).toEqual(expected);
    });

    it('should render TagsListLabels for both sections', () => {
      const expected = 2;
      let actual = 0;

      allChildren.forEach((comp) => {
        if (comp.find('.section-label').exists()) {
          actual++;
        }
      });

      expect(actual).toEqual(expected);
    });

    it('should render TagsListBlock for both Popular Tags section and Other Tags section', () => {
      const expected = 2;
      let actual = 0;

      allChildren.forEach((comp) => {
        if (comp.find('.tags-list').exists()) {
          actual++;
        }
      });
      expect(actual).toEqual(expected);
    });
  });
});
