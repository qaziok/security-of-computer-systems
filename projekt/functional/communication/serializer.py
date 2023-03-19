import pickle


class Serializer:
    @staticmethod
    def _serialize(data):
        if isinstance(data, (bytes, bytearray)):
            return data
        return pickle.dumps(data)

    @staticmethod
    def _deserialize(data):
        if isinstance(data, (bytes, bytearray)):
            return pickle.loads(data)
        return data
