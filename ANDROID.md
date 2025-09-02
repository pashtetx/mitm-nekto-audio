# Як запустити бота на андроїді?

Спочатку вам потрібно завантажити дві программи:

1. [Eruda (клік щоб встановити апк файл)](https://github.com/liriliri/eruda-android/releases/download/v1.2.0/eruda-v1.2.0-release.apk)
2. Termux (завантажити з Google Play)

Тепер вам потрібно зайти в Eruda та перейти на сторінку https://nekto.me/audiochat, після цього порозмовляйте 3-5 рази щоб пройти перевірку на спам та ботів. Далі натисніть на панель розробників (сіра кнопка), та відкрийте Console в консоль введіть:
```
console.log("User-id:", JSON.parse(localStorage.getItem("storage_audio_v2")).user.authToken);console.log("User-agent:", window.userAgentSW)
```
Потім збережіть що вам вивело в консолі (User-id, User-Agent). Та введіть для ресету:
```
localStorage.removeItem("storage_audio_v2"); location.reload();
```
Після команди сторінка повинна перезавнтажитись та як вона перезавантажилась порозмовляйте знову 3-5 рази, далі введіть першу команду та сбережіть вивід (User-id, User-Agent). 

## Termux

В термуксі потрібно встановити python, git та ініціалізувати простір:
```
pkg install python git && termux-setup-storage
```
Далі потрібно завантажити бота:
```
git clone https://github.com/pashtetx/mitm-nekto-audio.git && cd mitm-nekto-audio && mv "config.ini TEMPLATE" config.ini
```
Встановлюємо залежності:
```
pip install -r requirements.txt && pip install -U av
```
Далі відкриваєм конфіг файл (config.ini) через nano або ваш текстовий редактор:
```
nano config.ini
```
Переність все що ви отримали в браузері Eruda (User-Agent, User-id) до двох клієнтів (female-client, male-client). 

## Discord бот (для реал-тайму)

Щоб встановити бота в діскорд вам потрібно його створити ось гайд: https://3v-host.com/uk/blog/how-to-create-a-discord-bot/

А коли ви отримаєте токен внесіть його в конфіг.

## Допомога
В моєму телеграм каналі я вам допомжу якщо у вас виникла помилка: [клік](https://t.me/+ESHNRLki3qlkODQy)
