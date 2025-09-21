from rest_framework.response import Response
from rest_framework import serializers

def response(
    status_code: int,
    message: str | list,
    data: any = None,
    error: str = None,
    count_data: int = None
) -> Response:
    response = {
        "statusCode": status_code,
        "message": message
    }

    if error is not None:
        response["error"] = error
    if data is not None:
        response["data"] = data
    if count_data is not None:
        response["countData"] = count_data

    return Response(response, status=status_code)

class StandardResponseSerializerSuccess (serializers.Serializer):
    statusCode = serializers.IntegerField()
    message = serializers.CharField()    
    data = serializers.JSONField(required=False)

class StandardResponseSerializerError (serializers.Serializer):
    statusCode = serializers.IntegerField()
    message = serializers.CharField()
    error = serializers.CharField()

class StandardResponseSerializerSuccessList (serializers.Serializer):
    statusCode = serializers.IntegerField()
    message = serializers.CharField()    
    data = serializers.JSONField(required=False)
    countData = serializers.IntegerField()