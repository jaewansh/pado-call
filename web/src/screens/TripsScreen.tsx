import { useApp, type TripRecord } from '../state';
import { areaById, placeById, type AreaId, type Lang, type PlaceId } from '../data/places';
import { fmtMin, fmtTime, fmtWon, t } from '../i18n/strings';
import { Icon } from '../components/Icon';

const AIRPORT: Record<Lang, string> = { ko: '김해공항', en: 'Gimhae Airport', ja: '金海空港', zhHans: '金海机场', zhHant: '金海機場' };

function endName(tr: TripRecord, end: 'from' | 'to', lang: Lang): string {
  const v = tr[end];
  if (v === 'airport') return AIRPORT[lang];
  if (tr.kind === 'ride') return placeById(v as PlaceId).name[lang];
  return areaById(v as AreaId).name[lang];
}

function status(tr: TripRecord, clock: number, day: string): 'booked' | 'coming' | 'onboard' | 'done' {
  if (tr.day !== day) return 'booked';
  if (clock < tr.pickup) return tr.kind === 'ride' ? 'coming' : 'booked';
  if (clock < tr.arrive) return 'onboard';
  return 'done';
}

export function TripsScreen() {
  const { lang, trips, clock, day, cancelTrip, showToast, go } = useApp();
  if (!trips.length) {
    return (
      <div className="empty">
        <Icon name="ticket" size={44} />
        <h2>{t('trips.empty', lang)}</h2>
        <p>{t('trips.emptyBody', lang)}</p>
        <div className="row" style={{ justifyContent: 'center', flexWrap: 'wrap' }}>
          <button type="button" className="btn-ghost" onClick={() => go('call')}><Icon name="plane" size={16} />{t('call.seg.airport', lang)}</button>
          <button type="button" className="btn-ghost" onClick={() => go('call', { seg: 'ride' })}><Icon name="van" size={16} />{t('call.seg.ride', lang)}</button>
        </div>
      </div>
    );
  }
  return (
    <>
      <h2 className="section-title" style={{ marginTop: 6 }}>{t('trips.title', lang)}</h2>
      {trips.map((tr) => {
        const st = status(tr, clock, day);
        const kindLabel = tr.kind === 'arr' ? t('trips.airportArr', lang) : tr.kind === 'dep' ? t('trips.airportDep', lang) : t('trips.ride', lang);
        const color = tr.kind === 'ride' ? 'var(--teal-ink)' : 'var(--amber-ink)';
        return (
          <article key={tr.id} className={`trip${tr.cancelled ? ' cancelled' : ''}`}>
            <div className="between">
              <span className="kind" style={{ color }}>
                <Icon name={tr.kind === 'ride' ? 'van' : 'plane'} size={18} /> {kindLabel}
                {tr.note && tr.kind !== 'ride' ? <span className="pill" style={{ marginLeft: 4 }}>{tr.note}</span> : null}
              </span>
              <span className="pill teal">{tr.cancelled ? t('trips.cancelled', lang) : t(`trips.s.${st}` as 'trips.s.booked', lang)}</span>
            </div>
            <div className="od" style={{ marginTop: 10 }}>
              <div className="rail"><i style={{ background: tr.kind === 'ride' ? 'var(--teal)' : 'var(--amber)' }} /><span /><i style={{ background: 'var(--navy)' }} /></div>
              <div className="stack" style={{ gap: 8 }}>
                <div>
                  <div className="value">{endName(tr, 'from', lang)}</div>
                  <div className="sub">{t('trips.pickupAt', lang, { t: fmtTime(tr.pickup) })}{st === 'coming' && !tr.cancelled ? ` · ${fmtMin(tr.pickup - clock, lang)}` : ''}</div>
                </div>
                <div>
                  <div className="value">{endName(tr, 'to', lang)}</div>
                  <div className="sub">{t('trips.arriveAt', lang, { t: fmtTime(tr.arrive) })}</div>
                </div>
              </div>
            </div>
            <hr className="divider" />
            <div className="between" style={{ alignItems: 'flex-end' }}>
              <div>
                <div className="label">{t('trips.code', lang)}</div>
                <div className="code">{tr.code}</div>
                <div className="sub">{t('trips.show', lang)}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className="sub"><Icon name="users" size={14} /> {tr.pax}</div>
                <div className="value">{fmtWon(tr.fare)}</div>
              </div>
            </div>
            {!tr.cancelled && st !== 'done' ? (
              <div style={{ marginTop: 10 }}>
                <button type="button" className="link-btn" onClick={() => { cancelTrip(tr.id); showToast(t('toast.cancelled', lang)); }}>{t('trips.cancel', lang)}</button>
              </div>
            ) : null}
          </article>
        );
      })}
    </>
  );
}
