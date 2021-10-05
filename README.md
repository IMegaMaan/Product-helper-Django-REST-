### Первый запуск проекта
#### Для локального запуска проекта выполнить команды:
- `sudo docker-compose up -d --build`
- `sudo docker-compose exec backend python manage.py migrate --noinput` - применение миграций 
- `sudo ocker-compose exec backend python manage.py collectstatic --no-input` - сбор статики


#### Для запуска проекта на сервере через github action необходимо сделать `push` на ветку `master`:


### Документация и админ-панель
#### Документация находится по ссылке. Здесь же Вы найдете примеры использования api:
`http://localhost/docs/`
#### Админ-панель доступна по адресу:
`http://localhos/admin/` 
#### Сам проект доступен по адресу
`http://localhos/`

#### При первом запуске БД можно наполнить фикстурами(при необходимости)
Находятся в data:
- data/dump_ingredients.json;
- data/dump_tags.json;
- Загрузка осуществляется при необходимости командой `python manage.py loaddata <path_to_json>`

![example workflow](https://github.com/IMegaMaan/foodgram-project-react/actions/workflows/main.yml/badge.svg)

