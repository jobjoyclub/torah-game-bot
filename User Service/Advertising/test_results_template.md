# Шаблон результатов тестирования агента

## Структура Excel файла (.xlsx)

### Колонки таблицы:

| Колонка | Описание | Пример | Обязательно |
|---------|----------|---------|-------------|
| **Organization** | Полное официальное название организации | "Congregation Beth Israel" | ✅ |
| **Email** | Основной контактный email | "info@bethisrael.org" | ✅ |
| **Additional Email** | Дополнительный email (если есть) | "education@bethisrael.org" | ❌ |
| **Website** | URL официального сайта | "https://www.bethisrael.org" | ✅ |
| **Type** | Тип организации | "Religious Community" | ✅ |
| **City** | Город расположения | "New York" | ✅ |
| **Country** | Страна | "United States" | ✅ |
| **Language** | Предпочитаемый язык | "English" | ✅ |
| **Source** | Источник информации | "Official Website" | ✅ |
| **Last Verified** | Дата последней проверки | "2024-12-15" | ✅ |
| **Notes** | Примечания | "Active community, responds quickly" | ❌ |

### Примеры заполненных строк:

#### Пример 1: Религиозная община
```
Organization: "Temple Emanu-El"
Email: "info@templeemanuel.org"
Additional Email: "rabbi@templeemanuel.org"
Website: "https://www.templeemanuel.org"
Type: "Religious Community"
City: "San Francisco"
Country: "United States"
Language: "English"
Source: "Official Website"
Last Verified: "2024-12-15"
Notes: "Large Reform congregation, active in education"
```

#### Пример 2: Образовательное учреждение
```
Organization: "Jewish Community School of Berlin"
Email: "contact@jcs-berlin.de"
Additional Email: "admissions@jcs-berlin.de"
Website: "https://www.jcs-berlin.de"
Type: "Educational Institution"
City: "Berlin"
Country: "Germany"
Language: "German"
Source: "Social Media (Facebook)"
Last Verified: "2024-12-15"
Notes: "K-12 school, bilingual program"
```

#### Пример 3: Культурный центр
```
Organization: "Centre Communautaire Juif de Paris"
Email: "accueil@ccjp.fr"
Additional Email: "culture@ccjp.fr"
Website: "https://www.ccjp.fr"
Type: "Cultural Center"
City: "Paris"
Country: "France"
Language: "French"
Source: "Directory (European Jewish Congress)"
Last Verified: "2024-12-15"
Notes: "Major cultural center, hosts events"
```

#### Пример 4: Молодежная организация
```
Organization: "Hillel at University of Toronto"
Email: "info@hillelontario.org"
Additional Email: "programs@hillelontario.org"
Website: "https://www.hillelontario.org"
Type: "Youth Organization"
City: "Toronto"
Country: "Canada"
Language: "English"
Source: "Official Website"
Last Verified: "2024-12-15"
Notes: "Student organization, very active"
```

## Категории типов организаций:

### Приоритет 1 (Высший)
- **Religious Community** - Религиозные общины и синагоги
- **Educational Institution** - Образовательные учреждения

### Приоритет 2 (Высокий)
- **Cultural Center** - Культурные центры и музеи
- **Youth Organization** - Молодежные и студенческие организации

### Приоритет 3 (Средний)
- **Charity Foundation** - Благотворительные фонды
- **Social Services** - Социальные службы
- **Memorial Organization** - Исторические и мемориальные организации

### Приоритет 4 (Низкий)
- **Business Association** - Бизнес-ассоциации
- **Professional Union** - Профессиональные объединения
- **Sports Club** - Спортивные клубы
- **Leisure Club** - Досуговые клубы

## Источники информации:

### Официальные источники
- **Official Website** - Официальный сайт организации
- **Government Registry** - Государственный реестр
- **NGO Directory** - Справочник НКО

### Социальные сети
- **Facebook** - Страница в Facebook
- **Instagram** - Профиль в Instagram
- **LinkedIn** - Страница в LinkedIn
- **Twitter/X** - Профиль в Twitter/X

### Директории и базы данных
- **World Jewish Congress** - Всемирный еврейский конгресс
- **European Jewish Congress** - Европейский еврейский конгресс
- **JDC Directory** - Справочник JDC
- **Local Directory** - Местный справочник

## Языки коммуникации:

- **English** - Английский
- **Hebrew** - Иврит
- **Russian** - Русский
- **Spanish** - Испанский
- **French** - Французский
- **German** - Немецкий
- **Italian** - Итальянский
- **Portuguese** - Португальский
- **Arabic** - Арабский
- **Other** - Другой (указать в Notes)

## Критерии качества данных:

### ✅ Обязательные поля
- Organization (не пустое)
- Email (валидный формат)
- Website (рабочая ссылка)
- Type (из списка категорий)
- City (не пустое)
- Country (не пустое)
- Language (из списка языков)
- Source (из списка источников)
- Last Verified (дата в формате YYYY-MM-DD)

### ✅ Валидация email
- Проверка формата email
- Проверка домена
- Отметка о предпочтении веб-форм

### ✅ Валидация веб-сайта
- Проверка доступности сайта
- Проверка актуальности информации
- Отметка о неактивных сайтах

---

**Использование**: Этот шаблон поможет агенту структурировать результаты поиска и обеспечить единообразие данных.
