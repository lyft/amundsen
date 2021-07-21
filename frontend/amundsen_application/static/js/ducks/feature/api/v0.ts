// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import axios, { AxiosResponse, AxiosError } from 'axios';
import * as qs from 'simple-query-string';

import {
  FeatureCode,
  FeatureMetadata,
  FeaturePreviewQueryParams,
  PreviewData,
} from 'interfaces';
import { API_PATH } from 'ducks/tableMetadata/api/v0';
import { getQueryParams } from 'ducks/utilMethods';

export type GetFeatureAPI = {
  msg: string;
  featureData: FeatureMetadata;
};

type MessageAPI = { msg: string };

export type PreviewDataAPI = { previewData: PreviewData } & MessageAPI;

const FEATURE_BASE = '/api/metadata/v0';

export function getFeature(key: string, index?: string, source?: string) {
  const queryParams = qs.stringify({ key, index, source });
  return axios
    .get(`${FEATURE_BASE}/feature?${queryParams}`)
    .then((response: AxiosResponse<GetFeatureAPI>) => {
      const { data, status } = response;
      return {
        feature: data.featureData,
        statusCode: status,
      };
    })
    .catch((e) => {
      const { response } = e;
      const statusMessage = response.data?.msg;
      const statusCode = response?.status || 500;
      return Promise.reject({
        statusCode,
        statusMessage,
      });
    });
}

export function getFeaturePreviewData(queryParams: FeaturePreviewQueryParams) {
  return axios({
    url: '/api/preview/v0/feature_preview',
    method: 'POST',
    data: queryParams,
  })
    .then((response: AxiosResponse<PreviewDataAPI>) => ({
      previewData: response.data.previewData,
      status: response.status,
    }))
    .catch((e: AxiosError<PreviewDataAPI>) => {
      const { response } = e;
      const previewData = response?.data?.previewData || {};
      const status = response ? response.status : null;
      return Promise.reject({ previewData, status });
    });
}

export type GetFeatureCodeAPI = {
  msg: string;
  featureCode: FeatureCode;
};
export function getFeatureCode(key: string) {
  const queryParams = qs.stringify({ key });
  return axios
    .get(`${FEATURE_BASE}/get_feature_generation_code?${queryParams}`)
    .then((response: AxiosResponse<GetFeatureCodeAPI>) => {
      const { data, status } = response;
      return {
        featureCode: data,
        statusCode: status,
      };
    })
    .catch((e) => {
      const { response } = e;
      const statusMessage = response.data?.msg;
      const statusCode = response?.status || 500;
      return Promise.reject({
        statusCode,
        statusMessage,
      });
    });
}

export type GetFeatureDescriptionAPI = {
  msg: string;
  description: string;
};

export function getFeatureDescription(key: string) {
  const queryParams = qs.stringify({ key });
  return axios
    .get(`${FEATURE_BASE}/get_feature_description?${queryParams}`)
    .then((response: AxiosResponse<GetFeatureDescriptionAPI>) => {
      const { data, status } = response;
      return {
        description: data.description,
        statusCode: status,
      };
    })
    .catch((e) => {
      const { response } = e;
      const statusMessage = response.data?.msg;
      const statusCode = response?.status || 500;
      return Promise.reject({
        statusCode,
        statusMessage,
      });
    });
}

export function updateFeatureDescription(key: string, description: string) {
  return axios
    .put(`${FEATURE_BASE}/put_feature_description`, {
      key,
      description,
    })
    .then((response: AxiosResponse<GetFeatureAPI>) => {
      const { data, status } = response;
      return {
        feature: data.featureData,
        statusCode: status,
      };
    })
    .catch((e) => {
      const { response } = e;
      const statusMessage = response.data?.msg;
      const statusCode = response?.status || 500;
      return Promise.reject({
        statusCode,
        statusMessage,
      });
    });
}

export function getFeatureOwners(key: string) {
  const queryParams = getQueryParams({ key });
  return axios
    .get(`${API_PATH}/feature?${queryParams}`)
    .then(
      (response: AxiosResponse<GetFeatureAPI>) =>
        response.data.featureData.owners
    );
}
