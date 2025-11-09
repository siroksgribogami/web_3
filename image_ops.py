"""Операции с изображениями: умножение по оси на периодическую функцию (sin/cos)
и вспомогательная функция для сохранения цветовых гистограмм.
"""
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt


def apply_periodic(pil_image: Image.Image, period: float, func: str = 'sin', orientation: str = 'vertical') -> Image.Image:
    """
    Умножает каждый пиксель на периодическую функцию вдоль выбранной оси.
    - period: период в пикселях
    - func: 'sin' или 'cos'
    - orientation: 'vertical' — изменение по Y (строки), 'horizontal' — по X (столбцы)
    Функция нормализуется в диапазон [0,1]: 0.5*(1 + sin(2*pi*coord/period)).
    Возвращает новый объект PIL.Image (RGB).
    """
    if func not in ('sin', 'cos'):
        raise ValueError('параметр func должен быть "sin" или "cos"')
    if orientation not in ('vertical', 'horizontal'):
        raise ValueError('параметр orientation должен быть "vertical" или "horizontal"')
    if period <= 0:
        raise ValueError('параметр period должен быть > 0')

    arr = np.asarray(pil_image).astype(np.float32)  # H x W x 3
    H, W = arr.shape[:2]

    if orientation == 'vertical':
        coords = np.arange(H).reshape(H, 1)
    else:
        coords = np.arange(W).reshape(1, W)

    # compute phase
    omega = 2.0 * np.pi / float(period)
    phase = omega * coords
    if func == 'sin':
        values = 0.5 * (1.0 + np.sin(phase))
    else:
        values = 0.5 * (1.0 + np.cos(phase))

    # broadcast to H x W x 3
    if orientation == 'vertical':
        mask = np.repeat(values[:, :, np.newaxis], W, axis=1)
    else:
        mask = np.repeat(values[:, :, np.newaxis], H, axis=0)

    out = arr * mask
    out = np.clip(out, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def save_histogram(pil_image: Image.Image, out_path: str, title: str = None):
    """Сохранить цветовые гистограммы (R,G,B) в файл out_path (PNG)."""
    arr = np.asarray(pil_image)
    if arr.ndim == 3 and arr.shape[2] >= 3:
        r = arr[:, :, 0].ravel()
        g = arr[:, :, 1].ravel()
        b = arr[:, :, 2].ravel()
    else:
        r = arr.ravel()
        g = None
        b = None

    plt.figure(figsize=(6, 3))
    if title:
        plt.title(title)
    bins = 256
    plt.hist(r, bins=bins, color='r', alpha=0.5, label='R')
    if g is not None:
        plt.hist(g, bins=bins, color='g', alpha=0.5, label='G')
    if b is not None:
        plt.hist(b, bins=bins, color='b', alpha=0.5, label='B')
    plt.xlim(0, 255)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
