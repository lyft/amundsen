// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';
import { PREVIEW_COLUMN_MSG } from 'features/PreviewData/constants';
import {
  previewDataError,
  previewDataSuccess,
} from 'fixtures/metadata/previewData';

import {
  getSanitizedValue,
  PreviewDataLoader,
  PreviewDataProps,
  PreviewDataTable,
} from '.';

const setupLoader = () => {
  const wrapper = shallow(<PreviewDataLoader />);
  return wrapper;
};
describe('PreviewDataLoader', () => {
  it('should render without errors', () => {
    expect(() => {
      setupLoader();
    }).not.toThrow();
  });

  it('renders a header row', () => {
    const wrapper = setupLoader();
    const expected = 1;
    const actual = wrapper.find('.shimmer-header-row').length;
    expect(actual).toEqual(expected);
  });

  it('renders 8 data rows', () => {
    const wrapper = setupLoader();
    const expected = 8;
    const actual = wrapper.find('.shimmer-row').length;
    expect(actual).toEqual(expected);
  });
});

describe('getSanitizedValue', () => {
  it('returns a boolean as a string', () => {
    const input = true;
    const expected = 'true';
    const actual = getSanitizedValue(input);
    expect(actual).toEqual(expected);
  });

  it('returns a json object as string', () => {
    const input = { test: 2 };
    const expected = '{"test":2}';
    const actual = getSanitizedValue(input);
    expect(actual).toEqual(expected);
  });

  it('returns a string as-is', () => {
    const input = 'hello';
    const expected = 'hello';
    const actual = getSanitizedValue(input);
    expect(actual).toEqual(expected);
  });

  it('returns a message if the string is too long', () => {
    const input =
      'test message that is too longtest message that is too long test message that test message' +
      'is too longtest message that is too long test message that is too longtest message that is ' +
      'too long test message that is too longtest message that is too long test message that is too ' +
      'longtest message that is too long test message that is too longtest message that is too long ';
    const expected = PREVIEW_COLUMN_MSG;
    const actual = getSanitizedValue(input);
    expect(actual).toEqual(expected);
  });
});

const setup = (propOverrides?: Partial<PreviewDataProps>) => {
  const props = {
    isLoading: false,
    previewData: previewDataSuccess,
    ...propOverrides,
  };
  const wrapper = shallow<typeof PreviewDataTable>(
    <PreviewDataTable {...props} />
  );
  return { props, wrapper };
};

describe('PreviewDataTable', () => {
  it('it renders the loading state', () => {
    const { wrapper } = setup({ isLoading: true });
    expect(wrapper.find(PreviewDataLoader).exists).toBeTruthy();
  });

  it('it renders an error message if no data is available', () => {
    const { wrapper } = setup({ previewData: previewDataError });
    expect(wrapper.find('.error-message').exists).toBeTruthy();
  });

  it('it renders a table if data is present', () => {
    const { wrapper } = setup();
    expect(wrapper.find('.grid').exists).toBeTruthy();
  });

  it('it renders a header for each column', () => {
    const { props, wrapper } = setup();
    const headerCount = props.previewData.columns?.length || 0;
    expect(wrapper.find('.grid-header').length).toEqual(headerCount);
  });

  it('it renders a data cell for each column', () => {
    const { props, wrapper } = setup();
    const dataCount =
      (props.previewData.data?.length || 0) *
      (props.previewData.columns?.length || 0);
    expect(wrapper.find('.grid-data-cell').length).toEqual(dataCount);
  });
});
