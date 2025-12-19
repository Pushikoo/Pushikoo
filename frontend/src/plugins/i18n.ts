import { createI18n } from "vue-i18n";
import en from "@/locales/en.json";
import zh from "@/locales/zh.json";
import ja from "@/locales/ja.json";

export type MessageSchema = typeof en;

// Detect browser language and map to supported locales
const getBrowserLanguage = (): "en" | "zh" | "ja" => {
  const browserLang = navigator.language.toLowerCase();
  if (browserLang.startsWith("zh")) return "zh";
  if (browserLang.startsWith("ja")) return "ja";
  return "en"; // fallback to English
};

const i18n = createI18n<[MessageSchema], "en" | "zh" | "ja">({
  legacy: false,
  locale: localStorage.getItem("locale") || getBrowserLanguage(),
  fallbackLocale: "en",
  messages: {
    en,
    zh,
    ja,
  },
});

export default i18n;
