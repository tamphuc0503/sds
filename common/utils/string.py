def split_and_strip(text, separator):
    lines = [text.strip() for text in text.split(separator) if text.strip() != ""]
    return lines
