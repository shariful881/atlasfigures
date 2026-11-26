// Sunrise, sunset and solar noon — NOAA Solar Calculator equations (Global Monitoring Laboratory, "General Solar
// Position Calculations"; https://gml.noaa.gov/grad/solcalc/), the method most sunrise tables use. Sunrise/sunset =
// the moment the sun's centre is 0.833° below the horizon (refraction + the sun's radius), at sea level. Accuracy is
// about one minute for latitudes between ±60°. Used at build time (monthly tables) and in the browser ("today").
// Returns times as UTC milliseconds; callers format them in the city's time zone.
const rad = (d: number) => (d * Math.PI) / 180;
const deg = (r: number) => (r * 180) / Math.PI;

function solar(jc: number) {
  const L0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360;
  const M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc);
  const e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc);
  const C = Math.sin(rad(M)) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + Math.sin(rad(2 * M)) * (0.019993 - 0.000101 * jc) + Math.sin(rad(3 * M)) * 0.000289;
  const trueLong = L0 + C;
  const omega = 125.04 - 1934.136 * jc;
  const lambda = trueLong - 0.00569 - 0.00478 * Math.sin(rad(omega));
  const eps0 = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60;
  const eps = eps0 + 0.00256 * Math.cos(rad(omega));
  const decl = deg(Math.asin(Math.sin(rad(eps)) * Math.sin(rad(lambda))));
  const y = Math.tan(rad(eps / 2)) ** 2;
  const eqTime = 4 * deg(y * Math.sin(2 * rad(L0)) - 2 * e * Math.sin(rad(M)) + 4 * e * y * Math.sin(rad(M)) * Math.cos(2 * rad(L0)) - 0.5 * y * y * Math.sin(4 * rad(L0)) - 1.25 * e * e * Math.sin(2 * rad(M)));
  return { decl, eqTime };
}

/** Sun events for the calendar date y-m-d (UTC date used as the day's anchor) at latitude/longitude (east +).
 *  rise/set are null when the sun does not rise or set that day (polar day/night). */
export function sunTimes(y: number, m: number, d: number, lat: number, lon: number) {
  const dayStart = Date.UTC(y, m - 1, d);
  const jd = dayStart / 86400000 + 2440587.5;
  // iterate once around local noon for better precision
  let noonMin = 720 - 4 * lon;
  for (let i = 0; i < 2; i++) {
    const jc = (jd + noonMin / 1440 - 2451545) / 36525;
    noonMin = 720 - 4 * lon - solar(jc).eqTime;
  }
  const event = (rising: boolean) => {
    let t = noonMin;
    for (let i = 0; i < 3; i++) {
      const jc = (jd + t / 1440 - 2451545) / 36525;
      const { decl, eqTime } = solar(jc);
      const cosH = (Math.cos(rad(90.833)) / (Math.cos(rad(lat)) * Math.cos(rad(decl)))) - Math.tan(rad(lat)) * Math.tan(rad(decl));
      if (cosH > 1 || cosH < -1) return null;
      const ha = deg(Math.acos(cosH));
      t = 720 - 4 * (lon + (rising ? ha : -ha)) - eqTime;
    }
    return dayStart + t * 60000;
  };
  return { rise: event(true), set: event(false), noon: dayStart + noonMin * 60000 };
}
