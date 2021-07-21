// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Modal } from 'react-bootstrap';

import { mount } from 'enzyme';

import Linkify from 'react-linkify';

import { ImagePreview, ImagePreviewProps } from '.';

import ShimmeringDashboardLoader from '../ShimmeringDashboardLoader';

import * as Constants from './constants';

describe('ImagePreview', () => {
  const setup = (propOverrides?: Partial<ImagePreviewProps>) => {
    const props = {
      uri: 'test:uri/value',
      redirectUrl: 'someUrl',
      ...propOverrides,
    };

    const wrapper = mount<ImagePreview>(<ImagePreview {...props} />);
    return { props, wrapper };
  };

  describe('onSuccess', () => {
    let currentState;
    beforeAll(() => {
      const { wrapper } = setup();
      wrapper.instance().onSuccess();
      currentState = wrapper.state();
    });
    it('sets the loading state to false', () => {
      expect(currentState.isLoading).toBe(false);
    });
    it('sets the hasError state to false', () => {
      expect(currentState.hasError).toBe(false);
    });
  });

  describe('onError', () => {
    let currentState;
    beforeAll(() => {
      const { wrapper } = setup();
      const event = {} as React.SyntheticEvent<HTMLImageElement>;
      wrapper.instance().onError(event);
      currentState = wrapper.state();
    });
    it('sets the loading state to false', () => {
      expect(currentState.isLoading).toBe(false);
    });
    it('sets the hasError state to false', () => {
      expect(currentState.hasError).toBe(true);
    });
  });

  describe('render', () => {
    describe('when no error', () => {
      describe('when loading', () => {
        let wrapper;
        beforeAll(() => {
          wrapper = setup().wrapper;
          wrapper.instance().setState({ isLoading: true, hasError: false });
        });

        it('renders the loading dashboard', () => {
          expect(wrapper.find(ShimmeringDashboardLoader).exists()).toBeTruthy();
        });

        it('renders hidden img', () => {
          expect(wrapper.find('img').props().style).toEqual({
            visibility: 'hidden',
          });
        });
      });

      describe('when loaded', () => {
        let props;
        let wrapper;

        beforeAll(() => {
          const setupResult = setup();
          props = setupResult.props;
          wrapper = setupResult.wrapper;
          wrapper.instance().setState({ isLoading: false, hasError: false });
          wrapper.update();
        });

        it('renders visible img with correct props', () => {
          const elementProps = wrapper.find('img').props();

          expect(elementProps.style).toEqual({ visibility: 'visible' });
          expect(elementProps.src).toEqual(
            `${Constants.PREVIEW_BASE}/${props.uri}/${Constants.PREVIEW_END}`
          );
          expect(elementProps.onLoad).toBe(wrapper.instance().onSuccess);
          expect(elementProps.onError).toBe(wrapper.instance().onError);
        });

        it('renders a button', () => {
          const expected = 1;
          const actual = wrapper.find('.preview-button').length;

          expect(actual).toEqual(expected);
        });
      });
    });

    describe('when there is an error', () => {
      it('renders a link', () => {
        const { wrapper } = setup();

        wrapper.instance().setState({ hasError: true });
        wrapper.update();

        expect(wrapper.find(Linkify).exists()).toBeTruthy();
      });
    });
  });

  describe('lifecycle', () => {
    let wrapper;

    describe('when clicking on the dashboard preview button', () => {
      beforeAll(() => {
        const setupResult = setup();

        wrapper = setupResult.wrapper;
        wrapper.instance().setState({ isLoading: false, hasError: false });
      });

      it('should open a modal', () => {
        const expected = 1;

        wrapper.find('.preview-button').simulate('click');

        const actual = wrapper.find(Modal).length;
        expect(actual).toEqual(expected);
      });

      describe('when closing the modal', () => {
        it('should remove the modal markup', () => {
          const expected = 0;

          wrapper.find('.preview-button').simulate('click');
          wrapper.find('.modal-header .close').simulate('click');

          const actual = wrapper.find(Modal).length;
          expect(actual).toEqual(expected);
        });
      });
    });
  });
});
