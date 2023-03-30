import pickle


class Serializer:
    @staticmethod
    def _serialize(data):
        if isinstance(data, (bytes, bytearray)):
            return data
        return pickle.dumps(data)

    @staticmethod
    def _deserialize(data):
        if isinstance(data, (bytes, bytearray)) and data.startswith(b'\x80\x04'):
            return pickle.loads(data)
        return None
