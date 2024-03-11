# Платформа yatube

Yatube — это платформа для публикаций, блог с регистрацией пользователей.

### Пользователи могут: 
1. Подписываться на любимых авторов
2. Оставлять комментарии к постам
3. Публиковать собственные посты

Проект покрыт Unit-тестами

### Стек:
1. Django==2.2.16
2. pytest==6.2.4
3. pytest-django==4.4.0
4. pytest-pythonpath==0.7.3

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:OlegPrizov/hw05_final.git
cd hw05_final
```

Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
source env/bin/activate
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

Выполнить миграции:
```
python3 manage.py migrate
```

Запустить проект:
```
cd yatube
python3 manage.py runserver
```

### Автор 
[Олег Призов](https://github.com/OlegPrizov) 
dockerhub_username: olegprizov
