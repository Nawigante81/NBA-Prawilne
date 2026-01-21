import { createContext } from 'react';

import { Language, SUPPORTED_LANGUAGES } from './translations';

export type TFunction = (key: string, vars?: Record<string, string | number>) => string;

export type I18nContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  locale: string;
  t: TFunction;
  supportedLanguages: typeof SUPPORTED_LANGUAGES;
};

export const I18nContext = createContext<I18nContextValue | null>(null);
