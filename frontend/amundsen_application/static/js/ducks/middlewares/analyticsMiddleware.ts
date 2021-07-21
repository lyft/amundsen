// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { Middleware } from 'redux';

import { trackEvent } from 'utils/analytics';
import { RootState } from '../rootReducer';

export const analyticsMiddleware: Middleware<
  {}, // legacy type parameter added to satisfy interface signature
  RootState
> = ({ getState }) => (next) => (action) => {
  const result = next(action);

  // Intercept actions with meta analytics
  if (!action.meta || !action.meta.analytics) {
    return result;
  }

  const { name, payload } = action.meta.analytics;
  trackEvent(name, payload);

  return result;
};
