import codecs


class Utf8:
    @staticmethod
    def encode(data):
        return codecs.encode(data, encoding="utf-8")

    @staticmethod
    def decode(data):
        return codecs.decode(data, encoding="utf-8")
