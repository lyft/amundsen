// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import { GlobalState } from 'ducks/rootReducer';
import { getLastIndexed } from 'ducks/lastIndexed/reducer';
import { GetLastIndexedRequest } from 'ducks/lastIndexed/types';

import { formatDateTimeLong } from 'utils/dateUtils';

import './styles.scss';

// Props
interface StateFromProps {
  lastIndexed: number | null;
}

interface DispatchFromProps {
  getLastIndexed: () => GetLastIndexedRequest;
}

export type FooterProps = StateFromProps & DispatchFromProps;

const ShimmeringFooterLoader: React.FC = () => (
  <div className="shimmer-footer">
    <div className="shimmer-footer-row is-shimmer-animated" />
  </div>
);

export class Footer extends React.Component<FooterProps> {
  componentDidMount() {
    const { getLastIndexed } = this.props;

    getLastIndexed();
  }

  generateDateTimeString = (lastIndexed: number): string =>
    formatDateTimeLong({ epochTimestamp: lastIndexed });

  render() {
    let content = <ShimmeringFooterLoader />;

    if (this.props.lastIndexed) {
      content = (
        <div>
          {`Amundsen was last indexed on ${this.generateDateTimeString(
            this.props.lastIndexed
          )}`}
        </div>
      );
    }

    return (
      <footer>
        <div className="phantom-div" />
        <div id="footer" className="footer">
          {content}
        </div>
      </footer>
    );
  }
}

export const mapStateToProps = (state: GlobalState): StateFromProps => ({
  lastIndexed: state.lastIndexed.lastIndexed,
});

export const mapDispatchToProps = (dispatch) =>
  bindActionCreators({ getLastIndexed }, dispatch);

export default connect<StateFromProps, DispatchFromProps>(
  mapStateToProps,
  mapDispatchToProps
)(Footer);
