/** Builders for the markers of the real map (positions are real WGS84 coordinates). */
import { AIRPORT, areaById, placesInZone, type AreaId, type Lang, type PlaceId } from '../data/places';
import type { ZoneId } from '../data/scenario';
import { CI_COLORS, ciLevel } from '../engine/crowd';
import { fmtCi } from '../i18n/strings';
import { curve, type MapMark } from './RealMap';

/** Label side per place, chosen so neighbouring labels do not collide at the zone zoom. */
const LABEL_POS: Record<PlaceId, MapMark['labelPos']> = {
  gwangalli: 'bottom',
  millak: 'top',
  centum: 'top',
  haeundae: 'top',
  dongbaek: 'bottom',
  blueline: 'top',
  busanstn: 'left',
  cruise: 'top',
  nampo: 'bottom',
  gamcheon: 'top',
  huinnyeoul: 'left',
  taejongdae: 'top',
};

export interface CrowdState {
  id: PlaceId;
  ci: number;
  open: boolean;
}

export function crowdMarks(zone: ZoneId, lang: Lang, crowd: CrowdState[], selected: PlaceId | null): MapMark[] {
  return placesInZone(zone).map((p) => {
    const c = crowd.find((x) => x.id === p.id);
    if (!c) return { id: p.id, lng: p.lng, lat: p.lat, kind: 'place' as const, label: p.short[lang], labelPos: LABEL_POS[p.id] };
    return {
      id: p.id,
      lng: p.lng,
      lat: p.lat,
      kind: 'crowd' as const,
      color: c.open ? CI_COLORS[ciLevel(c.ci)] : '#9aa6b3',
      halo: c.open ? Math.round(16 + 22 * Math.min(1.7, Math.max(0, c.ci))) : 0,
      label: c.open ? `${p.short[lang]} ${fmtCi(c.ci)}` : p.short[lang],
      dim: !c.open,
      selected: selected === p.id,
      clickable: true,
      ariaLabel: p.name[lang],
      labelPos: LABEL_POS[p.id],
    };
  });
}

/** Vehicles in service, parked next to the hubs of the zone. */
function vanMarks(zone: ZoneId, n: number): MapMark[] {
  const hubs = placesInZone(zone).filter((p) => p.hub);
  return Array.from({ length: n }, (_, i) => {
    const h = hubs[i % hubs.length];
    const k = Math.floor(i / hubs.length);
    return { id: `van-${i}`, lng: h.lng + 0.0022 + 0.0016 * k, lat: h.lat + 0.0012 + 0.0006 * k, kind: 'van' as const };
  });
}

export function rideMarks(zone: ZoneId, lang: Lang, from: PlaceId, to: PlaceId, vans: number): MapMark[] {
  const places = placesInZone(zone).map((p): MapMark => {
    const kind = p.id === from ? 'pickup' : p.id === to ? 'dest' : 'place';
    return { id: p.id, lng: p.lng, lat: p.lat, kind, label: p.short[lang], labelPos: LABEL_POS[p.id], clickable: kind === 'place', ariaLabel: p.name[lang] };
  });
  return [...vanMarks(zone, vans), ...places];
}

export function rideLine(from: { lng: number; lat: number }, to: { lng: number; lat: number }): [number, number][] {
  return curve([from.lng, from.lat], [to.lng, to.lat], 0.16);
}

const AIRPORT_NAME: Record<Lang, string> = { ko: '김해공항', en: 'Gimhae Airport', ja: '金海空港', zhHans: '金海机场', zhHant: '金海機場' };

/** Airport ↔ hotel area (direction: 'arr' airport → hotel, 'dep' hotel → airport). */
export function airportMarks(area: AreaId, lang: Lang): MapMark[] {
  const a = areaById(area);
  return [
    { id: 'airport', lng: AIRPORT.lng, lat: AIRPORT.lat, kind: 'airport', label: AIRPORT_NAME[lang], labelPos: 'bottom' },
    { id: 'hotel', lng: a.lng, lat: a.lat, kind: 'hotel', label: a.name[lang], labelPos: 'top' },
  ];
}

export function airportLine(area: AreaId): [number, number][] {
  const a = areaById(area);
  return curve([AIRPORT.lng, AIRPORT.lat], [a.lng, a.lat], -0.12, 40);
}

export function airportFit(area: AreaId): [number, number][] {
  const a = areaById(area);
  return [
    [AIRPORT.lng, AIRPORT.lat],
    [a.lng, a.lat],
  ];
}
