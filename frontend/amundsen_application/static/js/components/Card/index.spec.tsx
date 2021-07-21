// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link, BrowserRouter } from 'react-router-dom';
import { mount } from 'enzyme';

import Card, { CardProps } from '.';

const setup = (propOverrides?: Partial<CardProps>) => {
  const props = {
    ...propOverrides,
  };
  const wrapper = mount<typeof Card>(
    <BrowserRouter>
      <Card {...props} />
    </BrowserRouter>
  );

  return { props, wrapper };
};

describe('Card', () => {
  describe('render', () => {
    it('renders without issues', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('renders the main container', () => {
      const { wrapper } = setup();
      const expected = 1;
      const actual = wrapper.find('.card').length;

      expect(actual).toEqual(expected);
    });

    describe('header', () => {
      it('renders a header section', () => {
        const { wrapper } = setup();
        const expected = 1;
        const actual = wrapper.find('.card-header').length;

        expect(actual).toEqual(expected);
      });

      describe('subtitle', () => {
        it('renders a title if passed', () => {
          const { wrapper } = setup({ title: 'test title' });
          const expected = 1;
          const actual = wrapper.find('.card-title').length;

          expect(actual).toEqual(expected);
        });

        it('does not render a title if missing', () => {
          const { wrapper } = setup();
          const expected = 0;
          const actual = wrapper.find('.card-title').length;

          expect(actual).toEqual(expected);
        });
      });

      describe('subtitle', () => {
        it('renders a subtitle if passed', () => {
          const { wrapper } = setup({ subtitle: 'test subtitle' });
          const expected = 1;
          const actual = wrapper.find('.card-subtitle').length;

          expect(actual).toEqual(expected);
        });

        it('does not render a subtitle if missing', () => {
          const { wrapper } = setup();
          const expected = 0;
          const actual = wrapper.find('.card-subtitle').length;

          expect(actual).toEqual(expected);
        });
      });
    });

    describe('body', () => {
      it('renders a body section', () => {
        const { wrapper } = setup();
        const expected = 1;
        const actual = wrapper.find('.card-body').length;

        expect(actual).toEqual(expected);
      });

      describe('copy', () => {
        it('renders a copy if passed', () => {
          const { wrapper } = setup({ copy: 'test copy' });
          const expected = 1;
          const actual = wrapper.find('.card-copy').length;

          expect(actual).toEqual(expected);
        });

        it('does not render a copy if missing', () => {
          const { wrapper } = setup();
          const expected = 0;
          const actual = wrapper.find('.card-copy').length;

          expect(actual).toEqual(expected);
        });
      });
    });

    describe('when is loading', () => {
      it('holds a loading state', () => {
        const { wrapper } = setup({ isLoading: true });
        const expected = 1;
        const actual = wrapper.find('.card.is-loading').length;

        expect(actual).toEqual(expected);
      });

      it('renders a shimmer loader', () => {
        const { wrapper } = setup({ isLoading: true });
        const expected = 1;
        const actual = wrapper.find('.card-shimmer-loader').length;

        expect(actual).toEqual(expected);
      });

      it('renders five rows of line loaders', () => {
        const { wrapper } = setup({ isLoading: true });
        const expected = 5;
        const actual = wrapper.find('.card-shimmer-row').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when an href is passed', () => {
      it('should render a link', () => {
        const testPath = 'fakePath';
        const { wrapper } = setup({ href: testPath });
        const expected = 1;
        const actual = wrapper.find('a.card').length;

        expect(actual).toEqual(expected);
      });

      it('renders a react router Link', () => {
        const testPath = 'fakePath';
        const { wrapper } = setup({ href: testPath });
        const expected = 1;
        const actual = wrapper.find(Link).length;

        expect(actual).toEqual(expected);
      });

      it('sets the link to the passed href', () => {
        const testPath = 'fakePath';
        const { wrapper } = setup({ href: testPath });
        const expected = '/' + testPath;
        const actual = wrapper
          .find('a.card')
          .getDOMNode()
          .attributes.getNamedItem('href')?.value;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('lifetime', () => {
    describe('when clicking on an interactive card', () => {
      it('should call the onClick handler', () => {
        const clickSpy = jest.fn();
        const { wrapper } = setup({
          onClick: clickSpy,
          href: 'testPath',
        });
        const expected = 1;

        wrapper.find(Link).simulate('click');

        const actual = clickSpy.mock.calls.length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
