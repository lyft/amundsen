// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import reducer, { pageViewed, pageViewActionType, UIReducerState } from '.';

describe('UI ducks', () => {
  describe('actions', () => {
    describe('pageViewed', () => {
      it('returns the action to track a page view', () => {
        const expected = '/testURL';
        const action = pageViewed(expected);
        const { type, meta } = action;

        expect(type).toEqual(pageViewActionType);
        expect(meta.analytics.name).toEqual(pageViewActionType);
        expect(meta.analytics.payload.category).toEqual('pageView');
        expect(meta.analytics.payload.label).toEqual(expected);
      });
    });
  });

  describe('reducer', () => {
    const testState: UIReducerState = {};

    describe('when pageViewed is triggered', () => {
      it('should return the existing state', () => {
        const expected = testState;
        const actual = reducer(testState, pageViewed('/testURL'));

        expect(actual).toEqual(expected);
      });
    });
  });
});
