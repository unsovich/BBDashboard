# Настройка Supabase для АНО «Синяя птица» Dashboard

## Зачем нужен Supabase?

Streamlit Cloud использует **ephemeral filesystem** - все локальные файлы (`.pkl`, `.json`) удаляются при каждом перезапуске или деплое приложения. Supabase решает эту проблему, предоставляя облачное хранилище PostgreSQL.

## Шаг 1: Создание проекта в Supabase

1. Перейдите на [supabase.com](https://supabase.com)
2. Зарегистрируйтесь или войдите в аккаунт
3. Нажмите **"New Project"**
4. Заполните поля:
   - **Name**: `bb-dashboard` (или любое другое имя)
   - **Database Password**: создайте надежный пароль (сохраните его!)
   - **Region**: выберите ближайший регион (например, `Europe (Frankfurt)`)
5. Нажмите **"Create new project"**
6. Дождитесь создания проекта (1-2 минуты)

## Шаг 2: Получение credentials

1. В панели Supabase перейдите в **Settings** → **API**
2. Скопируйте два значения:
   - **Project URL** (например, `https://abcdefgh.supabase.co`)
   - **anon public** ключ (в разделе Project API keys)

## Шаг 3: Выполнение SQL скрипта

1. В панели Supabase перейдите в **SQL Editor**
2. Нажмите **"New Query"**
3. Откройте файл `supabase_setup.sql` из проекта
4. Скопируйте весь SQL код и вставьте в редактор
5. Нажмите **"Run"** (или Ctrl+Enter)
6. Убедитесь, что все команды выполнились успешно
7. Проверьте создание таблиц в разделе **Table Editor**

Должны быть созданы таблицы:
- `kpi_history`
- `campaign_groups`
- `campaigns`
- `collection_history`
- `program_financials`

## Шаг 4: Локальная разработка

### Установка зависимостей

```bash
pip install supabase python-dotenv
```

### Создание .env файла

1. Скопируйте файл `.env.example` в `.env`:
   ```bash
   cp .env.example .env
   ```

2. Откройте `.env` и вставьте ваши credentials:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-public-key
   USE_LOCAL_STORAGE=false
   ```

3. **Важно**: Убедитесь, что `.env` добавлен в `.gitignore` (уже должен быть)

### Тестирование подключения

Запустите приложение локально:
```bash
streamlit run main.py
```

В консоли должно появиться сообщение:
```
✅ Successfully connected to Supabase
```

## Шаг 5: Миграция существующих данных

Если у вас уже есть данные в локальных файлах (`.pkl`, `.json`), выполните миграцию:

```bash
python migrate_to_supabase.py
```

Скрипт:
1. Прочитает все локальные файлы
2. Загрузит данные в Supabase
3. Создаст резервные копии локальных файлов
4. Покажет отчет о миграции

## Шаг 6: Настройка Streamlit Cloud

1. Перейдите в настройки вашего приложения на [share.streamlit.io](https://share.streamlit.io)
2. Откройте **Settings** → **Secrets**
3. Добавьте следующие секреты:

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
USE_LOCAL_STORAGE = false
```

4. Сохраните изменения
5. Приложение автоматически перезапустится

## Шаг 7: Верификация

После деплоя на Streamlit Cloud:

1. Откройте приложение
2. Проверьте, что данные загружаются
3. Добавьте новый KPI или кампанию
4. Перезапустите приложение (Settings → Reboot)
5. Убедитесь, что данные сохранились

## Режимы работы

### Режим Supabase (Production)
```
USE_LOCAL_STORAGE=false
```
- Все данные хранятся в облаке
- Данные персистентны между перезапусками
- Требует подключения к интернету

### Локальный режим (Development)
```
USE_LOCAL_STORAGE=true
```
- Данные хранятся в `.pkl` и `.json` файлах
- Полезно для разработки и тестирования
- Не требует подключения к Supabase

## Структура базы данных

### kpi_history
Хранит историю всех KPI показателей
- `date_start` - дата начала периода
- `category` - категория KPI (например, "SMM (Вовлеченность)")
- `kpi_id` - уникальный идентификатор KPI
- `actual` - фактическое значение
- `target` - целевое значение

### campaigns
Данные фандрайзинговых кампаний
- `campaign_id` - уникальный ID кампании
- `group_id` - ID группы (для мультиканальности)
- `channel` - канал (VK, Telegram, Email, Website)
- `collected_amount` - собранная сумма

### collection_history
История обновлений сборов
- `campaign_id` - ссылка на кампанию
- `amount_added` - добавленная сумма
- `total_after_update` - общая сумма после обновления

### program_financials
Финансовые показатели программ
- `program` - название программы
- `year`, `month` - период
- `income` - доходы
- `expenses` - расходы

## Troubleshooting

### Ошибка: "Supabase library not installed"
```bash
pip install supabase
```

### Ошибка: "Failed to connect to Supabase"
- Проверьте корректность `SUPABASE_URL` и `SUPABASE_KEY`
- Убедитесь, что проект Supabase активен
- Проверьте подключение к интернету

### Данные не сохраняются
- Убедитесь, что `USE_LOCAL_STORAGE=false`
- Проверьте логи в Supabase Dashboard → Logs
- Убедитесь, что RLS политики настроены правильно

### Медленная работа
- Проверьте количество записей в таблицах
- Убедитесь, что индексы созданы (из `supabase_setup.sql`)
- Рассмотрите возможность архивирования старых данных

## Безопасность

> ⚠️ **ВАЖНО**: Никогда не коммитьте файл `.env` в Git!

> 🔒 **RLS Policies**: Текущие политики Row Level Security разрешают все операции для упрощения. В production рекомендуется настроить более строгие политики доступа.

## Monitoring

### Просмотр данных
1. **Supabase Dashboard** → **Table Editor**
2. Выберите таблицу для просмотра данных

### Статистика
Выполните в SQL Editor:
```sql
SELECT * FROM get_table_stats();
```

Покажет количество записей в каждой таблице.

## Backup

Supabase автоматически создает резервные копии. Для ручного экспорта:

1. **Database** → **Backups**
2. Настройте расписание автоматических бэкапов (доступно в платных планах)

Для критичных данных рекомендуется периодически экспортировать данные:
```bash
python export_data.py  # создайте этот скрипт при необходимости
```

## Поддержка

При возникновении проблем:
1. Проверьте логи Supabase: Dashboard → Logs
2. Проверьте логи Streamlit Cloud
3. Обратитесь к [документации Supabase](https://supabase.com/docs)
