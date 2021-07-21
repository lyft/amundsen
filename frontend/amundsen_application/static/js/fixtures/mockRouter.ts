import { RouteComponentProps } from 'react-router';

import * as History from 'history';

// Mock React-Router
export function getMockRouterProps<P>(
  data: P,
  location: Partial<History.Location> = {}
): RouteComponentProps<P> {
  const mockLocation: History.Location = {
    hash: '',
    key: '',
    pathname: '',
    search: '',
    state: {},
    ...location,
  };

  const props: RouteComponentProps<P> = {
    match: {
      isExact: true,
      params: data,
      path: '',
      url: '',
    },
    location: mockLocation,
    // This history object is a mock and `null`s many of the required methods. The
    // tests are designed not to trigger them, if they do, an error is expected.
    // So cast this as any.
    history: <any>{
      length: 2,
      action: 'POP',
      location: mockLocation,
      push: null,
      replace: null,
      go: null,
      goBack: null,
      goForward: null,
      block: null,
      createHref: null,
      listen: null,
    },
    staticContext: {},
  };

  return props;
}
