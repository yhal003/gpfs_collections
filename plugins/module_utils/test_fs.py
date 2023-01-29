from fs import text2table

def test_empty():
    i = ""
    o = text2table(i)
    assert o == {}

def test_empty_header():
    i = "command:header:HEADER:\n"
    o = text2table(i)
    assert o == {"header": []}

def test_simple_value():
    i = ("command:header:HEADER:key\n"
         "command:header:value")
    o = text2table(i)
    assert o == {"header": [{"key":"value"}]}

def test_two_rows():
    i = ("command:header:HEADER:key\n"
         "command:header:value1\n"
         "command:header:value2\n")
    o = text2table(i)
    assert o == {"header": [{"key": "value1"},
                            {"key": "value2"}]}

def test_two_empty_headers():
    i = ("command:header1:HEADER:k11\n"
         "command:header2:HEADER:k12\n")
    o = text2table(i)
    assert o == {"header1": [], "header2": [] }

def test_two_headers():
    i = ("command:header1:HEADER:k11\n"
         "command:header2:HEADER:k12\n"
         "command:header1:v11\n"
         "command:header2:v12\n")
    o = text2table(i)
    assert o == {"header1": [{"k11": "v11"}],
                 "header2": [{"k12": "v12"}] }

def test_two_headers_two_values():
    i = ("command:header1:HEADER:k11:k21\n"
         "command:header2:HEADER:k12:k22\n"
         "command:header1:v11:v21\n"
         "command:header2:v12:v22\n")
    o = text2table(i)
    assert o == {"header1": [{"k11": "v11", "k21": "v21"}],
                 "header2": [{"k12": "v12", "k22": "v22"}] } 

def test_two_headers_two_values_different_lengths():
    i = ("command:header1:HEADER:k11:k21\n"
         "command:header2:HEADER:k12\n"
         "command:header1:v11:v21\n"
         "command:header2:v12\n")
    o = text2table(i)
    assert o == {"header1": [{"k11": "v11", "k21": "v21"}],
                 "header2": [{"k12": "v12"}] }

def test_headers_without_names():
    i = ("command::HEADER:k1:k2:k3\n"
         "command::v1:v2:v3\n")
    o = text2table(i)
    assert o == {"": [{"k1": "v1", "k2": "v2", "k3": "v3"}]}