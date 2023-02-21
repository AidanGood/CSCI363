def load_file(filename):
    "read a file into a list of bytes for packetization"
    with open(filename, 'rb') as f:
        r = f.read()
    return r
