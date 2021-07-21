// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link, BrowserRouter } from 'react-router-dom';
import { mount } from 'enzyme';

import Card from '../../Card';

import AnnouncementsList, { AnnouncementsListProps } from '.';

const TWO_FAKE_ANNOUNCEMENTS = [
  {
    date: '01/01/2000',
    title: 'False Alarm',
    html_content: '<div>Just kidding</div>',
  },
  {
    date: '12/31/1999',
    title: 'Y2K',
    html_content: '<div>The end of the world</div>',
  },
];
const FOUR_FAKE_ANNOUNCEMENTS = [
  {
    date: '01/01/2020',
    title: 'New Test',
    html_content: '<div>New test</div>',
  },
  {
    date: '12/31/2009',
    title: 'Old Test',
    html_content: '<div>Old test</div>',
  },
  {
    date: '01/01/2000',
    title: 'False Alarm',
    html_content: '<div>Just kidding</div>',
  },
  {
    date: '12/31/1999',
    title: 'Y2K',
    html_content: '<div>The end of the world</div>',
  },
];
const EMPTY_ANNOUNCEMENTS = [];

const setup = (propOverrides?: Partial<AnnouncementsListProps>) => {
  const props = {
    announcements: [],
    ...propOverrides,
  };
  const wrapper = mount<typeof AnnouncementsList>(
    <BrowserRouter>
      <AnnouncementsList {...props} />
    </BrowserRouter>
  );

  return { props, wrapper };
};

describe('AnnouncementsList', () => {
  describe('render', () => {
    it('renders without issues', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('renders a title', () => {
      const { wrapper } = setup();
      const expected = 1;
      const actual = wrapper.find('.announcements-list-title').length;

      expect(actual).toEqual(expected);
    });

    describe('See more link', () => {
      it('should render a "See more" link', () => {
        const { wrapper } = setup({ announcements: TWO_FAKE_ANNOUNCEMENTS });
        const expected = 1;
        const actual = wrapper.find('a.announcements-list-more-link').length;

        expect(actual).toEqual(expected);
      });

      it('renders a react router Link', () => {
        const { wrapper } = setup({ announcements: TWO_FAKE_ANNOUNCEMENTS });
        const expected = TWO_FAKE_ANNOUNCEMENTS.length + 1;
        const actual = wrapper.find(Link).length;

        expect(actual).toEqual(expected);
      });

      it('takes users to the announcements page', () => {
        const { wrapper } = setup({ announcements: TWO_FAKE_ANNOUNCEMENTS });
        const expected = '/announcements';
        const actual = wrapper
          .find('a.announcements-list-more-link')
          .getDOMNode()
          .attributes.getNamedItem('href')?.value;

        expect(actual).toEqual(expected);
      });
    });

    describe('announcements list', () => {
      it('should render a list container', () => {
        const { wrapper } = setup();
        const expected = 1;
        const actual = wrapper.find('.announcements-list').length;

        expect(actual).toEqual(expected);
      });

      describe('when loading', () => {
        it('should render three cards', () => {
          const { wrapper } = setup({
            announcements: EMPTY_ANNOUNCEMENTS,
            isLoading: true,
          });
          const expected = 3;
          const actual = wrapper.find(Card).length;

          expect(actual).toEqual(expected);
        });

        it('should render three cards in loading state', () => {
          const { wrapper } = setup({
            announcements: EMPTY_ANNOUNCEMENTS,
            isLoading: true,
          });
          const expected = 3;
          const actual = wrapper.find('.card-shimmer-loader').length;

          expect(actual).toEqual(expected);
        });

        it('should not render the see more link', () => {
          const { wrapper } = setup({
            announcements: EMPTY_ANNOUNCEMENTS,
            isLoading: true,
          });
          const expected = 0;
          const actual = wrapper.find('a.announcements-list-more-link').length;

          expect(actual).toEqual(expected);
        });
      });

      describe('when non-empty list of announcements', () => {
        it('should render announcements', () => {
          const { wrapper } = setup({ announcements: TWO_FAKE_ANNOUNCEMENTS });
          const expected = 2;
          const actual = wrapper.find('.announcement').length;

          expect(actual).toEqual(expected);
        });

        it('should render announcement cards', () => {
          const { wrapper } = setup({ announcements: TWO_FAKE_ANNOUNCEMENTS });
          const expected = 2;
          const actual = wrapper.find(Card).length;

          expect(actual).toEqual(expected);
        });

        describe('when number of announcements is more than three', () => {
          it('should render three announcements', () => {
            const { wrapper } = setup({
              announcements: FOUR_FAKE_ANNOUNCEMENTS,
            });
            const expected = 3;
            const actual = wrapper.find(Card).length;

            expect(actual).toEqual(expected);
            wrapper.unmount();
          });

          it('should render them starting on the latest announcement', () => {
            const { wrapper } = setup({
              announcements: FOUR_FAKE_ANNOUNCEMENTS,
            });
            const firstCardDate = wrapper
              .find(Card)
              .at(0)
              .find('.card-subtitle')
              .text();
            const lastCardDate = wrapper
              .find(Card)
              .at(1)
              .find('.card-subtitle')
              .text();
            const actual = new Date(firstCardDate) >= new Date(lastCardDate);
            const expected = true;

            expect(actual).toEqual(expected);
          });
        });
      });

      describe('when empty list of announcements', () => {
        it('should render the empty message', () => {
          const { wrapper } = setup({ announcements: EMPTY_ANNOUNCEMENTS });
          const expected = 1;
          const actual = wrapper.find('.empty-announcement').length;

          expect(actual).toEqual(expected);
        });

        it('should not render the see more link', () => {
          const { wrapper } = setup({ announcements: EMPTY_ANNOUNCEMENTS });
          const expected = 0;
          const actual = wrapper.find('a.announcements-list-more-link').length;

          expect(actual).toEqual(expected);
        });
      });

      describe('when error on fetch', () => {
        it('should render the error message', () => {
          const { wrapper } = setup({
            announcements: EMPTY_ANNOUNCEMENTS,
            hasError: true,
          });
          const expected = 1;
          const actual = wrapper.find('.error-announcement').length;

          expect(actual).toEqual(expected);
        });

        it('should not render the see more link', () => {
          const { wrapper } = setup({
            announcements: EMPTY_ANNOUNCEMENTS,
            hasError: true,
          });
          const expected = 0;
          const actual = wrapper.find('a.announcements-list-more-link').length;

          expect(actual).toEqual(expected);
        });
      });
    });
  });
});
