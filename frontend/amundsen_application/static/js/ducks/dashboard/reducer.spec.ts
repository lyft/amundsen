import { dashboardMetadata } from 'fixtures/metadata/dashboard';
import reducer, {
  getDashboard,
  getDashboardFailure,
  getDashboardSuccess,
  initialDashboardState,
  DashboardReducerState,
} from './reducer';

describe('dashboard reducer', () => {
  let testState: DashboardReducerState;
  beforeAll(() => {
    testState = {
      isLoading: false,
      statusCode: 200,
      dashboard: initialDashboardState,
    };
  });

  it('should return the existing state if action is not handled', () => {
    expect(reducer(testState, { type: 'INVALID.ACTION' })).toEqual(testState);
  });

  it('should handle GetDashboard.REQUEST', () => {
    expect(reducer(testState, getDashboard({ uri: 'testUri' }))).toEqual({
      ...testState,
      isLoading: true,
      statusCode: null,
    });
  });

  it('should handle GetDashboard.SUCCESS', () => {
    expect(
      reducer(
        testState,
        getDashboardSuccess({
          dashboard: dashboardMetadata,
          statusCode: 202,
        })
      )
    ).toEqual({
      isLoading: false,
      statusCode: 202,
      dashboard: dashboardMetadata,
    });
  });

  it('should handle GetDashboard.FAILURE', () => {
    expect(
      reducer(
        testState,
        getDashboardFailure({
          statusCode: 500,
        })
      )
    ).toEqual({
      isLoading: false,
      statusCode: 500,
      dashboard: initialDashboardState,
    });
  });
});
