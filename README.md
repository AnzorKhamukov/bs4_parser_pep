# Проект парсинг PEP
## Описание
 Этот парсер помогает быть в курсе новостей в мире Python. Он выполняет четыре функции:

- собирает ссылки на статьи о нововведениях в Python, переходит по ним и забирает информацию об авторах и редакторах статей;
- собирает информацию о статусах версий Python;
- скачивает архив с актуальной документацией;
- собирает данные о документах PEP, считает их количество в каждом статусе и общее количество PEP и сравнивает статусы на главной   странице со статусами в отдельной карточке PEP.
- Парсер работает в разных режимах через аргументы командной строки. В него включено логирование и обработка ошибок.
## Запуск на Macbook
```html
 git clone git@github.com:anzorkhamukov/bs4_parser_pep.git
 cd bs4_parser_pep
 python3 -m venv env
 source venv/bin/activate
 python3 -m pip install --upgrade pip
 pip3 install -r requirements.txt
 cd scr
 python3 main.py whats-new [-ключ аргумент]
 python3 main.py latest-versions [-ключ аргумент]
 python3 main.py download [-ключ аргумент]
 python main.py pep [-ключ аргумент]
```
## Аргументы
Справка о режимах работы парсера и синтаксисе:
```html
-h, --help
```
Очистка кеша перед выполнением парсинга:
```html
-c, --clear-cache
```
Дополнительные способы вывода данных (для всех режимов работы, кроме download):
```html
-o {pretty,file}, --output {pretty,file}
```
