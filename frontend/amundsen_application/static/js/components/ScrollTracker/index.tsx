// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { throttle } from 'throttle-debounce';
import { logAction } from 'utils/analytics';

export interface ScrollTrackerProps {
  targetId: string;
}

interface ScrollTrackerState {
  thresholds: number[];
}

export default class ScrollTracker extends React.Component<
  ScrollTrackerProps,
  ScrollTrackerState
> {
  private readonly throttledScroll: any;

  constructor(props) {
    super(props);

    this.state = {
      thresholds: [25, 50, 75, 100],
    };

    this.throttledScroll = throttle(100, false, this.onScroll);
  }

  componentDidMount() {
    window.addEventListener('scroll', this.throttledScroll);
  }

  componentWillUnmount() {
    window.removeEventListener('scroll', this.throttledScroll);
  }

  onScroll = () => {
    if (this.state.thresholds.length === 0) {
      window.removeEventListener('scroll', this.throttledScroll);
      return;
    }
    const threshold = this.state.thresholds[0];
    const scrollTop =
      window.pageYOffset ||
      document.documentElement.scrollTop ||
      document.body.scrollTop ||
      0;
    const windowHeight = window.innerHeight || document.body.clientHeight;
    const contentHeight = document.body.offsetHeight;
    const scrollableAmount = Math.max(contentHeight - windowHeight, 1);

    if (threshold <= (100 * scrollTop) / scrollableAmount) {
      this.state.thresholds.shift();
      this.fireAnalyticsEvent(threshold);
    }
  };

  fireAnalyticsEvent = (threshold: number) => {
    logAction({
      command: 'scroll',
      target_id: this.props.targetId,
      value: threshold.toString(),
    });
  };

  render() {
    return null;
  }
}
