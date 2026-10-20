# ✿ Kawaii XFCE

Тёмное сливово-розовое оформление для XFCE 4.20 (X11): обои с луной и котиком, виджет-котик с часами и состоянием компьютера, розовая панель со статистикой, меню «Пуск» в том же стиле и немного полезных мелочей. Всё настроено так, чтобы работать быстро через RDP и VNC: композитор выключен, а прозрачность виджета нарисована из обоев.

<p align="center">
  <img src="preview/wallpaper.png" width="640" alt="обои Kawaii Night"><br>
  <img src="preview/widget.png" width="260" alt="виджет">
  <img src="preview/menu.png" width="360" alt="меню">
</p>

## Что внутри

| | |
|---|---|
| 🌙 **Обои** | `wallpapers/kawaii-night.png` (2560×1440), нарисованы скриптом `tools/make-wallpaper.py` |
| 🐱 **Виджет** | `scripts/kawaii-widget.py`: котик моргает и меняет настроение от нагрузки, часы, дата, приветствие, полоски CPU / RAM / диск / температура, скорость сети, аптайм |
| 💗 **Панель** | список окон-«таблеток», мордочка `(◕‿◕) ♡ cpu ✿ ram ☁ °` (genmon), розовый график CPU, часы `✿ Tue 20 Oct ♡ 18:44` |
| 🌸 **Меню «Пуск»** | Whisker Menu: тёмный фон, скруглённый поиск, розовая подсветка, аватарка-котик |
| 🔤 **Шрифты** | Quicksand для интерфейса, Fira Code (Nerd Font) для терминала, цветные эмодзи раньше чёрно-белого Symbola |
| 📁 **Иконки** | Papirus-Dark с розовыми папками, собирается без sudo (`tools/make-pink-papirus.sh`) |
| 💻 **Терминал** | xfce4-terminal в цветах темы |
| 🐈 **oneko** | котик бегает за курсором |
| ⌨️ `--keys` | сочетания как в Windows (Win, Win+D/E/L/V/R, Win+стрелки, Win+Shift+S) и раскладка us,ru по Ctrl+Space, которая сама возвращается после переподключения RDP |
| 🖥 `--vnc` | VNC-сервер TigerVNC только для домашней сети: UTF-8 буфер обмена, TLS, x11vnc как запасной вариант |

## Установка

1. Зависимости (Debian 13 / Ubuntu):

   ```bash
   sudo apt install fonts-quicksand fonts-firacode fonts-noto-color-emoji fonts-noto-cjk \
     papirus-icon-theme breeze-cursor-theme xfce4-whiskermenu-plugin xfce4-genmon-plugin \
     xfce4-cpugraph-plugin xfce4-clipman xfce4-taskmanager python3-gi python3-gi-cairo \
     python3-cairo gir1.2-gtk-3.0 oneko
   ```

   По желанию: `tigervnc-scraping-server` для `--vnc`.

2. GTK-тема [Dracula](https://github.com/dracula/gtk): распакуй её в `~/.themes/Dracula`.

3. По желанию: [FiraCode Nerd Font](https://github.com/ryanoasis/nerd-fonts/releases) в `~/.local/share/fonts`, тогда в терминале появятся иконки.

4. Запуск:

   ```bash
   ./install.sh                  # оформление, виджет, терминал, меню
   ./install.sh --panel          # плюс пересобрать верхнюю панель (заменит текущую!)
   ./install.sh --panel --keys   # плюс сочетания клавиш и раскладка
   ```

Всё, что установщик перезаписывает, сохраняется в `~/.config/kawaii-backup/<дата>/`.

## Настройка

- **Имя в приветствии виджета** берётся из `$USER`, поменять можно через `KAWAII_NAME=Имя` в `~/.config/autostart/kawaii-widget.desktop` (`Exec=env KAWAII_NAME=Имя …`).
- **Место виджета** задаётся константами `X, Y` в начале `kawaii-widget.py`.
- **VNC:** пароль в `~/.vnc/passwd` (`tigervncpasswd`), сетевой интерфейс и порт задаются через `KAWAII_VNC_IFACE` / `KAWAII_VNC_PORT`.

## Заметки

- Композитор выключен специально: через RDP/VNC это самое заметное ускорение. Если включить его обратно, виджет сам перезапустится с настоящей прозрачностью.
- В TigerVNC 1.15 опция `HostsFile` роняет сервер при подключении, поэтому VNC слушает только адрес в домашней сети.
- Если подключаешься через xrdp, не перезапускай службу `xrdp` при открытой сессии: менеджер сессий её «забудет», и войти снова получится только после перезагрузки.

Сделано с ♡ и котиками (｡•ᴗ•｡)
