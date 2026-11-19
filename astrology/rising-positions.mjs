import { EclipticGeoMoon, MakeTime, SiderealTime, SunPosition, e_tilt } from './astronomy-engine.mjs';

const rad = Math.PI / 180;
const hour = 3600000;
const circle = value => (value % 360 + 360) % 360;
const formatters = new Map();

function calendar(zone) {
  if (!formatters.has(zone)) {
    formatters.set(zone, new Intl.DateTimeFormat('en-GB', {
      timeZone: zone, calendar: 'gregory', numberingSystem: 'latn', hourCycle: 'h23',
      year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit',
      minute: '2-digit', second: '2-digit'
    }));
  }
  return formatters.get(zone);
}

function localWallClock(timestamp, formatter) {
  const f = Object.fromEntries(formatter.formatToParts(timestamp).map(({type,value}) => [type,value]));
  return Date.parse(`${f.year}-${f.month}-${f.day}T${f.hour}:${f.minute}:${f.second}Z`);
}

function nominalDay(date) {
  if (!/^(19|20)\d\d-\d\d-\d\d$/.test(date)) throw new RangeError('date');
  const nominal = Date.parse(date + 'T00:00:00Z');
  if (!Number.isFinite(nominal) || new Date(nominal).toISOString().slice(0,10) !== date) throw new RangeError('date');
  return nominal;
}

export function localInstants(date, time, zone) {
  const day = nominalDay(date);
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(time)) throw new RangeError('time');
  const [hours, minutes] = time.split(':').map(Number);
  const nominal = day + hours * hour + minutes * 60000;
  const formatter = calendar(zone);
  const offsets = new Set();
  for (let sample = nominal - 48 * hour; sample <= nominal + 48 * hour; sample += 6 * hour) {
    offsets.add(localWallClock(sample, formatter) - sample);
  }
  return [...offsets].map(offset => nominal - offset).filter(candidate => localWallClock(candidate, formatter) === nominal).sort();
}

export function risingLongitude(timestamp, latitude, longitude) {
  if (!Number.isFinite(timestamp) || !Number.isFinite(latitude) || Math.abs(latitude) >= 90 ||
      !Number.isFinite(longitude) || Math.abs(longitude) > 180) throw new RangeError('coordinates');
  const time = MakeTime(new Date(timestamp));
  const theta = circle(SiderealTime(time) * 15 + longitude) * rad;
  const tilt = e_tilt(time).tobl * rad;
  const phi = latitude * rad;
  const y = Math.cos(theta) * Math.cos(phi);
  const x = -(Math.sin(theta) * Math.cos(tilt) * Math.cos(phi) + Math.sin(phi) * Math.sin(tilt));
  if (Math.hypot(x,y) < 1e-10) return null;
  let result = Math.atan2(y,x);
  // At high latitudes the eastern intersection can be the opposite root.
  const east = -Math.sin(theta) * Math.cos(result) + Math.cos(theta) * Math.cos(tilt) * Math.sin(result);
  if (Math.abs(east) < 1e-12) return null;
  if (east < 0) result += Math.PI;
  return circle(result / rad);
}

export function positions(utc, latitude, longitude) {
  const instant = new Date(utc);
  return [SunPosition(instant).elon, EclipticGeoMoon(instant).lon, risingLongitude(utc, latitude, longitude)];
}

export function signIndex(degree) {
  return degree == null ? null : Math.floor(circle(degree)/30);
}

export function localDayPositions(date, zone) {
  const nominal = nominalDay(date);
  const formatter = calendar(zone);
  // Gather each UTC segment of the civil date. Sampling by second around
  // entry/exit also handles DST, skipped dates and UTC offsets with seconds.
  const ranges = [];
  const sameDay = utc => Math.floor(localWallClock(utc,formatter)/86400000) === nominal/86400000;
  const boundary = (lo, hi, starts) => {
    while (hi-lo > 1000) {
      const mid = Math.floor((lo+hi)/2000)*1000;
      if (sameDay(mid) === starts) hi=mid;
      else lo=mid;
    }
    return hi;
  };
  const begin = nominal - 36*hour;
  const end = nominal + 60*hour;
  let pending = null;
  for (let utc=begin; utc<=end; utc+=15*60000) {
    if (sameDay(utc)) {
      if (pending === null) pending = boundary(utc-15*60000,utc,true);
    } else if (pending !== null) {
      ranges.push([pending,boundary(utc-15*60000,utc,false)-1]);
      pending=null;
    }
  }
  if (!ranges.length) return null;
  const signs = [new Set(), new Set()];
  for (const [start,finish] of ranges) {
    // The geocentric Sun and Moon progress in longitude and neither crosses
    // more than one sign boundary in these civil-date ranges.
    for (const utc of [start, finish]) {
      const instant = new Date(utc);
      signs[0].add(signIndex(SunPosition(instant).elon));
      signs[1].add(signIndex(EclipticGeoMoon(instant).lon));
    }
  }
  return [...signs.map(set => [...set]), []];
}
