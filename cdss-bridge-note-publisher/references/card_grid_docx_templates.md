# Word Card Grid & Callout Box XML Templates (python-docx)

## 1. Callout Alert Box (Single-Cell Table with Colored Left Border)
```python
def set_callout_style(cell, background_hex="FFF8E1", border_hex="D93025"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    
    # Background fill
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{background_hex}"/>')
    tcPr.append(shd)

    # 3pt solid left accent border (sz="24" is 3pt, 24/8 = 3)
    tcBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_hex}"/>'
        f'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'</w:tblBorders>'
    )
    tcPr.append(tcBorders)
```

## 2. Card Grid (4-Column Native Word Table)
- **Top banner**: Merged across 4 columns, fill `#0A2540`, text bold white Arial 11pt.
- **Card cells**: Fill `#F8FAFC`, hairline borders `#CBD5E1`, internal title bold Arial 9.5pt in sapphire `#1967D2`, body bullets Calibri 8.5pt.
