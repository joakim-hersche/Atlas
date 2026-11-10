// Glossary entries for the spatial statistics (keys as in pipeline/i18n/glossary.yaml). Kept here until
// the pipeline glossary carries them; an entry of the same key in glossary.json takes precedence.
import type { GlossEntry } from './glossary.svelte';

const n = ' ';

export const SPATIAL_GLOSS: Record<string, GlossEntry> = {
  morans_i: {
    term_en: "Moran's I", term_de: "Moran's I", term_fr: "I de Moran",
    en: 'One number for how much places that touch each other resemble each other. Above 0: similar values sit together; around 0: no pattern; below 0: neighbours tend to be opposites. The maximum depends on the map, so compare it with the expected value, not with 1.',
    de: 'Eine Zahl dafür, wie ähnlich sich aneinandergrenzende Orte sind. Über 0: ähnliche Werte liegen beieinander; um 0: kein Muster; unter 0: Nachbarn sind eher Gegensätze. Das Maximum hängt von der Karte ab; vergleichen Sie deshalb mit dem Erwartungswert, nicht mit 1.',
    fr: `Un nombre qui dit à quel point des lieux voisins se ressemblent. Au-dessus de 0${n}: les valeurs proches se regroupent${n}; autour de 0${n}: aucune structure${n}; en dessous de 0${n}: les voisins ont tendance à s’opposer. Le maximum dépend de la carte${n}: comparez à la valeur attendue, pas à 1.`,
  },
  permutation_p: {
    term_en: 'Permutation p-value', term_de: 'Permutations-p-Wert', term_fr: 'Valeur p par permutation',
    en: 'A test by shuffling: the values are moved around the map at random, 999 times. The p-value is the share of maps (the real one included) that look at least as clustered as the real one. Small = unlikely to be chance. The smallest possible value is 0.001.',
    de: 'Ein Test durch Mischen: Die Werte werden 999 Mal zufällig auf der Karte verteilt. Der p-Wert ist der Anteil der Karten (die echte eingeschlossen), die mindestens so stark gruppiert aussehen wie die echte. Klein = kaum Zufall. Der kleinstmögliche Wert ist 0.001.',
    fr: `Un test par mélange${n}: les valeurs sont redistribuées au hasard sur la carte, 999 fois. La valeur p est la part des cartes (la vraie comprise) au moins aussi groupées que la vraie. Petite = peu probablement dû au hasard. La plus petite valeur possible est 0.001.`,
  },
  lisa: {
    term_en: 'Local clusters (LISA)', term_de: 'Lokale Cluster (LISA)', term_fr: 'Groupes locaux (LISA)',
    en: 'Local Indicators of Spatial Association. For every place: are it and its neighbours both high (High–High) or both low (Low–Low), or does it stand out from them (High–Low, Low–High)? Only places where the pattern is stronger than in random shuffles are coloured.',
    de: 'Lokale Indikatoren räumlicher Assoziation. Für jeden Ort: Sind er und seine Nachbarn beide hoch (hoch–hoch) oder beide tief (tief–tief), oder sticht er heraus (hoch–tief, tief–hoch)? Gefärbt werden nur Orte, bei denen das Muster stärker ist als bei zufälligem Mischen.',
    fr: `Indicateurs locaux d’association spatiale. Pour chaque lieu${n}: lui et ses voisins sont-ils tous deux élevés (haut–haut) ou tous deux bas (bas–bas), ou se démarque-t-il (haut–bas, bas–haut)${n}? Seuls les lieux où la structure est plus forte qu’avec un mélange au hasard sont colorés.`,
  },
  bivariate_map: {
    term_en: 'Bivariate map', term_de: 'Bivariate Karte', term_fr: 'Carte bivariée',
    en: 'Two metrics at once. Each metric is cut into a lower, middle and upper third of places; the colour shows the combination, so the darkest cell means high on both.',
    de: 'Zwei Kennzahlen gleichzeitig. Jede wird in ein unteres, mittleres und oberes Drittel der Orte geteilt; die Farbe zeigt die Kombination, die dunkelste Zelle also hoch bei beiden.',
    fr: `Deux indicateurs à la fois. Chacun est coupé en tiers inférieur, moyen et supérieur des lieux${n}; la couleur montre la combinaison, la case la plus foncée signifiant élevé pour les deux.`,
  },
  contiguity: {
    term_en: 'Neighbours (contiguity)', term_de: 'Nachbarn (Kontiguität)', term_fr: 'Voisins (contiguïté)',
    en: 'Two places are neighbours if their boundaries share a stretch of at least 10 m (BFS generalised boundaries, 2026). Each neighbour counts equally. Places without a land border, such as islands, have no neighbours and are left out.',
    de: 'Zwei Orte sind Nachbarn, wenn ihre Grenzen auf mindestens 10 m aneinanderstossen (BFS generalisierte Grenzen, 2026). Jeder Nachbar zählt gleich. Orte ohne Landgrenze, etwa Inseln, haben keine Nachbarn und bleiben ausser Betracht.',
    fr: 'Deux lieux sont voisins si leurs limites ont en commun un tronçon d’au moins 10 m (limites généralisées OFS, 2026). Chaque voisin compte pour autant. Les lieux sans frontière terrestre, comme les îles, n’ont pas de voisins et sont exclus.',
  },
  fdr: {
    term_en: 'False discovery rate (FDR)', term_de: 'Falschentdeckungsrate (FDR)', term_fr: 'Taux de fausses découvertes (FDR)',
    en: 'When thousands of places are tested at once, some look special by chance alone. The Benjamini–Hochberg correction keeps the expected share of false alarms among the flagged places at 5 %. It flags fewer places than the plain p < 0.05 rule.',
    de: 'Werden Tausende Orte gleichzeitig getestet, fallen einige allein durch Zufall auf. Die Korrektur nach Benjamini–Hochberg hält den erwarteten Anteil falscher Alarme unter den markierten Orten bei 5 %. Sie markiert weniger Orte als die einfache Regel p < 0.05.',
    fr: 'Quand des milliers de lieux sont testés à la fois, certains paraissent particuliers par pur hasard. La correction de Benjamini–Hochberg maintient à 5 % la part attendue de fausses alertes parmi les lieux signalés. Elle en signale moins que la simple règle p < 0.05.',
  },
};
