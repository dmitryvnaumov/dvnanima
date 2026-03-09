import cv2
import numpy as np
import argparse
from pathlib import Path


def get_fourier_samples(image_path, num_points=1500, threshold=200):
    # 1. Загружаем и обрабатываем
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    # Инвертируем, чтобы линии были белыми на черном фоне для поиска контуров
    _, binary = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY_INV)
    
    # 2. Ищем контуры
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []
    
    # Берем самый длинный (основной) контур
    main_contour = max(contours, key=len).reshape(-1, 2)
    
    # Замыкаем линию
    main_contour = np.vstack([main_contour, main_contour[0]])
    
    # 3. Равномерное сэмплирование (интерполяция)
    dists = np.sqrt(np.sum(np.diff(main_contour, axis=0)**2, axis=1))
    cum_dist = np.concatenate(([0], np.cumsum(dists)))
    total_dist = cum_dist[-1]
    
    target_dists = np.linspace(0, total_dist, num_points, endpoint=False)
    x_sampled = np.interp(target_dists, cum_dist, main_contour[:, 0])
    y_sampled = np.interp(target_dists, cum_dist, main_contour[:, 1])
    
    # 4. Нормализация для Manim (центрирование и масштаб)
    x_sampled -= np.mean(x_sampled)
    y_sampled -= np.mean(y_sampled)
    y_sampled = -y_sampled # В изображениях Y идет вниз, в Manim — вверх
    
    # Масштабируем так, чтобы портрет вписался в экран (например, по высоте 7 единиц)
    scale = 3.5 / max(np.max(np.abs(x_sampled)), np.max(np.abs(y_sampled)))
    x_sampled *= scale
    y_sampled *= scale
    
    return [complex(x, y) for x, y in zip(x_sampled, y_sampled)]

def save_points_to_svg(points, filename="portrait.svg"):
    # Определяем границы (viewBox)
    xs = [p.real for p in points]
    ys = [p.imag for p in points]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max_x - min_x
    height = max_y - min_y

    # Генерируем путь (Path Data)
    # M - перемещение в начало, L - линия к следующей точке
    path_data = f"M {points[0].real},{points[0].imag} "
    for p in points[1:]:
        path_data += f"L {p.real},{p.imag} "
    path_data += "Z" # Замыкаем линию

    # Собираем XML структуру SVG
    svg_template = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {width} {height}">
    <path d="{path_data}" fill="none" stroke="black" stroke-width="0.05"/>
</svg>"""

    with open(filename, "w") as f:
        f.write(svg_template)
    print(f"Файл {filename} успешно сохранен!")

def main():
    parser = argparse.ArgumentParser(description="Convert a raster image to a single-path SVG for Fourier drawing.")
    parser.add_argument("input", nargs="?", default="Fourie.png", help="Input image (png/jpg). Default: Fourie.png")
    parser.add_argument("-o", "--output", default="", help="Output SVG filename. Default: <input>.svg")
    parser.add_argument("-n", "--num-points", type=int, default=1500, help="Number of sampled points")
    parser.add_argument("-t", "--threshold", type=int, default=200, help="Binary threshold (0-255)")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"Input image not found: {in_path}")

    out_path = Path(args.output) if args.output else in_path.with_suffix(".svg")
    points = get_fourier_samples(str(in_path), num_points=args.num_points, threshold=args.threshold)
    save_points_to_svg(points, str(out_path))


if __name__ == "__main__":
    main()
