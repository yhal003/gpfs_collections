def text2table(text):

    headers = {}
    results = {}
    for l in text.split():
        values = l.split(":")
        header_name = values[1]
        if values[2] == "HEADER":
            headers[header_name] = values[3:]
            results[header_name] = []
        else:
            current_header = headers[header_name]
            current_values = values[2:]
            new_row = dict(zip(current_header, current_values))
            results[header_name] += [new_row]

    return results