// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow, mount } from 'enzyme';
import {
  NO_WATERMARK_LINE_1,
  NO_WATERMARK_LINE_2,
  WatermarkType,
} from './constants';
import WatermarkLabel, { WatermarkLabelProps } from '.';

describe('WatermarkLabel', () => {
  const setup = (propOverrides?: Partial<WatermarkLabelProps>) => {
    const props = {
      watermarks: [
        {
          create_time: '2018-10-16 11:03:17',
          partition_key: 'ds',
          partition_value: '2018-08-03',
          watermark_type: 'low_watermark',
        },
        {
          create_time: '2019-10-15 11:03:17',
          partition_key: 'ds',
          partition_value: '2019-10-15',
          watermark_type: 'high_watermark',
        },
      ],
      ...propOverrides,
    };

    const wrapper = shallow<WatermarkLabel>(<WatermarkLabel {...props} />);
    return { wrapper, props };
  };

  describe('formatWatermarkDate', () => {
    it('Parses a date string and converts it to a new format', () => {
      const { wrapper } = setup();
      const dateString = '2019-10-15';
      const formattedDate = wrapper.instance().formatWatermarkDate(dateString);
      expect(formattedDate).toBe('Oct 15, 2019');
    });
  });

  describe('getWatermarkValue', () => {
    const { wrapper } = setup();

    it('Gets the high watermark value', () => {
      const highWatermark = wrapper
        .instance()
        .getWatermarkValue(WatermarkType.HIGH);
      expect(highWatermark).toBe('2019-10-15');
    });

    it('Gets the low watermark value', () => {
      const highWatermark = wrapper
        .instance()
        .getWatermarkValue(WatermarkType.LOW);
      expect(highWatermark).toBe('2018-08-03');
    });

    it('Returns null if no partition is found', () => {
      const { wrapper } = setup({ watermarks: [] });
      const nullWatermark = wrapper
        .instance()
        .getWatermarkValue(WatermarkType.LOW);
      expect(nullWatermark).toBe(null);
    });
  });

  describe('renderWatermarkInfo', () => {
    const { wrapper } = setup();
    const instance = wrapper.instance();

    it('renders a no-watermark message if there are no watermarks', () => {
      const watermarkInfo = instance.renderWatermarkInfo(null, null);
      expect(shallow(watermarkInfo).text()).toBe(
        `${NO_WATERMARK_LINE_1}${NO_WATERMARK_LINE_2}`
      );
    });

    it('renders the date when present', () => {
      const watermarkInfo = instance.renderWatermarkInfo(
        '2018-08-03',
        '2019-10-15'
      );
      const watermark = mount(watermarkInfo);
      const startTime = watermark.find('.date-range-value').at(0).text();
      const endTime = watermark.find('.date-range-value').at(1).text();

      expect(startTime).toBe('Aug 03, 2018');
      expect(endTime).toBe('Oct 15, 2019');
    });
  });

  describe('render', () => {
    const { wrapper, props } = setup();
    const instance = wrapper.instance();
    const getWatermarkValueSpy = jest.spyOn(instance, 'getWatermarkValue');
    const renderWatermarkInfoSpy = jest.spyOn(instance, 'renderWatermarkInfo');
    instance.render();

    it('calls getWatermarkValue with both high and low values', () => {
      expect(getWatermarkValueSpy).toHaveBeenCalledWith(WatermarkType.LOW);
      expect(getWatermarkValueSpy).toHaveBeenCalledWith(WatermarkType.HIGH);
    });

    it('calls renderWatermarkInfo', () => {
      const low = props.watermarks[0].partition_value;
      const high = props.watermarks[1].partition_value;
      expect(renderWatermarkInfoSpy).toHaveBeenCalledWith(low, high);
    });

    it('renders the watermark-range image', () => {
      expect(wrapper.find('img.range-icon').exists()).toBe(true);
    });
  });
});
