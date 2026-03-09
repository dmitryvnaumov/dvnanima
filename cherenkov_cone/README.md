# Cherenkov Cone Prototype

Этот каталог содержит визуальный прототип пересечения черенковского конуса с боковой поверхностью цилиндрического детектора.

## Что делает код

Точка входа `cherenkov_prototype.py`:

- читает параметры из `run.cfg`;
- задает трек мюона `r(s) = r0 + s u`;
- строит черенковский конус с вершиной в текущем положении мюона;
- аналитически вычисляет пересечение конуса с боковой поверхностью цилиндра;
- визуализирует сцену в 3D;
- может одновременно показывать развертку цилиндра в 2D;
- может сохранять видео и историю пересечений по кадрам.

## Геометрическая модель

Используется стандартное неявное уравнение двуконуса:

```text
((r - a) · u)^2 = |r - a|^2 cos^2(theta_c)
```

где:

- `a` — вершина конуса, то есть текущее положение мюона;
- `u` — единичный вектор трека;
- `theta_c` — угол Черенкова.

Для боковой поверхности цилиндра:

```text
x = R cos(phi)
y = R sin(phi)
z = z
```

пересечение считается аналитически как решение квадратного уравнения по `z(phi)`. В коде используется только нужная наппа двуконуса через параметр `nappe`.

## Структура кода

### `cherenkov_prototype.py`

- `run_prototype` — основной pipeline: чтение конфига, построение сцены, цикл по кадрам, запись видео и сохранение истории.

### `cherenkov_config.py`

- `_parse_bool` — разбирает булевы значения из `run.cfg`.
- `_parse_vec3` — разбирает векторы вида `x, y, z`.
- `load_cfg` — читает `run.cfg` и собирает словарь параметров.

### `cherenkov_geometry.py`

- `normalize` — нормирует вектор.
- `make_track_points` — семплирует линию трека для отрисовки.
- `_nappe_mask` — выбирает нужную часть двуконуса.
- `_branches_from_masked_curve` — режет периодическую кривую на непрерывные ветви.
- `analytic_intersection_curve_on_cylinder` — основной аналитический расчет пересечения.
- `verify_intersection` — проверяет residuals для цилиндра и конуса.
- `make_oms_on_cylinder` — расставляет OMs по строкам на цилиндре.
- `unwrap_cylinder_points` — разворачивает точки цилиндра в координаты `(s, z)`, где `s = R phi`.
- `_ordered_segment_point_chunks` — группирует точки по сегментам.
- `segmented_points_to_polylines` — восстанавливает список полилиний из сегментов.
- `polylines_to_segmented_points` — превращает список полилиний в плоские массивы.
- `build_unwrapped_multiline_polydata` — строит линии для 2D-развертки с учетом шва `phi = 0 / 2pi`.
- `make_unwrapped_outline` — рисует прямоугольную рамку развертки.
- `make_unwrapped_string_guides` — рисует вертикальные направляющие по строкам.
- `nearest_distance_to_polylines` — оценивает расстояние от OMs до текущей линии пересечения.

### `cherenkov_history.py`

- `save_history_npz` — сохраняет историю в `npz`.
- `save_history_vtm` — сохраняет историю в `vtm` для PyVista/ParaView.
- `build_multiline_polydata` — собирает несколько сегментов в один `PolyData`.

### `cherenkov_viewer.py`

- `apply_camera` — применяет 3D-камеру.
- `apply_unwrapped_camera` — выставляет камеру для 2D-развертки.
- `show_history_viewer` — открывает отдельный просмотрщик слайдера по кадрам.

В `show_history_viewer` доступны:

- 3D-сцена;
- опциональная 2D-развертка цилиндра;
- клавиши `j/k`, `a/d`, `Left/Right`;
- slider `Frame`.

## Файлы

- `cherenkov_prototype.py` — точка входа и основной render loop.
- `cherenkov_config.py` — чтение и нормализация конфигурации.
- `cherenkov_geometry.py` — геометрия, аналитическое пересечение и unwrap.
- `cherenkov_history.py` — сохранение истории.
- `cherenkov_viewer.py` — camera helpers и history viewer.
- `__init__.py` — marker для пакетного импорта.
- `run.cfg` — все runtime-параметры.
- `cherenkov_cylinder.mp4` — видео, если `save_movie = 1`.
- `cherenkov_history.npz` — массивы истории, если `save_history_npz = 1`.
- `cherenkov_history.vtm` — геометрия истории, если `save_history_vtm = 1`.

## Параметры в `run.cfg`

### `[run]`

- `save_movie` — сохранять ли видео.
- `movie_path` — путь к выходному `.mp4`.
- `n_frames` — число кадров анимации.
- `show_progress` — печатать ли прогресс по кадрам.
- `movie_fps` — FPS видео.
- `movie_format` — backend для `imageio`.
- `movie_codec` — codec для видео.
- `movie_is_batch` — флаг writer'а `imageio`.
- `history_stride` — как часто сохранять кадры в history.
- `save_history_npz` — сохранить `npz`.
- `history_npz_path` — путь к `npz`.
- `save_history_vtm` — сохранить `vtm`.
- `history_vtm_path` — путь к `vtm`.
- `show_history_viewer` — открыть отдельный history viewer после расчета.

### `[detector]`

- `cluster_radius` — радиус цилиндра.
- `z_min`, `z_max` — нижняя и верхняя границы по `z`.
- `cylinder_resolution` — детализация wireframe цилиндра.
- `cyl_sample_phi` — число значений `phi` для аналитического пересечения.
- `n_strings` — число строк OMs.
- `oms_per_string` — число OMs на строке.

### `[optics]`

- `n_refr` — показатель преломления среды.
- `beta` — `v/c` для частицы.

### `[track]`

- `r0` — стартовая точка трека.
- `u` — направление трека.
- `s_start`, `s_end` — диапазон параметра движения.
- `draw_s_min`, `draw_s_max` — диапазон видимой линии трека.
- `draw_points` — число точек для отрисовки трека.

### `[intersection]`

- `analytic_eps` — численный эпсилон для особых случаев в аналитическом решении.
- `apex_inside_only` — показывать пересечение только когда вершина внутри цилиндра.
- `nappe` — какую наппу двуконуса брать: `trailing`, `leading`, `both`.
- `clip_to_visual_cone` — обрезать пересечение длиной видимого конуса.
- `max_forward_distance` — дополнительная осевая отсечка вдоль конуса.
- `verify_geometry` — печатать проверку residuals.
- `verify_every` — как часто проверять геометрию.
- `verify_atol` — порог для residuals.
- `min_points` — минимальная длина ветви пересечения.
- `activation_distance` — расстояние активации OMs от линии пересечения.
- `curve_line_width` — толщина линии пересечения в 3D.
- `curve_color` — цвет линии пересечения.

### `[visual]`

- `plot_theme` — тема PyVista.
- `window_width`, `window_height` — размер окна.
- `show_unwrapped_view` — включить 2D-развертку рядом с 3D.
- `cylinder_line_width`, `cylinder_opacity` — вид цилиндра.
- `track_line_width` — толщина трека.
- `om_point_size` — размер OMs в 3D.
- `unwrap_om_point_size` — размер OMs в 2D.
- `unwrap_curve_line_width` — толщина линии пересечения в 2D-развертке.
- `unwrap_curve_point_size` — размер точек пересечения в 2D-развертке.
- `unwrap_active_om_point_size` — размер активных OMs в 2D.
- `apex_radius` — размер вершины конуса.
- `cone_height`, `cone_resolution`, `cone_opacity` — вид конуса.
- `camera_position`, `camera_focal`, `camera_view_up`, `parallel_projection` — 3D-камера для интерактива.
- `movie_camera_position`, `movie_camera_focal`, `movie_camera_view_up`, `movie_parallel_projection` — отдельная камера для видео.
- `title_text` — заголовок сцены.

## Запуск

Из каталога `cherenkov_cone`:

```bash
python cherenkov_prototype.py
```

Или из корня проекта:

```bash
python cherenkov_cone/cherenkov_prototype.py
```

## Зависимости

Нужны:

```bash
pip install numpy pyvista imageio av
```

Для интерактивного режима нужен рабочий OpenGL/GUI backend. Для сохранения видео используется `imageio` с PyAV backend.

## Практические режимы

### Только интерактивный просмотр

```ini
save_movie = 0
show_history_viewer = 0
```

### Интерактив + отдельный history viewer

```ini
save_movie = 0
show_history_viewer = 1
```

### Сохранить видео и потом открыть history viewer

```ini
save_movie = 1
show_history_viewer = 1
```

## Что смотреть при отладке

- если пересечение выглядит слишком грубым, увеличь `cyl_sample_phi`;
- если линия слишком короткая, проверь `clip_to_visual_cone` и `max_forward_distance`;
- если ранние пересечения выглядят странно, проверь `nappe`;
- если хочется более "объемного" вида, меняй `camera_position` и отключай `parallel_projection`.
