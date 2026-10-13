'use strict';
// First powered-light pass, docs/tower_design/README.md. Stops are BEFORE the
// generator's existing LIGHT_STOPS_ADD. No exposure, sky, alarm or state writes.
// Small neutral pools reveal authored color; landings retain district accents.
function tune(label, color, radius, stops) {
  const room = /^(power hall light|tp bay (light|doorway|pad)|tod light (base|vault|conduit|shaft|wing)|spire light (base|arrival|hub|summit))/;
  const landing = /^(tod light lap\d+ (mid|end)$|spire light lap\d+$)/;
  const lounge = /^tod light lap\d+ breather/;
  if (landing.test(label)) return {color, radius: 300, stops: 8.2, farEdge: .65, spec: -1};
  if (lounge.test(label) || room.test(label)) {
    const c = color.split(/\s+/).map(Number).map(v => +(0.45 + 0.55 * v).toFixed(4));
    return {color: c.join(' '), radius: Math.min(radius, 460), stops: 8.5, farEdge: .65, spec: -1};
  }
  // docs/196 THE DEPARTURE HALL: the room profile's softness (farEdge, no spec
  // hotspots on the tiles) but its OWN colours - each gate's light IS its
  // district's colour, so it must not be desaturated like the room pools above.
  if (/^transit hall /.test(label))
    return {color, radius: Math.min(radius, 460), stops, farEdge: .65, spec: -1};
  // docs/202 THE HAVENS (the safe zones): the field's cool key, the district pools
  // on the threshold and pad and the anchor gems' cyan keep THEIR colours (never
  // the room pools' desaturation above), with the same soft room profile.
  if (/^tod light lap\d+ haven /.test(label))
    return {color, radius: Math.min(radius, 480), stops, farEdge: .65, spec: -1};
  if (/^(tod|spire) light route /.test(label))
    return {color: '0.78 0.88 1', radius: 280, stops: 8.5, farEdge: .6, spec: -1};
  return {color, radius, stops};
}

function stairPools(laps, lapRise, flightRise, pathCentre, x = 0, y = 0) {
  const rows = [];
  for (let lap = 0; lap < laps; lap++) {
    const s = lap % 2 ? -1 : 1, z = lap * lapRise;
    // Same parity and flight midpoints as the generated stairs. 120u above
    // each flight's midpoint; radius stays below the 384u floor pitch.
    rows.push({label: `lap${lap + 1} flight1`, origin: [x + s * pathCentre, y, z + flightRise / 2 + 120]});
    rows.push({label: `lap${lap + 1} flight2`, origin: [x, y + s * pathCentre, z + flightRise * 1.5 + 120]});
  }
  return rows;
}
module.exports = {tune, stairPools};
