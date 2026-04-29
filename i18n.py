
import os
import json
import Domoticz

class I18n:
    def __init__(self, language='en'):
        self.language = language
        self.translations = {}
        self.load_language(language)

    def load_language(self, language):
        base_dir = os.path.dirname(__file__)
        lang_file = os.path.join(base_dir, 'lang', f'{language}.json')

        if not os.path.exists(lang_file):
            # Fallback to English
            lang_file = os.path.join(base_dir, 'lang', 'en.json')

        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            except Exception as e:
                try:
                    Domoticz.Error(f"Error loading language file {lang_file}: {e}")
                except:
                    pass

    def t(self, key, **kwargs):
        text = self.translations.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

# Global instance
_i18n = I18n('en')

def set_language(language):
    _i18n.load_language(language)

def _(key, **kwargs):
    return _i18n.t(key, **kwargs)
