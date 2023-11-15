from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class FanshionReportViewSet(viewsets.ViewSet):
    def list(self, request):
        pass

    def create(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass

    @action(methods=['post'], detail=False)
    def get(self, request):
        pass

    @action(methods=['get'], detail=False)
    def image(self, request):
        pass