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


def _get_flowers():
    """Scan static/svg_elements for .svg files and produce randomized positions.
    Returns a list of dicts: {url, top, left, size, rotate, opacity}.
    """
    svg_dir = os.path.join(STATIC_DIR, 'svg_elements')
    flowers = []
    if os.path.isdir(svg_dir):
        files = [f for f in os.listdir(svg_dir) if f.lower().endswith('.svg')]
        max_items = min(18, len(files))  # limit to avoid overdraw
        chosen = files[:max_items]
        for name in chosen:
            flowers.append({
                'url': f'/static/svg_elements/{name}',
                'top': random.randint(0, 85),   # percent
                'left': random.randint(0, 85),  # percent
                'size': random.randint(64, 160),  # px
                'rotate': random.randint(0, 360),
                'opacity': round(random.uniform(0.15, 0.35), 2),
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
        raise HTTPException(status_code=400, detail='func must be sin or cos')
    if orientation not in ('vertical', 'horizontal'):
        raise HTTPException(status_code=400, detail='orientation must be vertical or horizontal')
    if period <= 0:
        raise HTTPException(status_code=400, detail='period must be > 0')

    # read uploaded file into PIL Image
    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Invalid image file: {e}')

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
    image_ops.save_histogram(img, hist_orig_path, title='Original image color histograms')
    image_ops.save_histogram(processed, hist_proc_path, title='Processed image color histograms')

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
