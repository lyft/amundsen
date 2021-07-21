// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { mount } from 'enzyme';

import { emptyFeatureCode } from 'ducks/feature/reducer';
import {
  GenerationCode,
  GenerationCodeLoader,
  GenerationCodeProps,
  LazyCodeBlock,
} from './index';

const setup = (propOverrides?: Partial<GenerationCodeProps>) => {
  const props: GenerationCodeProps = {
    isLoading: false,
    featureCode: emptyFeatureCode,
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount(<GenerationCode {...props} />);
  return { props, wrapper };
};

describe('GenerationCode', () => {
  describe('render', () => {
    it('should render without errors', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    it('should render a loading state', () => {
      const { wrapper } = setup({ isLoading: true });
      expect(wrapper.find(<GenerationCodeLoader />)).toBeTruthy();
    });

    it('should renders a lazy code block', () => {
      const { wrapper } = setup();
      expect(wrapper.find(LazyCodeBlock)).toBeTruthy();
    });
  });
});
