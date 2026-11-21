// Z80 song table for the unprotected arcade shangon set.
// Titles corroborated with Super-Hang-On-Ultimate/source/src/sho_music.c.
// All four pointers and their 13 channel records were checked in epr-10649c.88.
export const TRACKS = [
  { title: 'Outride a Crisis', command: 0x9d, header: 0x1f21 },
  { title: 'Sprinter', command: 0x82, header: 0x4fc3 },
  { title: 'Winning Run', command: 0x96, header: 0x3c84 },
  { title: 'Hard Road', command: 0x81, header: 0x6107 }
];
export function parseSongHeaders(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.length !== 0x8000)
    throw new Error('Expected the 32 KiB Z80 program ROM (epr-10649c.88)');
  const word = p => bytes[p] | (bytes[p + 1] << 8);
  return TRACKS.map(track => {
    const pointerOffset = 0x6c0 + 2 * (track.command - 0x81);
    if (word(pointerOffset) !== track.header || bytes[track.header] !== 13)
      throw new Error('Unexpected song table in this ROM');
    const channels = Array.from({length:13}, (_, i) => {
      const p=track.header + 1 + 9*i;
      const id=bytes[p+1], address=word(p+3);
      if (id!==(i<8?0x80+i:0x40+i-8) || address>=bytes.length)
        throw new Error('Unexpected channel header');
      return {id, kind:i<8?'FM':'PCM', address, raw:Array.from(bytes.slice(p,p+9))};
    });
    return {...track, pointerOffset, channels};
  });
}
// This module reads metadata only; it does not synthesize music.
