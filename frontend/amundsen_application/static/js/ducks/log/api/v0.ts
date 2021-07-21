import axios from 'axios';

export interface ActionLogParams {
  command: string;
  target_id?: string;
  target_type?: string;
  label?: string;
  location?: string;
  value?: string;
}

export interface ClickLogParams {
  target_id?: string;
  target_type?: string;
  label?: string;
  value?: string;
}

export const BASE_URL = '/api/log/v0/log_event';

/* TODO: Consider what we want to do on success/failure, if anything */
export function postActionLog(params: ActionLogParams) {
  axios.post(BASE_URL, params);
}
