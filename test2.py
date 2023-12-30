from PIL import Image, ImageOps
from pytesseract import pytesseract

pytesseract.tesseract_cmd = r'/usr/local/Homebrew/Cellar/tesseract/5.3.3/bin/tesseract'

im = Image.open(r"download.png")
im_greystyle = ImageOps.grayscale(im)
im_threshold = im_greystyle.point(lambda p: p > 165 and 255)
im_crop = im_threshold.crop((140, 170, 510, 270))
im_invert = ImageOps.invert(im_crop)
im_invert.show()    
im_invert.save("stromzaehler.jpg", quality=100, subsampling=0)
result = pytesseract.image_to_string(Image.open('stromzaehler.jpg'), lang='eng', config='--psm 8')
print(result)