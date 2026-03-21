class EDIReader:
    def __init__(self, raw_content: str):
        self.raw_content = raw_content
        self.element_delimiter = None
        self.segment_terminator = None
        self.subelement_delimiter = None

    def bootstrap(self) -> bool:
        if not self.raw_content.startswith("ISA"):
            raise ValueError("File does not begin with ISA — not a valid X12 file")
        
        self.element_delimiter = self.raw_content[3]
        els = self.raw_content.split(self.element_delimiter, 16)
        self.subelement_delimiter = els[16][0]
        self.segment_terminator = els[16][1]
        
        return True

    def get_segments(self) -> list:
        self.bootstrap()
        return [s.strip() for s in self.raw_content.split(self.segment_terminator) if s.strip()]

    def detect_transaction_type(self, segments: list) -> str:
        for seg in segments:
            els = [e.strip() for e in seg.split(self.element_delimiter)]
            if els[0] == "GS":
                if len(els) > 1 and els[1] == "HP": return "835"
                if len(els) > 1 and els[1] == "BE": return "834"
            if els[0] == "BHT" and len(els) > 6:
                if els[6] == "CH": return "837P"
                if els[6] == "RP": return "837I"
        
        # Fallback if BHT06 is missing
        for seg in segments:
            els = [e.strip() for e in seg.split(self.element_delimiter)]
            if els[0] == "ST" and len(els) > 1:
                if els[1] == "837": return "837P"
                elif els[1] == "835": return "835"
                elif els[1] == "834": return "834"

        raise ValueError("Cannot detect transaction type")