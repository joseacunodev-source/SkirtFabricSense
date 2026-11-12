"""Place the user's five screenshots and explanations in a plain Word document."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
IMAGES=ROOT/'output/progress_report_2026-11-11'
OUTPUT=ROOT/'output/SkirtFabricSense_Progress_Report_Screenshots.docx'
items=[
('03_code_training.png','Model training code',
 'This code prepares the MobileNetV2 model to classify skirts as pleated or non-pleated. It supports transfer learning and controlled fine-tuning, checks that dataset assignments and label order remain consistent, and verifies that a forward pass runs on the GPU.'),
('04_code_frame_freshness.png','Handling outdated predictions',
 'This code checks whether a completed prediction is still valid before displaying it. Results are discarded when the camera disconnects, the scene changes, or the frame becomes too old. This helps prevent a previous skirt\'s classification from appearing as the current result.'),
('01_current_camera_ui_desktop.png','Desktop interface',
 'The desktop interface brings together the camera preview, camera controls, garment presentation options, and classification panels. Pleating, hemline length, fabric appearance, and model score have separate status displays. The screenshot shows the camera-off state, so no classification results are presented.'),
('02_current_camera_ui_800x480.png','Small screen interface',
 'This screenshot shows the interface at an 800 × 480 resolution, matching the intended Raspberry Pi display. The camera preview and result panels remain side by side, while some lower controls and reference information require scrolling. Physical touchscreen usability still needs testing.'),
('05_code_hemline_rules.png','Hemline classification rules',
 'This code assigns a hemline category using a calibrated waist-to-floor reference and eight category boundaries. It checks the supplied measurements and returns an uncertain result when the hem position overlaps a boundary. The rules are implemented, while actual wearer-reference detection and physical calibration remain unfinished.'),
]
doc=Document()
s=doc.sections[0];s.orientation=WD_ORIENT.LANDSCAPE
s.page_width=Inches(11);s.page_height=Inches(8.5)
s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Inches(.5)
normal=doc.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(11)
normal.font.color.rgb=RGBColor(0,0,0)
normal.paragraph_format.space_after=Pt(6)
normal.paragraph_format.line_spacing=1.08
for name in ['Title','Heading 1','Caption']:
 st=doc.styles[name];st.font.name='Arial';st.font.color.rgb=RGBColor(0,0,0)
 st.paragraph_format.space_before=Pt(0);st.paragraph_format.space_after=Pt(6)
doc.styles['Title'].font.size=Pt(17)
doc.styles['Heading 1'].font.size=Pt(12)
doc.styles['Heading 1'].font.bold=True
doc.core_properties.title='SkirtFabricSense Progress Report Screenshots'
doc.core_properties.subject='Project screenshots with short explanations'
doc.core_properties.author=''
for i,(filename,title,paragraph) in enumerate(items):
 if i:doc.add_page_break()
 if i==0:
  p=doc.add_paragraph('SkirtFabricSense Progress Report Screenshots','Title')
 p=doc.add_paragraph(f'Figure {i+1}  {title}','Heading 1')
 p.paragraph_format.keep_with_next=True
 image=IMAGES/filename
 with Image.open(image) as im:w,h=im.size
 width=min(10,5.8*w/h)
 p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 p.paragraph_format.space_after=Pt(8)
 shape=p.add_run().add_picture(str(image),width=Inches(width))
 shape._inline.docPr.set('descr',title)
 p=doc.add_paragraph(paragraph)
 p.paragraph_format.widow_control=True
for element in [doc.styles.element, doc.element]:
 for border in element.xpath('.//w:pBdr'):
  border.getparent().remove(border)
doc.save(OUTPUT)
print(OUTPUT)
