// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import globalState from 'fixtures/globalState';

import { mapStateToProps, mapDispatchToProps } from '.';

jest.mock('config/config-utils', () => ({
  showAllTags: jest.fn(),
  getCuratedTags: () => ['curated_tag_1'],
}));

describe('TagsListContainer', () => {
  describe('mapDispatchToProps', () => {
    let dispatch;
    let props;

    beforeAll(() => {
      dispatch = jest.fn(() => Promise.resolve());
      props = mapDispatchToProps(dispatch);
    });

    it('requests all the tags', () => {
      const expected = { type: 'amundsen/allTags/GET_REQUEST' };

      props.getAllTags();

      expect(dispatch.mock.calls[0][0]).toEqual(expected);
    });
  });

  describe('mapStateToProps', () => {
    it('sets isLoading on props', () => {
      const expected = globalState.tags.allTags.isLoading;
      const actual = mapStateToProps(globalState).isLoading;

      expect(actual).toEqual(expected);
    });

    let result;
    let expectedCuratedTags;
    let expectedOtherTags;
    let expectedPopularTags;
    beforeEach(() => {
      result = mapStateToProps(globalState);
      const allTags = globalState.tags.allTags.tags;

      expectedCuratedTags = [allTags[0]];
      expectedOtherTags = [allTags[2], allTags[1]];
      expectedPopularTags = [];
    });

    it('sets curatedTags on the props', () => {
      expect(result.curatedTags).toEqual(expectedCuratedTags);
    });

    it('sets otherTags on the props', () => {
      expect(result.otherTags).toEqual(expectedOtherTags);
    });

    it('sets popularTags on the props', () => {
      expect(result.popularTags).toEqual(expectedPopularTags);
    });
  });
});
