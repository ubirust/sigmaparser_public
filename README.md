# Sigmaparser – Парсер недвижимости в реальном времени

[sigmaparser.ru](https://sigmaparser.ru/) – парсер недвижимости в реальном времени. Данный парсер мониторит новейшие объявления на Авито и Циан.

Стоит отметить, что парсер может мониторить и другие категории, например: автомобили, ноутбуки, телефоны и т.д.

Я целенаправленно сузил аудиторию ЦА, чтобы было легче продавать данный продукт и разрабатывать рекламные материалы.

## Основные особенности
Одной из самых сложных задач при разработке этого парсера было создание многопоточного мониторинга для каждого пользователя, а также многопоточный обход блокировок. 

Полный код проекта я не выкладываю, так как его разработка заняла у меня полгода, а еще полгода ушло на исправление ошибок и продвижение.
![contributions](https://github.com/ubirust/sigmaparser_public/blob/main/images/contributions.jpg)
*Моя активность в закрытых репозиториях*

Эти усилия оправдались: продукт стал прибыльным. Теперь я получаю уведомления о новых оплатах, даже когда сплю.

![orders](https://github.com/ubirust/sigmaparser_public/blob/main/images/orders.jpg)
*Уведомления об оплатах на почте*

Здесь я подробно объясню, как функционирует данный парсер и какие технологии применяются для обхода различных блокировок

Также расскажу:
1.	Почему я выбрал многопоточность, а не асинхронные запросы через aiohttp.
2.	Как сэкономить на прокси.
3.	Какие есть виды блокировок на Авито и как их можно обойти.
4.	На чем работает сам бот в Телеграм.
5.	Как автоматически генерировать API-ссылку для парсинга.
6.	Почему я выбрал Wordpress для лендинга и как связал Wordpress, Личный кабинет и Телеграм-бота на одном сервере.
7.	Как работает система выдачи ключей на подписку.

## Почему я выбрал многопоточность, а не асинхронные запросы через aiohttp
Я тестировал различные способы парсинга: многопоточность, асинхронные запросы и мультипроцессинг. Асинхронные запросы через aiohttp пришлось исключить, так как они часто блокировались, что делало парсинг невозможным. В итоге я остановился на использовании обычных HTTP-запросов (requests).

У каждого пользователя создается два новых потока: один для Авито, другой для Циан. Такая архитектура позволяет не мешать запросам других пользователей.

## Как сэкономить на прокси
Сначала я использовал статические IPv4 прокси из-за их дешевизны. Однако такие прокси быстро блокировались, особенно при большом количестве пользователей.

Все проверено за вас, можете не терять время на статику, а сразу брать мобильные прокси. 
Да, они дорогие, но в них есть авторотация ip.

<img src="https://github.com/ubirust/sigmaparser_public/blob/main/images/proxy.jpg" alt="ip1" width="800">
<p><em>Мобильная прокси ферма</em>

Также мобильные прокси априори редко банятся, так как один адрес у мобильного оператора обслуживает до микрорайона.

Таким образом, чтобы система стабильно работало, я подключил несколько мобильных прокси с авторотацией ip.

В идеале для каждого пользователя иметь свои мобильные прокси, но по экономическим причинам не могу это позволить, так как вся прибыль продукта ушла бы только на прокси.

Возможно, нужно внедрить в личном кабинете окошко, где пользователь мог бы вставить свои прокси.

## Виды блокировок на Авито и их обход
Основные виды блокировок:

1. Доступ ограничен: проблема с IP.
<img src="https://github.com/ubirust/sigmaparser_public/blob/main/images/ip1.png" alt="ip1" width="800"/>

2. Что-то пошло не так.
<img src="https://github.com/ubirust/sigmaparser_public/blob/main/images/wh.png" alt="ip2" width="800"/>

3. Доступ ограничен: проблема с IP (версия 2).
<img src="https://github.com/ubirust/sigmaparser_public/blob/main/images/ip2.png" alt="ip2" width="800"/>

Тут стоит отметить, что такие ошибки могут возникнуть даже тогда, когда вы используете чистые ip. Это я к тому, что простая ротация прокси вам не поможет.

Авито также отслеживает сам запрос и что в нем содержится, я сейчас имею ввиду: headers, cookies

Для того, чтобы обойти блок, вам нужно сгенерировать уникальные куки, это делается через Selenium.

### Алгоритм обхода блокировки по IP

1. **Использование свежих прокси:**
   Алгоритм начинается с выбора чистых прокси-серверов, которые ранее нигде не использовались. 
   Это гарантирует, что данные IP-адреса не заблокированы целевым сайтом.

2. **Запрос через Selenium:**
   Используя выбранные прокси, алгоритм инициирует запрос через браузер, контролируемый Selenium. 
   Это позволяет эмулировать действия реального пользователя и повысить шансы обхода блокировок.

3. **Автоматическое отслеживание Fetch-запросов:**
   Программа отслеживает все Fetch-запросы в Network панели браузера, фиксируя и анализируя их в реальном времени.

4. **Извлечение чистых куков:**
   Из отслеживаемых Fetch-запросов алгоритм извлекает чистые куки, которые ранее не использовались для парсинга. 
   Эти куки запоминаются и сохраняются.

5. **Вставка куков в основной поток:**
   Извлеченные чистые куки интегрируются в основной поток парсинга, что позволяет обойти блокировку по IP.

6. **Автоматическое срабатывание при блокировке:**
   Алгоритм автоматически запускается при обнаружении блокировки по IP, обеспечивая бесперебойный процесс парсинга.

Вам остается просто написать этот алгоритм, который срабатывает при каждом блоке по ip 😉

## Как автоматически генерировать API-ссылку для парсинга

Для того, чтобы АВТОМАТИЧЕСКИ сгенерировать api ссылку (это ссылка нужно для парсинга, сам пользователь не поймет откуда ее достать) также используется Selenium.
Конкретно эту задачу я вынес в отдельный процесс через Celery.

В файле `generate_api_avito.py` содержится пример кода для генерации API-ссылки для Авито.

## Почему я выбрал Wordpress для лендинга и как связал Wordpress, Личный кабинет и Телеграм-бота на одном сервере

Wordpress хорошо ранжируется в поисковиках и имеет множество плагинов. 
![analytics](https://github.com/ubirust/sigmaparser_public/blob/main/images/analytics.jpg)
*Метрика посещений*

Для отправки писем и управления ключами я использовал соответствующие плагины, а логику активации подписки и продления написал вручную. 

Личный кабинет и Телеграм-бот работают на FastAPI. 

Телеграм-бот работает на Webhook, это когда Telegram сам вызывает обработчик события/сообщения, когда в боте происходит какая‑то активность

Код запуска бота на Webhook + FastAPI указан в `bot.py`

Все компоненты связаны на одном сервере с помощью NGINX.

## Что дальше?

Планируется доработка CRM на Django. В эту систему будут в режиме реального времени поступать новые объявления, при этом будет осуществляться синхронизация между CRM и мобильным приложением через Wi-Fi. 

![analytics](https://github.com/ubirust/sigmaparser_public/blob/main/images/crm.jpg)
*CRM*

При появлении нового объявления у пользователя автоматически совершается звонок по указанному в объявлении номеру, и данное объявление отображается в CRM.

У меня сейчас нет времени, чтобы завершить работу над CRM, так что не понятно, когда это будет реализовано. 

Но вы можете скачать мои наработки здесь: https://github.com/ubirust/crm_for_agent_django

## Контакты

Если у вас есть вопросы/предложения, связывайтесь со мной по этим контактам:
- Telegram: [@ubirust](https://t.me/ubirust)

