// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import './styles.scss';

import { Watermark } from 'interfaces';
import { formatDate } from 'utils/dateUtils';
import {
  HIGH_WATERMARK_LABEL,
  NO_WATERMARK_LINE_1,
  NO_WATERMARK_LINE_2,
  LOW_WATERMARK_LABEL,
  WATERMARK_INPUT_FORMAT,
  WatermarkType,
} from './constants';

export interface WatermarkLabelProps {
  watermarks: Watermark[];
}

class WatermarkLabel extends React.Component<WatermarkLabelProps> {
  formatWatermarkDate = (dateString: string) =>
    formatDate({
      dateString,
      dateStringFormat: WATERMARK_INPUT_FORMAT,
    });

  getWatermarkValue = (type: WatermarkType) => {
    const watermark = this.props.watermarks.find(
      (watermark: Watermark) => watermark.watermark_type === type
    );
    return (watermark && watermark.partition_value) || null;
  };

  renderWatermarkInfo = (low: string | null, high: string | null) => {
    if (low === null && high === null) {
      return (
        <div className="body-2">
          {NO_WATERMARK_LINE_1}
          <br />
          {NO_WATERMARK_LINE_2}
        </div>
      );
    }

    return (
      <div className="date-ranges">
        {low && (
          <p className="date-range body-2">
            <span className="date-range-label">{LOW_WATERMARK_LABEL}</span>
            <time className="date-range-value">
              {this.formatWatermarkDate(low)}
            </time>
          </p>
        )}
        {high && (
          <p className="date-range body-2">
            <span className="date-range-label">{HIGH_WATERMARK_LABEL}</span>
            <time className="date-range-value">
              {this.formatWatermarkDate(high)}
            </time>
          </p>
        )}
      </div>
    );
  };

  render() {
    const low = this.getWatermarkValue(WatermarkType.LOW);
    const high = this.getWatermarkValue(WatermarkType.HIGH);

    return (
      <div className="watermark-label">
        <img
          className="range-icon"
          src="/static/images/watermark-range.png"
          alt=""
        />
        {this.renderWatermarkInfo(low, high)}
      </div>
    );
  }
}

export default WatermarkLabel;
