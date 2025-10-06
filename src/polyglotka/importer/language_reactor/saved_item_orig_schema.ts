// Source: https://www.languagereactor.com/help/export#json

export type savedItem_EXPORT_t = savedWord_EXPORT_t | savedPhrase_EXPORT_t;


interface savedWord_EXPORT_t {

   itemType: 'WORD';

   langCode_G: string;

   context: {

       wordIndex: number;

       phrase: phrase_EXPORT_t;

   } | null;

   tags: string[];

   learningStage: 'LEARNING' | 'KNOWN' | 'SKIPPED'

   wordTranslationsArr: string[] | null;

   translationLangCode_G: string;


   wordType: 'lemma' | 'form';


   word: {

       text: string;

       translit?: string; // currently only Korean, Thai, Japanese (kana)

       pinyin?: string[];

       tones?: number[];

   };


   timeModified_ms: number;

   audio: itemAudio_EXPORT_t | null;

   freqRank: number | null;

}


interface savedPhrase_EXPORT_t {

   itemType: 'PHRASE';

   langCode_G: string;

   translationLangCode_G: string;

   tags: string[];

   learningStage: 'LEARNING' | 'KNOWN' | 'SKIPPED'

   context: {

       phrase: phrase_EXPORT_t;

   };

   timeModified_ms: number;

   audio: itemAudio_EXPORT_t | null;

   freqRank: number | null;

}


export interface phrase_EXPORT_t {

   subtitleTokens: {

       0: Array<ud_single_EXPORT_t> | null;

       1: Array<ud_single_EXPORT_t>;

       2: Array<ud_single_EXPORT_t> | null;

   };

   subtitles: {

       0: string | null;

       1: string;

       2: string | null;

   };

   mTranslations: {

       0: string | null;

       1: string;

       2: string | null;

   } | null;

   hTranslations: {

       0: string | null;

       1: string;

       2: string | null;

   } | null;

   reference:

       | NF_reference_EXPORT_t

       | YT_reference_EXPORT_t

       | TEXT_reference_EXPORT_t

       | VIDEO_FILE_reference_EXPORT_t

       | DICTIONARY_reference_EXPORT_t;

   thumb_prev: thumbImage_EXPORT_t | null;

   thumb_next: thumbImage_EXPORT_t | null;

}


interface ud_single_EXPORT_t {

   form: {

       text: string;

       translit?: string; // currently only Korean, Thai, Japanese (kana)

       pinyin?: string[];

       tones?: number[];

       // hash?: string;

   };

   pos: // 17 Universal POS tags:

   | 'ADJ'

       | 'ADP'

       | 'ADV'

       | 'AUX'

       | 'NOUN'

       | 'PROPN'

       | 'VERB'

       | 'DET'

       | 'SYM'

       | 'INTJ'

       | 'CCONJ'

       | 'PUNCT'

       | 'X'

       | 'NUM'

       | 'PART'

       | 'PRON'

       | 'SCONJ'

       // Unknown text, either UDPipe returned nothing

       // for this token, or simpleNLP identified it as

       // not whitespace and not punctuation:

       | '_'

       // Whitespace:

       | 'WS';

   index?: number;

   lemma?: {

       text: string;

       translit?: string; // currently only Korean, Thai, Japanese (kana)

       pinyin?: string[];

       tones?: number[];

       // hash: string;

   };

   xpos?: string;

   features?: any;

   pointer?: number;

   deprel?: string;

   freq?: number;

}


export interface YT_reference_EXPORT_t {

   source: 'YOUTUBE';

   channelId: string | null;

   ownerChannelName: string | null;

   langCode_YT: string; // Youtube langauge code

   langCode_G: string | null; // not always available

   title: string | null; // not always available

   movieId: string;

   subtitleIndex: number;

   numSubs: number;

   startTime_ms: number | null; // not available for older items

   endTime_ms: number | null; // not available for older items

}


export interface NF_reference_EXPORT_t {

   source: 'NETFLIX';

   movieId: string;

   langCode_N: string;

   langCode_G: string | null;

   title: string | null;

   subtitleIndex: number;

   numSubs: number;

   startTime_ms: number | null;

   endTime_ms: number | null;

}


type TEXT_reference_EXPORT_t = {

   source: 'TEXT';

   movieId: null; // null if unsaved text, or text id if saved.

   title: string | null;

   tm: {

       langCode_G: langCode_G_t;

   };

   url: string | null;

};


type VIDEO_FILE_reference_EXPORT_t = {

   source: 'VIDEO_FILE';

   movieId: string; // subs md5, used for querying

   title: string; // file name, used for querying

   subtitleIndex: number;

   numSubs: number;

   startTime_ms: number;

   endTime_ms: number;

   tm: {

       langCode_G: langCode_G_t;

       subsFileName: string;

   };

};


type DICTIONARY_reference_EXPORT_t = {

   source: 'DICTIONARY';

   tm: {

       langCode_G: langCode_G_t;

   };

   // title, movieId probably won't be used, but make TS checks more simple

   title: string | null;

   movieId: string | null;

};


export interface thumbImage_EXPORT_t {

   height: number;

   width: number;

   time: number;

   dataURL: string;

}


export interface itemAudio_EXPORT_t {

   source: 'microsoft' | 'google' | 'movie';

   voice: string | null;

   outputFormat: string; // e.g. 'Audio24Khz48KBitRateMonoMp3'

   dateCreated: number; // unix timestamp

   dataURL: string;

}