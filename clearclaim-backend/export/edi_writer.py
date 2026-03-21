from parser.models import ParsedEDI

def write_edi(parsed: ParsedEDI) -> str:
    lines = []
    ed = parsed.delimiter_element
    st = parsed.delimiter_segment
    for seg in parsed.raw_segments:
        if seg.id == "UNPARSEABLE":
            lines.append(seg.raw_line)
            continue
            
        if seg.id == "ISA":
            # ISA relies on exact column widths. Safest to retain the raw line.
            lines.append(seg.raw_line)
            continue
            
        elements = [seg.id]
        
        max_pos = max((e.position for e in seg.elements), default=0)
        
        pos_map = {}
        for el in seg.elements:
            if el.position not in pos_map:
                pos_map[el.position] = []
            pos_map[el.position].append(el)
            
        for i in range(1, max_pos + 1):
            if i in pos_map:
                els = pos_map[i]
                if len(els) > 1:
                    els.sort(key=lambda x: x.raw_key)
                    val = parsed.delimiter_subelement.join(e.value for e in els)
                    elements.append(val)
                else:
                    elements.append(els[0].value)
            else:
                elements.append("")
        
        lines.append(ed.join(elements) + st)
            
    return "\n".join(lines)