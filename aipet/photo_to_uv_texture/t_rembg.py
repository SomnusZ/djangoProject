import time
from rembg import remove, new_session
from PIL import Image
#
#
# model_path = "model/BiRefNet-general-epoch_244.onnx"
# # model_name = "birefnet-massive"
# model_name = "birefnet-general"
# new_session = new_session(model_name, model_path)
#
# start = time.time()
# input_path = "image/UserImage/cat10.jpg"
# output_path = "image/UserImage/cat1_rembg.png"
#
#
# input_image = Image.open(input_path)
# output_image_rgba = remove(input_image, session=new_session, post_process_mask=True)
# # output_image = output_image_rgba.convert('RGB')
#
# output_image_rgba.save(output_path)
# print(time.time() - start)


def resize_max_side(img: Image.Image, max_side: int = 1024) -> Image.Image:
    w, h = img.size
    scale = max_side / max(w, h)
    if scale >= 1:
        return img
    new_w, new_h = int(w * scale), int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)

start = time.time()

session = new_session("birefnet-general")

input_image = Image.open("image/UserImage/cat10.jpg").convert("RGB")
input_image = resize_max_side(input_image, max_side=1024)  # ✅ 关键

output = remove(input_image, session=session, post_process_mask=True)
output.save("image/UserImage/cat1_rembg.png")

print("cost:", time.time() - start)


