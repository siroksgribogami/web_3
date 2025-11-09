from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
import os
import uuid
import random
from PIL import Image
import io
import image_ops

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI()
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# If a top-level svg_elements folder exists (project root), expose it at /svg_elements
ALT_SVG_DIR = os.path.join(BASE_DIR, 'svg_elements')
if os.path.isdir(ALT_SVG_DIR):
    app.mount('/svg_elements', StaticFiles(directory=ALT_SVG_DIR), name='svg_elements')


def _get_flowers():
    """Сканирует каталоги с SVG-цветами и возвращает список декораций.
    Локации поиска по приоритету:
      1) static/svg_elements (если есть и в нём есть .svg)
      2) svg_elements в корне проекта (если есть и в нём есть .svg)

    Возвращает список словарей:
      {url, top, left, size, rotate, opacity}
    """
    flowers = []

    def list_svgs(dir_path: str):
        try:
            return [f for f in os.listdir(dir_path) if f.lower().endswith('.svg')]
        except Exception:
            return []

    static_svg_dir = os.path.join(STATIC_DIR, 'svg_elements')

    # 1) Пытаемся взять из static/svg_elements
    files = []
    url_prefix = '/static/svg_elements'
    if os.path.isdir(static_svg_dir):
        files = list_svgs(static_svg_dir)

    # 2) Если файлов нет, пробуем корень проекта svg_elements
    if not files and os.path.isdir(ALT_SVG_DIR):
        files = list_svgs(ALT_SVG_DIR)
        url_prefix = '/svg_elements'

    # Если всё равно пусто — возвращаем пустой список (ничего не рисуем)
    if not files:
        return flowers

    # Немного перемешаем, чтобы картинки были разнообразны
    random.shuffle(files)

    # Разрешим дублирование: берем до 22 элементов, повторяя список при необходимости
    target_count = min(22, max(8, len(files)))
    while len(flowers) < target_count:
        name = random.choice(files)
        flowers.append({
            'url': f'{url_prefix}/{name}',
            'top': random.randint(0, 85),
            'left': random.randint(0, 85),
            'size': random.randint(72, 180),
            'rotate': random.randint(0, 360),
            'opacity': round(random.uniform(0.28, 0.6), 2),
        })
    return flowers


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    context = {'request': request, 'flowers': _get_flowers()}
    return templates.TemplateResponse('index.html', context)


@app.post('/', response_class=HTMLResponse)
async def process(request: Request,
                  file: UploadFile = File(...),
                  period: float = Form(...),
                  func: str = Form('sin'),
                  orientation: str = Form('vertical')):
    # validate inputs
    if func not in ('sin', 'cos'):
        raise HTTPException(status_code=400, detail='параметр func должен быть sin или cos')
    if orientation not in ('vertical', 'horizontal'):
        raise HTTPException(status_code=400, detail='параметр orientation должен быть vertical или horizontal')
    if period <= 0:
        raise HTTPException(status_code=400, detail='параметр period должен быть > 0')

    # read uploaded file into PIL Image
    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Неверный файл изображения: {e}')

    # save original
    uid = uuid.uuid4().hex
    orig_name = f'orig_{uid}.jpg'
    orig_path = os.path.join(STATIC_DIR, orig_name)
    img.save(orig_path, format='JPEG')

    # apply periodic transform
    processed = image_ops.apply_periodic(img, period=period, func=func, orientation=orientation)
    proc_name = f'proc_{uid}.jpg'
    proc_path = os.path.join(STATIC_DIR, proc_name)
    processed.save(proc_path, format='JPEG')

    # save histograms
    hist_orig = f'hist_orig_{uid}.png'
    hist_proc = f'hist_proc_{uid}.png'
    hist_orig_path = os.path.join(STATIC_DIR, hist_orig)
    hist_proc_path = os.path.join(STATIC_DIR, hist_proc)
    image_ops.save_histogram(img, hist_orig_path, title='Гистограммы цветов — оригинал')
    image_ops.save_histogram(processed, hist_proc_path, title='Гистограммы цветов — обработано')

    # build urls
    base = request.base_url._url.rstrip('/')
    context = {
        'request': request,
        'orig_url': f'/static/{orig_name}',
        'proc_url': f'/static/{proc_name}',
        'hist_orig_url': f'/static/{hist_orig}',
        'hist_proc_url': f'/static/{hist_proc}',
        'period': period,
        'func': func,
        'orientation': orientation,
        'flowers': _get_flowers(),
    }
    return templates.TemplateResponse('result.html', context)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='127.0.0.1', port=8000, reload=True)
