import axios from 'axios';

import * as API from '../v0';

jest.mock('axios');

describe('submitFeedback', () => {
  let formData: FormData;
  beforeAll(() => {
    formData = new FormData();
    API.submitFeedback(formData);
  });

  it('calls axios with expected payload', () => {
    expect(axios).toHaveBeenCalledWith({
      data: formData,
      method: 'post',
      url: '/api/mail/v0/feedback',
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  });
});
