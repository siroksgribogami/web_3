from PIL import Image
import numpy as np
import image_ops


def test_apply_periodic_shape_and_range():
    # create a small test image 40x30 with mid-gray
    W, H = 40, 30
    arr = np.full((H, W, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)

    out = image_ops.apply_periodic(img, period=10, func='sin', orientation='vertical')
    assert out.size == img.size
    out_arr = np.asarray(out)
    assert out_arr.dtype == np.uint8
    assert out_arr.min() >= 0 and out_arr.max() <= 255

    # check horizontal mode too
    out2 = image_ops.apply_periodic(img, period=7, func='cos', orientation='horizontal')
    assert out2.size == img.size
    out2_arr = np.asarray(out2)
    assert out2_arr.min() >= 0 and out2_arr.max() <= 255
