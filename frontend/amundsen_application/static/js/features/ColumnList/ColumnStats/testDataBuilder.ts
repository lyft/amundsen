// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

const defaultConfig = {
  stats: [],
};

/**
 * Generates test data for the table data
 * @example
 * let testData = new TestDataBuilder()
 *                         .withEightStats()
 *                         .build();
 */
function TestDataBuilder(config = {}) {
  this.Klass = TestDataBuilder;
  this.config = {
    ...defaultConfig,
    ...config,
  };

  this.withEightStats = () => {
    const attr = {
      stats: [
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count',
          stat_val: '12345',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count_null',
          stat_val: '123',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count_distinct',
          stat_val: '22',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count_zero',
          stat_val: '44',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'max',
          stat_val: '1237466454',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'min',
          stat_val: '856',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'avg',
          stat_val: '2356575',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'stddev',
          stat_val: '1234563',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withFourStats = () => {
    const attr = {
      stats: [
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count',
          stat_val: '12345',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count_null',
          stat_val: '123',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'avg',
          stat_val: '2356575',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'stddev',
          stat_val: '1234563',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withThreeStats = () => {
    const attr = {
      stats: [
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count',
          stat_val: '12345',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'avg',
          stat_val: '2356575',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'stddev',
          stat_val: '1234563',
        },
      ],
    };

    return new this.Klass(attr);
  };
  this.withNonNumericStats = () => {
    const attr = {
      stats: [
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'count',
          stat_val: '12345',
        },
        {
          end_epoch: 1571616000,
          start_epoch: 1571616000,
          stat_type: 'date',
          stat_val: '2020-11-03',
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withEmptyStats = () => {
    const attr = { stats: [] };

    return new this.Klass(attr);
  };

  this.build = () => this.config;
}

export default TestDataBuilder;
