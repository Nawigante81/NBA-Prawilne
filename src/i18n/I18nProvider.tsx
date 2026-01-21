import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { I18nContext, I18nContextValue, TFunction } from './context';
import { Language, SUPPORTED_LANGUAGES, translations } from './translations';

const STORAGE_KEY = 'app.language';


const interpolate = (template: string, vars?: Record<string, string | number>) => {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    const value = vars[key];
    return value === undefined || value === null ? match : String(value);
  });
};

const detectDefaultLanguage = (): Language => {
  const navLang = typeof navigator !== 'undefined' ? navigator.language : '';
  return navLang.toLowerCase().startsWith('pl') ? 'pl' : 'en';
};

export const I18nProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'pl' || stored === 'en') return stored;
    } catch {
      // ignore
    }
    return detectDefaultLanguage();
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, language);
    } catch {
      // ignore
    }

    // Keep document language in sync for a11y/formatting.
    if (typeof document !== 'undefined') {
      document.documentElement.lang = language;
    }
  }, [language]);

  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next);
  }, []);

  const t: TFunction = useCallback(
    (key, vars) => {
      const dict = translations[language];
      const fallback = translations.en;
      const raw = dict[key] ?? fallback[key] ?? key;
      return interpolate(raw, vars);
    },
    [language]
  );

  const value: I18nContextValue = useMemo(
    () => ({
      language,
      setLanguage,
      locale: language === 'pl' ? 'pl-PL' : 'en-US',
      t,
      supportedLanguages: SUPPORTED_LANGUAGES,
    }),
    [language, setLanguage, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

