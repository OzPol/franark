"""Export the four maintained architecture views as a standalone PDF."""
import argparse
from io import BytesIO
from pathlib import Path
import subprocess
import reportlab

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from render_diagrams import DIAGRAMS, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "output/pdf/Franark_SFC_System_Atlas.pdf")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A3)
    font_dir = Path(reportlab.__file__).parent / "fonts"
    pdfmetrics.registerFont(TTFont("AtlasRegular", str(font_dir / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("AtlasBold", str(font_dir / "VeraBd.ttf")))
    document = canvas.Canvas(str(args.output), pagesize=(width, height))
    document.setTitle("Franark - SFC System Atlas")
    document.setAuthor("Ozlem Polat")
    for index, (name, (title, caption, body)) in enumerate(DIAGRAMS.items(), start=1):
        document.setFillColorRGB(0.04, 0.04, 0.04)
        document.setFont("AtlasRegular", 13)
        document.drawString(42, height - 38, "FRANARK / SFC PILOT")
        document.setFont("AtlasBold", 26)
        document.drawString(42, height - 76, title)
        document.setFont("AtlasRegular", 14)
        document.drawString(42, height - 104, caption)
        rendered = subprocess.run(["dot", "-Gdpi=160", "-Tpng", str(ROOT / "docs/diagrams" / (name + ".dot"))],
                                  check=True, capture_output=True).stdout
        image = ImageReader(BytesIO(rendered))
        image_width, image_height = image.getSize()
        available_width, available_height = width - 84, height - 220
        ratio = min(available_width / image_width, available_height / image_height)
        draw_width, draw_height = image_width * ratio, image_height * ratio
        document.drawImage(image, (width - draw_width) / 2, 90 + (available_height - draw_height) / 2,
                           width=draw_width, height=draw_height, mask="auto")
        document.setFont("AtlasRegular", 12)
        legend = "Solid: implemented pilot. Dashed: optional or external connection requiring configuration or verification."
        document.drawString(42, 57, legend)
        document.setFont("AtlasRegular", 11)
        document.drawString(42, 32, "SFC deployment target | capability-foundation | Synthetic pilot; tenant integration not yet verified")
        document.drawRightString(width - 42, 32, f"{index} / {len(DIAGRAMS)}")
        document.showPage()
    document.save()
    print(args.output)


if __name__ == "__main__":
    main()
