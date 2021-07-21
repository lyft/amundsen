export interface AnalyticsEvent {
  name: string;
  payload: { [prop: string]: unknown };
}
