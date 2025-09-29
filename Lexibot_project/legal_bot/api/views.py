from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from legal_bot.modules import rag_qa  

class BotQueryAPIView(APIView):
    def post(self, request):
        query = request.data.get("query", "")
        lang = request.data.get("lang", "auto")

        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Process query through your RAG/LLM pipeline
        try:
            answer = rag_qa.get_answer(query, lang)  # <-- your pipeline function
            return Response({"answer": answer})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
