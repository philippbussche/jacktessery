from PIL import Image, ImageOps
from pytesseract import pytesseract

pytesseract.tesseract_cmd = r'/usr/local/Homebrew/Cellar/tesseract/5.3.3/bin/tesseract'

im = Image.open(r"IMG_6306.jpg")
im_greystyle = ImageOps.grayscale(im) 
im_threshold = im_greystyle.point(lambda p: p > 230 and 255)
im_crop = im_threshold.crop((1730, 1650, 2010, 1890))
im_invert = ImageOps.invert(im_crop)
im_invert.save("result.jpg", quality=100, subsampling=0)
im_invert.show()
result = pytesseract.image_to_string(Image.open('result.jpg'), lang='ssd', config='--psm 8')
print(int(result))