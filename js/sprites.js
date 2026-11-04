// sprites.js — pixel-art sprite factory.
// Every icon in the app is a character grid rendered to crisp SVG <rect>s,
// so nothing depends on image assets and everything scales without blurring.

const PAL = {
  '.': null,             // transparent
  K: '#1A1A2E',          // outline / ink
  W: '#FFFFFF',
  R: '#E63946', r: '#F2606C',
  B: '#2A6FDB', b: '#5B95E8',
  Y: '#FFC94A', y: '#FFE49B',
  G: '#3FA34D', g: '#66C173',
  P: '#7B4FBF', p: '#A47FDB',
  O: '#F4801F', o: '#FBAD60',
  T: '#2AB7B0', t: '#68D6D0',
  S: '#C9C9D8',          // steel / grey
  D: '#8A8AA0',          // dark grey
  F: '#F5EAD0',          // paper shade
  N: '#7A4A22',          // brown
  n: '#B0703A',
};

// Each sprite is an array of equal-length strings.
const SPRITES = {
  coin: [
    '..KKKK..',
    '.KYYYYK.',
    'KYYOOYYK',
    'KYOYYOYK',
    'KYOYYOYK',
    'KYYOOYYK',
    '.KYYYYK.',
    '..KKKK..',
  ],
  star: [
    '...KK...',
    '...YY...',
    '.KKYYKK.',
    'KYYYYYYK',
    '.KYYYYK.',
    '..KYYK..',
    '.KYKKYK.',
    '.K....K.',
  ],
  heart: [
    '.KK..KK.',
    'KRRKKRRK',
    'KRWRRRRK',
    'KRRRRRRK',
    '.KRRRRK.',
    '..KRRK..',
    '...KK...',
    '........',
  ],
  gem: [
    '..KKKK..',
    '.KTTTTK.',
    'KTWTTTTK',
    'KTTTTTTK',
    '.KTTTTK.',
    '..KTTK..',
    '...KK...',
    '........',
  ],
  mushroom: [
    '..KKKK..',
    '.KRRRRK.',
    'KRWWRRRK',
    'KRWWRRRK',
    'KRRRRRRK',
    '.KWWWWK.',
    '.KWKKWK.',
    '..KKKK..',
  ],
  brick: [
    'KKKKKKKK',
    'KNNKNNNK',
    'KNNKNNNK',
    'KKKKKKKK',
    'KNNNKNNK',
    'KNNNKNNK',
    'KKKKKKKK',
    '........',
  ],
  qblock: [
    'KKKKKKKK',
    'KYYYYYYK',
    'KYKKKYYK',
    'KYYYKYYK',
    'KYYKYYYK',
    'KYYKYYYK',
    'KYYYYYYK',
    'KKKKKKKK',
  ],
  invader: [
    '..K..K..',
    '.KGKKGK.',
    '.KGGGGK.',
    'KGKGGKGK',
    'KGGGGGGK',
    '..K..K..',
    '.K....K.',
    'K......K',
  ],
  ghost: [
    '..KKKK..',
    '.KPPPPK.',
    'KPWKPWKP',
    'KPPPPPPK',
    'KPPPPPPK',
    'KPKPKPKP',
    'K.K.K.K.',
    '........',
  ],
  controller: [
    '.KKKKKK.',
    'KSSSSSSK',
    'KSKSSRSK',
    'KKKKSSSK',
    'KSKSSRSK',
    'KSSSSSSK',
    '.KKKKKK.',
    '........',
  ],
  floppy: [
    'KKKKKKKK',
    'KBBWWBBK',
    'KBBWWBBK',
    'KBBBBBBK',
    'KBWWWWBK',
    'KBWKKWBK',
    'KBWWWWBK',
    'KKKKKKKK',
  ],
  cartridge: [
    'KKKKKKKK',
    'KPPPPPPK',
    'KPWWWWPK',
    'KPWKKWPK',
    'KPPPPPPK',
    'KKSKKSKK',
    'KSSKKSSK',
    'KKKKKKKK',
  ],
  book: [
    'KKKKKKKK',
    'KBBBKOOK',
    'KBWBKOWK',
    'KBBBKOOK',
    'KBWBKOWK',
    'KBBBKOOK',
    'KBBBKOOK',
    'KKKKKKKK',
  ],
  clock: [
    '..KKKK..',
    '.KWWWWK.',
    'KWWKWWWK',
    'KWWKWWWK',
    'KWWKKWWK',
    'KWWWWWWK',
    '.KWWWWK.',
    '..KKKK..',
  ],
  trophy: [
    'KKKKKKKK',
    'KYYYYYYK',
    'SKYYYYKS',
    '.KYYYYK.',
    '..KYYK..',
    '...YY...',
    '..KYYK..',
    '.KKKKKK.',
  ],
  sword: [
    '.....KK.',
    '....KSK.',
    '...KSKK.',
    '..KSKK..',
    '.KKSK...',
    'KNKKK...',
    'KKNK....',
    'K.KK....',
  ],
  potion: [
    '...KK...',
    '...KK...',
    '..KKKK..',
    '.KPPPPK.',
    'KPPWPPPK',
    'KPPPPPPK',
    'KPPPPPPK',
    '.KKKKKK.',
  ],
  key: [
    '.KKK....',
    'KYKYK...',
    'KYKYK...',
    '.KYK....',
    '..KYK...',
    '...KYKK.',
    '...KYKK.',
    '....KK..',
  ],
  scroll: [
    '.KKKKKK.',
    'KFFFFFFK',
    'KFKKKKFK',
    'KFFFFFFK',
    'KFKKKKFK',
    'KFFFFFFK',
    'KFKKKFFK',
    '.KKKKKK.',
  ],
  bolt: [
    '....KK..',
    '...KYK..',
    '..KYYK..',
    '.KYYKKK.',
    'KYYYYYK.',
    '.KKKYK..',
    '...KYK..',
    '...KK...',
  ],
  flag: [
    'KK......',
    'KKKKKK..',
    'KKGGGGK.',
    'KKGGGGK.',
    'KKKKKK..',
    'KK......',
    'KK......',
    'KKKK....',
  ],
  chart: [
    'K......K',
    'K....KK.',
    'K..KKBK.',
    'K.KBKBK.',
    'K.KBKBKK',
    'KKKBKBKG',
    'KKBKBKGK',
    'KKKKKKKK',
  ],
  brain: [
    '..KKKK..',
    '.KpppPK.',
    'KpPpPppK',
    'KppPpPpK',
    'KpPppPpK',
    'KppPpppK',
    '.KppppK.',
    '..KKKK..',
  ],
  calendar: [
    'K.KKKK.K',
    'KKKKKKKK',
    'KWWWWWWK',
    'KWRRWWWK',
    'KWRRWWWK',
    'KWWWWRRK',
    'KWWWWRRK',
    'KKKKKKKK',
  ],
  target: [
    '..KKKK..',
    '.KWWWWK.',
    'KWRRRRWK',
    'KWRWWRWK',
    'KWRWWRWK',
    'KWRRRRWK',
    '.KWWWWK.',
    '..KKKK..',
  ],
  skull: [
    '.KKKKKK.',
    'KWWWWWWK',
    'KWKWWKWK',
    'KWKWWKWK',
    'KWWKKWWK',
    'KWWWWWWK',
    '.KWKWKW.',
    '..KKKK..',
  ],
  castle: [
    'K.K..K.K',
    'KKKKKKKK',
    'KSSDDSSK',
    'KSSDDSSK',
    'KSKKKKSK',
    'KSKRRKSK',
    'KSKRRKSK',
    'KKKKKKKK',
  ],
  onelife: [
    'KKKKKKKK',
    'KGGGGGGK',
    'KGWKKWGK',
    'KGWKKWGK',
    'KGWWWWGK',
    'KGKWWKGK',
    'KGGGGGGK',
    'KKKKKKKK',
  ],
  coffee: [
    '..SS....',
    '.SS.....',
    'KKKKKK..',
    'KOOOOOKK',
    'KOOOOO.K',
    'KNNNNNKK',
    '.KNNNK..',
    '..KKK...',
  ],
  food: [
    '..GG....',
    '..NN....',
    '.KRRKK..',
    'KRRRRRK.',
    'KRRRRRRK',
    'KRRRRRRK',
    '.KRRRRK.',
    '..KKKK..',
  ],
  meal: [
    '..KKKK..',
    '.KYYYYK.',
    'KYWWWWYK',
    'KWWNNWWK',
    'KWWNNWWK',
    'KYWWWWYK',
    '.KYYYYK.',
    '..KKKK..',
  ],
};

/**
 * Render a sprite to an inline SVG string.
 * @param {string} name  key in SPRITES
 * @param {number} size  rendered pixel size of the whole sprite
 * @param {string} cls   extra classes on the <svg>
 */
export function sprite(name, size = 32, cls = '') {
  const map = SPRITES[name];
  if (!map) return '';
  const rows = map.length;
  const cols = map[0].length;
  let rects = '';
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const fill = PAL[map[y][x]];
      if (!fill) continue;
      rects += `<rect x="${x}" y="${y}" width="1" height="1" fill="${fill}"/>`;
    }
  }
  return (
    `<svg class="sprite ${cls}" width="${size}" height="${(size / cols) * rows}" ` +
    `viewBox="0 0 ${cols} ${rows}" shape-rendering="crispEdges" aria-hidden="true" ` +
    `focusable="false">${rects}</svg>`
  );
}

export const SPRITE_NAMES = Object.keys(SPRITES);

/** Sprite for a difficulty level. */
export function difficultySprite(level, size = 22) {
  const map = { easy: 'gem', medium: 'coin', hard: 'skull' };
  return sprite(map[level] || 'qblock', size);
}
