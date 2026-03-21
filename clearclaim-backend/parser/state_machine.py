import yaml
import os
from parser.models import ParsedEDI, EDILoop, EDISegment, EDIElement
from parser.edi_reader import EDIReader

class ParserState:
    def __init__(self, loop_defs_path: str):
        with open(loop_defs_path, 'r') as f:
            self.loop_defs = yaml.safe_load(f)
        
        self.current_loop_stack = []
        # ROOT loop initialization
        self.root_loop = EDILoop(loop_id="ROOT", loop_name="Transaction Root", segments=[], children=[])
        self.current_loop_stack.append(self.root_loop)

    def transition(self, segment_id: str, elements: list) -> EDILoop:
        # Search from top of stack downwards to find if segment opens a new child loop
        for i in range(len(self.current_loop_stack)-1, -1, -1):
            active_loop = self.current_loop_stack[i]
            active_def = self._find_def(self.loop_defs, active_loop.loop_id)
            
            if not active_def:
                continue
            
            for child_def in active_def.get("children", []):
                if child_def["opening_segment"] == segment_id:
                    qualifier_match = child_def.get("opening_qualifier")
                    match = True
                    if qualifier_match:
                        pos = qualifier_match["element"] - 1
                        if pos < len(elements) and elements[pos] == qualifier_match["value"]:
                            match = True
                        else:
                            match = False
                    
                    if match:
                        # Pop the stack down to the active parent
                        self.current_loop_stack = self.current_loop_stack[:i+1]
                        
                        new_loop = EDILoop(
                            loop_id=child_def["loop_id"],
                            loop_name=child_def["name"],
                            segments=[],
                            children=[]
                        )
                        self.current_loop_stack[-1].children.append(new_loop)
                        self.current_loop_stack.append(new_loop)
                        return new_loop

        return self.current_loop_stack[-1]
        
    def _find_def(self, current_def, loop_id):
        if current_def["loop_id"] == loop_id:
            return current_def
        for child in current_def.get("children", []):
            res = self._find_def(child, loop_id)
            if res:
                return res
        return None

def parse_edi(raw_content: str) -> ParsedEDI:
    reader = EDIReader(raw_content)
    raw_segments = reader.get_segments()
    transaction_type = reader.detect_transaction_type(raw_segments)
    
    # Load correct grammar
    base_dir = os.path.dirname(__file__)
    grammar_map = {
        "837P": "837p_loops.yaml",
        "837I": "837i_loops.yaml",
        "835": "835_loops.yaml",
        "834": "834_loops.yaml"
    }
    loop_file = grammar_map.get(transaction_type, "837p_loops.yaml")
    state = ParserState(os.path.join(base_dir, "loop_definitions", loop_file))
    
    parsed_segments = []
    sender_id, receiver_id, interchange_date = "", "", ""
    
    if raw_segments:
        isa_els = raw_segments[0].split(reader.element_delimiter)
        if len(isa_els) >= 10:
            sender_id = isa_els[6].strip()
            receiver_id = isa_els[8].strip()
            interchange_date = isa_els[9].strip()

    transaction_set_count = 1
    for seg in reversed(raw_segments):
        els = seg.split(reader.element_delimiter)
        if els[0] == "GE" and len(els) > 1:
            try:
                transaction_set_count = int(els[1])
            except:
                pass
            break

    for line_num, raw_seg in enumerate(raw_segments, 1):
        try:
            els = raw_seg.split(reader.element_delimiter)
            segment_id = els[0]
            elements_data = els[1:]
            
            parsed_elements = []
            for i, val in enumerate(elements_data, 1):
                if reader.subelement_delimiter in val and segment_id not in ("ISA", "GS", "GE", "IEA"):
                    sub_els = val.split(reader.subelement_delimiter)
                    for j, sub_val in enumerate(sub_els, 1):
                        parsed_elements.append(EDIElement(
                            position=i,
                            label=f"{segment_id}0{i}-{j}" if i < 10 else f"{segment_id}{i}-{j}",
                            value=sub_val,
                            raw_key=f"{segment_id}_{i:02d}_{j:02d}"
                        ))
                else:
                    parsed_elements.append(EDIElement(
                        position=i,
                        label=f"{segment_id}0{i}" if i < 10 else f"{segment_id}{i}",
                        value=val,
                        raw_key=f"{segment_id}_{i:02d}"
                    ))
            
            active_loop = state.transition(segment_id, elements_data)
            
            parsed_seg = EDISegment(
                id=segment_id,
                loop_id=active_loop.loop_id if active_loop else "ROOT",
                elements=parsed_elements,
                raw_line=raw_seg,
                line_number=line_num
            )
            parsed_segments.append(parsed_seg)
            if active_loop:
                active_loop.segments.append(parsed_seg)
                
        except Exception as e:
            parsed_segments.append(EDISegment(
                id="UNPARSEABLE", loop_id="UNKNOWN",
                elements=[], raw_line=raw_seg, line_number=line_num
            ))

    return ParsedEDI(
        file_name="parsed.edi",
        transaction_type=transaction_type,
        sender_id=sender_id,
        receiver_id=receiver_id,
        interchange_date=interchange_date,
        transaction_set_count=transaction_set_count,
        delimiter_segment=reader.segment_terminator,
        delimiter_element=reader.element_delimiter,
        delimiter_subelement=reader.subelement_delimiter,
        loops=state.root_loop.children,
        raw_segments=parsed_segments
    )