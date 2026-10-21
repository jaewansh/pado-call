/** Demo state shared by every screen: language, scenario day, demo clock, operating levers, trips. */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { AreaId, Lang, PlaceId } from './data/places';
import { DEFAULT_LEVERS, type DayType, type Levers, type ZoneId } from './data/scenario';
import { LANGS } from './i18n/strings';

export type TripKind = 'arr' | 'dep' | 'ride';
export interface TripRecord {
  id: string;
  kind: TripKind;
  code: string;
  day: DayType;
  createdAt: number; // demo minute of day when booked
  pickup: number; // minute of day
  arrive: number; // minute of day (median)
  zone: ZoneId;
  from: PlaceId | AreaId | 'airport';
  to: PlaceId | AreaId | 'airport';
  pax: number;
  fare: number;
  note?: string; // flight number etc.
  cancelled?: boolean;
}

export interface Route {
  path: string; // 'call' | 'wave' | 'trips' | 'control' | 'model'
  params: URLSearchParams;
}

interface Ctx {
  lang: Lang;
  setLang: (l: Lang) => void;
  day: DayType;
  setDay: (d: DayType) => void;
  clock: number;
  setClock: (m: number) => void;
  levers: Levers;
  setLevers: (l: Levers) => void;
  trips: TripRecord[];
  addTrip: (t: Omit<TripRecord, 'id' | 'code'>) => TripRecord;
  cancelTrip: (id: string) => void;
  toast: string | null;
  showToast: (s: string) => void;
  route: Route;
  go: (path: string, params?: Record<string, string>) => void;
}

const StateCtx = createContext<Ctx | null>(null);
const STORE = 'padocall.trips.v1';
const CODE_CHARS = 'ACDEFGHJKMNPQRTUVWXY34679';

function readTrips(): TripRecord[] {
  try {
    const raw = window.localStorage.getItem(STORE);
    const v = raw ? JSON.parse(raw) : [];
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}
function writeTrips(v: TripRecord[]) {
  try {
    window.localStorage.setItem(STORE, JSON.stringify(v));
  } catch {
    /* storage unavailable (private mode, preview) — trips stay in memory */
  }
}

function parseRoute(): Route {
  const h = window.location.hash.replace(/^#\/?/, '');
  const [path, qs] = h.split('?');
  return { path: path || 'call', params: new URLSearchParams(qs ?? '') };
}

function initialLang(q: URLSearchParams): Lang {
  const fromQ = q.get('lang') as Lang | null;
  if (fromQ && LANGS.some((l) => l.id === fromQ)) return fromQ;
  const nav = (navigator.language || 'en').toLowerCase();
  if (nav.startsWith('ko')) return 'ko';
  if (nav.startsWith('ja')) return 'ja';
  if (nav.startsWith('zh')) return /tw|hk|mo|hant/.test(nav) ? 'zhHant' : 'zhHans';
  return 'en';
}

function initialClock(q: URLSearchParams): number {
  const v = q.get('t');
  if (v && /^\d{3,4}$/.test(v)) {
    const n = Number(v);
    return Math.min(23 * 60 + 50, Math.floor(n / 100) * 60 + (n % 100));
  }
  return 19 * 60 + 30;
}

export function StateProvider({ children }: { children: ReactNode }) {
  const q = useMemo(() => new URLSearchParams(window.location.search), []);
  const [lang, setLang] = useState<Lang>(() => initialLang(q));
  const [day, setDay] = useState<DayType>(() => (['weekday', 'weekend', 'cruise', 'drone'].includes(q.get('day') ?? '') ? (q.get('day') as DayType) : 'drone'));
  const [clock, setClock] = useState<number>(() => initialClock(q));
  const [levers, setLevers] = useState<Levers>(DEFAULT_LEVERS);
  const [trips, setTrips] = useState<TripRecord[]>(() => (q.get('fresh') ? [] : readTrips()));
  const [toast, setToast] = useState<string | null>(null);
  const [route, setRoute] = useState<Route>(parseRoute);
  const toastTimer = useRef<number | undefined>(undefined);

  useEffect(() => {
    const on = () => setRoute(parseRoute());
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);

  useEffect(() => {
    const html = LANGS.find((l) => l.id === lang)?.html ?? 'en';
    document.documentElement.lang = route.path === 'control' || route.path === 'model' ? 'ko' : html;
  }, [lang, route.path]);

  const go = useCallback((path: string, params?: Record<string, string>) => {
    const qs = params ? `?${new URLSearchParams(params).toString()}` : '';
    window.location.hash = `#/${path}${qs}`;
    window.scrollTo({ top: 0 });
  }, []);

  const showToast = useCallback((s: string) => {
    setToast(s);
    window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const addTrip = useCallback((tr: Omit<TripRecord, 'id' | 'code'>) => {
    const code = Array.from({ length: 4 }, () => CODE_CHARS[Math.floor(Math.random() * CODE_CHARS.length)]).join('');
    const rec: TripRecord = { ...tr, id: `${Date.now()}-${Math.floor(Math.random() * 1e6)}`, code: `PD-${code}` };
    setTrips((prev) => {
      const next = [rec, ...prev].slice(0, 30);
      writeTrips(next);
      return next;
    });
    return rec;
  }, []);

  const cancelTrip = useCallback((id: string) => {
    setTrips((prev) => {
      const next = prev.map((x) => (x.id === id ? { ...x, cancelled: true } : x));
      writeTrips(next);
      return next;
    });
  }, []);

  const value: Ctx = { lang, setLang, day, setDay, clock, setClock, levers, setLevers, trips, addTrip, cancelTrip, toast, showToast, route, go };
  return <StateCtx.Provider value={value}>{children}</StateCtx.Provider>;
}

export function useApp(): Ctx {
  const c = useContext(StateCtx);
  if (!c) throw new Error('StateProvider missing');
  return c;
}
