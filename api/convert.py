from http.server import BaseHTTPRequestHandler
import json
import base64
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance

DEFAULT_RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
CHAT_RAMP_BLOCKS = "█▓▒░ "
CHAT_RAMP_CLASSIC = "@#S%?*+;:,. "

RAMPS = {
    "blocks": CHAT_RAMP_BLOCKS,
    "classic": CHAT_RAMP_CLASSIC,
    "detailed": DEFAULT_RAMP,
}


def _apply_gamma(img_l, gamma):
    gamma = max(gamma, 1e-6)
    inv = 1.0 / gamma
    table = [int(((i / 255.0) ** inv) * 255) for i in range(256)]
    return img_l.point(table)


def _compute_size(img_w, img_h, max_w, max_h, aspect):
    eff_h = img_h * aspect
    scale = min(max_w / img_w, max_h / eff_h)
    return max(1, int(img_w * scale)), max(1, int(eff_h * scale))


def _image_to_ascii(img, max_width, max_height, ramp, aspect, contrast, gamma, dither, double):
    gray = img.convert("L")
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(max(0.0, contrast))
    gray = _apply_gamma(gray, gamma)
    w, h = gray.size
    new_w, new_h = _compute_size(w, h, max_width, max_height, aspect)
    gray = gray.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    if dither:
        gray = gray.convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=256, dither=Image.Dither.FLOYDSTEINBERG
        ).convert("L")
    n = len(ramp) - 1
    chars = [ramp[int((px / 255) * n)] for px in gray.getdata()]
    lines = []
    for i in range(0, len(chars), new_w):
        row = "".join(chars[i : i + new_w])
        if double:
            row = "".join(ch * 2 for ch in row)
        lines.append(row)
    return "\n".join(lines)


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))

            img = Image.open(BytesIO(base64.b64decode(data["image"])))
            if data.get("invert"):
                img = ImageOps.invert(img.convert("L"))

            ramp = RAMPS.get(data.get("ramp", "blocks"), CHAT_RAMP_BLOCKS)

            result = _image_to_ascii(
                img=img,
                max_width=int(data.get("max_width", 80)),
                max_height=int(data.get("max_height", 40)),
                ramp=ramp,
                aspect=float(data.get("aspect", 0.55)),
                contrast=float(data.get("contrast", 1.6)),
                gamma=float(data.get("gamma", 0.75)),
                dither=bool(data.get("dither", False)),
                double=bool(data.get("double", False)),
            )
            self._respond(200, {"ascii": result})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode("utf-8"))
