// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';
import globalState from 'fixtures/globalState';
import { ResourceType } from 'interfaces';

import { mapDispatchToProps, mapStateToProps } from '.';

describe('AnnouncementsListContainer', () => {
  describe('mapDispatchToProps', () => {
    let dispatch;
    let props;

    beforeAll(() => {
      dispatch = jest.fn(() => Promise.resolve());
      props = mapDispatchToProps(dispatch);
    });

    describe('announcementsGet', () => {
      it('sets announcementsGet on the props', () => {
        const expected = 'function';
        const actual = typeof props.announcementsGet;

        expect(actual).toEqual(expected);
      });

      it('should request the announcements', () => {
        const expected = { type: 'amundsen/announcements/GET_REQUEST' };

        props.announcementsGet();

        expect(dispatch.mock.calls[0][0]).toEqual(expected);
      });
    });
  });

  describe('mapStateToProps', () => {
    it('sets isLoading on the props', () => {
      const expected = globalState.announcements.isLoading;
      const actual = mapStateToProps(globalState).isLoading;

      expect(actual).toEqual(expected);
    });

    it('sets statusCode on the props', () => {
      const expected = globalState.announcements.statusCode;
      const actual = mapStateToProps(globalState).statusCode;

      expect(actual).toEqual(expected);
    });

    it('sets posts on the props', () => {
      const expected = globalState.announcements.posts;
      const actual = mapStateToProps(globalState).announcements;

      expect(actual).toEqual(expected);
    });
  });
});
