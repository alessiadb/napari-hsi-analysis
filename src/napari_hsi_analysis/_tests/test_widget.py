import numpy as np


def test_something(make_napari_viewer):
    viewer = make_napari_viewer()
    im_data = np.random.random((10, 200, 100))
    viewer.add_image(im_data)
