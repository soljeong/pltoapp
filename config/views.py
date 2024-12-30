from django.http import JsonResponse
from django.shortcuts import render

# Render the homepage
def home(request):

    return render(request, 'home.html')

def result(request):
    user_input = request.POST.get('user_input', '')  # 폼에서 전달된 값
    context = {
        'user_input': user_input,
        'response_message': f"당신이 입력한 값은 '{user_input}'입니다. 더미 답변: 확인되었습니다."
    }
    return render(request, 'result.html', context)