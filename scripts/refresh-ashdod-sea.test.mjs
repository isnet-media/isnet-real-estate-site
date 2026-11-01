import test from 'node:test';
import assert from 'node:assert/strict';
import {parseSea,localTime} from './refresh-ashdod-sea.mjs';
const now=new Date('2026-11-01T10:00:00Z');
function fixture(range='40 / 30-50',id='213') {return `<IssueDateTime>2026-11-01 00:06</IssueDateTime><Location><LocationId>${id}</LocationId><LocationNameEng>Southern Coast</LocationNameEng><TimeUnitData><DateTimeFrom>2026-11-01 08:00</DateTimeFrom><DateTimeTo>2026-11-01 20:00</DateTimeTo><Element><ElementName>Sea status and waves height</ElementName><ElementValue>${range}</ElementValue></Element></TimeUnitData></Location>`;}
test('extracts wave centimetres, not sea-state code',()=>assert.deepEqual(parseSea(fixture(),now).periods[0],{from:'2026-11-01T08:00',to:'2026-11-01T20:00',minCm:30,maxCm:50}));
test('rejects other regions and malformed or reversed ranges',()=>{for(const xml of [fixture('40 / 50-30'),fixture('unavailable'),fixture('40 / 30-50','210')])assert.throws(()=>parseSea(xml,now));});
test('does not publish expired forecast',()=>assert.throws(()=>parseSea(fixture(),new Date('2026-11-02T10:00:00Z'))));
test('uses Israel local time, including summer time',()=>{assert.equal(localTime(now),'2026-11-01T12:00');assert.equal(localTime(new Date('2026-07-01T10:00:00Z')),'2026-07-01T13:00');});
