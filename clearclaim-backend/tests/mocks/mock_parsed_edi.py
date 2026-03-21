from parser.models import ParsedEDI

def get_mock_parsed_edi() -> ParsedEDI:
    return ParsedEDI(
        file_name="test.edi",
        transaction_type="837P",
        sender_id="SENDERID",
        receiver_id="RECEIVERID",
        interchange_date="230115",
        transaction_set_count=1,
        delimiter_segment="~",
        delimiter_element="*",
        delimiter_subelement=":",
        loops=[],
        raw_segments=[]
    )