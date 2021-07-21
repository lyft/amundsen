// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import {
  updateFilterByCategory,
  UpdateFilterRequest,
} from 'ducks/search/filters/reducer';

import { GlobalState } from 'ducks/rootReducer';
import { FilterType, IconSizes } from 'interfaces';
import InfoButton from 'components/InfoButton';
import { CLEAR_BTN_TEXT } from '../constants';

import CheckBoxFilter, { CheckboxFilterProperties } from '../CheckBoxFilter';
import InputFilter from '../InputFilter';

export interface OwnProps {
  categoryId: string;
  helpText?: string;
  title: string;
  type: FilterType;
  options?: CheckboxFilterProperties[];
}

export interface StateFromProps {
  hasValue: boolean;
}

export interface DispatchFromProps {
  clearFilter: (categoryId: string) => UpdateFilterRequest;
}

export type FilterSectionProps = OwnProps & DispatchFromProps & StateFromProps;

export class FilterSection extends React.Component<FilterSectionProps> {
  onClearFilter = () => {
    this.props.clearFilter(this.props.categoryId);
  };

  renderFilterComponent = () => {
    const { categoryId, options, type } = this.props;

    if (type === FilterType.INPUT_SELECT) {
      return <InputFilter categoryId={categoryId} />;
    }
    if (type === FilterType.CHECKBOX_SELECT) {
      return (
        <CheckBoxFilter
          categoryId={categoryId}
          checkboxProperties={options || []}
        />
      );
    }
  };

  render = () => {
    const { categoryId, hasValue, helpText, title } = this.props;

    return (
      <div className="search-filter-section">
        <div className="search-filter-section-header">
          <div className="search-filter-section-title">
            <label
              className="search-filter-section-label title-2"
              htmlFor={categoryId}
            >
              {title}
            </label>
            {helpText && (
              <InfoButton
                infoText={helpText}
                placement="top"
                size={IconSizes.SMALL}
              />
            )}
          </div>
          {hasValue && (
            <button
              onClick={this.onClearFilter}
              className="btn btn-link clear-button"
              type="button"
            >
              {CLEAR_BTN_TEXT}
            </button>
          )}
        </div>
        {this.renderFilterComponent()}
      </div>
    );
  };
}

export const mapStateToProps = (state: GlobalState, ownProps: OwnProps) => {
  const filterState = state.search.filters;
  const filterValue = filterState[state.search.resource]
    ? filterState[state.search.resource][ownProps.categoryId]
    : null;
  let hasValue = false;
  if (filterValue && ownProps.type === FilterType.CHECKBOX_SELECT) {
    Object.keys(filterValue).forEach((key) => {
      if (filterValue[key] === true) {
        hasValue = true;
      }
    });
  } else if (ownProps.type === FilterType.INPUT_SELECT) {
    hasValue = !!filterValue;
  }

  return {
    hasValue,
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      clearFilter: (categoryId: string) =>
        updateFilterByCategory({ categoryId, value: undefined }),
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps, OwnProps>(
  mapStateToProps,
  mapDispatchToProps
)(FilterSection);
