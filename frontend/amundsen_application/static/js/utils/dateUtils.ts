import * as Moment from 'moment-timezone';
import AppConfig from 'config/config';

const timezone = Moment.tz.guess();

interface TimestampDateConfig {
  timestamp: number;
}

interface EpochDateConfig {
  epochTimestamp: number;
}

interface StringDateConfig {
  dateString: string;
  dateStringFormat: string;
}

type DateConfig = TimestampDateConfig | EpochDateConfig | StringDateConfig;

// This function is only exported for testing
export function getMomentDate(config: DateConfig): Moment.Moment {
  let moment;
  const { timestamp } = config as TimestampDateConfig;
  const epoch = (config as EpochDateConfig).epochTimestamp;
  const { dateString, dateStringFormat } = config as StringDateConfig;
  if (timestamp !== undefined) {
    moment = Moment(timestamp);
  } else if (epoch !== undefined) {
    moment = Moment(epoch * 1000);
  } else if (dateString && dateStringFormat) {
    moment = Moment(dateString, dateStringFormat);
  } else {
    throw new Error('Cannot format date with invalid DateConfig object.');
  }
  return moment.tz(timezone);
}

export function formatDate(config: DateConfig) {
  const date = getMomentDate(config);
  return date.format(AppConfig.date.default);
}

export function formatDateTimeShort(config: DateConfig) {
  const date = getMomentDate(config);
  return date.format(AppConfig.date.dateTimeShort);
}

export function formatDateTimeLong(config: DateConfig) {
  const date = getMomentDate(config);
  return date.format(AppConfig.date.dateTimeLong);
}
