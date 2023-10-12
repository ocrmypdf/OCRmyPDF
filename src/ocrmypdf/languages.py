# SPDX-FileCopyrightText: 2023 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Language codes and names from ISO 639.

Derived from
https://www.loc.gov/standards/iso639-2/ascii_8bits.html
"""


from typing import NamedTuple


class ISOCodeData(NamedTuple):
    alt: str
    alpha_2: str
    english: str
    french: str


ISO_639_3 = {
    'aar': ISOCodeData(alt='', alpha_2='aa', english='Afar', french='afar'),
    'abk': ISOCodeData(alt='', alpha_2='ab', english='Abkhazian', french='abkhaze'),
    'ace': ISOCodeData(alt='', alpha_2='', english='Achinese', french='aceh'),
    'ach': ISOCodeData(alt='', alpha_2='', english='Acoli', french='acoli'),
    'ada': ISOCodeData(alt='', alpha_2='', english='Adangme', french='adangme'),
    'ady': ISOCodeData(alt='', alpha_2='', english='Adyghe; Adygei', french='adyghé'),
    'afa': ISOCodeData(
        alt='',
        alpha_2='',
        english='Afro-Asiatic languages',
        french='afro-asiatiques, langues',
    ),
    'afh': ISOCodeData(alt='', alpha_2='', english='Afrihili', french='afrihili'),
    'afr': ISOCodeData(alt='', alpha_2='af', english='Afrikaans', french='afrikaans'),
    'ain': ISOCodeData(alt='', alpha_2='', english='Ainu', french='aïnou'),
    'aka': ISOCodeData(alt='', alpha_2='ak', english='Akan', french='akan'),
    'akk': ISOCodeData(alt='', alpha_2='', english='Akkadian', french='akkadien'),
    'alb': ISOCodeData(alt='sqi', alpha_2='sq', english='Albanian', french='albanais'),
    'ale': ISOCodeData(alt='', alpha_2='', english='Aleut', french='aléoute'),
    'alg': ISOCodeData(
        alt='',
        alpha_2='',
        english='Algonquian languages',
        french='algonquines, langues',
    ),
    'alt': ISOCodeData(
        alt='', alpha_2='', english='Southern Altai', french='altai du Sud'
    ),
    'amh': ISOCodeData(alt='', alpha_2='am', english='Amharic', french='amharique'),
    'ang': ISOCodeData(
        alt='',
        alpha_2='',
        english='English, Old (ca.450-1100)',
        french='anglo-saxon (ca.450-1100)',
    ),
    'anp': ISOCodeData(alt='', alpha_2='', english='Angika', french='angika'),
    'apa': ISOCodeData(
        alt='', alpha_2='', english='Apache languages', french='apaches, langues'
    ),
    'ara': ISOCodeData(alt='', alpha_2='ar', english='Arabic', french='arabe'),
    'arc': ISOCodeData(
        alt='',
        alpha_2='',
        english='Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)',
        french="araméen d'empire (700-300 BCE)",
    ),
    'arg': ISOCodeData(alt='', alpha_2='an', english='Aragonese', french='aragonais'),
    'arm': ISOCodeData(alt='hye', alpha_2='hy', english='Armenian', french='arménien'),
    'arn': ISOCodeData(
        alt='',
        alpha_2='',
        english='Mapudungun; Mapuche',
        french='mapudungun; mapuche; mapuce',
    ),
    'arp': ISOCodeData(alt='', alpha_2='', english='Arapaho', french='arapaho'),
    'art': ISOCodeData(
        alt='',
        alpha_2='',
        english='Artificial languages',
        french='artificielles, langues',
    ),
    'arw': ISOCodeData(alt='', alpha_2='', english='Arawak', french='arawak'),
    'asm': ISOCodeData(alt='', alpha_2='as', english='Assamese', french='assamais'),
    'ast': ISOCodeData(
        alt='',
        alpha_2='',
        english='Asturian; Bable; Leonese; Asturleonese',
        french='asturien; bable; léonais; asturoléonais',
    ),
    'ath': ISOCodeData(
        alt='',
        alpha_2='',
        english='Athapascan languages',
        french='athapascanes, langues',
    ),
    'aus': ISOCodeData(
        alt='',
        alpha_2='',
        english='Australian languages',
        french='australiennes, langues',
    ),
    'ava': ISOCodeData(alt='', alpha_2='av', english='Avaric', french='avar'),
    'ave': ISOCodeData(alt='', alpha_2='ae', english='Avestan', french='avestique'),
    'awa': ISOCodeData(alt='', alpha_2='', english='Awadhi', french='awadhi'),
    'aym': ISOCodeData(alt='', alpha_2='ay', english='Aymara', french='aymara'),
    'aze': ISOCodeData(alt='', alpha_2='az', english='Azerbaijani', french='azéri'),
    'bad': ISOCodeData(
        alt='', alpha_2='', english='Banda languages', french='banda, langues'
    ),
    'bai': ISOCodeData(
        alt='', alpha_2='', english='Bamileke languages', french='bamiléké, langues'
    ),
    'bak': ISOCodeData(alt='', alpha_2='ba', english='Bashkir', french='bachkir'),
    'bal': ISOCodeData(alt='', alpha_2='', english='Baluchi', french='baloutchi'),
    'bam': ISOCodeData(alt='', alpha_2='bm', english='Bambara', french='bambara'),
    'ban': ISOCodeData(alt='', alpha_2='', english='Balinese', french='balinais'),
    'baq': ISOCodeData(alt='eus', alpha_2='eu', english='Basque', french='basque'),
    'bas': ISOCodeData(alt='', alpha_2='', english='Basa', french='basa'),
    'bat': ISOCodeData(
        alt='', alpha_2='', english='Baltic languages', french='baltes, langues'
    ),
    'bej': ISOCodeData(alt='', alpha_2='', english='Beja; Bedawiyet', french='bedja'),
    'bel': ISOCodeData(alt='', alpha_2='be', english='Belarusian', french='biélorusse'),
    'bem': ISOCodeData(alt='', alpha_2='', english='Bemba', french='bemba'),
    'ben': ISOCodeData(alt='', alpha_2='bn', english='Bengali', french='bengali'),
    'ber': ISOCodeData(
        alt='', alpha_2='', english='Berber languages', french='berbères, langues'
    ),
    'bho': ISOCodeData(alt='', alpha_2='', english='Bhojpuri', french='bhojpuri'),
    'bih': ISOCodeData(
        alt='', alpha_2='bh', english='Bihari languages', french='langues biharis'
    ),
    'bik': ISOCodeData(alt='', alpha_2='', english='Bikol', french='bikol'),
    'bin': ISOCodeData(alt='', alpha_2='', english='Bini; Edo', french='bini; edo'),
    'bis': ISOCodeData(alt='', alpha_2='bi', english='Bislama', french='bichlamar'),
    'bla': ISOCodeData(alt='', alpha_2='', english='Siksika', french='blackfoot'),
    'bnt': ISOCodeData(
        alt='', alpha_2='', english='Bantu languages', french='bantou, langues'
    ),
    'bos': ISOCodeData(alt='', alpha_2='bs', english='Bosnian', french='bosniaque'),
    'bra': ISOCodeData(alt='', alpha_2='', english='Braj', french='braj'),
    'bre': ISOCodeData(alt='', alpha_2='br', english='Breton', french='breton'),
    'btk': ISOCodeData(
        alt='', alpha_2='', english='Batak languages', french='batak, langues'
    ),
    'bua': ISOCodeData(alt='', alpha_2='', english='Buriat', french='bouriate'),
    'bug': ISOCodeData(alt='', alpha_2='', english='Buginese', french='bugi'),
    'bul': ISOCodeData(alt='', alpha_2='bg', english='Bulgarian', french='bulgare'),
    'bur': ISOCodeData(alt='mya', alpha_2='my', english='Burmese', french='birman'),
    'byn': ISOCodeData(alt='', alpha_2='', english='Blin; Bilin', french='blin; bilen'),
    'cad': ISOCodeData(alt='', alpha_2='', english='Caddo', french='caddo'),
    'cai': ISOCodeData(
        alt='',
        alpha_2='',
        english='Central American Indian languages',
        french="amérindiennes de L'Amérique centrale, langues",
    ),
    'car': ISOCodeData(
        alt='', alpha_2='', english='Galibi Carib', french='karib; galibi; carib'
    ),
    'cat': ISOCodeData(
        alt='', alpha_2='ca', english='Catalan; Valencian', french='catalan; valencien'
    ),
    'cau': ISOCodeData(
        alt='',
        alpha_2='',
        english='Caucasian languages',
        french='caucasiennes, langues',
    ),
    'ceb': ISOCodeData(alt='', alpha_2='', english='Cebuano', french='cebuano'),
    'cel': ISOCodeData(
        alt='',
        alpha_2='',
        english='Celtic languages',
        french='celtiques, langues; celtes, langues',
    ),
    'cha': ISOCodeData(alt='', alpha_2='ch', english='Chamorro', french='chamorro'),
    'chb': ISOCodeData(alt='', alpha_2='', english='Chibcha', french='chibcha'),
    'che': ISOCodeData(alt='', alpha_2='ce', english='Chechen', french='tchétchène'),
    'chg': ISOCodeData(alt='', alpha_2='', english='Chagatai', french='djaghataï'),
    'chi': ISOCodeData(alt='zho', alpha_2='zh', english='Chinese', french='chinois'),
    'chk': ISOCodeData(alt='', alpha_2='', english='Chuukese', french='chuuk'),
    'chm': ISOCodeData(alt='', alpha_2='', english='Mari', french='mari'),
    'chn': ISOCodeData(
        alt='', alpha_2='', english='Chinook jargon', french='chinook, jargon'
    ),
    'cho': ISOCodeData(alt='', alpha_2='', english='Choctaw', french='choctaw'),
    'chp': ISOCodeData(
        alt='', alpha_2='', english='Chipewyan; Dene Suline', french='chipewyan'
    ),
    'chr': ISOCodeData(alt='', alpha_2='', english='Cherokee', french='cherokee'),
    'chu': ISOCodeData(
        alt='',
        alpha_2='cu',
        english='Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic',
        french="slavon d'église; vieux slave; slavon liturgique; vieux bulgare",
    ),
    'chv': ISOCodeData(alt='', alpha_2='cv', english='Chuvash', french='tchouvache'),
    'chy': ISOCodeData(alt='', alpha_2='', english='Cheyenne', french='cheyenne'),
    'cmc': ISOCodeData(
        alt='', alpha_2='', english='Chamic languages', french='chames, langues'
    ),
    'cnr': ISOCodeData(alt='', alpha_2='', english='Montenegrin', french='monténégrin'),
    'cop': ISOCodeData(alt='', alpha_2='', english='Coptic', french='copte'),
    'cor': ISOCodeData(alt='', alpha_2='kw', english='Cornish', french='cornique'),
    'cos': ISOCodeData(alt='', alpha_2='co', english='Corsican', french='corse'),
    'cpe': ISOCodeData(
        alt='',
        alpha_2='',
        english='Creoles and pidgins, English based',
        french="créoles et pidgins basés sur l'anglais",
    ),
    'cpf': ISOCodeData(
        alt='',
        alpha_2='',
        english='Creoles and pidgins, French-based',
        french='créoles et pidgins basés sur le français',
    ),
    'cpp': ISOCodeData(
        alt='',
        alpha_2='',
        english='Creoles and pidgins, Portuguese-based',
        french='créoles et pidgins basés sur le portugais',
    ),
    'cre': ISOCodeData(alt='', alpha_2='cr', english='Cree', french='cree'),
    'crh': ISOCodeData(
        alt='',
        alpha_2='',
        english='Crimean Tatar; Crimean Turkish',
        french='tatar de Crimé',
    ),
    'crp': ISOCodeData(
        alt='', alpha_2='', english='Creoles and pidgins', french='créoles et pidgins'
    ),
    'csb': ISOCodeData(alt='', alpha_2='', english='Kashubian', french='kachoube'),
    'cus': ISOCodeData(
        alt='', alpha_2='', english='Cushitic languages', french='couchitiques, langues'
    ),
    'cze': ISOCodeData(alt='ces', alpha_2='cs', english='Czech', french='tchèque'),
    'dak': ISOCodeData(alt='', alpha_2='', english='Dakota', french='dakota'),
    'dan': ISOCodeData(alt='', alpha_2='da', english='Danish', french='danois'),
    'dar': ISOCodeData(alt='', alpha_2='', english='Dargwa', french='dargwa'),
    'day': ISOCodeData(
        alt='', alpha_2='', english='Land Dayak languages', french='dayak, langues'
    ),
    'del': ISOCodeData(alt='', alpha_2='', english='Delaware', french='delaware'),
    'den': ISOCodeData(
        alt='', alpha_2='', english='Slave (Athapascan)', french='esclave (athapascan)'
    ),
    'dgr': ISOCodeData(alt='', alpha_2='', english='Dogrib', french='dogrib'),
    'din': ISOCodeData(alt='', alpha_2='', english='Dinka', french='dinka'),
    'div': ISOCodeData(
        alt='', alpha_2='dv', english='Divehi; Dhivehi; Maldivian', french='maldivien'
    ),
    'doi': ISOCodeData(alt='', alpha_2='', english='Dogri', french='dogri'),
    'dra': ISOCodeData(
        alt='',
        alpha_2='',
        english='Dravidian languages',
        french='dravidiennes, langues',
    ),
    'dsb': ISOCodeData(
        alt='', alpha_2='', english='Lower Sorbian', french='bas-sorabe'
    ),
    'dua': ISOCodeData(alt='', alpha_2='', english='Duala', french='douala'),
    'dum': ISOCodeData(
        alt='',
        alpha_2='',
        english='Dutch, Middle (ca.1050-1350)',
        french='néerlandais moyen (ca. 1050-1350)',
    ),
    'dut': ISOCodeData(
        alt='nld', alpha_2='nl', english='Dutch; Flemish', french='néerlandais; flamand'
    ),
    'dyu': ISOCodeData(alt='', alpha_2='', english='Dyula', french='dioula'),
    'dzo': ISOCodeData(alt='', alpha_2='dz', english='Dzongkha', french='dzongkha'),
    'efi': ISOCodeData(alt='', alpha_2='', english='Efik', french='efik'),
    'egy': ISOCodeData(
        alt='', alpha_2='', english='Egyptian (Ancient)', french='égyptien'
    ),
    'eka': ISOCodeData(alt='', alpha_2='', english='Ekajuk', french='ekajuk'),
    'elx': ISOCodeData(alt='', alpha_2='', english='Elamite', french='élamite'),
    'eng': ISOCodeData(alt='', alpha_2='en', english='English', french='anglais'),
    'enm': ISOCodeData(
        alt='',
        alpha_2='',
        english='English, Middle (1100-1500)',
        french='anglais moyen (1100-1500)',
    ),
    'epo': ISOCodeData(alt='', alpha_2='eo', english='Esperanto', french='espéranto'),
    'est': ISOCodeData(alt='', alpha_2='et', english='Estonian', french='estonien'),
    'ewe': ISOCodeData(alt='', alpha_2='ee', english='Ewe', french='éwé'),
    'ewo': ISOCodeData(alt='', alpha_2='', english='Ewondo', french='éwondo'),
    'fan': ISOCodeData(alt='', alpha_2='', english='Fang', french='fang'),
    'fao': ISOCodeData(alt='', alpha_2='fo', english='Faroese', french='féroïen'),
    'fat': ISOCodeData(alt='', alpha_2='', english='Fanti', french='fanti'),
    'fij': ISOCodeData(alt='', alpha_2='fj', english='Fijian', french='fidjien'),
    'fil': ISOCodeData(
        alt='', alpha_2='', english='Filipino; Pilipino', french='filipino; pilipino'
    ),
    'fin': ISOCodeData(alt='', alpha_2='fi', english='Finnish', french='finnois'),
    'fiu': ISOCodeData(
        alt='',
        alpha_2='',
        english='Finno-Ugrian languages',
        french='finno-ougriennes, langues',
    ),
    'fon': ISOCodeData(alt='', alpha_2='', english='Fon', french='fon'),
    'fre': ISOCodeData(alt='fra', alpha_2='fr', english='French', french='français'),
    'frm': ISOCodeData(
        alt='',
        alpha_2='',
        english='French, Middle (ca.1400-1600)',
        french='français moyen (1400-1600)',
    ),
    'fro': ISOCodeData(
        alt='',
        alpha_2='',
        english='French, Old (842-ca.1400)',
        french='français ancien (842-ca.1400)',
    ),
    'frr': ISOCodeData(
        alt='', alpha_2='', english='Northern Frisian', french='frison septentrional'
    ),
    'frs': ISOCodeData(
        alt='', alpha_2='', english='Eastern Frisian', french='frison oriental'
    ),
    'fry': ISOCodeData(
        alt='', alpha_2='fy', english='Western Frisian', french='frison occidental'
    ),
    'ful': ISOCodeData(alt='', alpha_2='ff', english='Fulah', french='peul'),
    'fur': ISOCodeData(alt='', alpha_2='', english='Friulian', french='frioulan'),
    'gaa': ISOCodeData(alt='', alpha_2='', english='Ga', french='ga'),
    'gay': ISOCodeData(alt='', alpha_2='', english='Gayo', french='gayo'),
    'gba': ISOCodeData(alt='', alpha_2='', english='Gbaya', french='gbaya'),
    'gem': ISOCodeData(
        alt='', alpha_2='', english='Germanic languages', french='germaniques, langues'
    ),
    'geo': ISOCodeData(alt='kat', alpha_2='ka', english='Georgian', french='géorgien'),
    'ger': ISOCodeData(alt='deu', alpha_2='de', english='German', french='allemand'),
    'gez': ISOCodeData(alt='', alpha_2='', english='Geez', french='guèze'),
    'gil': ISOCodeData(alt='', alpha_2='', english='Gilbertese', french='kiribati'),
    'gla': ISOCodeData(
        alt='',
        alpha_2='gd',
        english='Gaelic; Scottish Gaelic',
        french='gaélique; gaélique écossais',
    ),
    'gle': ISOCodeData(alt='', alpha_2='ga', english='Irish', french='irlandais'),
    'glg': ISOCodeData(alt='', alpha_2='gl', english='Galician', french='galicien'),
    'glv': ISOCodeData(alt='', alpha_2='gv', english='Manx', french='manx; mannois'),
    'gmh': ISOCodeData(
        alt='',
        alpha_2='',
        english='German, Middle High (ca.1050-1500)',
        french='allemand, moyen haut (ca. 1050-1500)',
    ),
    'goh': ISOCodeData(
        alt='',
        alpha_2='',
        english='German, Old High (ca.750-1050)',
        french='allemand, vieux haut (ca. 750-1050)',
    ),
    'gon': ISOCodeData(alt='', alpha_2='', english='Gondi', french='gond'),
    'gor': ISOCodeData(alt='', alpha_2='', english='Gorontalo', french='gorontalo'),
    'got': ISOCodeData(alt='', alpha_2='', english='Gothic', french='gothique'),
    'grb': ISOCodeData(alt='', alpha_2='', english='Grebo', french='grebo'),
    'grc': ISOCodeData(
        alt='',
        alpha_2='',
        english='Greek, Ancient (to 1453)',
        french="grec ancien (jusqu'à 1453)",
    ),
    'gre': ISOCodeData(
        alt='ell',
        alpha_2='el',
        english='Greek, Modern (1453-)',
        french='grec moderne (après 1453)',
    ),
    'grn': ISOCodeData(alt='', alpha_2='gn', english='Guarani', french='guarani'),
    'gsw': ISOCodeData(
        alt='',
        alpha_2='',
        english='Swiss German; Alemannic; Alsatian',
        french='suisse alémanique; alémanique; alsacien',
    ),
    'guj': ISOCodeData(alt='', alpha_2='gu', english='Gujarati', french='goudjrati'),
    'gwi': ISOCodeData(alt='', alpha_2='', english="Gwich'in", french="gwich'in"),
    'hai': ISOCodeData(alt='', alpha_2='', english='Haida', french='haida'),
    'hat': ISOCodeData(
        alt='',
        alpha_2='ht',
        english='Haitian; Haitian Creole',
        french='haïtien; créole haïtien',
    ),
    'hau': ISOCodeData(alt='', alpha_2='ha', english='Hausa', french='haoussa'),
    'haw': ISOCodeData(alt='', alpha_2='', english='Hawaiian', french='hawaïen'),
    'heb': ISOCodeData(alt='', alpha_2='he', english='Hebrew', french='hébreu'),
    'her': ISOCodeData(alt='', alpha_2='hz', english='Herero', french='herero'),
    'hil': ISOCodeData(alt='', alpha_2='', english='Hiligaynon', french='hiligaynon'),
    'him': ISOCodeData(
        alt='',
        alpha_2='',
        english='Himachali languages; Western Pahari languages',
        french='langues himachalis; langues paharis occidentales',
    ),
    'hin': ISOCodeData(alt='', alpha_2='hi', english='Hindi', french='hindi'),
    'hit': ISOCodeData(alt='', alpha_2='', english='Hittite', french='hittite'),
    'hmn': ISOCodeData(alt='', alpha_2='', english='Hmong; Mong', french='hmong'),
    'hmo': ISOCodeData(alt='', alpha_2='ho', english='Hiri Motu', french='hiri motu'),
    'hrv': ISOCodeData(alt='', alpha_2='hr', english='Croatian', french='croate'),
    'hsb': ISOCodeData(
        alt='', alpha_2='', english='Upper Sorbian', french='haut-sorabe'
    ),
    'hun': ISOCodeData(alt='', alpha_2='hu', english='Hungarian', french='hongrois'),
    'hup': ISOCodeData(alt='', alpha_2='', english='Hupa', french='hupa'),
    'iba': ISOCodeData(alt='', alpha_2='', english='Iban', french='iban'),
    'ibo': ISOCodeData(alt='', alpha_2='ig', english='Igbo', french='igbo'),
    'ice': ISOCodeData(
        alt='isl', alpha_2='is', english='Icelandic', french='islandais'
    ),
    'ido': ISOCodeData(alt='', alpha_2='io', english='Ido', french='ido'),
    'iii': ISOCodeData(
        alt='', alpha_2='ii', english='Sichuan Yi; Nuosu', french='yi de Sichuan'
    ),
    'ijo': ISOCodeData(
        alt='', alpha_2='', english='Ijo languages', french='ijo, langues'
    ),
    'iku': ISOCodeData(alt='', alpha_2='iu', english='Inuktitut', french='inuktitut'),
    'ile': ISOCodeData(
        alt='', alpha_2='ie', english='Interlingue; Occidental', french='interlingue'
    ),
    'ilo': ISOCodeData(alt='', alpha_2='', english='Iloko', french='ilocano'),
    'ina': ISOCodeData(
        alt='',
        alpha_2='ia',
        english='Interlingua (International Auxiliary Language Association)',
        french='interlingua (langue auxiliaire internationale)',
    ),
    'inc': ISOCodeData(
        alt='', alpha_2='', english='Indic languages', french='indo-aryennes, langues'
    ),
    'ind': ISOCodeData(alt='', alpha_2='id', english='Indonesian', french='indonésien'),
    'ine': ISOCodeData(
        alt='',
        alpha_2='',
        english='Indo-European languages',
        french='indo-européennes, langues',
    ),
    'inh': ISOCodeData(alt='', alpha_2='', english='Ingush', french='ingouche'),
    'ipk': ISOCodeData(alt='', alpha_2='ik', english='Inupiaq', french='inupiaq'),
    'ira': ISOCodeData(
        alt='', alpha_2='', english='Iranian languages', french='iraniennes, langues'
    ),
    'iro': ISOCodeData(
        alt='', alpha_2='', english='Iroquoian languages', french='iroquoises, langues'
    ),
    'ita': ISOCodeData(alt='', alpha_2='it', english='Italian', french='italien'),
    'jav': ISOCodeData(alt='', alpha_2='jv', english='Javanese', french='javanais'),
    'jbo': ISOCodeData(alt='', alpha_2='', english='Lojban', french='lojban'),
    'jpn': ISOCodeData(alt='', alpha_2='ja', english='Japanese', french='japonais'),
    'jpr': ISOCodeData(
        alt='', alpha_2='', english='Judeo-Persian', french='judéo-persan'
    ),
    'jrb': ISOCodeData(
        alt='', alpha_2='', english='Judeo-Arabic', french='judéo-arabe'
    ),
    'kaa': ISOCodeData(alt='', alpha_2='', english='Kara-Kalpak', french='karakalpak'),
    'kab': ISOCodeData(alt='', alpha_2='', english='Kabyle', french='kabyle'),
    'kac': ISOCodeData(
        alt='', alpha_2='', english='Kachin; Jingpho', french='kachin; jingpho'
    ),
    'kal': ISOCodeData(
        alt='', alpha_2='kl', english='Kalaallisut; Greenlandic', french='groenlandais'
    ),
    'kam': ISOCodeData(alt='', alpha_2='', english='Kamba', french='kamba'),
    'kan': ISOCodeData(alt='', alpha_2='kn', english='Kannada', french='kannada'),
    'kar': ISOCodeData(
        alt='', alpha_2='', english='Karen languages', french='karen, langues'
    ),
    'kas': ISOCodeData(alt='', alpha_2='ks', english='Kashmiri', french='kashmiri'),
    'kau': ISOCodeData(alt='', alpha_2='kr', english='Kanuri', french='kanouri'),
    'kaw': ISOCodeData(alt='', alpha_2='', english='Kawi', french='kawi'),
    'kaz': ISOCodeData(alt='', alpha_2='kk', english='Kazakh', french='kazakh'),
    'kbd': ISOCodeData(alt='', alpha_2='', english='Kabardian', french='kabardien'),
    'kha': ISOCodeData(alt='', alpha_2='', english='Khasi', french='khasi'),
    'khi': ISOCodeData(
        alt='', alpha_2='', english='Khoisan languages', french='khoïsan, langues'
    ),
    'khm': ISOCodeData(
        alt='', alpha_2='km', english='Central Khmer', french='khmer central'
    ),
    'kho': ISOCodeData(
        alt='', alpha_2='', english='Khotanese; Sakan', french='khotanais; sakan'
    ),
    'kik': ISOCodeData(alt='', alpha_2='ki', english='Kikuyu; Gikuyu', french='kikuyu'),
    'kin': ISOCodeData(alt='', alpha_2='rw', english='Kinyarwanda', french='rwanda'),
    'kir': ISOCodeData(
        alt='', alpha_2='ky', english='Kirghiz; Kyrgyz', french='kirghiz'
    ),
    'kmb': ISOCodeData(alt='', alpha_2='', english='Kimbundu', french='kimbundu'),
    'kok': ISOCodeData(alt='', alpha_2='', english='Konkani', french='konkani'),
    'kom': ISOCodeData(alt='', alpha_2='kv', english='Komi', french='kom'),
    'kon': ISOCodeData(alt='', alpha_2='kg', english='Kongo', french='kongo'),
    'kor': ISOCodeData(alt='', alpha_2='ko', english='Korean', french='coréen'),
    'kos': ISOCodeData(alt='', alpha_2='', english='Kosraean', french='kosrae'),
    'kpe': ISOCodeData(alt='', alpha_2='', english='Kpelle', french='kpellé'),
    'krc': ISOCodeData(
        alt='', alpha_2='', english='Karachay-Balkar', french='karatchai balkar'
    ),
    'krl': ISOCodeData(alt='', alpha_2='', english='Karelian', french='carélien'),
    'kro': ISOCodeData(
        alt='', alpha_2='', english='Kru languages', french='krou, langues'
    ),
    'kru': ISOCodeData(alt='', alpha_2='', english='Kurukh', french='kurukh'),
    'kua': ISOCodeData(
        alt='', alpha_2='kj', english='Kuanyama; Kwanyama', french='kuanyama; kwanyama'
    ),
    'kum': ISOCodeData(alt='', alpha_2='', english='Kumyk', french='koumyk'),
    'kur': ISOCodeData(alt='', alpha_2='ku', english='Kurdish', french='kurde'),
    'kut': ISOCodeData(alt='', alpha_2='', english='Kutenai', french='kutenai'),
    'lad': ISOCodeData(alt='', alpha_2='', english='Ladino', french='judéo-espagnol'),
    'lah': ISOCodeData(alt='', alpha_2='', english='Lahnda', french='lahnda'),
    'lam': ISOCodeData(alt='', alpha_2='', english='Lamba', french='lamba'),
    'lao': ISOCodeData(alt='', alpha_2='lo', english='Lao', french='lao'),
    'lat': ISOCodeData(alt='', alpha_2='la', english='Latin', french='latin'),
    'lav': ISOCodeData(alt='', alpha_2='lv', english='Latvian', french='letton'),
    'lez': ISOCodeData(alt='', alpha_2='', english='Lezghian', french='lezghien'),
    'lim': ISOCodeData(
        alt='',
        alpha_2='li',
        english='Limburgan; Limburger; Limburgish',
        french='limbourgeois',
    ),
    'lin': ISOCodeData(alt='', alpha_2='ln', english='Lingala', french='lingala'),
    'lit': ISOCodeData(alt='', alpha_2='lt', english='Lithuanian', french='lituanien'),
    'lol': ISOCodeData(alt='', alpha_2='', english='Mongo', french='mongo'),
    'loz': ISOCodeData(alt='', alpha_2='', english='Lozi', french='lozi'),
    'ltz': ISOCodeData(
        alt='',
        alpha_2='lb',
        english='Luxembourgish; Letzeburgesch',
        french='luxembourgeois',
    ),
    'lua': ISOCodeData(alt='', alpha_2='', english='Luba-Lulua', french='luba-lulua'),
    'lub': ISOCodeData(
        alt='', alpha_2='lu', english='Luba-Katanga', french='luba-katanga'
    ),
    'lug': ISOCodeData(alt='', alpha_2='lg', english='Ganda', french='ganda'),
    'lui': ISOCodeData(alt='', alpha_2='', english='Luiseno', french='luiseno'),
    'lun': ISOCodeData(alt='', alpha_2='', english='Lunda', french='lunda'),
    'luo': ISOCodeData(
        alt='',
        alpha_2='',
        english='Luo (Kenya and Tanzania)',
        french='luo (Kenya et Tanzanie)',
    ),
    'lus': ISOCodeData(alt='', alpha_2='', english='Lushai', french='lushai'),
    'mac': ISOCodeData(
        alt='mkd', alpha_2='mk', english='Macedonian', french='macédonien'
    ),
    'mad': ISOCodeData(alt='', alpha_2='', english='Madurese', french='madourais'),
    'mag': ISOCodeData(alt='', alpha_2='', english='Magahi', french='magahi'),
    'mah': ISOCodeData(alt='', alpha_2='mh', english='Marshallese', french='marshall'),
    'mai': ISOCodeData(alt='', alpha_2='', english='Maithili', french='maithili'),
    'mak': ISOCodeData(alt='', alpha_2='', english='Makasar', french='makassar'),
    'mal': ISOCodeData(alt='', alpha_2='ml', english='Malayalam', french='malayalam'),
    'man': ISOCodeData(alt='', alpha_2='', english='Mandingo', french='mandingue'),
    'mao': ISOCodeData(alt='mri', alpha_2='mi', english='Maori', french='maori'),
    'map': ISOCodeData(
        alt='',
        alpha_2='',
        english='Austronesian languages',
        french='austronésiennes, langues',
    ),
    'mar': ISOCodeData(alt='', alpha_2='mr', english='Marathi', french='marathe'),
    'mas': ISOCodeData(alt='', alpha_2='', english='Masai', french='massaï'),
    'may': ISOCodeData(alt='msa', alpha_2='ms', english='Malay', french='malais'),
    'mdf': ISOCodeData(alt='', alpha_2='', english='Moksha', french='moksa'),
    'mdr': ISOCodeData(alt='', alpha_2='', english='Mandar', french='mandar'),
    'men': ISOCodeData(alt='', alpha_2='', english='Mende', french='mendé'),
    'mga': ISOCodeData(
        alt='',
        alpha_2='',
        english='Irish, Middle (900-1200)',
        french='irlandais moyen (900-1200)',
    ),
    'mic': ISOCodeData(
        alt='', alpha_2='', english="Mi'kmaq; Micmac", french="mi'kmaq; micmac"
    ),
    'min': ISOCodeData(alt='', alpha_2='', english='Minangkabau', french='minangkabau'),
    'mis': ISOCodeData(
        alt='', alpha_2='', english='Uncoded languages', french='langues non codées'
    ),
    'mkh': ISOCodeData(
        alt='', alpha_2='', english='Mon-Khmer languages', french='môn-khmer, langues'
    ),
    'mlg': ISOCodeData(alt='', alpha_2='mg', english='Malagasy', french='malgache'),
    'mlt': ISOCodeData(alt='', alpha_2='mt', english='Maltese', french='maltais'),
    'mnc': ISOCodeData(alt='', alpha_2='', english='Manchu', french='mandchou'),
    'mni': ISOCodeData(alt='', alpha_2='', english='Manipuri', french='manipuri'),
    'mno': ISOCodeData(
        alt='', alpha_2='', english='Manobo languages', french='manobo, langues'
    ),
    'moh': ISOCodeData(alt='', alpha_2='', english='Mohawk', french='mohawk'),
    'mon': ISOCodeData(alt='', alpha_2='mn', english='Mongolian', french='mongol'),
    'mos': ISOCodeData(alt='', alpha_2='', english='Mossi', french='moré'),
    'mul': ISOCodeData(
        alt='', alpha_2='', english='Multiple languages', french='multilingue'
    ),
    'mun': ISOCodeData(
        alt='', alpha_2='', english='Munda languages', french='mounda, langues'
    ),
    'mus': ISOCodeData(alt='', alpha_2='', english='Creek', french='muskogee'),
    'mwl': ISOCodeData(alt='', alpha_2='', english='Mirandese', french='mirandais'),
    'mwr': ISOCodeData(alt='', alpha_2='', english='Marwari', french='marvari'),
    'myn': ISOCodeData(
        alt='', alpha_2='', english='Mayan languages', french='maya, langues'
    ),
    'myv': ISOCodeData(alt='', alpha_2='', english='Erzya', french='erza'),
    'nah': ISOCodeData(
        alt='', alpha_2='', english='Nahuatl languages', french='nahuatl, langues'
    ),
    'nai': ISOCodeData(
        alt='',
        alpha_2='',
        english='North American Indian languages',
        french='nord-amérindiennes, langues',
    ),
    'nap': ISOCodeData(alt='', alpha_2='', english='Neapolitan', french='napolitain'),
    'nau': ISOCodeData(alt='', alpha_2='na', english='Nauru', french='nauruan'),
    'nav': ISOCodeData(alt='', alpha_2='nv', english='Navajo; Navaho', french='navaho'),
    'nbl': ISOCodeData(
        alt='',
        alpha_2='nr',
        english='Ndebele, South; South Ndebele',
        french='ndébélé du Sud',
    ),
    'nde': ISOCodeData(
        alt='',
        alpha_2='nd',
        english='Ndebele, North; North Ndebele',
        french='ndébélé du Nord',
    ),
    'ndo': ISOCodeData(alt='', alpha_2='ng', english='Ndonga', french='ndonga'),
    'nds': ISOCodeData(
        alt='',
        alpha_2='',
        english='Low German; Low Saxon; German, Low; Saxon, Low',
        french='bas allemand; bas saxon; allemand, bas; saxon, bas',
    ),
    'nep': ISOCodeData(alt='', alpha_2='ne', english='Nepali', french='népalais'),
    'new': ISOCodeData(
        alt='', alpha_2='', english='Nepal Bhasa; Newari', french='nepal bhasa; newari'
    ),
    'nia': ISOCodeData(alt='', alpha_2='', english='Nias', french='nias'),
    'nic': ISOCodeData(
        alt='',
        alpha_2='',
        english='Niger-Kordofanian languages',
        french='nigéro-kordofaniennes, langues',
    ),
    'niu': ISOCodeData(alt='', alpha_2='', english='Niuean', french='niué'),
    'nno': ISOCodeData(
        alt='',
        alpha_2='nn',
        english='Norwegian Nynorsk; Nynorsk, Norwegian',
        french='norvégien nynorsk; nynorsk, norvégien',
    ),
    'nob': ISOCodeData(
        alt='',
        alpha_2='nb',
        english='Bokmål, Norwegian; Norwegian Bokmål',
        french='norvégien bokmål',
    ),
    'nog': ISOCodeData(alt='', alpha_2='', english='Nogai', french='nogaï; nogay'),
    'non': ISOCodeData(
        alt='', alpha_2='', english='Norse, Old', french='norrois, vieux'
    ),
    'nor': ISOCodeData(alt='', alpha_2='no', english='Norwegian', french='norvégien'),
    'nqo': ISOCodeData(alt='', alpha_2='', english="N'Ko", french="n'ko"),
    'nso': ISOCodeData(
        alt='',
        alpha_2='',
        english='Pedi; Sepedi; Northern Sotho',
        french='pedi; sepedi; sotho du Nord',
    ),
    'nub': ISOCodeData(
        alt='', alpha_2='', english='Nubian languages', french='nubiennes, langues'
    ),
    'nwc': ISOCodeData(
        alt='',
        alpha_2='',
        english='Classical Newari; Old Newari; Classical Nepal Bhasa',
        french='newari classique',
    ),
    'nya': ISOCodeData(
        alt='',
        alpha_2='ny',
        english='Chichewa; Chewa; Nyanja',
        french='chichewa; chewa; nyanja',
    ),
    'nym': ISOCodeData(alt='', alpha_2='', english='Nyamwezi', french='nyamwezi'),
    'nyn': ISOCodeData(alt='', alpha_2='', english='Nyankole', french='nyankolé'),
    'nyo': ISOCodeData(alt='', alpha_2='', english='Nyoro', french='nyoro'),
    'nzi': ISOCodeData(alt='', alpha_2='', english='Nzima', french='nzema'),
    'oci': ISOCodeData(
        alt='',
        alpha_2='oc',
        english='Occitan (post 1500)',
        french='occitan (après 1500)',
    ),
    'oji': ISOCodeData(alt='', alpha_2='oj', english='Ojibwa', french='ojibwa'),
    'ori': ISOCodeData(alt='', alpha_2='or', english='Oriya', french='oriya'),
    'orm': ISOCodeData(alt='', alpha_2='om', english='Oromo', french='galla'),
    'osa': ISOCodeData(alt='', alpha_2='', english='Osage', french='osage'),
    'oss': ISOCodeData(
        alt='', alpha_2='os', english='Ossetian; Ossetic', french='ossète'
    ),
    'ota': ISOCodeData(
        alt='',
        alpha_2='',
        english='Turkish, Ottoman (1500-1928)',
        french='turc ottoman (1500-1928)',
    ),
    'oto': ISOCodeData(
        alt='', alpha_2='', english='Otomian languages', french='otomi, langues'
    ),
    'paa': ISOCodeData(
        alt='', alpha_2='', english='Papuan languages', french='papoues, langues'
    ),
    'pag': ISOCodeData(alt='', alpha_2='', english='Pangasinan', french='pangasinan'),
    'pal': ISOCodeData(alt='', alpha_2='', english='Pahlavi', french='pahlavi'),
    'pam': ISOCodeData(
        alt='', alpha_2='', english='Pampanga; Kapampangan', french='pampangan'
    ),
    'pan': ISOCodeData(
        alt='', alpha_2='pa', english='Panjabi; Punjabi', french='pendjabi'
    ),
    'pap': ISOCodeData(alt='', alpha_2='', english='Papiamento', french='papiamento'),
    'pau': ISOCodeData(alt='', alpha_2='', english='Palauan', french='palau'),
    'peo': ISOCodeData(
        alt='',
        alpha_2='',
        english='Persian, Old (ca.600-400 B.C.)',
        french='perse, vieux (ca. 600-400 av. J.-C.)',
    ),
    'per': ISOCodeData(alt='fas', alpha_2='fa', english='Persian', french='persan'),
    'phi': ISOCodeData(
        alt='',
        alpha_2='',
        english='Philippine languages',
        french='philippines, langues',
    ),
    'phn': ISOCodeData(alt='', alpha_2='', english='Phoenician', french='phénicien'),
    'pli': ISOCodeData(alt='', alpha_2='pi', english='Pali', french='pali'),
    'pol': ISOCodeData(alt='', alpha_2='pl', english='Polish', french='polonais'),
    'pon': ISOCodeData(alt='', alpha_2='', english='Pohnpeian', french='pohnpei'),
    'por': ISOCodeData(alt='', alpha_2='pt', english='Portuguese', french='portugais'),
    'pra': ISOCodeData(
        alt='', alpha_2='', english='Prakrit languages', french='prâkrit, langues'
    ),
    'pro': ISOCodeData(
        alt='',
        alpha_2='',
        english='Provençal, Old (to 1500); Occitan, Old (to 1500)',
        french="provençal ancien (jusqu'à 1500); occitan ancien (jusqu'à 1500)",
    ),
    'pus': ISOCodeData(alt='', alpha_2='ps', english='Pushto; Pashto', french='pachto'),
    'qaa': ISOCodeData(
        alt='',
        alpha_2='',
        english='Reserved for local use',
        french="réservée à l'usage local",
    ),
    'que': ISOCodeData(alt='', alpha_2='qu', english='Quechua', french='quechua'),
    'raj': ISOCodeData(alt='', alpha_2='', english='Rajasthani', french='rajasthani'),
    'rap': ISOCodeData(alt='', alpha_2='', english='Rapanui', french='rapanui'),
    'rar': ISOCodeData(
        alt='',
        alpha_2='',
        english='Rarotongan; Cook Islands Maori',
        french='rarotonga; maori des îles Cook',
    ),
    'roa': ISOCodeData(
        alt='', alpha_2='', english='Romance languages', french='romanes, langues'
    ),
    'roh': ISOCodeData(alt='', alpha_2='rm', english='Romansh', french='romanche'),
    'rom': ISOCodeData(alt='', alpha_2='', english='Romany', french='tsigane'),
    'rum': ISOCodeData(
        alt='ron',
        alpha_2='ro',
        english='Romanian; Moldavian; Moldovan',
        french='roumain; moldave',
    ),
    'run': ISOCodeData(alt='', alpha_2='rn', english='Rundi', french='rundi'),
    'rup': ISOCodeData(
        alt='',
        alpha_2='',
        english='Aromanian; Arumanian; Macedo-Romanian',
        french='aroumain; macédo-roumain',
    ),
    'rus': ISOCodeData(alt='', alpha_2='ru', english='Russian', french='russe'),
    'sad': ISOCodeData(alt='', alpha_2='', english='Sandawe', french='sandawe'),
    'sag': ISOCodeData(alt='', alpha_2='sg', english='Sango', french='sango'),
    'sah': ISOCodeData(alt='', alpha_2='', english='Yakut', french='iakoute'),
    'sai': ISOCodeData(
        alt='',
        alpha_2='',
        english='South American Indian languages',
        french='sud-amérindiennes, langues',
    ),
    'sal': ISOCodeData(
        alt='', alpha_2='', english='Salishan languages', french='salishennes, langues'
    ),
    'sam': ISOCodeData(
        alt='', alpha_2='', english='Samaritan Aramaic', french='samaritain'
    ),
    'san': ISOCodeData(alt='', alpha_2='sa', english='Sanskrit', french='sanskrit'),
    'sas': ISOCodeData(alt='', alpha_2='', english='Sasak', french='sasak'),
    'sat': ISOCodeData(alt='', alpha_2='', english='Santali', french='santal'),
    'scn': ISOCodeData(alt='', alpha_2='', english='Sicilian', french='sicilien'),
    'sco': ISOCodeData(alt='', alpha_2='', english='Scots', french='écossais'),
    'sel': ISOCodeData(alt='', alpha_2='', english='Selkup', french='selkoupe'),
    'sem': ISOCodeData(
        alt='', alpha_2='', english='Semitic languages', french='sémitiques, langues'
    ),
    'sga': ISOCodeData(
        alt='',
        alpha_2='',
        english='Irish, Old (to 900)',
        french="irlandais ancien (jusqu'à 900)",
    ),
    'sgn': ISOCodeData(
        alt='', alpha_2='', english='Sign Languages', french='langues des signes'
    ),
    'shn': ISOCodeData(alt='', alpha_2='', english='Shan', french='chan'),
    'sid': ISOCodeData(alt='', alpha_2='', english='Sidamo', french='sidamo'),
    'sin': ISOCodeData(
        alt='', alpha_2='si', english='Sinhala; Sinhalese', french='singhalais'
    ),
    'sio': ISOCodeData(
        alt='', alpha_2='', english='Siouan languages', french='sioux, langues'
    ),
    'sit': ISOCodeData(
        alt='',
        alpha_2='',
        english='Sino-Tibetan languages',
        french='sino-tibétaines, langues',
    ),
    'sla': ISOCodeData(
        alt='', alpha_2='', english='Slavic languages', french='slaves, langues'
    ),
    'slo': ISOCodeData(alt='slk', alpha_2='sk', english='Slovak', french='slovaque'),
    'slv': ISOCodeData(alt='', alpha_2='sl', english='Slovenian', french='slovène'),
    'sma': ISOCodeData(
        alt='', alpha_2='', english='Southern Sami', french='sami du Sud'
    ),
    'sme': ISOCodeData(
        alt='', alpha_2='se', english='Northern Sami', french='sami du Nord'
    ),
    'smi': ISOCodeData(
        alt='', alpha_2='', english='Sami languages', french='sames, langues'
    ),
    'smj': ISOCodeData(alt='', alpha_2='', english='Lule Sami', french='sami de Lule'),
    'smn': ISOCodeData(alt='', alpha_2='', english='Inari Sami', french="sami d'Inari"),
    'smo': ISOCodeData(alt='', alpha_2='sm', english='Samoan', french='samoan'),
    'sms': ISOCodeData(alt='', alpha_2='', english='Skolt Sami', french='sami skolt'),
    'sna': ISOCodeData(alt='', alpha_2='sn', english='Shona', french='shona'),
    'snd': ISOCodeData(alt='', alpha_2='sd', english='Sindhi', french='sindhi'),
    'snk': ISOCodeData(alt='', alpha_2='', english='Soninke', french='soninké'),
    'sog': ISOCodeData(alt='', alpha_2='', english='Sogdian', french='sogdien'),
    'som': ISOCodeData(alt='', alpha_2='so', english='Somali', french='somali'),
    'son': ISOCodeData(
        alt='', alpha_2='', english='Songhai languages', french='songhai, langues'
    ),
    'sot': ISOCodeData(
        alt='', alpha_2='st', english='Sotho, Southern', french='sotho du Sud'
    ),
    'spa': ISOCodeData(
        alt='', alpha_2='es', english='Spanish; Castilian', french='espagnol; castillan'
    ),
    'srd': ISOCodeData(alt='', alpha_2='sc', english='Sardinian', french='sarde'),
    'srn': ISOCodeData(
        alt='', alpha_2='', english='Sranan Tongo', french='sranan tongo'
    ),
    'srp': ISOCodeData(alt='', alpha_2='sr', english='Serbian', french='serbe'),
    'srr': ISOCodeData(alt='', alpha_2='', english='Serer', french='sérère'),
    'ssa': ISOCodeData(
        alt='',
        alpha_2='',
        english='Nilo-Saharan languages',
        french='nilo-sahariennes, langues',
    ),
    'ssw': ISOCodeData(alt='', alpha_2='ss', english='Swati', french='swati'),
    'suk': ISOCodeData(alt='', alpha_2='', english='Sukuma', french='sukuma'),
    'sun': ISOCodeData(alt='', alpha_2='su', english='Sundanese', french='soundanais'),
    'sus': ISOCodeData(alt='', alpha_2='', english='Susu', french='soussou'),
    'sux': ISOCodeData(alt='', alpha_2='', english='Sumerian', french='sumérien'),
    'swa': ISOCodeData(alt='', alpha_2='sw', english='Swahili', french='swahili'),
    'swe': ISOCodeData(alt='', alpha_2='sv', english='Swedish', french='suédois'),
    'syc': ISOCodeData(
        alt='', alpha_2='', english='Classical Syriac', french='syriaque classique'
    ),
    'syr': ISOCodeData(alt='', alpha_2='', english='Syriac', french='syriaque'),
    'tah': ISOCodeData(alt='', alpha_2='ty', english='Tahitian', french='tahitien'),
    'tai': ISOCodeData(
        alt='', alpha_2='', english='Tai languages', french='tai, langues'
    ),
    'tam': ISOCodeData(alt='', alpha_2='ta', english='Tamil', french='tamoul'),
    'tat': ISOCodeData(alt='', alpha_2='tt', english='Tatar', french='tatar'),
    'tel': ISOCodeData(alt='', alpha_2='te', english='Telugu', french='télougou'),
    'tem': ISOCodeData(alt='', alpha_2='', english='Timne', french='temne'),
    'ter': ISOCodeData(alt='', alpha_2='', english='Tereno', french='tereno'),
    'tet': ISOCodeData(alt='', alpha_2='', english='Tetum', french='tetum'),
    'tgk': ISOCodeData(alt='', alpha_2='tg', english='Tajik', french='tadjik'),
    'tgl': ISOCodeData(alt='', alpha_2='tl', english='Tagalog', french='tagalog'),
    'tha': ISOCodeData(alt='', alpha_2='th', english='Thai', french='thaï'),
    'tib': ISOCodeData(alt='bod', alpha_2='bo', english='Tibetan', french='tibétain'),
    'tig': ISOCodeData(alt='', alpha_2='', english='Tigre', french='tigré'),
    'tir': ISOCodeData(alt='', alpha_2='ti', english='Tigrinya', french='tigrigna'),
    'tiv': ISOCodeData(alt='', alpha_2='', english='Tiv', french='tiv'),
    'tkl': ISOCodeData(alt='', alpha_2='', english='Tokelau', french='tokelau'),
    'tlh': ISOCodeData(
        alt='', alpha_2='', english='Klingon; tlhIngan-Hol', french='klingon'
    ),
    'tli': ISOCodeData(alt='', alpha_2='', english='Tlingit', french='tlingit'),
    'tmh': ISOCodeData(alt='', alpha_2='', english='Tamashek', french='tamacheq'),
    'tog': ISOCodeData(
        alt='', alpha_2='', english='Tonga (Nyasa)', french='tonga (Nyasa)'
    ),
    'ton': ISOCodeData(
        alt='',
        alpha_2='to',
        english='Tonga (Tonga Islands)',
        french='tongan (Îles Tonga)',
    ),
    'tpi': ISOCodeData(alt='', alpha_2='', english='Tok Pisin', french='tok pisin'),
    'tsi': ISOCodeData(alt='', alpha_2='', english='Tsimshian', french='tsimshian'),
    'tsn': ISOCodeData(alt='', alpha_2='tn', english='Tswana', french='tswana'),
    'tso': ISOCodeData(alt='', alpha_2='ts', english='Tsonga', french='tsonga'),
    'tuk': ISOCodeData(alt='', alpha_2='tk', english='Turkmen', french='turkmène'),
    'tum': ISOCodeData(alt='', alpha_2='', english='Tumbuka', french='tumbuka'),
    'tup': ISOCodeData(
        alt='', alpha_2='', english='Tupi languages', french='tupi, langues'
    ),
    'tur': ISOCodeData(alt='', alpha_2='tr', english='Turkish', french='turc'),
    'tut': ISOCodeData(
        alt='', alpha_2='', english='Altaic languages', french='altaïques, langues'
    ),
    'tvl': ISOCodeData(alt='', alpha_2='', english='Tuvalu', french='tuvalu'),
    'twi': ISOCodeData(alt='', alpha_2='tw', english='Twi', french='twi'),
    'tyv': ISOCodeData(alt='', alpha_2='', english='Tuvinian', french='touva'),
    'udm': ISOCodeData(alt='', alpha_2='', english='Udmurt', french='oudmourte'),
    'uga': ISOCodeData(alt='', alpha_2='', english='Ugaritic', french='ougaritique'),
    'uig': ISOCodeData(
        alt='', alpha_2='ug', english='Uighur; Uyghur', french='ouïgour'
    ),
    'ukr': ISOCodeData(alt='', alpha_2='uk', english='Ukrainian', french='ukrainien'),
    'umb': ISOCodeData(alt='', alpha_2='', english='Umbundu', french='umbundu'),
    'und': ISOCodeData(
        alt='', alpha_2='', english='Undetermined', french='indéterminée'
    ),
    'urd': ISOCodeData(alt='', alpha_2='ur', english='Urdu', french='ourdou'),
    'uzb': ISOCodeData(alt='', alpha_2='uz', english='Uzbek', french='ouszbek'),
    'vai': ISOCodeData(alt='', alpha_2='', english='Vai', french='vaï'),
    'ven': ISOCodeData(alt='', alpha_2='ve', english='Venda', french='venda'),
    'vie': ISOCodeData(alt='', alpha_2='vi', english='Vietnamese', french='vietnamien'),
    'vol': ISOCodeData(alt='', alpha_2='vo', english='Volapük', french='volapük'),
    'vot': ISOCodeData(alt='', alpha_2='', english='Votic', french='vote'),
    'wak': ISOCodeData(
        alt='', alpha_2='', english='Wakashan languages', french='wakashanes, langues'
    ),
    'wal': ISOCodeData(
        alt='', alpha_2='', english='Wolaitta; Wolaytta', french='wolaitta; wolaytta'
    ),
    'war': ISOCodeData(alt='', alpha_2='', english='Waray', french='waray'),
    'was': ISOCodeData(alt='', alpha_2='', english='Washo', french='washo'),
    'wel': ISOCodeData(alt='cym', alpha_2='cy', english='Welsh', french='gallois'),
    'wen': ISOCodeData(
        alt='', alpha_2='', english='Sorbian languages', french='sorabes, langues'
    ),
    'wln': ISOCodeData(alt='', alpha_2='wa', english='Walloon', french='wallon'),
    'wol': ISOCodeData(alt='', alpha_2='wo', english='Wolof', french='wolof'),
    'xal': ISOCodeData(
        alt='', alpha_2='', english='Kalmyk; Oirat', french='kalmouk; oïrat'
    ),
    'xho': ISOCodeData(alt='', alpha_2='xh', english='Xhosa', french='xhosa'),
    'yao': ISOCodeData(alt='', alpha_2='', english='Yao', french='yao'),
    'yap': ISOCodeData(alt='', alpha_2='', english='Yapese', french='yapois'),
    'yid': ISOCodeData(alt='', alpha_2='yi', english='Yiddish', french='yiddish'),
    'yor': ISOCodeData(alt='', alpha_2='yo', english='Yoruba', french='yoruba'),
    'ypk': ISOCodeData(
        alt='', alpha_2='', english='Yupik languages', french='yupik, langues'
    ),
    'zap': ISOCodeData(alt='', alpha_2='', english='Zapotec', french='zapotèque'),
    'zbl': ISOCodeData(
        alt='',
        alpha_2='',
        english='Blissymbols; Blissymbolics; Bliss',
        french='symboles Bliss; Bliss',
    ),
    'zen': ISOCodeData(alt='', alpha_2='', english='Zenaga', french='zenaga'),
    'zgh': ISOCodeData(
        alt='',
        alpha_2='',
        english='Standard Moroccan Tamazight',
        french='amazighe standard marocain',
    ),
    'zha': ISOCodeData(
        alt='', alpha_2='za', english='Zhuang; Chuang', french='zhuang; chuang'
    ),
    'znd': ISOCodeData(
        alt='', alpha_2='', english='Zande languages', french='zandé, langues'
    ),
    'zul': ISOCodeData(alt='', alpha_2='zu', english='Zulu', french='zoulou'),
    'zun': ISOCodeData(alt='', alpha_2='', english='Zuni', french='zuni'),
    'zxx': ISOCodeData(
        alt='',
        alpha_2='',
        english='No linguistic content; Not applicable',
        french='pas de contenu linguistique; non applicable',
    ),
    'zza': ISOCodeData(
        alt='',
        alpha_2='',
        english='Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki',
        french='zaza; dimili; dimli; kirdki; kirmanjki; zazaki',
    ),
}


def iso_639_2_from_3(iso3: str) -> str:
    """Convert ISO 639-3 code to ISO 639-2 code."""
    if iso3 in ISO_639_3:
        return ISO_639_3[iso3].alpha_2
    else:
        return ""
