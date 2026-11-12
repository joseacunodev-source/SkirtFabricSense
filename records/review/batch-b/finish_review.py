"""Append visual notes from sheets 23-28 inspected on 2026-10-04."""
import json
import runpy
import sys
from pathlib import Path

pages = {
23: [
('P','Structured broad pleats visible from waistband through flared hem.'),
('P','Repeated stitched waist pleats open into broad folds; full skirt visible.'),
('n','Smooth wrap panels; long vest covers waistband.'),
('N','Smooth circular flare with soft drape rather than regular pressed pleats.'),
('U','Plaid and broad folds obscure whether vertical lines are seams or pleats.'),
('U','Only a narrow upper strip visible below sweater; hem outside frame.'),
('U','Waist covered by shirt and jacket; soft gathers cannot establish pleating.'),
('P','Hanging floral skirt has repeated narrow regular pleats; waistband and hem visible.'),
('N','Hanging floral skirt has smooth panels and gently flared hem.'),
('N','Smooth fitted black skirt with front slit; waistband and hem visible.'),
('U','Jacket obscures most skirt; visible strip insufficient for appearance label.'),
('U','Coat and scarf hide waistband; pale texture insufficient to resolve pleating.')],
24: [
('n','Smooth flared pink panels; sweater hides waistband.'),
('U','Soft gathered waistband and broad folds; pleating construction unclear.'),
('n','Smooth fitted gray upper panel; hem outside image.'),
('U','Patterned gathered skirt; folds too indistinct for confident pleating label.'),
('U','Long coat obscures skirt; narrow visible portion insufficient.'),
('N','Rotated photograph shows smooth fitted skirt from waist to hem.'),
('P','Fine regular vertical pleats visible below belt through hem.'),
('N','Smooth asymmetric skirt with large draped side folds, no repeated pleats.'),
('N','Yellow wrap skirt has diagonal drape and smooth base; full skirt visible.'),
('p','Repeated broad pleats visible; jacket covers waistband.'),
('n','Smooth fitted printed mini; black top covers waistband.'),
('U','Handbag obscures central skirt and pattern masks fold structure.')],
25: [
('N','Smooth fitted gray skirt with pockets; waistband to hem visible.'),
('n','Smooth fitted pink panel; reclining pose and blouse obscure full waistband.'),
('U','Jacket and large handbag obscure upper and central skirt.'),
('N','Smooth red circular flare; soft radial drape rather than repeated pressed pleats.'),
('N','Hanging tan skirt shows smooth flared panels and seam lines.'),
('n','Smooth black pencil skirt; jacket covers waistband.'),
('n','Smooth pale mini; raised leg and hand obscure complete garment view.'),
('N','Smooth straight blue skirt; waistband and hem visible.'),
('P','Regular narrow pleating on lower dark section; full skirt outline visible.'),
('n','Quilted mini with horizontal quilting; red jacket covers waistband.'),
('N','Fitted black skirt with diagonal ruching rather than regular pleating.'),
('U','Low-resolution floral skirt and jacket coverage prevent confident fold review.')],
26: [
('n','Fitted printed panel with diagonal wrinkles; hem outside frame.'),
('n','Smooth black pencil skirt; tied blouse partly covers waistband.'),
('N','Full red printed skirt has smooth flared panels and soft drape.'),
('N','Smooth fitted long black skirt with irregular pooling at floor.'),
('n','Smooth teal skirt with slit; sweater covers waistband.'),
('n','Smooth long skirt with soft broad drape; shirt covers waistband.'),
('N','Smooth white straight skirt with ordinary horizontal creases; full view.'),
('n','Smooth fitted denim mini; seated pose and top obscure waist.'),
('U','Seated folded pose, hands and blouse obscure complete skirt shape.'),
('n','Smooth black panel skirt; jacket covers waistband.'),
('N','Fitted lace skirt; continuous surface without regular pleats and full hem visible.'),
('n','Small floral skirt with flounced hem; blouse covers waistband.')],
27: [
('U','Coat covers almost entire skirt; only narrow strip visible.'),
('P','Broad regular folds begin below high waistband; full striped skirt visible.'),
('U','Printed flared skirt has folds but pattern prevents confident pleat distinction.'),
('N','Smooth long slit skirt section with irregular floor drape; full waist-to-hem outline.'),
('n','Smooth long green skirt; matching top covers waistband.'),
('n','Smooth long textured skirt; peplum covers waistband.'),
('U','Vertical print and drape overlap; cannot confidently separate pleats from pattern.'),
('n','Smooth layered curved panels; jacket covers part of waistband.'),
('U','Crinkled tiered surface cannot confidently distinguish permanent pleating from gathers.'),
('P','Several regular broad waist pleats visible in hanging striped skirt.'),
('n','Smooth flared metallic skirt; handbag obscures central panel.'),
('N','Hanging denim skirt has smooth flared panels with visible seams.')],
28: [
('U','Wrap garment held outward; posed open drape unsuitable for normal full-skirt assessment.'),
('N','Smooth fitted gray mini with surface distressing, waist and hem visible.'),
('U','Seated pose and arms obscure most skirt.'),
('U','Hem outside image; only upper patterned panel visible.'),
('U','Hem outside image and sleeve obscures printed panel.'),
('U','Complex balloon draping and pockets obscure distinction between pleats and gathers.'),
('n','Smooth purple straight skirt; top covers waistband.'),
('n','Smooth red flare held outward; shirt covers waistband.'),
('N','Smooth fitted striped skirt; full waistband and hem visible.')]
}

for page, notes in pages.items():
    sys.argv = ['save_page.py', str(page), json.dumps(notes)]
    runpy.run_path(str(Path(__file__).with_name('save_page.py')), run_name='__main__')
