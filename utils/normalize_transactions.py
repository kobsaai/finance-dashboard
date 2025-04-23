import re

def parse_transaction(text: str) -> dict:
    if is_paypal_transaction(text):
        return parse_paypal_text(text)

    return parse_standard_transaction(text)

def is_paypal_transaction(text: str) -> bool:
    return 'PayPal Europe' in text or 'PayPal (Europe)' in text

def parse_standard_transaction(text: str) -> dict:
    """

    :param text: _description_
    :type text: str
    :return: _description_
    :rtype: dict
    """
    result = {}

    auftraggeber_match = re.search(r"Auftraggeber:\s*(.+?)\s*(Buchungstext:|$)", text)
    empfaenger_match = re.search(r"Empfänger:\s*(.+?)\s*(Kto/IBAN:|Buchungstext:|$)", text)

    if auftraggeber_match:
        result["Wer"] = auftraggeber_match.group(1).strip()
    elif empfaenger_match:
        result["Wer"] = empfaenger_match.group(1).strip()

    buchungstext_match = re.search(r"Buchungstext:\s*(.+)", text)
    if buchungstext_match:
        # Fallback: Versuche ersten sinnvollen Teil als "Wer"
        if "Wer" not in result:
            buchungstext = buchungstext_match.group(1).strip()
            fallback = re.split(r"[,|\.|Ref\.|\n]", buchungstext)[0].strip()
            result["Wer"] = fallback

    ref_match = re.search(r"Ref\.\s*([A-Z0-9\/]+)", text)
    if ref_match:
        result["ref"] = ref_match.group(1).strip()


    return result
def parse_paypal_text(text: str) -> dict:
    """_summary_

    :param text: _description_
    :type text: str
    :return: _description_
    :rtype: dict
    """
    result = {'Wer': 'PayPal'}

    # Extract 
    match_buchungstext = re.search(r"Buchungstext:\s*(.+)", text)
    buchungstext = match_buchungstext.group(1) if match_buchungstext else text

    # Flexibler "Ihr Einkauf bei"-Matcher
    match = re.search(
        r"I\s*?h\s*?r\s*?E\s*?i\s*?n\s*?k\s*?a\s*?u\s*?f\s*?b\s*?e\s*?i\s+(.*)",
        buchungstext,
        re.IGNORECASE,
    )

    if match:
        raw = match.group(1).strip()
        clean = re.split(r"(Ref\.|,|\.|\n)", raw)[0].strip()
        if clean:
            result["Wer"] = clean

    # Referenz extrahieren
    ref_match = re.search(r"Ref\.\s*([A-Z0-9\/]+)", buchungstext)
    if ref_match:
        result["ref"] = ref_match.group(1).strip()


    return result

def parse_buchungstext(text):
    result = {}

    # Auftraggeber oder Empfänger
    auftraggeber_match = re.search(r"Auftraggeber:\s*(.+?)\s*(Buchungstext:|$)", text)
    empfaenger_match = re.search(r"Empfänger:\s*(.+?)\s*(Kto/IBAN:|Buchungstext:|$)", text)
    
    if auftraggeber_match:
        result["Wer"] = auftraggeber_match.group(1).strip()
    if empfaenger_match:
        result["Wer"] = empfaenger_match.group(1).strip()

    # Referenz
    ref_match = re.search(r"Ref\.\s*([A-Z0-9\/]+)", text)
    if ref_match:
        result["ref"] = ref_match.group(1).strip()

    return result

def parse_paypal_text(buchungstext: str) -> dict:
    if 'PayPal Europe' not in buchungstext and 'PayPal (Europe)' not in buchungstext:
        return {}

    result = {'Wer': 'PayPal'}

    # flexibles Pattern für "Ihr Einkauf bei"
    pattern = r"I\s*?h\s*?r\s*?E\s*?i\s*?n\s*?k\s*?a\s*?u\s*?f\s*?b\s*?e\s*?i\s+(.*)"
    match = re.search(pattern, buchungstext, re.IGNORECASE)

    if match:
        händler_raw = match.group(1).strip()
        händler_clean = re.split(r"(Ref\.|,|\.)", händler_raw)[0].strip()
        if händler_clean:
            result['Wer'] = händler_clean

    return result