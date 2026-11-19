"""Interface translations: English, Russian, Ukrainian and German."""

from __future__ import annotations

import os

LANGUAGES = {"en": "English", "ru": "Русский", "uk": "Українська", "de": "Deutsch"}
# "auto" follows the system language; the rest are fixed choices.
LANGUAGE_CHOICES = ["auto", "en", "ru", "uk", "de"]

STRINGS: dict[str, dict[str, str]] = {
    "add_folder": {
        "en": "Add music folder",
        "ru": "Добавить папку с музыкой",
        "uk": "Додати теку з музикою",
        "de": "Musikordner hinzufügen",
    },
    "search_library": {
        "en": "Search your library",
        "ru": "Поиск в библиотеке",
        "uk": "Пошук у бібліотеці",
        "de": "Bibliothek durchsuchen",
    },
    "search_jamendo": {
        "en": "Search Jamendo, then press Enter",
        "ru": "Поиск на Jamendo, затем Enter",
        "uk": "Пошук на Jamendo, потім Enter",
        "de": "Jamendo durchsuchen, dann Enter drücken",
    },
    "jamendo_tooltip": {
        "en": "Search Jamendo online (type, then press Enter)",
        "ru": "Поиск на Jamendo (введите и нажмите Enter)",
        "uk": "Пошук на Jamendo (введіть і натисніть Enter)",
        "de": "Jamendo online durchsuchen (eingeben, dann Enter)",
    },
    "settings_tooltip": {
        "en": "Settings (Ctrl+,)",
        "ru": "Настройки (Ctrl+,)",
        "uk": "Налаштування (Ctrl+,)",
        "de": "Einstellungen (Strg+,)",
    },
    "profile_default": {
        "en": "Profile",
        "ru": "Профиль",
        "uk": "Профіль",
        "de": "Profil",
    },
    "mini_tooltip": {
        "en": "Mini player (Ctrl+M)",
        "ru": "Мини-плеер (Ctrl+M)",
        "uk": "Міні-програвач (Ctrl+M)",
        "de": "Mini-Player (Strg+M)",
    },
    "nothing_playing": {
        "en": "Nothing playing",
        "ru": "Ничего не играет",
        "uk": "Нічого не відтворюється",
        "de": "Nichts wird abgespielt",
    },
    "start_hint": {
        "en": "Add a music folder or search Jamendo to begin",
        "ru": "Добавьте папку с музыкой или найдите музыку на Jamendo",
        "uk": "Додайте теку з музикою або знайдіть музику на Jamendo",
        "de": "Füge einen Musikordner hinzu oder suche bei Jamendo",
    },
    "prev_tooltip": {
        "en": "Previous (Ctrl+Left)",
        "ru": "Предыдущий (Ctrl+←)",
        "uk": "Попередній (Ctrl+←)",
        "de": "Zurück (Strg+Links)",
    },
    "next_tooltip": {
        "en": "Next (Ctrl+Right)",
        "ru": "Следующий (Ctrl+→)",
        "uk": "Наступний (Ctrl+→)",
        "de": "Weiter (Strg+Rechts)",
    },
    "play_pause": {
        "en": "Play / Pause",
        "ru": "Воспроизведение / пауза",
        "uk": "Відтворення / пауза",
        "de": "Wiedergabe / Pause",
    },
    "equalizer": {
        "en": "Equalizer",
        "ru": "Эквалайзер",
        "uk": "Еквалайзер",
        "de": "Equalizer",
    },
    "add_to_library": {
        "en": "Add to library",
        "ru": "Добавить в библиотеку",
        "uk": "Додати до бібліотеки",
        "de": "Zur Bibliothek hinzufügen",
    },
    "in_library": {
        "en": "In library",
        "ru": "В библиотеке",
        "uk": "У бібліотеці",
        "de": "In der Bibliothek",
    },
    "type_something": {
        "en": "Type something to search for",
        "ru": "Введите, что искать",
        "uk": "Введіть, що шукати",
        "de": "Gib einen Suchbegriff ein",
    },
    "need_client_id": {
        "en": "Add your Jamendo client ID in Settings",
        "ru": "Добавьте Client ID Jamendo в настройках",
        "uk": "Додайте Client ID Jamendo у налаштуваннях",
        "de": "Füge deine Jamendo-Client-ID in den Einstellungen hinzu",
    },
    "searching": {
        "en": "Searching Jamendo…",
        "ru": "Поиск на Jamendo…",
        "uk": "Пошук на Jamendo…",
        "de": "Suche bei Jamendo…",
    },
    "search_failed": {
        "en": "Jamendo search failed: {error}",
        "ru": "Ошибка поиска на Jamendo: {error}",
        "uk": "Помилка пошуку на Jamendo: {error}",
        "de": "Jamendo-Suche fehlgeschlagen: {error}",
    },
    "results_count": {
        "en": "{count} results from Jamendo",
        "ru": "Результатов на Jamendo: {count}",
        "uk": "Результатів на Jamendo: {count}",
        "de": "{count} Ergebnisse von Jamendo",
    },
    "choose_folder_title": {
        "en": "Choose your music folder",
        "ru": "Выберите папку с музыкой",
        "uk": "Оберіть теку з музикою",
        "de": "Wähle deinen Musikordner",
    },
    "scanning": {
        "en": "Scanning library…",
        "ru": "Сканирование библиотеки…",
        "uk": "Сканування бібліотеки…",
        "de": "Bibliothek wird durchsucht…",
    },
    "tracks_loaded": {
        "en": "{count} tracks loaded",
        "ru": "Загружено треков: {count}",
        "uk": "Завантажено треків: {count}",
        "de": "{count} Titel geladen",
    },
    "added_to_library": {
        "en": "Added {title} to your library",
        "ru": "{title} добавлен в библиотеку",
        "uk": "{title} додано до бібліотеки",
        "de": "{title} wurde zur Bibliothek hinzugefügt",
    },
    "playback_error": {
        "en": "Playback error: {message}",
        "ru": "Ошибка воспроизведения: {message}",
        "uk": "Помилка відтворення: {message}",
        "de": "Wiedergabefehler: {message}",
    },
    "update_available": {
        "en": "Liquid Glass {version} is available",
        "ru": "Доступна Liquid Glass {version}",
        "uk": "Доступна Liquid Glass {version}",
        "de": "Liquid Glass {version} ist verfügbar",
    },
    "update_button": {
        "en": "Update",
        "ru": "Обновить",
        "uk": "Оновити",
        "de": "Aktualisieren",
    },
    "no_terminal": {
        "en": "No terminal found. Run liquid-glass-update in a terminal.",
        "ru": "Терминал не найден. Запустите liquid-glass-update в терминале.",
        "uk": "Термінал не знайдено. Запустіть liquid-glass-update у терміналі.",
        "de": "Kein Terminal gefunden. Führe liquid-glass-update in einem Terminal aus.",
    },
    "settings_title": {
        "en": "Settings",
        "ru": "Настройки",
        "uk": "Налаштування",
        "de": "Einstellungen",
    },
    "profile_group": {
        "en": "Profile",
        "ru": "Профиль",
        "uk": "Профіль",
        "de": "Profil",
    },
    "profile_desc": {
        "en": "Stored only on this computer.",
        "ru": "Хранится только на этом компьютере.",
        "uk": "Зберігається лише на цьому комп'ютері.",
        "de": "Wird nur auf diesem Computer gespeichert.",
    },
    "icon_row": {
        "en": "Icon",
        "ru": "Значок",
        "uk": "Значок",
        "de": "Symbol",
    },
    "icon_sub": {
        "en": "Choose an image from your files",
        "ru": "Выберите изображение из файлов",
        "uk": "Оберіть зображення з файлів",
        "de": "Wähle ein Bild aus deinen Dateien",
    },
    "change": {
        "en": "Change",
        "ru": "Изменить",
        "uk": "Змінити",
        "de": "Ändern",
    },
    "remove_icon": {
        "en": "Remove icon",
        "ru": "Удалить значок",
        "uk": "Видалити значок",
        "de": "Symbol entfernen",
    },
    "username": {
        "en": "Username",
        "ru": "Имя пользователя",
        "uk": "Ім'я користувача",
        "de": "Benutzername",
    },
    "display_name": {
        "en": "Display name",
        "ru": "Отображаемое имя",
        "uk": "Відображуване ім'я",
        "de": "Anzeigename",
    },
    "choose_icon_title": {
        "en": "Choose an icon",
        "ru": "Выберите значок",
        "uk": "Оберіть значок",
        "de": "Wähle ein Symbol",
    },
    "images_filter": {
        "en": "Images",
        "ru": "Изображения",
        "uk": "Зображення",
        "de": "Bilder",
    },
    "invalid_image": {
        "en": "Choose a PNG, JPG or WebP image",
        "ru": "Выберите изображение PNG, JPG или WebP",
        "uk": "Оберіть зображення PNG, JPG або WebP",
        "de": "Wähle ein PNG-, JPG- oder WebP-Bild",
    },
    "appearance_group": {
        "en": "Appearance",
        "ru": "Оформление",
        "uk": "Оформлення",
        "de": "Darstellung",
    },
    "theme_row": {
        "en": "Theme",
        "ru": "Тема",
        "uk": "Тема",
        "de": "Design",
    },
    "theme_sub": {
        "en": "Liquid Glass is the default look",
        "ru": "Liquid Glass — тема по умолчанию",
        "uk": "Liquid Glass — тема за замовчуванням",
        "de": "Liquid Glass ist das Standarddesign",
    },
    "theme_liquid_glass": {
        "en": "Liquid Glass",
        "ru": "Liquid Glass",
        "uk": "Liquid Glass",
        "de": "Liquid Glass",
    },
    "theme_plain": {
        "en": "Plain dark",
        "ru": "Простая тёмная",
        "uk": "Проста темна",
        "de": "Schlicht dunkel",
    },
    "language_row": {
        "en": "Language",
        "ru": "Язык",
        "uk": "Мова",
        "de": "Sprache",
    },
    "language_sub": {
        "en": "Restart the app to apply",
        "ru": "Перезапустите приложение, чтобы применить",
        "uk": "Перезапустіть застосунок, щоб застосувати",
        "de": "Starte die App neu, um die Änderung zu übernehmen",
    },
    "language_auto": {
        "en": "Automatic",
        "ru": "Автоматически",
        "uk": "Автоматично",
        "de": "Automatisch",
    },
    "language_restart": {
        "en": "Restart Liquid Glass to apply the language",
        "ru": "Перезапустите Liquid Glass, чтобы применить язык",
        "uk": "Перезапустіть Liquid Glass, щоб застосувати мову",
        "de": "Starte Liquid Glass neu, um die Sprache zu übernehmen",
    },
    "jamendo_group": {
        "en": "Jamendo",
        "ru": "Jamendo",
        "uk": "Jamendo",
        "de": "Jamendo",
    },
    "jamendo_desc": {
        "en": "Client ID from the Jamendo developer portal, used for online search.",
        "ru": "Client ID из портала разработчиков Jamendo, нужен для поиска онлайн.",
        "uk": "Client ID з порталу розробників Jamendo, потрібен для пошуку онлайн.",
        "de": "Client-ID aus dem Jamendo-Entwicklerportal, für die Online-Suche.",
    },
    "client_id": {
        "en": "Client ID",
        "ru": "Client ID",
        "uk": "Client ID",
        "de": "Client-ID",
    },
    "client_saved": {
        "en": "Jamendo client ID saved",
        "ru": "Client ID Jamendo сохранён",
        "uk": "Client ID Jamendo збережено",
        "de": "Jamendo-Client-ID gespeichert",
    },
    "client_removed": {
        "en": "Jamendo client ID removed",
        "ru": "Client ID Jamendo удалён",
        "uk": "Client ID Jamendo видалено",
        "de": "Jamendo-Client-ID entfernt",
    },
    "library_group": {
        "en": "Library",
        "ru": "Библиотека",
        "uk": "Бібліотека",
        "de": "Bibliothek",
    },
    "music_folder": {
        "en": "Music folder",
        "ru": "Папка с музыкой",
        "uk": "Тека з музикою",
        "de": "Musikordner",
    },
    "not_set": {
        "en": "Not set",
        "ru": "Не задана",
        "uk": "Не вказано",
        "de": "Nicht festgelegt",
    },
    "choose_button": {
        "en": "Choose",
        "ru": "Выбрать",
        "uk": "Вибрати",
        "de": "Auswählen",
    },
}

_active = "en"


def resolve_language(setting: str) -> str:
    """Turn a setting ('auto' or a language code) into a supported language code."""
    if setting in LANGUAGES:
        return setting
    raw = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
    code = raw.split("_")[0].split(".")[0].lower()
    return code if code in LANGUAGES else "en"


def set_language(setting: str) -> None:
    global _active
    _active = resolve_language(setting)


def t(key: str, **values) -> str:
    entry = STRINGS[key]
    text = entry.get(_active) or entry["en"]
    return text.format(**values) if values else text
